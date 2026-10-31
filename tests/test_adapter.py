"""Tests für die MD-Adapter (Spec 4.1, 11). Lesen die Quelldateien in md/ über tools.pdx."""
import unittest
from pathlib import Path

from tools import check
from tools.pdx import Node, parse_file, walk

ROOT = Path(__file__).resolve().parent.parent
EFFECTS = ROOT / "md/common/scripted_effects/cml_adapter_md_effects.txt"
TRIGGERS = ROOT / "md/common/scripted_triggers/cml_adapter_md_triggers.txt"


def top(path: Path) -> dict[str, Node]:
    return {n.key: n for n in parse_file(path)}


def all_defs() -> dict[str, Node]:
    out: dict[str, Node] = {}
    for p in (EFFECTS, TRIGGERS):
        if p.exists():
            out.update(top(p))
    return out


def find(node: Node, key: str) -> list[Node]:
    return [n for n in walk(node.value) if n.key == key] if isinstance(node.value, list) else []


def val(n: Node) -> str:
    v = n.value
    return v.strip('"') if isinstance(v, str) else ""


class AdapterTest(unittest.TestCase):
    def test_all_adapters_defined(self) -> None:
        defs = all_defs()
        for name in check.ADAPTER_NAMES:
            self.assertIn(name, defs, name)

    def test_entry_visible_names_forks(self) -> None:
        t = all_defs()["cml_adapter_entry_visible"]
        focuses = {val(n) for n in find(t, "has_completed_focus")}
        for f in ("SOV_zyuganov", "SOV_communist_party_dominance",
                  "SOV_honor_gorbachevs_legacy", "SOV_national_patriotic_alliance"):
            self.assertIn(f, focuses)
        flags = {val(n) for n in find(t, "has_country_flag")}
        self.assertIn("SOV_cml_path", flags)

    def test_entry_blocked_and_in_power(self) -> None:
        defs = all_defs()
        blocked = {val(n) for n in find(defs["cml_adapter_entry_blocked"], "has_completed_focus")}
        self.assertEqual(blocked, {"SOV_communist_party_dominance", "SOV_honor_gorbachevs_legacy",
                                   "SOV_national_patriotic_alliance"})
        power = {n.key for n in walk(defs["cml_adapter_cml_in_power"].value)}
        self.assertIn("emerging_communist_state_are_in_power", power)
        self.assertIn("neutrality_neutral_communism_are_in_power", power)

    def test_leader_ideology(self) -> None:
        e = all_defs()["cml_adapter_install_leader"]
        leaders = find(e, "create_country_leader")
        self.assertEqual(len(leaders), 1)
        kids = {c.key: val(c) for c in leaders[0].value if isinstance(c.value, str)}
        self.assertEqual(kids["ideology"], "communist_state")
        self.assertEqual(kids["name"], "Darja Wolnowa")
        self.assertEqual(kids["picture"], "GFX_portrait_generic_europe_female_01")

    def test_treasury_uses_md_effect(self) -> None:
        e = all_defs()["cml_adapter_treasury"]
        sets = [n for n in find(e, "set_temp_variable")]
        self.assertTrue(any(c.key == "treasury_change" and val(c) == "cml_treasury_change"
                            for s in sets for c in s.value))
        self.assertTrue(any(val(n) == "yes" for n in find(e, "modify_treasury_effect")))

    def test_opinion_adapters_call_md(self) -> None:
        defs = all_defs()
        for adapter, md in (("cml_adapter_cadres_opinion", "change_communist_cadres_opinion"),
                            ("cml_adapter_unions_opinion", "change_labour_unions_opinion"),
                            ("cml_adapter_siloviki_opinion", "change_intelligence_community_opinion")):
            calls = find(defs[adapter], md)
            self.assertEqual(len(calls), 1, adapter)
            self.assertEqual(val(calls[0]), "yes")

    def test_every_effect_logs(self) -> None:
        defs = all_defs()
        for name in check.ADAPTER_NAMES:
            if "entry" in name or name == "cml_adapter_cml_in_power":
                continue
            logs = [val(n) for n in find(defs[name], "log")]
            self.assertTrue(any(name in l for l in logs), name)


if __name__ == "__main__":
    unittest.main()
