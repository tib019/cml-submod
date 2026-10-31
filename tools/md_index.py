"""Erzeugt ein ID-Verzeichnis eines Millennium-Dawn-Stands (tools/md_index.json).

Mit --rev wird ausschließlich über git gelesen (Sparse-Checkout-tauglich),
sonst direkt vom Dateisystem. Defekte Dateien werden übersprungen und auf
stderr gemeldet; das Skript bricht nie ab.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.pdx import Node, parse, walk  # noqa: E402

FILE_PREFIXES = ("common/", "events/", "localisation/", "gfx/", "interface/")
EMPTY_BLOB = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
PARSED_PREFIXES = ("common/", "events/", "interface/")
KEYS = (
    "version", "files", "focuses", "ideas", "characters", "scripted_effects",
    "scripted_triggers", "event_namespaces", "sprites", "decision_categories",
    "decisions", "dynamic_modifiers",
)


class _Source:
    def list_files(self) -> list[str]:
        raise NotImplementedError

    def read(self, path: str) -> str:
        raise NotImplementedError

    def prefetch(self, paths: list[str]) -> None:
        pass


class _GitSource(_Source):
    def __init__(self, root: Path, rev: str) -> None:
        self.root, self.rev = root, rev

    def _git(self, *args: str) -> bytes:
        res = subprocess.run(
            ["git", "-c", "gc.auto=0", "-C", str(self.root), *args],
            capture_output=True, check=True,
        )
        return res.stdout

    def list_files(self) -> list[str]:
        out = self._git("ls-tree", "-r", "--name-only", "-z", self.rev)
        return [p.decode("utf-8", "replace") for p in out.split(b"\0") if p]

    def read(self, path: str) -> str:
        return self._git("show", f"{self.rev}:{path}").decode("utf-8", "replace")

    def prefetch(self, paths: list[str]) -> None:
        """Holt fehlende Blobs eines partiellen Klons gebündelt (statt einzeln je git show)."""
        wanted = set(paths)
        out = self._git("ls-tree", "-r", "-z", "--format=%(objectname) %(path)", self.rev)
        oids: list[str] = []
        oids_seen: set[str] = set()
        for entry in out.split(b"\0"):
            oid, _, path = entry.decode("utf-8", "replace").partition(" ")
            if path in wanted and oid not in oids_seen and oid != EMPTY_BLOB:
                oids_seen.add(oid)
                oids.append(oid)
        for i in range(0, len(oids), 400):
            try:
                self._git("fetch", "origin", "--no-tags", "--no-write-fetch-head", *oids[i:i + 400])
            except subprocess.CalledProcessError as exc:
                tail = exc.stderr.decode("utf-8", "replace").strip()[-200:]
                print(f"Vorabladen fehlgeschlagen (Block {i}): {tail}", file=sys.stderr)
            except OSError as exc:
                print(f"Vorabladen fehlgeschlagen (Block {i}): {exc}", file=sys.stderr)


class _FsSource(_Source):
    def __init__(self, root: Path) -> None:
        self.root = root

    def list_files(self) -> list[str]:
        return [p.relative_to(self.root).as_posix()
                for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts]

    def read(self, path: str) -> str:
        return (self.root / path).read_bytes().decode("utf-8", "replace")


def _blocks(nodes: list[Node]) -> list[Node]:
    return [n for n in nodes if n.key and isinstance(n.value, list)]


def _scalar(node: Node) -> str:
    return node.value.strip('"') if isinstance(node.value, str) else ""


def build_index(md_root: Path, rev: str | None) -> dict:
    src: _Source = _GitSource(Path(md_root), rev) if rev else _FsSource(Path(md_root))
    all_files = sorted(src.list_files())
    sets: dict[str, set[str]] = {k: set() for k in KEYS if k not in ("version", "files")}
    version = ""

    def load(path: str) -> list[Node] | None:
        try:
            return parse(src.read(path))
        except Exception as exc:  # noqa: BLE001 - robust gegen jede Dateiart
            print(f"übersprungen: {path}: {exc}", file=sys.stderr)
            return None

    src.prefetch([f for f in all_files
                  if f == "descriptor.mod" or (f.startswith(PARSED_PREFIXES) and f.endswith((".txt", ".gfx")))])

    def under(prefix: str, ext: str) -> list[str]:
        return [f for f in all_files if f.startswith(prefix) and f.endswith(ext)]

    for f in under("common/scripted_effects/", ".txt"):
        if (nodes := load(f)) is not None:
            sets["scripted_effects"].update(n.key for n in _blocks(nodes))
    for f in under("common/scripted_triggers/", ".txt"):
        if (nodes := load(f)) is not None:
            sets["scripted_triggers"].update(n.key for n in _blocks(nodes))
    for f in under("common/dynamic_modifiers/", ".txt"):
        if (nodes := load(f)) is not None:
            sets["dynamic_modifiers"].update(n.key for n in _blocks(nodes))
    for f in under("common/ideas/", ".txt"):
        if (nodes := load(f)) is not None:
            for top in _blocks(nodes):
                if top.key == "ideas":
                    for cat in _blocks(top.value):
                        sets["ideas"].update(n.key for n in _blocks(cat.value))
    for f in under("common/characters/", ".txt"):
        if (nodes := load(f)) is not None:
            for top in _blocks(nodes):
                if top.key == "characters":
                    sets["characters"].update(n.key for n in _blocks(top.value))
    for f in under("common/national_focus/", ".txt"):
        if (nodes := load(f)) is not None:
            for n in walk(nodes):
                if n.key in ("focus", "shared_focus") and isinstance(n.value, list):
                    for kid in n.value:
                        if kid.key == "id" and isinstance(kid.value, str):
                            sets["focuses"].add(_scalar(kid))
    for f in under("common/decisions/categories/", ".txt"):
        if (nodes := load(f)) is not None:
            sets["decision_categories"].update(n.key for n in _blocks(nodes))
    for f in under("common/decisions/", ".txt"):
        if f.startswith("common/decisions/categories/"):
            continue
        if (nodes := load(f)) is not None:
            for cat in _blocks(nodes):
                sets["decisions"].update(n.key for n in _blocks(cat.value))
    for f in under("events/", ".txt"):
        if (nodes := load(f)) is not None:
            for n in walk(nodes):
                if n.key in ("namespace", "add_namespace") and isinstance(n.value, str):
                    sets["event_namespaces"].add(_scalar(n))
    for f in under("interface/", ".gfx"):
        if (nodes := load(f)) is not None:
            for n in walk(nodes):
                if n.key.lower().endswith("spritetype") and isinstance(n.value, list):
                    for kid in n.value:
                        if kid.key == "name" and isinstance(kid.value, str):
                            sets["sprites"].add(_scalar(kid))
    if "descriptor.mod" in all_files and (nodes := load("descriptor.mod")) is not None:
        for n in nodes:
            if n.key == "version" and isinstance(n.value, str):
                version = _scalar(n)

    index: dict = {"version": version,
                   "files": [f for f in all_files if f.startswith(FILE_PREFIXES)]}
    for k in KEYS:
        if k not in index:
            index[k] = sorted(sets[k])
    return {k: index[k] for k in KEYS}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("md_root", type=Path)
    ap.add_argument("--rev", default=None, help="git-Revision (z. B. v2.0.3), liest nur über git")
    ap.add_argument("--out", type=Path, default=Path("tools/md_index.json"))
    args = ap.parse_args(argv)
    index = build_index(args.md_root, args.rev)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("{\n")
        items = []
        for k, v in index.items():
            if isinstance(v, list):
                body = ",\n".join("  " + json.dumps(x, ensure_ascii=False) for x in v)
                items.append(f'"{k}": [\n{body}\n]' if v else f'"{k}": []')
            else:
                items.append(f'"{k}": {json.dumps(v, ensure_ascii=False)}')
        fh.write(",\n".join(items) + "\n}\n")
    print({k: (len(v) if isinstance(v, list) else v) for k, v in index.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
