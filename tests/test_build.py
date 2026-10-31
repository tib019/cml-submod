import tempfile
import unittest
from pathlib import Path

from tools import build

REPO = Path(__file__).resolve().parent.parent
BOM = "﻿"


class TestRender(unittest.TestCase):
    def test_render_replaces(self):
        self.assertEqual(build.render("a = @@x@@", {"x": 5}), "a = 5")
        self.assertEqual(build.render("a = @@x@@", {"x": 0.05}), "a = 0.05")

    def test_render_sign_kept(self):
        self.assertEqual(build.render("v = @@x@@", {"x": -3}), "v = -3")
        self.assertEqual(build.render("v = @@x@@", {"x": -0.05}), "v = -0.05")

    def test_render_int_without_point(self):
        out = build.render("@@a@@ @@b@@", {"a": 20, "b": 0.5})
        self.assertEqual(out, "20 0.5")

    def test_render_unknown_raises(self):
        with self.assertRaises(KeyError):
            build.render("a = @@y@@", {"x": 1})

    def test_render_without_placeholder_unchanged(self):
        self.assertEqual(build.render("a = 1 # @ @", {}), "a = 1 # @ @")


class TestLoadValues(unittest.TestCase):
    def test_load_values_real_file(self):
        v = build.load_values(REPO / "base" / "werte.toml")
        self.assertEqual(v["entry_pp"], 50)
        self.assertIsInstance(v["entry_pp"], int)
        self.assertEqual(v["f2_stab"], 0.02)
        self.assertEqual(v["e1_b_osc"], -3)
        self.assertEqual(v["e2_b_stab"], -0.05)
        self.assertEqual(v["threshold_13"], 100)
        self.assertEqual(v["e4_delay_days"], 10)

    def test_all_spec6_and_event_keys_present(self):
        v = build.load_values(REPO / "base" / "werte.toml")
        spec6 = """entry_pp entry_days event2_delay_days base_start osc_start monthly_base
        monthly_osc monthly_osc_amplified amplify_duration_days f2_cost f2_base f2_osc f2_stab
        f3_cost f3_cadres f3_base f3_osc f4_cost f4_treasury f4_stab f4_osc unions_after_swap
        f5_cost f5_siloviki f5_base f5_osc f5_pp f5_event_chance spirit_feedback_stab
        spirit_feedback_pp spirit_feedback_drift_def spirit_feedback_comm_drift spirit_dc_stab
        spirit_dc_pp spirit_exhausted_days spirit_exhausted_stab spirit_exhausted_factory
        spirit_exhausted_pp spirit_cult_stab f6_cost f6_base f6_osc_reduce f6_cadres f7_cost
        f8a_cost f8a_osc_max f8a_base f8b_cost f8b_base f8b_osc review_pp review_days
        review_cooldown review_wrong_base review_wrong_per_osc review_hit_base review_hit_cadres
        review_hit_corruption_chance review_wrong_osc review_wrong_stab damp_pp damp_cooldown
        damp_osc damp_base assemblies_treasury assemblies_cooldown assemblies_base assemblies_osc
        assemblies_unions rehab_pp rehab_base rehab_osc endcult_pp endcult_stab endcult_base
        spirit_standstill_days spirit_standstill_factory spirit_standstill_cg""".split()
        events = """e1_a_base e1_a_osc e1_b_osc e1_b_pp e2_a_stab e2_a_base e2_b_base e2_b_stab
        e3_a_base e3_a_osc e3_b_pp e3_b_osc e4_a_treasury e4_a_opinion e4_b_treasury e4_b_stab
        e5_a_osc e5_a_stab e5_a_siloviki e5_b_pp e5_b_siloviki e5_b_base e10_a_pp e10_a_osc
        e10_b_base e10_b_osc e11_a_base e11_a_osc e11_a_stab e11_b_osc e12_a_base e13_a_stab
        e20_a_base e4_delay_days threshold_10 threshold_11 threshold_12 threshold_13""".split()
        missing = [k for k in spec6 + events if k not in v]
        self.assertEqual(missing, [])
        self.assertEqual(len(spec6), 78)

    def test_spec6_positive_costs_stay_positive(self):
        v = build.load_values(REPO / "base" / "werte.toml")
        for k in ("f2_stab", "f3_cadres", "f4_stab", "f5_siloviki", "f6_osc_reduce",
                  "damp_osc", "endcult_stab", "spirit_feedback_stab"):
            self.assertGreater(v[k], 0, k)


class TestBuild(unittest.TestCase):
    def _mini_repo(self, root: Path) -> None:
        (root / "base" / "common").mkdir(parents=True)
        (root / "base" / "localisation" / "german").mkdir(parents=True)
        (root / "md" / "common").mkdir(parents=True)
        (root / "base" / "werte.toml").write_text("x = 5\ny = 0.05\n", encoding="utf-8")
        (root / "base" / "common" / "cml_a.txt").write_text("a = @@x@@\n", encoding="utf-8")
        (root / "base" / "localisation" / "german" / "cml_t_l_german.yml").write_bytes(
            (BOM + 'l_german:\n k:0 "Wert @@y@@"\n').encode("utf-8"))
        (root / "md" / "common" / "cml_b.txt").write_text("b = @@y@@\n", encoding="utf-8")
        (root / "md" / "descriptor.mod").write_text(
            'version="0.1.0"\nname="Test"\n', encoding="utf-8")

    def test_build_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            out = Path(d) / "dist"
            self._mini_repo(root)
            build.build(root, out)
            self.assertTrue((out / "cml_md" / "descriptor.mod").is_file())
            self.assertTrue((out / "cml_md.mod").is_file())
            self.assertFalse((out / "cml_md" / "werte.toml").exists())
            self.assertIn('path="mod/cml_md"', (out / "cml_md.mod").read_text(encoding="utf-8"))
            self.assertEqual((out / "cml_md" / "common" / "cml_a.txt").read_text(), "a = 5\n")
            self.assertEqual((out / "cml_md" / "common" / "cml_b.txt").read_text(), "b = 0.05\n")

    def test_build_yml_keeps_bom_and_renders(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            out = Path(d) / "dist"
            self._mini_repo(root)
            build.build(root, out)
            raw = (out / "cml_md" / "localisation" / "german" / "cml_t_l_german.yml").read_bytes()
            self.assertTrue(raw.startswith(BOM.encode("utf-8")))
            self.assertIn("Wert 0.05", raw.decode("utf-8"))

    def test_build_twice_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            out = Path(d) / "dist"
            self._mini_repo(root)
            build.build(root, out)
            (out / "cml_md" / "stale.txt").write_text("x")
            build.build(root, out)
            self.assertFalse((out / "cml_md" / "stale.txt").exists())

    def test_build_unknown_placeholder_raises(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            self._mini_repo(root)
            (root / "base" / "common" / "cml_a.txt").write_text("a = @@nope@@\n")
            with self.assertRaises(KeyError):
                build.build(root, Path(d) / "dist")


class TestDescriptor(unittest.TestCase):
    def test_descriptor_content(self):
        text = (REPO / "md" / "descriptor.mod").read_text(encoding="utf-8")
        self.assertIn('version="0.1.0"', text)
        self.assertIn('"Millennium Dawn: Developer Version"', text)
        self.assertIn('"Millennium Dawn: A Modern Day Mod"', text)
        self.assertIn('supported_version="1.19.*"', text)
        self.assertIn('"Alternative History"', text)
        self.assertIn('"National Focuses"', text)


if __name__ == "__main__":
    unittest.main()
