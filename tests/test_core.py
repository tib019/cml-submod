"""Tests für AP5: Kern (Einstieg, Effekte, Trigger, Monatsschleife). Lesen die Quelldateien über pdx."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.pdx import Node, parse_file

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "base"
ENTRY = BASE / "common/decisions/cml_entry_decisions.txt"
EFFECTS = BASE / "common/scripted_effects/cml_effects.txt"
LOOP = BASE / "events/cml_sov_loop_events.txt"
ENTRY_ID = "SOV_cml_signal_to_the_centre"


def val(n: Node) -> str:
    assert isinstance(n.value, str), f"Block statt Wert: {n.key}"
    v = n.value
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v


def kids(n: Node) -> list[Node]:
    return n.value if isinstance(n.value, list) else []


def child(n: Node, key: str) -> Node:
    for c in kids(n):
        if c.key == key:
            return c
    raise AssertionError(f"'{key}' fehlt in '{n.key}'")


def has_child(n: Node, key: str, value: str | None = None) -> bool:
    return any(c.key == key and (value is None or (isinstance(c.value, str) and val(c) == value)) for c in kids(n))


def all_nodes(nodes: list[Node], anc: tuple[Node, ...] = ()):
    for n in nodes:
        yield n, anc
        if isinstance(n.value, list):
            yield from all_nodes(n.value, anc + (n,))


def top(path: Path, key: str) -> Node:
    for n in parse_file(path):
        if n.key == key:
            return n
    raise AssertionError(f"'{key}' fehlt in {path.name}")


def effect(name: str) -> Node:
    return top(EFFECTS, name)


def entry_decision() -> Node:
    cat = top(ENTRY, "cml_feedback_entry_category")
    return child(cat, ENTRY_ID)


def event(eid: str) -> Node:
    for n in parse_file(LOOP):
        if n.key == "country_event" and has_child(n, "id", eid):
            return n
    raise AssertionError(f"Ereignis {eid} fehlt")


class TestEntry(unittest.TestCase):
    def test_entry_cancel_and_guard(self) -> None:
        d = entry_decision()
        self.assertTrue(has_child(child(d, "cancel_trigger"), "cml_adapter_entry_blocked", "yes"))
        remove = child(d, "remove_effect")
        top_level = kids(remove)
        self.assertTrue(top_level)
        for c in top_level:
            self.assertEqual(c.key, "if", "alles im remove_effect muss im Wächter-if stehen")
        guard = top_level[0]
        limit = child(guard, "limit")
        neg = child(limit, "NOT")
        self.assertTrue(has_child(neg, "cml_adapter_entry_blocked", "yes"))
        trees = [n for n, _ in all_nodes(kids(remove)) if n.key == "load_focus_tree"]
        self.assertEqual(len(trees), 1)
        self.assertEqual(val(child(trees[0], "tree")), "cml_russia_focus")
        self.assertTrue(any(n is trees[0] for n, _ in all_nodes(kids(guard))))

    def test_entry_costs(self) -> None:
        d = entry_decision()
        self.assertEqual(val(child(d, "cost")), "@@entry_pp@@")
        self.assertEqual(val(child(d, "days_remove")), "@@entry_days@@")
        self.assertEqual(val(child(d, "fire_only_once")), "yes")
        self.assertEqual(val(child(child(d, "ai_will_do"), "base")), "0")
        self.assertTrue(has_child(child(d, "available"), "cml_adapter_cml_in_power", "yes"))

    def test_entry_order(self) -> None:
        guard = kids(child(entry_decision(), "remove_effect"))[0]
        body = [c for c in kids(guard) if c.key != "limit"]
        keys = [(c.key, val(c) if isinstance(c.value, str) else None) for c in body]
        marks = [
            ("set_country_flag", "SOV_cml_path"),
            ("set_variable", None),
            ("add_dynamic_modifier", None),
            ("set_country_flag", "SOV_cml_campaign_active"),
            ("cml_adapter_install_cadres", "yes"),
            ("cml_adapter_rename_party", "yes"),
            ("load_focus_tree", None),
            ("country_event", None),
        ]
        pos = -1
        for k, v in marks:
            nxt = next((i for i, kv in enumerate(keys) if i > pos and kv[0] == k and (v is None or kv[1] == v)), None)
            self.assertIsNotNone(nxt, f"Reihenfolge verletzt bei {k} {v}")
            pos = nxt  # type: ignore[assignment]
        starts = [c for c in body if c.key == "set_variable"]
        self.assertEqual(len(starts), 3)
        ev = [c for c in body if c.key == "country_event"]
        ids = [val(child(c, "id")) for c in ev]
        self.assertEqual(ids, ["sov_cml.1", "sov_cml.2", "sov_cml.100"])
        self.assertEqual(val(child(ev[1], "days")), "@@event2_delay_days@@")
        self.assertEqual(val(child(ev[2], "days")), "30")


class TestEffects(unittest.TestCase):
    def test_add_effects_clamp(self) -> None:
        for name, var in (("cml_add_party_base", "SOV_cml_party_base"), ("cml_add_oscillation", "SOV_cml_oscillation")):
            e = effect(name)
            clamps = [n for n, _ in all_nodes(kids(e)) if n.key == "clamp_variable"]
            self.assertEqual(len(clamps), 1, name)
            self.assertEqual(val(child(clamps[0], "var")), var)
            self.assertEqual(val(child(clamps[0], "min")), "0")
            self.assertEqual(val(child(clamps[0], "max")), "100")
            self.assertTrue(has_child(e, "cml_check_thresholds", "yes"), name)
            adds = [n for n in kids(e) if n.key == "add_to_variable"]
            self.assertTrue(any(has_child(a, var, "cml_delta") for a in adds), name)
            order = [c.key for c in kids(e)]
            self.assertLess(order.index("clamp_variable"), order.index("cml_check_thresholds"))

    def test_wrongful_verdict(self) -> None:
        e = effect("cml_add_wrongful_verdict")
        add = child(e, "add_to_variable")
        self.assertEqual(val(child(add, "SOV_cml_wrongful_verdicts")), "1")

    def _threshold_branches(self) -> list[Node]:
        return [c for c in kids(effect("cml_check_thresholds")) if c.key == "if"]

    def test_thresholds_once(self) -> None:
        branches = self._threshold_branches()
        fired = set()
        for b in branches:
            limit = child(b, "limit")
            self.assertTrue(has_child(limit, "cml_campaign_active", "yes"))
            negs = [n for n in kids(limit) if n.key == "NOT" and any(
                c.key == "has_country_flag" and val(c).endswith("_fired") for c in kids(n))]
            self.assertEqual(len(negs), 1)
            flag = val(child(negs[0], "has_country_flag"))
            self.assertRegex(flag, r"^SOV_cml_threshold_(10|11|12|13|20)_fired$")
            self.assertTrue(has_child(b, "set_country_flag", flag), flag)
            fired.add(flag)
        self.assertEqual(fired, {f"SOV_cml_threshold_{n}_fired" for n in (10, 11, 12, 13, 20)})

    def test_threshold_routing(self) -> None:
        by_event: dict[str, Node] = {}
        for b in self._threshold_branches():
            for c in kids(b):
                if c.key == "country_event":
                    by_event[val(child(c, "id"))] = b
        for n in (10, 11, 12):
            lim = child(by_event[f"sov_cml.{n}"], "limit")
            chk = child(lim, "check_variable")
            self.assertEqual(chk.value[0].key, "SOV_cml_oscillation")  # type: ignore[index]
            self.assertEqual(chk.value[0].op, ">=")  # type: ignore[index]
            self.assertEqual(val(chk.value[0]), f"@@threshold_{n}@@")  # type: ignore[index]
        for eid, amplified in (("sov_cml.20", True), ("sov_cml.13", False)):
            lim = child(by_event[eid], "limit")
            chk = child(lim, "check_variable")
            self.assertEqual(val(chk.value[0]), "@@threshold_13@@")  # type: ignore[index]
            self.assertEqual(chk.value[0].op, ">=")  # type: ignore[index]
            if amplified:
                self.assertTrue(has_child(lim, "has_country_flag", "SOV_cml_amplified"))
            else:
                negs = [n for n in kids(lim) if n.key == "NOT" and has_child(n, "has_country_flag", "SOV_cml_amplified")]
                self.assertEqual(len(negs), 1)
        self.assertIsNot(by_event["sov_cml.13"], by_event["sov_cml.20"])

    def test_end_campaign(self) -> None:
        e = effect("cml_end_campaign")
        allk = [(n.key, n) for n, _ in all_nodes(kids(e))]
        rm = [n for k, n in allk if k == "remove_dynamic_modifier"]
        self.assertEqual(val(child(rm[0], "modifier")), "SOV_cml_feedback_modifier")
        self.assertTrue(has_child(e, "clr_country_flag", "SOV_cml_campaign_active"))
        self.assertTrue(has_child(e, "set_country_flag", "SOV_cml_phase1_done"))
        self.assertTrue(has_child(e, "add_ideas", "SOV_cml_democratic_centralism"))
        zero = [n for n in kids(e) if n.key == "set_variable" and has_child(n, "SOV_cml_oscillation", "0")]
        self.assertEqual(len(zero), 1)

    def test_collapse(self) -> None:
        e = effect("cml_collapse")
        mv = child(e, "multiply_variable")
        self.assertEqual(val(child(mv, "var")), "SOV_cml_party_base")
        self.assertEqual(val(child(mv, "value")), "0.5")
        self.assertEqual(val(child(e, "add_stability")), "@@e13_a_stab@@")
        ti = child(e, "add_timed_idea")
        self.assertEqual(val(child(ti, "idea")), "SOV_cml_exhausted_movement")
        self.assertEqual(val(child(ti, "days")), "@@spirit_exhausted_days@@")
        self.assertTrue(has_child(e, "cml_end_campaign", "yes"))

    def test_trigger_campaign_active(self) -> None:
        t = top(BASE / "common/scripted_triggers/cml_triggers.txt", "cml_campaign_active")
        self.assertTrue(has_child(t, "has_country_flag", "SOV_cml_campaign_active"))


class TestLoop(unittest.TestCase):
    def test_loop_event_hidden(self) -> None:
        ev = event("sov_cml.100")
        self.assertEqual(val(child(ev, "hidden")), "yes")
        self.assertEqual(val(child(ev, "is_triggered_only")), "yes")

    def test_monthly_loop_single(self) -> None:
        calls = []
        for p in sorted(BASE.rglob("*.txt")):
            for n, anc in all_nodes(parse_file(p)):
                if n.key == "country_event" and anc and isinstance(n.value, list) and has_child(n, "id", "sov_cml.100"):
                    calls.append((p, n, anc))
        files = sorted(p.name for p, _, _ in calls)
        self.assertEqual(files, ["cml_entry_decisions.txt", "cml_sov_loop_events.txt"])
        for p, n, anc in calls:
            if p.name == "cml_sov_loop_events.txt":
                guards = [a for a in anc if a.key == "if" and has_child(child(a, "limit"), "cml_campaign_active", "yes")]
                self.assertTrue(guards, "Selbstaufruf nur innerhalb von if cml_campaign_active")
                self.assertTrue(has_child(n, "days", "30"))
        ev = event("sov_cml.100")
        ifs = [c for c in kids(child(ev, "immediate")) if c.key == "if"]
        self.assertEqual(len(ifs), 1)
        self.assertTrue(has_child(child(ifs[0], "limit"), "cml_campaign_active", "yes"))
        self.assertEqual([c.key for c in kids(child(ev, "immediate"))], ["if"], "nichts außerhalb des if")

    def test_loop_uses_helpers_and_values(self) -> None:
        ev = event("sov_cml.100")
        text = {n.key for n, _ in all_nodes(kids(ev))}
        self.assertIn("cml_add_party_base", text)
        self.assertIn("cml_add_oscillation", text)
        vals = {val(n) for n, _ in all_nodes(kids(ev)) if isinstance(n.value, str)}
        for w in ("@@monthly_base@@", "@@monthly_osc@@", "@@monthly_osc_amplified@@", "@@amplify_duration_days@@"):
            self.assertIn(w, vals)


if __name__ == "__main__":
    unittest.main()
