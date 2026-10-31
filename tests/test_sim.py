import unittest
from pathlib import Path

from tools import build, sim

REPO = Path(__file__).resolve().parent.parent


def values() -> dict:
    return build.load_values(REPO / "base" / "werte.toml")


class TestClamp(unittest.TestCase):
    def test_clamp(self):
        s = sim.State(base=2, osc=98, wrong=0, month=0, fired=set(), ended=False)
        sim.add_osc(s, 10)
        sim.add_base(s, -5)
        self.assertEqual(s.osc, 100)
        self.assertEqual(s.base, 0)

    def test_clamp_upper_base_lower_osc(self):
        s = sim.State(base=99, osc=3, wrong=0, month=0, fired=set(), ended=False)
        sim.add_base(s, 50)
        sim.add_osc(s, -50)
        self.assertEqual((s.base, s.osc), (100, 0))


class TestPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = values()

    def test_nothing_path_months(self):
        r = sim.simulate("nichts", self.v)
        self.assertGreaterEqual(r.months, 34)
        self.assertLessEqual(r.months, 50)
        self.assertIn(13, r.fired)

    def test_nothing_path_events(self):
        r = sim.simulate("nichts", self.v)
        for n in (1, 2, 10, 11, 12):
            self.assertIn(n, r.fired)

    def test_clean_path_values_in_range(self):
        r = sim.simulate("sauber", self.v)
        self.assertTrue(0 <= r.base_end <= 100)
        self.assertTrue(0 <= r.osc_before_close <= 100)
        self.assertGreater(r.months, 0)

    def test_clean_path_fires_no_high_events(self):
        r = sim.simulate("sauber", self.v)
        for n in (1, 2, 3, 4):
            self.assertIn(n, r.fired)
        self.assertFalse(r.fired & {11, 12, 13})

    def test_radical_has_threshold_events(self):
        r = sim.simulate("radikal", self.v)
        self.assertTrue({10, 11} <= r.fired)

    def test_unknown_path_raises(self):
        with self.assertRaises(KeyError):
            sim.simulate("gibtsnicht", self.v)

    def test_thresholds_fire_once(self):
        # hoeherer Monatswert darf Schwellenereignisse nicht doppelt ausloesen
        v = dict(self.v)
        v["monthly_osc"] = 30
        r = sim.simulate("nichts", v)
        self.assertEqual(sorted(r.fired & {10, 11, 12, 13}), [10, 11, 12, 13])

    def test_jump_fires_only_highest(self):
        sm = sim._Sim(sim.PATHS["nichts"], dict(self.v))
        sm.s.osc = self.v["threshold_12"]
        sm.thresholds()
        self.assertEqual(sm.s.fired, {12})
        self.assertEqual(sm.s.flags, {10, 11, 12})
        sm.thresholds()
        self.assertEqual(sm.s.fired, {12})

    def test_input_values_not_mutated(self):
        v = dict(self.v)
        before = dict(v)
        sim.simulate("sauber", v)
        self.assertEqual(v, before)


class TestTargets(unittest.TestCase):
    def test_targets_with_spec_values(self):
        v = values()
        results = {p: sim.simulate(p, v) for p in ("sauber", "radikal", "nichts")}
        self.assertEqual(sim.check_targets(results), [])

    def test_check_targets_reports_miss(self):
        r = sim.Result(base_end=10, osc_before_close=90, months=1, fired={11},
                       reached_event20=False, base_max=10)
        res = {"sauber": r, "radikal": r, "nichts": r}
        self.assertGreaterEqual(len(sim.check_targets(res)), 3)


if __name__ == "__main__":
    unittest.main()
