"""Tests für AP8: Ereignisse (sov_cml.1-6, 10-13, 20) und Meinungsmodifikator."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tools.pdx import Node, parse_file

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "base/events/cml_sov_events.txt"
OPINION = ROOT / "base/common/opinion_modifiers/cml_opinion_modifiers.txt"
LOC_DE = ROOT / "base/localisation/german/cml_events_l_german.yml"
LOC_EN = ROOT / "base/localisation/english/cml_events_l_english.yml"
IDS = [1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 20]
ALLOWED_NUMBER_KEYS = {"id", "days", "random_days"}


def kids(n: Node) -> list[Node]:
    return n.value if isinstance(n.value, list) else []


def events() -> dict[str, Node]:
    out = {}
    for n in parse_file(EVENTS):
        if n.key == "country_event":
            for c in kids(n):
                if c.key == "id":
                    out[c.value] = n
    return out


def options(ev: Node) -> list[Node]:
    return [c for c in kids(ev) if c.key == "option"]


def walk(n: Node):
    yield n
    for c in kids(n):
        yield from walk(c)


def calls(n: Node, name: str) -> bool:
    return any(x.key == name and x.value == "yes" for x in walk(n))


class EventTests(unittest.TestCase):
    def test_event_ids(self) -> None:
        evs = events()
        for i in IDS:
            self.assertIn(f"sov_cml.{i}", evs)
            ev = evs[f"sov_cml.{i}"]
            self.assertTrue(any(c.key == "is_triggered_only" and c.value == "yes" for c in kids(ev)), i)
        self.assertEqual(len(evs), len(IDS))

    def test_option_counts(self) -> None:
        for i, ev in ((i, events()[f"sov_cml.{i}"]) for i in IDS):
            self.assertEqual(len(options(ev)), 1 if i in (6, 12, 13) else 2, f"Ereignis {i}")

    def test_collapse_used(self) -> None:
        evs = events()
        self.assertTrue(calls(evs["sov_cml.13"], "cml_collapse"))
        opt_b = options(evs["sov_cml.20"])[1]
        self.assertTrue(calls(opt_b, "cml_collapse"))
        self.assertFalse(calls(options(evs["sov_cml.20"])[0], "cml_collapse"))
        self.assertTrue(calls(options(evs["sov_cml.20"])[0], "cml_end_campaign"))

    def test_no_raw_numbers(self) -> None:
        num = re.compile(r"^-?\d+(\.\d+)?$")
        for eid, ev in events().items():
            for opt in options(ev):
                for n in walk(opt):
                    if isinstance(n.value, str) and num.match(n.value) and n.key not in ALLOWED_NUMBER_KEYS:
                        self.assertIn(n.value, ("0", "1"), f"{eid}: {n.key} = {n.value}")

    def test_no_fired_flags_set_by_events(self) -> None:
        text = EVENTS.read_text(encoding="utf-8")
        self.assertNotIn("_fired", text)

    def test_event2_has_picture(self) -> None:
        pic = [c.value for c in kids(events()["sov_cml.2"]) if c.key == "picture"]
        self.assertEqual(len(pic), 1)
        self.assertRegex(pic[0], r"^GFX_report_event_")
        self.assertIn(pic[0], json.loads((ROOT / "tools/md_index.json").read_text(encoding="utf-8"))["sprites"])

    def test_capital_controls_localised(self) -> None:
        for path in (LOC_DE, LOC_EN):
            text = path.read_text(encoding="utf-8-sig")
            self.assertRegex(text, r"(?m)^ cml_capital_controls:\d* \"", path.name)

    def test_capital_controls(self) -> None:
        mod = [n for n in parse_file(OPINION)][0]
        self.assertEqual(mod.key, "opinion_modifiers")
        m = [c for c in kids(mod) if c.key == "cml_capital_controls"][0]
        self.assertTrue(any(c.key == "value" and c.value == "@@e4_a_opinion@@" for c in kids(m)))
        opt_a = options(events()["sov_cml.4"])[0]
        targets = {c.value for n in walk(opt_a) if n.key == "add_opinion_modifier"
                   for c in kids(n) if c.key == "target"}
        self.assertEqual(targets, {"USA", "ENG", "FRA", "GER"})

    def test_loc_keys_both_languages(self) -> None:
        for path in (LOC_DE, LOC_EN):
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"), path.name)
            text = path.read_text(encoding="utf-8-sig")
            for i in IDS:
                keys = [f"sov_cml.{i}.t", f"sov_cml.{i}.d", f"sov_cml.{i}.a"]
                if i not in (6, 12, 13):
                    keys.append(f"sov_cml.{i}.b")
                for k in keys:
                    self.assertRegex(text, rf"(?m)^ {re.escape(k)}:\d* \"", f"{path.name}: {k}")


if __name__ == "__main__":
    unittest.main()
