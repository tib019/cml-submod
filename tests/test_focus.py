"""Tests für AP6: Fokusbaum cml_russia_focus (Spec 5.3 und 11)."""
from __future__ import annotations

import unittest
from pathlib import Path

from tests.test_core import all_nodes, child, has_child, kids, val
from tools.pdx import Node, parse_file

ROOT = Path(__file__).resolve().parent.parent
FOCUS_FILE = ROOT / "base/common/national_focus/cml_russia_focus.txt"

IDS = {
    "2": "SOV_cml_open_channels",
    "3": "SOV_cml_cadres_before_the_base",
    "4": "SOV_cml_cut_oligarch_ties",
    "5": "SOV_cml_untie_siloviki",
    "6": "SOV_cml_new_cadres",
    "7": "SOV_cml_centre_replies",
    "8a": "SOV_cml_close_the_loop",
    "8b": "SOV_cml_amplify_the_feedback",
}
POS = {"2": (4, 0), "3": (8, 0), "4": (6, 1), "5": (10, 1), "6": (7, 2), "7": (7, 3), "8a": (5, 4), "8b": (9, 4)}


def tree() -> Node:
    for n in parse_file(FOCUS_FILE):
        if n.key == "focus_tree":
            return n
    raise AssertionError("focus_tree fehlt")


def focuses() -> dict[str, Node]:
    out: dict[str, Node] = {}
    for n in kids(tree()):
        if n.key == "focus":
            out[val(child(n, "id"))] = n
    return out


def focus(nr: str) -> Node:
    return focuses()[IDS[nr]]


def reward(nr: str) -> list[Node]:
    return kids(child(focus(nr), "completion_reward"))


def reward_keys(nr: str) -> list[str]:
    return [c.key for c in reward(nr)]


def index_of(nr: str, key: str, value: str | None = None) -> int:
    for i, c in enumerate(reward(nr)):
        if c.key == key and (value is None or (isinstance(c.value, str) and val(c) == value)):
            return i
    raise AssertionError(f"{key} {value} fehlt in Fokus {nr}")


class TestTree(unittest.TestCase):
    def test_eight_focuses(self) -> None:
        self.assertEqual(sorted(focuses()), sorted(IDS.values()))

    def test_tree_not_default(self) -> None:
        t = tree()
        self.assertEqual(val(child(t, "id")), "cml_russia_focus")
        self.assertEqual(val(child(child(t, "country"), "factor")), "0")
        self.assertEqual(val(child(t, "default")), "no")

    def test_positions_and_costs(self) -> None:
        for nr, (x, y) in POS.items():
            f = focus(nr)
            self.assertEqual(val(child(f, "x")), str(x), nr)
            self.assertEqual(val(child(f, "y")), str(y), nr)
            key = "f" + nr + "_cost"
            self.assertEqual(val(child(f, "cost")), f"@@{key}@@", nr)

    def test_ai_zero(self) -> None:
        for nr in IDS:
            self.assertEqual(val(child(child(focus(nr), "ai_will_do"), "base")), "0", nr)

    def test_available(self) -> None:
        for nr in IDS:
            av = child(focus(nr), "available")
            self.assertTrue(has_child(av, "cml_adapter_cml_in_power", "yes"), nr)
            self.assertTrue(has_child(av, "has_country_flag", "SOV_cml_path"), nr)

    def test_log_first_and_icon(self) -> None:
        for nr, fid in IDS.items():
            first = reward(nr)[0]
            self.assertEqual(first.key, "log", nr)
            self.assertIn(f"Focus {fid}", val(first), nr)
            self.assertTrue(has_child(focus(nr), "icon"), nr)

    def test_prereq_f1_chain(self) -> None:
        for nr in ("4", "5"):
            pre = [c for c in kids(focus(nr)) if c.key == "prerequisite"]
            self.assertEqual(len(pre), 1)
            self.assertTrue(has_child(pre[0], "focus", IDS["3"]))
        for nr, p in (("7", "6"), ("8a", "7"), ("8b", "7")):
            pre = [c for c in kids(focus(nr)) if c.key == "prerequisite"]
            self.assertEqual(len(pre), 1, nr)
            self.assertTrue(has_child(pre[0], "focus", IDS[p]), nr)

    def test_prereq_f6(self) -> None:
        pre = [c for c in kids(focus("6")) if c.key == "prerequisite"]
        self.assertEqual(len(pre), 2)
        singles = [p for p in pre if [val(c) for c in kids(p)] == [IDS["2"]]]
        self.assertEqual(len(singles), 1)
        either = [p for p in pre if p is not singles[0]][0]
        self.assertEqual(sorted(val(c) for c in kids(either)), sorted([IDS["4"], IDS["5"]]))
        self.assertTrue(all(c.key == "focus" for c in kids(either)))

    def test_mutual_8a_8b(self) -> None:
        a = child(focus("8a"), "mutually_exclusive")
        b = child(focus("8b"), "mutually_exclusive")
        self.assertTrue(has_child(a, "focus", IDS["8b"]))
        self.assertTrue(has_child(b, "focus", IDS["8a"]))

    def test_f8_not_after_phase1(self) -> None:
        for k in ("8a", "8b"):
            av = child(focuses()[IDS[k]], "available")
            negs = [n for n in kids(av) if n.key == "NOT" and has_child(n, "has_country_flag", "SOV_cml_phase1_done")]
            self.assertEqual(len(negs), 1, k)

    def test_f8a_osc_gate(self) -> None:
        av = child(focus("8a"), "available")
        cv = child(av, "check_variable")
        self.assertEqual(cv.value[0].key, "SOV_cml_oscillation")
        self.assertEqual(cv.value[0].op, "<")
        self.assertEqual(val(cv.value[0]), "@@f8a_osc_max@@")


class TestRewards(unittest.TestCase):
    def test_f2(self) -> None:
        self.assertTrue(has_child(child(focus("2"), "completion_reward"), "set_country_flag", "SOV_cml_decisions_unlocked"))

    def test_f6_flag(self) -> None:
        self.assertTrue(has_child(child(focus("6"), "completion_reward"), "set_country_flag", "SOV_cml_cadre_school_discount"))

    def test_f8a_ends_campaign_after_base(self) -> None:
        self.assertLess(index_of("8a", "cml_add_party_base", "yes"), index_of("8a", "cml_end_campaign", "yes"))

    def test_f8b_flag_before_osc(self) -> None:
        self.assertLess(index_of("8b", "set_country_flag", "SOV_cml_amplified"),
                        index_of("8b", "cml_add_oscillation", "yes"))

    def test_treasury_set_before_call(self) -> None:
        keys = reward_keys("4")
        i_set = next(i for i, c in enumerate(reward("4")) if c.key == "set_temp_variable" and has_child(c, "cml_treasury_change"))
        self.assertLess(i_set, index_of("4", "cml_adapter_treasury", "yes"))
        self.assertIn("cml_adapter_purge_oligarchs", keys)

    def test_events(self) -> None:
        def ev(nr: str) -> list[Node]:
            return [n for n, _ in all_nodes(reward(nr)) if n.key == "country_event"]
        self.assertEqual([val(child(e, "id")) for e in ev("3")], ["sov_cml.3"])
        e4 = ev("4")
        self.assertEqual(val(child(e4[0], "id")), "sov_cml.4")
        self.assertEqual(val(child(e4[0], "days")), "@@e4_delay_days@@")
        self.assertEqual([val(child(e, "id")) for e in ev("6") + ev("7")], ["sov_cml.6"])
        e5 = ev("5")
        self.assertEqual(val(child(e5[0], "id")), "sov_cml.5")

    def test_f5_chance(self) -> None:
        text = FOCUS_FILE.read_text(encoding="utf-8")
        self.assertIn("@@f5_event_chance@@", text)
        self.assertIn("set_temp_variable_to_random", text)

    def test_no_raw_negative_placeholders(self) -> None:
        self.assertNotIn("-@@", FOCUS_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
