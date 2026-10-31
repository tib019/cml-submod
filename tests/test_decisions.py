"""Tests für AP7: Kategorie und fünf Entscheidungen (Spec 5.5). Lesen die Quelldateien über pdx."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from tools.pdx import Node, parse_file

ROOT = Path(__file__).resolve().parent.parent
DECISIONS = ROOT / "base/common/decisions/cml_feedback_decisions.txt"
CATEGORIES = ROOT / "base/common/decisions/categories/cml_decision_categories.txt"
WERTE = ROOT / "base/werte.toml"
CATEGORY = "cml_feedback_category"
IDS = [
    "SOV_cml_review_cadres", "SOV_cml_damp_the_feedback", "SOV_cml_workplace_assemblies",
    "SOV_cml_rehabilitation", "SOV_cml_end_the_cult",
]


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


def all_nodes(nodes: list[Node]):
    for n in nodes:
        yield n
        if isinstance(n.value, list):
            yield from all_nodes(n.value)


def category(path: Path, key: str) -> Node:
    for n in parse_file(path):
        if n.key == key:
            return n
    raise AssertionError(f"'{key}' fehlt in {path.name}")


def decision(did: str) -> Node:
    return child(category(DECISIONS, CATEGORY), did)


def find_all(node: Node, key: str) -> list[Node]:
    return [n for n in all_nodes(kids(node)) if n.key == key]


def cmp_nodes(node: Node, key: str) -> list[Node]:
    """check_variable-Blöcke unterhalb von node, deren Kind den Schlüssel trägt."""
    out = []
    for cv in find_all(node, "check_variable"):
        out.extend(c for c in kids(cv) if c.key == key)
    return out


class TestDecisions(unittest.TestCase):
    def test_five_decisions(self) -> None:
        cat = category(DECISIONS, CATEGORY)
        self.assertEqual([c.key for c in kids(cat)], IDS)
        for d in kids(cat):
            ai = child(d, "ai_will_do")
            self.assertEqual(val(child(ai, "base")), "0", d.key)
            for eff in ("complete_effect", "remove_effect"):
                if has_child(d, eff):
                    self.assertTrue(has_child(child(d, eff), "log"), f"{d.key}.{eff} ohne log")
            self.assertTrue(has_child(d, "complete_effect") or has_child(d, "remove_effect"), d.key)

    def test_campaign_decisions_visible_only_while_active(self) -> None:
        for did in IDS[:4]:
            self.assertTrue(has_child(child(decision(did), "visible"), "cml_campaign_active", "yes"), did)

    def test_review_costs_and_timers(self) -> None:
        d = decision("SOV_cml_review_cadres")
        self.assertEqual(val(child(d, "cost")), "@@review_pp@@")
        self.assertEqual(val(child(d, "days_remove")), "@@review_days@@")
        self.assertEqual(val(child(d, "days_re_enable")), "@@review_cooldown@@")
        self.assertTrue(has_child(child(d, "cancel_trigger"), "NOT"))

    def test_review_threshold_formula(self) -> None:
        remove = child(decision("SOV_cml_review_cadres"), "remove_effect")
        rnd = find_all(remove, "set_temp_variable_to_random")
        self.assertEqual(len(rnd), 2, "eine Zufallszahl für das Fehlurteil, eine für die Korruption")
        first = child(rnd[0], "var")
        self.assertEqual(val(first), "cml_roll")
        self.assertEqual(val(child(rnd[0], "min")), "0")
        self.assertEqual(val(child(rnd[0], "max")), "100")
        self.assertEqual(val(child(rnd[0], "integer")), "yes")
        stv = [c for c in find_all(remove, "set_temp_variable") if has_child(c, "cml_wrong_threshold")]
        self.assertEqual(val(child(stv[0], "cml_wrong_threshold")), "SOV_cml_oscillation")
        mul = [c for c in find_all(remove, "multiply_temp_variable") if has_child(c, "cml_wrong_threshold")]
        self.assertEqual(val(child(mul[0], "cml_wrong_threshold")), "@@review_wrong_per_osc@@")
        add = [c for c in find_all(remove, "add_to_temp_variable") if has_child(c, "cml_wrong_threshold")]
        self.assertEqual(val(child(add[0], "cml_wrong_threshold")), "@@review_wrong_base@@")
        # Reihenfolge: Basis zuletzt addiert (Schwelle = osc * pro_osc + basis)
        order = [n.key for n in kids(remove) if n.key in ("set_temp_variable", "multiply_temp_variable", "add_to_temp_variable")]
        self.assertLess(order.index("multiply_temp_variable"), order.index("add_to_temp_variable"))
        cmp = [c for c in cmp_nodes(remove, "cml_roll")]
        self.assertTrue(any(c.op == "<" and val(c) == "cml_wrong_threshold" for c in cmp))
        self.assertTrue(any(c.op == "<" and val(c) == "@@review_hit_corruption_chance@@" for c in cmp_nodes(remove, "cml_roll2")))
        self.assertTrue(find_all(remove, "cml_add_wrongful_verdict"))
        self.assertTrue(find_all(remove, "cml_adapter_reduce_corruption"))
        self.assertTrue(find_all(remove, "else"))

    def test_rehab_visible_at_three(self) -> None:
        d = decision("SOV_cml_rehabilitation")
        vis = child(d, "visible")
        gt = cmp_nodes(vis, "SOV_cml_wrongful_verdicts")
        self.assertTrue(any(c.op == ">" and val(c) == "2" for c in gt))
        sub = find_all(child(d, "complete_effect"), "subtract_from_variable")
        self.assertTrue(any(val(child(s, "SOV_cml_wrongful_verdicts")) == "3" for s in sub))

    def test_end_cult_outlives_campaign(self) -> None:
        d = decision("SOV_cml_end_the_cult")
        vis = child(d, "visible")
        self.assertEqual([(c.key, val(c)) for c in kids(vis)], [("has_country_flag", "SOV_cml_leader_cult")])
        self.assertEqual(val(child(d, "fire_only_once")), "yes")
        eff = child(d, "complete_effect")
        self.assertTrue(any(val(c) == "SOV_cml_leader_cult" for c in find_all(eff, "remove_ideas")))
        self.assertTrue(any(val(c) == "SOV_cml_leader_cult" for c in find_all(eff, "clr_country_flag")))

    def test_category_visibility(self) -> None:
        cat = category(CATEGORIES, CATEGORY)
        self.assertEqual(val(child(cat, "icon")), "GFX_decisions_category_political")
        self.assertTrue(has_child(child(cat, "allowed"), "original_tag", "SOV"))
        vis = child(child(cat, "visible"), "OR")
        flags = {val(c) for c in find_all(vis, "has_country_flag")}
        self.assertEqual(flags, {"SOV_cml_decisions_unlocked", "SOV_cml_leader_cult"})
        self.assertTrue(find_all(vis, "cml_campaign_active"))
        # AP5-Eintrag bleibt erhalten
        self.assertTrue(category(CATEGORIES, "cml_feedback_entry_category"))

    def test_assemblies_treasury_guard_matches_value(self) -> None:
        d = decision("SOV_cml_workplace_assemblies")
        werte = tomllib.loads(WERTE.read_text(encoding="utf-8"))
        self.assertTrue(has_child(child(d, "available"), f"treasury_higher_than_{werte['assemblies_treasury']}", "yes"))
        self.assertTrue(find_all(child(d, "complete_effect"), "cml_adapter_treasury"))
        self.assertEqual(val(child(d, "days_re_enable")), "@@assemblies_cooldown@@")


if __name__ == "__main__":
    unittest.main()
