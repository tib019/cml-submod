"""Prüfskript (Spec 8.2): Struktur, IDs gegen das MD-Verzeichnis, Lokalisierung. Nur Standardbibliothek."""
from __future__ import annotations

import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.pdx import Node, PdxSyntaxError, parse  # noqa: E402

ADAPTER_NAMES = [
    "cml_adapter_entry_visible", "cml_adapter_entry_blocked", "cml_adapter_cml_in_power",
    "cml_adapter_install_cadres", "cml_adapter_purge_oligarchs", "cml_adapter_cadres_opinion",
    "cml_adapter_unions_opinion", "cml_adapter_siloviki_opinion", "cml_adapter_reduce_corruption",
    "cml_adapter_treasury", "cml_adapter_install_leader", "cml_adapter_rename_party",
]

OWN_PREFIXES = ("cml_", "SOV_cml_")
NAMESPACE_PREFIXES = ("cml_", "SOV_cml_", "sov_cml")
EVENT_KEYS = {"country_event", "news_event", "state_event", "unit_leader_event", "operative_leader_event"}
SET_VARS = {
    "set_variable", "add_to_variable", "subtract_from_variable", "multiply_variable",
    "divide_variable", "set_temp_variable", "set_temp_variable_to_random", "clamp_variable",
}
PLACEHOLDER = re.compile(r"@@([A-Za-z0-9_.]+)@@")
LOC_KEY = re.compile(r"^\s+([A-Za-z0-9_.]+):\d*\s+\"")
LOC_VAR = re.compile(r"\[\?([^\]|]+)")
TOOLS_DIR = Path(__file__).resolve().parent


@dataclass
class Finding:
    rule: int
    path: str
    line: int
    msg: str


def format_finding(f: Finding) -> str:
    return f"{f.path}:{f.line}: [R{f.rule}] {f.msg}"


def load_word_list(path: Path) -> set[str]:
    out: set[str] = set()
    if not Path(path).exists():
        return out
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        word = line.split("#", 1)[0].strip()
        if word:
            out.add(word)
    return out


def sv(node: Node) -> str | None:
    """Skalarer Wert ohne Anführungszeichen, None bei Blöcken."""
    if isinstance(node.value, list):
        return None
    v = node.value
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v


def blocks(node: Node) -> list[Node]:
    return [c for c in node.value if isinstance(c.value, list)] if isinstance(node.value, list) else []


def iter_nodes(nodes: list[Node], parents: tuple[str, ...] = ()) -> Iterator[tuple[Node, tuple[str, ...]]]:
    for n in nodes:
        yield n, parents
        if isinstance(n.value, list):
            yield from iter_nodes(n.value, parents + (n.key,))


def norm_var(name: str) -> str:
    return name.split(".")[-1].split(":")[-1]


def is_own_var(name: str) -> bool:
    return norm_var(name).startswith(OWN_PREFIXES)


def line_of(text: str, pattern: str) -> int:
    m = re.search(pattern, text, re.M)
    return text.count("\n", 0, m.start()) + 1 if m else 0


class Checker:
    def __init__(self, root: Path, index: dict, keywords: set[str], allow: set[str]) -> None:
        self.root = root
        self.idx = {k: set(v) for k, v in index.items() if isinstance(v, list)}
        self.idx_files = set(index.get("files", []))
        self.keywords = keywords
        self.allow = allow
        self.findings: list[Finding] = []
        self.files: dict[str, str] = {}      # relativer Pfad -> Text
        self.trees: dict[str, list[Node]] = {}
        # eigene Definitionen: Art -> {id: (pfad, zeile)}
        self.defs: dict[str, dict[str, tuple[str, int]]] = {
            k: {} for k in ("focus", "idea", "character", "effect", "trigger", "decision", "category",
                            "modifier", "event", "tree", "sprite")
        }
        self.namespaces: set[str] = set()
        self.focus_info: dict[str, tuple[str, int, list[str], list[str]]] = {}

    def add(self, rule: int, path: str, line: int, msg: str) -> None:
        self.findings.append(Finding(rule, path, line, msg))

    # ---- Laden -------------------------------------------------------
    def load(self) -> None:
        for top in ("base", "md"):
            d = self.root / top
            if not d.is_dir():
                continue
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    rel = p.relative_to(self.root).as_posix()
                    self.files[rel] = p.read_bytes().decode("utf-8", errors="replace").lstrip("﻿")

    @staticmethod
    def sub(rel: str) -> str:
        return rel.split("/", 1)[1]

    def parse_all(self, values: dict | None) -> None:
        for rel, text in self.files.items():
            if not rel.endswith(".txt"):
                continue
            src = PLACEHOLDER.sub("0", text)
            try:
                self.trees[rel] = parse(src)
            except PdxSyntaxError as e:
                self.add(1, rel, e.line, e.msg)

    # ---- Definitionen sammeln (Regel 4 + Grundlage für 3/6/7/9) -------
    def define(self, kind: str, ident: str, rel: str, line: int, prefixes=OWN_PREFIXES) -> None:
        if not ident.startswith(prefixes):
            self.add(4, rel, line, f"{kind}-ID '{ident}' ohne Präfix cml_/SOV_cml_")
        elif kind != "event" and ident in self.idx_for(kind):
            self.add(4, rel, line, f"{kind}-ID '{ident}' kollidiert mit MD-ID")
        if ident in self.defs[kind]:
            p, l = self.defs[kind][ident]
            self.add(4, rel, line, f"{kind}-ID '{ident}' doppelt definiert (zuerst {p}:{l})")
        else:
            self.defs[kind][ident] = (rel, line)

    def idx_for(self, kind: str) -> set[str]:
        key = {"focus": "focuses", "idea": "ideas", "character": "characters", "effect": "scripted_effects",
               "trigger": "scripted_triggers", "decision": "decisions", "category": "decision_categories",
               "modifier": "dynamic_modifiers", "sprite": "sprites"}.get(kind)
        return self.idx.get(key, set()) if key else set()

    def collect(self) -> None:
        for rel, nodes in self.trees.items():
            s = self.sub(rel)
            if s.startswith("common/national_focus/"):
                for n in nodes:
                    if n.key == "focus_tree" and isinstance(n.value, list):
                        for c in n.value:
                            if c.key == "id" and sv(c):
                                self.define("tree", sv(c), rel, c.line)
                        for f in blocks(n):
                            if f.key in ("focus", "shared_focus"):
                                self.collect_focus(f, rel)
                    elif n.key == "shared_focus" and isinstance(n.value, list):
                        self.collect_focus(n, rel)
            elif s.startswith("common/ideas/"):
                for n in nodes:
                    if n.key == "ideas":
                        for cat in blocks(n):
                            for idea in blocks(cat):
                                self.define("idea", idea.key, rel, idea.line)
            elif s.startswith("common/characters/"):
                for n in nodes:
                    if n.key == "characters":
                        for ch in blocks(n):
                            self.define("character", ch.key, rel, ch.line)
            elif s.startswith("common/scripted_effects/"):
                for n in blocks_of(nodes):
                    self.define("effect", n.key, rel, n.line)
            elif s.startswith("common/scripted_triggers/"):
                for n in blocks_of(nodes):
                    self.define("trigger", n.key, rel, n.line)
            elif s.startswith("common/decisions/categories/"):
                for n in blocks_of(nodes):
                    self.define("category", n.key, rel, n.line)
            elif s.startswith("common/decisions/"):
                for cat in blocks_of(nodes):
                    for d in blocks(cat):
                        self.define("decision", d.key, rel, d.line)
            elif s.startswith("common/dynamic_modifiers/"):
                for n in blocks_of(nodes):
                    self.define("modifier", n.key, rel, n.line)
            elif s.startswith("events/"):
                for n in nodes:
                    if n.key == "add_namespace" and sv(n):
                        self.namespaces.add(sv(n))
                        if not sv(n).startswith(NAMESPACE_PREFIXES):
                            self.add(4, rel, n.line, f"Namespace '{sv(n)}' ohne Präfix cml_/SOV_cml_/sov_cml")
                    elif n.key in EVENT_KEYS and isinstance(n.value, list):
                        for c in n.value:
                            if c.key == "id" and sv(c):
                                self.define("event", sv(c), rel, c.line, NAMESPACE_PREFIXES)
        for rel, text in self.files.items():
            if rel.endswith(".gfx") and self.sub(rel).startswith("interface/"):
                for m in re.finditer(r'name\s*=\s*"([^"]+)"', text):
                    self.defs["sprite"].setdefault(m.group(1), (rel, text.count("\n", 0, m.start()) + 1))

    def collect_focus(self, f: Node, rel: str) -> None:
        fid, prereq, mutex = None, [], []
        for c in f.value:
            if c.key == "id" and sv(c):
                fid = sv(c)
                self.define("focus", fid, rel, c.line)
            elif c.key == "prerequisite" and isinstance(c.value, list):
                prereq += [(sv(x), x.line) for x in c.value if x.key == "focus" and sv(x)]
            elif c.key == "mutually_exclusive" and isinstance(c.value, list):
                mutex += [(sv(x), x.line) for x in c.value if x.key == "focus" and sv(x)]
        if fid:
            self.focus_info[fid] = (rel, f.line, prereq, mutex)  # type: ignore[assignment]

    # ---- bekannt? ------------------------------------------------------
    def known(self, kind: str, ident: str) -> bool:
        return ident in self.defs[kind] or ident in self.idx_for(kind) or ident in self.allow

    # ---- Regel 2 -------------------------------------------------------
    def rule2(self) -> None:
        wpath = self.root / "base" / "werte.toml"
        if not wpath.is_file():
            return
        try:
            values = tomllib.loads(wpath.read_text(encoding="utf-8-sig"))
        except tomllib.TOMLDecodeError as e:
            self.add(2, "base/werte.toml", 0, f"werte.toml nicht lesbar: {e}")
            return
        used: set[str] = set()
        for rel, text in self.files.items():
            if rel.endswith("werte.toml") or not rel.endswith((".txt", ".yml", ".mod", ".gfx")):
                continue
            for no, line in enumerate(text.splitlines(), 1):
                for m in PLACEHOLDER.finditer(line):
                    used.add(m.group(1))
                    if m.group(1) not in values:
                        self.add(2, rel, no, f"Platzhalter @@{m.group(1)}@@ steht nicht in werte.toml")
        wtext = wpath.read_text(encoding="utf-8-sig")
        for k in values:
            if k not in used:
                self.add(2, "base/werte.toml", line_of(wtext, rf"^\s*{re.escape(k)}\s*="), f"Wert '{k}' wird nirgends genutzt")

    # ---- Regel 3 / 6 / 7 / 8 über den Syntaxbaum -----------------------
    def sprite_ok(self, cands: set[str]) -> bool:
        sprites = self.idx.get("sprites", set())
        return any(c in sprites or c in self.defs["sprite"] or c in self.allow for c in cands)

    def check_ref(self, kind: str, ident: str | None, rel: str, line: int) -> None:
        if ident and not self.known(kind, ident):
            self.add(3, rel, line, f"unbekannte {kind}-ID '{ident}'")

    def id_list(self, n: Node) -> list[tuple[str, int]]:
        """Werte eines Aufrufs: skalar, Liste ohne Schlüssel oder Block mit idea/id/character."""
        if not isinstance(n.value, list):
            return [(sv(n), n.line)]  # type: ignore[list-item]
        out = []
        for c in n.value:
            if not isinstance(c.value, list) and (c.key == "" or c.key in ("idea", "id", "character")):
                out.append((sv(c), c.line))
        return out  # type: ignore[return-value]

    def rule_tree(self) -> None:
        reads: list[tuple[str, str, int]] = []
        sets: set[str] = set()
        for rel, nodes in self.trees.items():
            s = self.sub(rel)
            for n, parents in iter_nodes(nodes):
                v = sv(n)
                parent = parents[-1] if parents else ""
                depth = len(parents)
                key = n.key
                # --- Regel 3: Aufrufe
                if key == "has_completed_focus" or key in ("complete_national_focus", "unlock_national_focus"):
                    for i, l in self.id_list(n):
                        self.check_ref("focus", i, rel, l)
                elif key in ("has_idea", "add_ideas", "remove_ideas"):
                    for i, l in self.id_list(n):
                        self.check_ref("idea", i, rel, l)
                elif key == "swap_ideas" and isinstance(n.value, list):
                    for c in n.value:
                        if c.key in ("add_idea", "remove_idea"):
                            self.check_ref("idea", sv(c), rel, c.line)
                elif key == "add_timed_idea" and isinstance(n.value, list):
                    for c in n.value:
                        if c.key == "idea":
                            self.check_ref("idea", sv(c), rel, c.line)
                elif key == "promote_character":
                    for i, l in self.id_list(n):
                        self.check_ref("character", i, rel, l)
                elif key in ("add_dynamic_modifier", "remove_dynamic_modifier") and isinstance(n.value, list):
                    for c in n.value:
                        if c.key == "modifier":
                            self.check_ref("modifier", sv(c), rel, c.line)
                elif key == "load_focus_tree":
                    tree = sv(n) if v is not None else next((sv(c) for c in n.value if c.key == "tree"), None)
                    if tree and tree.startswith(OWN_PREFIXES) and tree not in self.defs["tree"] and tree not in self.allow:
                        self.add(3, rel, n.line, f"unbekannter Fokusbaum '{tree}'")
                elif key == "icon" and v is not None:
                    self.rule_icon(s, v, rel, n.line)
                elif key == "picture" and v is not None:
                    self.rule_picture(s, parent, depth, v, rel, n.line)
                elif v == "yes" and key and not key.startswith("@"):
                    self.rule_yes(key, rel, n.line)
                # --- Regel 6: Voraussetzungen (nur Existenz hier, Seitigkeit separat)
                # --- Regel 7: Ereignisaufrufe
                if key in EVENT_KEYS and depth > 0:
                    eid = v if v is not None else next((sv(c) for c in n.value if c.key == "id"), None)
                    if eid:
                        self.check_event(eid, rel, n.line)
                # --- Regel 8: Variablen
                self.collect_vars(n, rel, reads, sets)
        # Textverweise [?var]
        for rel, text in self.files.items():
            if rel.endswith((".yml", ".txt")):
                for no, line in enumerate(text.splitlines(), 1):
                    for m in LOC_VAR.finditer(line):
                        if is_own_var(m.group(1).strip()):
                            reads.append((norm_var(m.group(1).strip()), rel, no))
        for name, rel, line in reads:
            if name not in sets:
                self.add(8, rel, line, f"Variable '{name}' wird gelesen, aber nirgends gesetzt")

    def collect_vars(self, n: Node, rel: str, reads: list, sets: set) -> None:
        if not isinstance(n.value, list):
            return
        if n.key in SET_VARS:
            for c in n.value:
                cv = sv(c)
                if c.key == "var":
                    if cv and is_own_var(cv):
                        sets.add(norm_var(cv))
                    continue
                if c.key and is_own_var(c.key):
                    sets.add(norm_var(c.key))
                if cv and is_own_var(cv):
                    reads.append((norm_var(cv), rel, c.line))
        elif n.key == "check_variable":
            for c in n.value:
                cv = sv(c)
                if c.key == "var":
                    if cv and is_own_var(cv):
                        reads.append((norm_var(cv), rel, c.line))
                    continue
                if c.key and is_own_var(c.key):
                    reads.append((norm_var(c.key), rel, c.line))
                if cv and is_own_var(cv):
                    reads.append((norm_var(cv), rel, c.line))

    def rule_icon(self, s: str, x: str, rel: str, line: int) -> None:
        if s.startswith("common/national_focus/"):
            cands = {x, "GFX_" + x}
        elif s.startswith(("common/dynamic_modifiers/", "common/decisions/")):
            cands = {x, "GFX_" + x, "GFX_decision_" + x, "GFX_decision_category_" + x}
        else:
            return
        if not self.sprite_ok(cands):
            self.add(3, rel, line, f"unbekanntes Sprite '{x}' (icon)")

    def rule_picture(self, s: str, parent: str, depth: int, x: str, rel: str, line: int) -> None:
        if parent == "create_country_leader":
            if not (x.endswith(".dds") or self.sprite_ok({x})):
                self.add(3, rel, line, f"unbekanntes Sprite '{x}' (Führerporträt)")
        elif s.startswith("common/ideas/"):
            if not self.sprite_ok({"GFX_idea_" + x}):
                self.add(3, rel, line, f"unbekanntes Sprite 'GFX_idea_{x}' (picture '{x}')")
        elif s.startswith("events/") and parent in EVENT_KEYS and depth == 1:
            if not self.sprite_ok({x, "GFX_" + x}):
                self.add(3, rel, line, f"unbekanntes Sprite '{x}' (Ereignisbild)")

    def rule_yes(self, key: str, rel: str, line: int) -> None:
        if key.startswith(OWN_PREFIXES):
            if key not in self.defs["effect"] and key not in self.defs["trigger"] and key not in self.allow:
                self.add(3, rel, line, f"unbekannter eigener scripted effect/trigger '{key}'")
        elif not (key in self.idx.get("scripted_effects", ()) or key in self.idx.get("scripted_triggers", ())
                  or key in self.keywords or key in self.allow):
            self.add(3, rel, line, f"unbekannter Aufruf '{key} = yes' (weder MD noch Engine-Schlüsselwort)")

    def check_event(self, eid: str, rel: str, line: int) -> None:
        ns = eid.rsplit(".", 1)[0]
        if eid in self.allow:
            return
        if ns in self.namespaces:
            if eid not in self.defs["event"]:
                self.add(7, rel, line, f"Ereignis '{eid}' ist nicht definiert")
        elif ns not in self.idx.get("event_namespaces", ()):
            self.add(7, rel, line, f"Ereignis '{eid}': Namespace '{ns}' unbekannt")

    # ---- Regel 6 -------------------------------------------------------
    def rule6(self) -> None:
        for fid, (rel, line, prereq, mutex) in self.focus_info.items():
            for x, l in prereq:
                if not self.known("focus", x):
                    self.add(6, rel, l, f"Voraussetzung auf unbekannten Fokus '{x}' (in {fid})")
            for x, l in mutex:
                if not self.known("focus", x):
                    self.add(6, rel, l, f"Ausschluss auf unbekannten Fokus '{x}' (in {fid})")
                elif x in self.focus_info and fid not in [m for m, _ in self.focus_info[x][3]]:
                    self.add(6, rel, l, f"einseitiger Ausschluss: {fid} schließt {x} aus, aber nicht umgekehrt")

    # ---- Regel 5 -------------------------------------------------------
    def rule5(self) -> None:
        for rel in self.files:
            if self.sub(rel) in self.idx_files:
                self.add(5, rel, 0, "Pfad gleicht einer MD-Datei (v2.0.3) und würde sie überschreiben")

    # ---- Regel 9 -------------------------------------------------------
    def rule9(self) -> None:
        keys: dict[str, dict[str, tuple[str, int]]] = {"german": {}, "english": {}}
        for rel, text in self.files.items():
            if not rel.endswith(".yml"):
                continue
            m = re.search(r"/localisation/(german|english)/", rel)
            if not m:
                continue
            lang = m.group(1)
            raw = (self.root / rel).read_bytes()
            if not raw.startswith(b"\xef\xbb\xbf"):
                self.add(9, rel, 1, "Lokalisierungsdatei ist nicht UTF-8 mit BOM")
            lines = text.splitlines()
            head = next((l.strip() for l in lines if l.strip() and not l.strip().startswith("#")), "")
            if head != f"l_{lang}:":
                self.add(9, rel, 1, f"falsche Kopfzeile '{head}', erwartet 'l_{lang}:'")
            for no, l in enumerate(lines, 1):
                km = LOC_KEY.match(l)
                if km:
                    keys[lang].setdefault(km.group(1), (rel, no))
        for a, b in (("german", "english"), ("english", "german")):
            for k, (rel, no) in keys[a].items():
                if k not in keys[b]:
                    self.add(9, rel, no, f"Schlüssel '{k}' nur in {a}, fehlt in {b}")
        have = keys["german"]
        need: list[tuple[str, str, int]] = []
        for fid, (rel, line, _, _) in self.focus_info.items():
            need += [(fid, rel, line), (fid + "_desc", rel, line)]
        for kind in ("idea", "category"):
            need += [(i, p, l) for i, (p, l) in self.defs[kind].items()]
        for i, (p, l) in self.defs["decision"].items():
            need += [(i, p, l), (i + "_desc", p, l)]
        for rel, nodes in self.trees.items():
            if self.sub(rel).startswith("events/"):
                for n in nodes:
                    if n.key in EVENT_KEYS and isinstance(n.value, list):
                        need += self.event_keys(n, rel)
        seen: set[str] = set()
        for k, rel, line in need:
            if k not in have and k not in seen:
                seen.add(k)
                self.add(9, rel, line, f"Lokalisierungsschlüssel '{k}' fehlt")

    def event_keys(self, ev: Node, rel: str) -> list[tuple[str, str, int]]:
        out = []
        for c in ev.value:
            if c.key in ("title", "desc") and sv(c):
                out.append((sv(c), rel, c.line))
            elif c.key == "desc" and isinstance(c.value, list):
                out += [(sv(t), rel, t.line) for t in c.value if t.key == "text" and sv(t)]
            elif c.key == "option" and isinstance(c.value, list):
                out += [(sv(t), rel, t.line) for t in c.value if t.key == "name" and sv(t)]
        return out

    # ---- Regel 10 ------------------------------------------------------
    def rule10(self) -> None:
        defined: set[str] = set()
        for rel, nodes in self.trees.items():
            if rel.startswith("md/") and self.sub(rel).startswith(("common/scripted_effects/", "common/scripted_triggers/")):
                defined |= {n.key for n in blocks_of(nodes)}
        for name in ADAPTER_NAMES:
            if name not in defined:
                self.add(10, "md", 0, f"Adapter '{name}' ist in md/ nicht definiert")


def blocks_of(nodes: list[Node]) -> list[Node]:
    return [n for n in nodes if isinstance(n.value, list) and n.key and not n.key.startswith("@")]


def check(repo_root: Path, index: dict, engine_keywords: set[str] | None = None,
          allowlist: set[str] | None = None) -> list[Finding]:
    root = Path(repo_root)
    kw = load_word_list(TOOLS_DIR / "engine_keywords.txt") if engine_keywords is None else set(engine_keywords)
    al = load_word_list(TOOLS_DIR / "vanilla_allowlist.txt") if allowlist is None else set(allowlist)
    c = Checker(root, index, kw, al)
    c.load()
    c.parse_all(None)
    c.collect()
    c.rule2()
    c.rule_tree()
    c.rule5()
    c.rule6()
    c.rule9()
    c.rule10()
    return sorted(c.findings, key=lambda f: (f.path, f.line, f.rule, f.msg))


def main() -> int:
    root = TOOLS_DIR.parent
    index = json.loads((TOOLS_DIR / "md_index.json").read_text(encoding="utf-8"))
    findings = check(root, index)
    for f in findings:
        print(format_finding(f))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
