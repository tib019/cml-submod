"""Tests für tools/check.py (Spec 8.2). Fixtures entstehen im Test als kleine Repos in Tempordnern."""
import tempfile
import unittest
from pathlib import Path

from tools import check

BOM = "﻿"

# kleiner In-Memory-Index (statt der 7,6-MB-Datei)
INDEX = {
    "version": "2.0.3",
    "files": ["common/national_focus/05_russia.txt", "interface/md.gfx"],
    "focuses": ["SOV_zyuganov", "SOV_other"],
    "ideas": ["oligarchs", "communist_cadres"],
    "characters": ["SOV_someone"],
    "scripted_effects": ["change_labour_unions_opinion", "decrease_corruption"],
    "scripted_triggers": ["emerging_communist_state_are_in_power"],
    "event_namespaces": ["sov_other"],
    "sprites": ["GFX_focus_x", "GFX_idea_pic", "GFX_portrait_p", "GFX_event_pic"],
    "decision_categories": [],
    "decisions": [],
    "dynamic_modifiers": ["md_mod"],
}
KEYWORDS = {"hidden", "is_triggered_only", "always"}
ALLOW = {"vanilla_thing"}

EFFECT_ADAPTERS = [
    "cml_adapter_install_cadres", "cml_adapter_purge_oligarchs", "cml_adapter_cadres_opinion",
    "cml_adapter_unions_opinion", "cml_adapter_siloviki_opinion", "cml_adapter_reduce_corruption",
    "cml_adapter_treasury", "cml_adapter_install_leader", "cml_adapter_rename_party",
]
TRIGGER_ADAPTERS = ["cml_adapter_entry_visible", "cml_adapter_entry_blocked", "cml_adapter_cml_in_power"]


def loc(lang: str, entries: dict, bom: bool = True) -> str:
    head = f"l_{lang}:\n" + "".join(f' {k}:0 "{v}"\n' for k, v in entries.items())
    return (BOM if bom else "") + head


def good_files() -> dict:
    effects = "".join(f"{n} = {{ log = \"x\" }}\n" for n in EFFECT_ADAPTERS)
    effects = effects.replace(
        'cml_adapter_install_leader = { log = "x" }',
        'cml_adapter_install_leader = { create_country_leader = { name = "N" picture = GFX_portrait_p ideology = communist_state } }',
    )
    triggers = "".join(f"{n} = {{ always = yes }}\n" for n in TRIGGER_ADAPTERS)
    keys = {
        "SOV_cml_a": "A", "SOV_cml_a_desc": "A d", "SOV_cml_b": "B", "SOV_cml_b_desc": "B d",
        "cml_idea_a": "Idee", "sov_cml.1.t": "T", "sov_cml.1.d": "D", "sov_cml.1.a": "O",
    }
    en = {k: "x" for k in keys}
    return {
        "base/werte.toml": "f1_cost = 10\n",
        "md/common/scripted_effects/cml_adapter_md_effects.txt": effects,
        "md/common/scripted_triggers/cml_adapter_md_triggers.txt": triggers,
        "base/common/national_focus/cml_russia_focus.txt": """
focus_tree = {
  id = cml_russia_focus
  focus = {
    id = SOV_cml_a
    icon = GFX_focus_x
    cost = @@f1_cost@@
    prerequisite = { focus = SOV_zyuganov }
    mutually_exclusive = { focus = SOV_cml_b }
    completion_reward = {
      add_ideas = cml_idea_a
      add_political_power = 5
      cml_core_effect = yes
      country_event = { id = sov_cml.1 days = 7 }
      set_variable = { SOV_cml_party_base = 5 }
      if = { limit = { check_variable = { SOV_cml_party_base > 3 } has_completed_focus = SOV_zyuganov } }
    }
  }
  focus = {
    id = SOV_cml_b
    icon = focus_x
    cost = @@f1_cost@@
    mutually_exclusive = { focus = SOV_cml_a }
  }
}
""",
        "base/common/ideas/cml_ideas.txt": "ideas = { country = { cml_idea_a = { picture = pic } } }\n",
        "base/common/scripted_effects/cml_effects.txt": "cml_core_effect = { hidden_effect = { log = \"x\" } }\n",
        "base/events/cml_sov_events.txt": """
add_namespace = sov_cml
country_event = {
  id = sov_cml.1
  title = sov_cml.1.t
  desc = sov_cml.1.d
  is_triggered_only = yes
  option = { name = sov_cml.1.a }
}
""",
        "base/localisation/german/cml_core_l_german.yml": loc("german", keys),
        "base/localisation/english/cml_core_l_english.yml": loc("english", en),
    }


class CheckBase(unittest.TestCase):
    def repo(self, files: dict) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_bytes(content.encode("utf-8"))
        return root

    def run_check(self, files: dict, index: dict | None = None):
        root = self.repo(files)
        return check.check(root, index or INDEX, engine_keywords=KEYWORDS, allowlist=ALLOW)

    def rules(self, findings) -> set:
        return {f.rule for f in findings}

    def variant(self, **changes) -> dict:
        files = good_files()
        for k, v in changes.items():
            files[k.replace("__", "/").replace("_DOT_", ".")] = v
        return files

    def with_files(self, **extra) -> dict:
        return self.variant(**extra)


class TestGood(CheckBase):
    def test_good_repo_clean(self):
        self.assertEqual(self.run_check(good_files()), [])

    def test_adapter_names_constant(self):
        self.assertEqual(len(check.ADAPTER_NAMES), 12)
        self.assertEqual(set(check.ADAPTER_NAMES), set(EFFECT_ADAPTERS + TRIGGER_ADAPTERS))

    def test_default_lists_load(self):
        kw = check.load_word_list(Path(check.__file__).parent / "engine_keywords.txt")
        self.assertIn("hidden", kw)
        self.assertIn("fire_only_once", kw)
        self.assertIn("cancel_if_not_visible", kw)
        al = check.load_word_list(Path(check.__file__).parent / "vanilla_allowlist.txt")
        self.assertIsInstance(al, set)

    def test_load_word_list_comments(self):
        root = self.repo({"w.txt": "# kopf\nabc  # grund\n\n  def\n"})
        self.assertEqual(check.load_word_list(root / "w.txt"), {"abc", "def"})


class TestRule1(CheckBase):
    def test_r1_ok(self):
        self.assertNotIn(1, self.rules(self.run_check(good_files())))

    def test_r1_fail(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = "cml_core_effect = {\n  log = \"x\"\n"
        f = [x for x in self.run_check(files) if x.rule == 1]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].line, 1)
        self.assertTrue(f[0].path.endswith("cml_effects.txt"))

    def test_r1_extra_close(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = "cml_core_effect = { }\n}\n"
        self.assertIn(1, self.rules(self.run_check(files)))

    def test_r1_brace_in_string_and_comment_ok(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = (
            'cml_core_effect = { log = "a { b" } # { offen\n'
        )
        self.assertNotIn(1, self.rules(self.run_check(files)))


class TestRule2(CheckBase):
    def test_r2_ok(self):
        self.assertNotIn(2, self.rules(self.run_check(good_files())))

    def test_r2_unknown_placeholder(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = "cml_core_effect = { add_stability = @@nope@@ }\n"
        f = [x for x in self.run_check(files) if x.rule == 2]
        self.assertTrue(any("nope" in x.msg for x in f))

    def test_r2_unused_value(self):
        files = good_files()
        files["base/werte.toml"] = "f1_cost = 10\nunused_x = 3\n"
        f = [x for x in self.run_check(files) if x.rule == 2]
        self.assertTrue(any("unused_x" in x.msg for x in f))

    def test_r2_skipped_without_werte(self):
        files = good_files()
        del files["base/werte.toml"]
        files["base/common/national_focus/cml_russia_focus.txt"] = files[
            "base/common/national_focus/cml_russia_focus.txt"
        ].replace("@@f1_cost@@", "10")
        self.assertNotIn(2, self.rules(self.run_check(files)))

    def test_r2_placeholder_in_loc_counts_as_use(self):
        files = good_files()
        files["base/werte.toml"] = "f1_cost = 10\nloc_v = 2\n"
        files["base/localisation/german/cml_core_l_german.yml"] = files[
            "base/localisation/german/cml_core_l_german.yml"
        ].replace('"A d"', '"A d @@loc_v@@"')
        self.assertNotIn(2, self.rules(self.run_check(files)))


class TestRule3(CheckBase):
    def edit_effects(self, body: str) -> dict:
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = f"cml_core_effect = {{ {body} }}\n"
        return files

    def test_r3_ok_md_and_own_ids(self):
        body = "add_ideas = oligarchs has_idea = cml_idea_a remove_ideas = { communist_cadres } promote_character = SOV_someone"
        self.assertNotIn(3, self.rules(self.run_check(self.edit_effects(body))))

    def test_r3_fail_unknown_idea(self):
        f = [x for x in self.run_check(self.edit_effects("add_ideas = ghost_idea")) if x.rule == 3]
        self.assertEqual(len(f), 1)
        self.assertIn("ghost_idea", f[0].msg)

    def test_r3_fail_list_swap_timed_character_focus(self):
        body = (
            "add_ideas = { oligarchs ghost1 } swap_ideas = { add_idea = ghost2 remove_idea = oligarchs } "
            "add_timed_idea = { idea = ghost3 days = 5 } promote_character = ghost4 "
            "has_completed_focus = ghost5"
        )
        msgs = " ".join(x.msg for x in self.run_check(self.edit_effects(body)) if x.rule == 3)
        for g in ("ghost1", "ghost2", "ghost3", "ghost4", "ghost5"):
            self.assertIn(g, msgs)

    def test_r3_load_focus_tree_own_prefix(self):
        ok = self.edit_effects("load_focus_tree = { tree = cml_russia_focus }")
        self.assertNotIn(3, self.rules(self.run_check(ok)))
        bad = self.edit_effects("load_focus_tree = { tree = cml_missing_tree }")
        self.assertIn(3, self.rules(self.run_check(bad)))

    def test_r3_yes_call_cml_must_be_defined(self):
        self.assertIn(3, self.rules(self.run_check(self.edit_effects("cml_missing = yes"))))
        self.assertNotIn(3, self.rules(self.run_check(self.edit_effects("cml_adapter_treasury = yes"))))

    def test_r3_yes_call_non_cml(self):
        # im Index, Schlüsselwort, Allowlist: ok; sonst Fund
        ok = self.edit_effects("change_labour_unions_opinion = yes always = yes vanilla_thing = yes")
        self.assertNotIn(3, self.rules(self.run_check(ok)))
        self.assertIn(3, self.rules(self.run_check(self.edit_effects("unknown_effect = yes"))))

    def test_r3_non_yes_values_not_calls(self):
        body = "add_political_power = 5 set_country_flag = some_flag clamp_variable = { var = SOV_cml_x min = 0 }"
        files = self.edit_effects(body + " set_variable = { SOV_cml_x = 1 }")
        self.assertNotIn(3, self.rules(self.run_check(files)))

    def test_r3_focus_icon(self):
        files = good_files()
        files["base/common/national_focus/cml_russia_focus.txt"] = files[
            "base/common/national_focus/cml_russia_focus.txt"
        ].replace("icon = GFX_focus_x", "icon = missing_icon")
        f = [x for x in self.run_check(files) if x.rule == 3]
        self.assertTrue(any("missing_icon" in x.msg for x in f))

    def test_r3_idea_picture_needs_gfx_idea_prefix(self):
        files = good_files()
        files["base/common/ideas/cml_ideas.txt"] = "ideas = { country = { cml_idea_a = { picture = focus_x } } }\n"
        self.assertIn(3, self.rules(self.run_check(files)))  # GFX_idea_focus_x fehlt
        files["base/common/ideas/cml_ideas.txt"] = "ideas = { country = { cml_idea_a = { picture = GFX_idea_pic } } }\n"
        self.assertIn(3, self.rules(self.run_check(files)))  # GFX_idea_GFX_idea_pic fehlt

    def test_r3_leader_picture(self):
        files = good_files()
        key = "md/common/scripted_effects/cml_adapter_md_effects.txt"
        files[key] = files[key].replace("GFX_portrait_p", "GFX_unknown_portrait")
        self.assertIn(3, self.rules(self.run_check(files)))
        files[key] = files[key].replace("GFX_unknown_portrait", "own_portrait.dds")
        self.assertNotIn(3, self.rules(self.run_check(files)))

    def test_r3_decision_and_modifier_icons(self):
        files = good_files()
        files["base/common/decisions/cml_feedback_decisions.txt"] = (
            "cml_cat = { cml_dec = { icon = pic } }\n"
        )
        files["base/common/decisions/categories/cml_decision_categories.txt"] = "cml_cat = { icon = pic }\n"
        files["base/common/dynamic_modifiers/cml_dynamic_modifiers.txt"] = "cml_mod = { icon = GFX_focus_x }\n"
        f = [x for x in self.run_check(files) if x.rule == 3]
        # 'pic' ist weder pic, GFX_pic, GFX_decision_pic noch GFX_decision_category_pic im Index
        self.assertEqual(len([x for x in f if "pic" in x.msg]), 2)
        idx = dict(INDEX, sprites=INDEX["sprites"] + ["GFX_decision_pic", "GFX_decision_category_pic"])
        self.assertEqual([x for x in self.run_check(files, idx) if x.rule == 3], [])

    def test_r3_event_picture(self):
        files = good_files()
        files["base/events/cml_sov_events.txt"] = files["base/events/cml_sov_events.txt"].replace(
            "is_triggered_only = yes", "is_triggered_only = yes picture = missing_pic"
        )
        self.assertIn(3, self.rules(self.run_check(files)))
        files["base/events/cml_sov_events.txt"] = files["base/events/cml_sov_events.txt"].replace(
            "missing_pic", "event_pic"
        )
        self.assertNotIn(3, self.rules(self.run_check(files)))

    def test_r3_vanilla_allowlist_for_ids_and_sprites(self):
        files = self.edit_effects("add_ideas = vanilla_thing")
        self.assertNotIn(3, self.rules(self.run_check(files)))

    def test_r3_dynamic_modifier_call(self):
        ok = self.edit_effects("add_dynamic_modifier = { modifier = md_mod }")
        self.assertNotIn(3, self.rules(self.run_check(ok)))
        bad = self.edit_effects("add_dynamic_modifier = { modifier = ghost_mod }")
        self.assertIn(3, self.rules(self.run_check(bad)))


class TestRule4(CheckBase):
    def test_r4_ok(self):
        self.assertNotIn(4, self.rules(self.run_check(good_files())))

    def test_r4_fail_prefix(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = "my_effect = { log = \"x\" }\ncml_core_effect = { log = \"x\" }\n"
        f = [x for x in self.run_check(files) if x.rule == 4]
        self.assertEqual(len(f), 1)
        self.assertIn("my_effect", f[0].msg)

    def test_r4_fail_duplicate(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects2.txt"] = "cml_core_effect = { log = \"y\" }\n"
        f = [x for x in self.run_check(files) if x.rule == 4]
        self.assertEqual(len(f), 1)
        self.assertIn("doppelt", f[0].msg)

    def test_r4_fail_collides_with_md_id(self):
        files = good_files()
        files["base/common/ideas/cml_ideas.txt"] = "ideas = { country = { oligarchs = { picture = pic } } }\n"
        self.assertIn(4, self.rules(self.run_check(files)))

    def test_r4_focus_and_idea_prefix(self):
        files = good_files()
        files["base/common/national_focus/cml_russia_focus.txt"] = files[
            "base/common/national_focus/cml_russia_focus.txt"
        ].replace("id = SOV_cml_b", "id = SOV_plain_b").replace("focus = SOV_cml_b", "focus = SOV_plain_b")
        self.assertTrue(any("SOV_plain_b" in x.msg for x in self.run_check(files) if x.rule == 4))


class TestRule5(CheckBase):
    def test_r5_ok(self):
        self.assertNotIn(5, self.rules(self.run_check(good_files())))

    def test_r5_overrides_md_path(self):
        files = good_files()
        files["base/common/national_focus/05_russia.txt"] = "focus_tree = { id = cml_x }\n"
        f = [x for x in self.run_check(files) if x.rule == 5]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].path, "base/common/national_focus/05_russia.txt")

    def test_r5_fail_md_dir(self):
        files = good_files()
        files["md/interface/md.gfx"] = "spriteTypes = { }\n"
        self.assertIn(5, self.rules(self.run_check(files)))


class TestRule6(CheckBase):
    def test_r6_ok(self):
        self.assertNotIn(6, self.rules(self.run_check(good_files())))

    def test_r6_unknown_prerequisite(self):
        files = good_files()
        files["base/common/national_focus/cml_russia_focus.txt"] = files[
            "base/common/national_focus/cml_russia_focus.txt"
        ].replace("focus = SOV_zyuganov }", "focus = SOV_ghost }")
        f = [x for x in self.run_check(files) if x.rule == 6]
        self.assertEqual(len(f), 1)
        self.assertIn("SOV_ghost", f[0].msg)

    def test_r6_unknown_exclusive(self):
        files = good_files()
        files["base/common/national_focus/cml_russia_focus.txt"] = files[
            "base/common/national_focus/cml_russia_focus.txt"
        ].replace("mutually_exclusive = { focus = SOV_cml_b }", "mutually_exclusive = { focus = SOV_ghost }")
        self.assertIn(6, self.rules(self.run_check(files)))

    def test_r6_one_sided_exclusion(self):
        files = good_files()
        files["base/common/national_focus/cml_russia_focus.txt"] = files[
            "base/common/national_focus/cml_russia_focus.txt"
        ].replace("    mutually_exclusive = { focus = SOV_cml_a }\n", "")
        f = [x for x in self.run_check(files) if x.rule == 6]
        self.assertEqual(len(f), 1)
        self.assertIn("einseitig", f[0].msg)


class TestRule7(CheckBase):
    def edit_effects(self, body: str) -> dict:
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = f"cml_core_effect = {{ {body} }}\n"
        return files

    def test_r7_ok(self):
        self.assertNotIn(7, self.rules(self.run_check(good_files())))
        ok = self.edit_effects("country_event = sov_cml.1 country_event = { id = sov_other.5 }")
        self.assertNotIn(7, self.rules(self.run_check(ok)))

    def test_r7_fail_own_namespace_unknown_id(self):
        f = [x for x in self.run_check(self.edit_effects("country_event = { id = sov_cml.99 }")) if x.rule == 7]
        self.assertEqual(len(f), 1)
        self.assertIn("sov_cml.99", f[0].msg)

    def test_r7_fail_unknown_namespace(self):
        self.assertIn(7, self.rules(self.run_check(self.edit_effects("country_event = nowhere.1"))))

    def test_r7_scalar_form(self):
        self.assertIn(7, self.rules(self.run_check(self.edit_effects("country_event = sov_cml.98"))))


class TestRule8(CheckBase):
    def edit_effects(self, body: str) -> dict:
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = f"cml_core_effect = {{ {body} }}\n"
        return files

    def test_r8_ok(self):
        # SOV_cml_party_base wird im Fokus gesetzt und gelesen
        self.assertNotIn(8, self.rules(self.run_check(good_files())))

    def test_r8_fail_read_never_set(self):
        files = self.edit_effects("if = { limit = { check_variable = { cml_never_set > 3 } } }")
        f = [x for x in self.run_check(files) if x.rule == 8]
        self.assertEqual(len(f), 1)
        self.assertIn("cml_never_set", f[0].msg)

    def test_r8_fail_loc_reference(self):
        files = good_files()
        files["base/localisation/german/cml_core_l_german.yml"] = files[
            "base/localisation/german/cml_core_l_german.yml"
        ].replace('"A d"', '"A d [?SOV_cml_nowhere|0]"')
        self.assertIn(8, self.rules(self.run_check(files)))

    def test_r8_loc_reference_to_set_variable_ok(self):
        files = good_files()
        files["base/localisation/german/cml_core_l_german.yml"] = files[
            "base/localisation/german/cml_core_l_german.yml"
        ].replace('"A d"', '"A d [?SOV_cml_party_base|0]"')
        self.assertNotIn(8, self.rules(self.run_check(files)))

    def test_r8_setters_recognised(self):
        for setter in ("add_to_variable", "subtract_from_variable", "multiply_variable", "divide_variable", "set_temp_variable"):
            body = f"{setter} = {{ cml_tmp = 1 }} if = {{ limit = {{ check_variable = {{ cml_tmp > 0 }} }} }}"
            self.assertNotIn(8, self.rules(self.run_check(self.edit_effects(body))), setter)

    def test_r8_clamp_and_random_set(self):
        body = (
            "set_temp_variable_to_random = { var = cml_roll min = 0 max = 100 integer = yes } "
            "if = { limit = { check_variable = { cml_roll < 5 } } }"
        )
        self.assertNotIn(8, self.rules(self.run_check(self.edit_effects(body))))

    def test_r8_rhs_variable_is_read(self):
        files = self.edit_effects("set_variable = { SOV_cml_party_base = cml_unset_source }")
        f = [x for x in self.run_check(files) if x.rule == 8]
        self.assertTrue(any("cml_unset_source" in x.msg for x in f))

    def test_r8_non_cml_variables_ignored(self):
        files = self.edit_effects("if = { limit = { check_variable = { some_md_var > 3 } } }")
        self.assertNotIn(8, self.rules(self.run_check(files)))


class TestRule9(CheckBase):
    GER = "base/localisation/german/cml_core_l_german.yml"
    ENG = "base/localisation/english/cml_core_l_english.yml"

    def test_r9_ok(self):
        self.assertNotIn(9, self.rules(self.run_check(good_files())))

    def test_loc_bom(self):
        files = good_files()
        files[self.GER] = files[self.GER].lstrip(BOM)
        f = [x for x in self.run_check(files) if x.rule == 9]
        self.assertEqual(len(f), 1)
        self.assertIn("BOM", f[0].msg)

    def test_loc_both_languages(self):
        files = good_files()
        files[self.GER] = files[self.GER] + ' only_german:0 "x"\n'
        f = [x for x in self.run_check(files) if x.rule == 9]
        self.assertEqual(len(f), 1)
        self.assertIn("only_german", f[0].msg)

    def test_loc_only_english_key(self):
        files = good_files()
        files[self.ENG] = files[self.ENG] + ' only_english:0 "x"\n'
        self.assertIn(9, self.rules(self.run_check(files)))

    def test_loc_keys_union_over_files(self):
        files = good_files()
        files["base/localisation/german/cml_extra_l_german.yml"] = loc("german", {"extra_k": "x"})
        files["base/localisation/english/cml_extra_l_english.yml"] = loc("english", {"extra_k": "x"})
        self.assertNotIn(9, self.rules(self.run_check(files)))

    def test_r9_opinion_modifier_ok(self):
        files = good_files()
        files["base/common/opinion_modifiers/cml_opinion_modifiers.txt"] = "opinion_modifiers = { cml_op = { value = 5 } }\n"
        for p in (self.GER, self.ENG):
            files[p] = files[p] + ' cml_op:0 "x"\n'
        self.assertNotIn(9, self.rules(self.run_check(files)))

    def test_r9_opinion_modifier_fail(self):
        files = good_files()
        files["base/common/opinion_modifiers/cml_opinion_modifiers.txt"] = "opinion_modifiers = { cml_op = { value = 5 } }\n"
        f = [x for x in self.run_check(files) if x.rule == 9]
        self.assertEqual(len(f), 1)
        self.assertIn("cml_op", f[0].msg)

    def test_loc_wrong_header(self):
        files = good_files()
        files[self.GER] = files[self.GER].replace("l_german:", "l_english:", 1)
        self.assertIn(9, self.rules(self.run_check(files)))

    def test_loc_missing_focus_key(self):
        files = good_files()
        files[self.GER] = files[self.GER].replace(' SOV_cml_a_desc:0 "A d"\n', "")
        files[self.ENG] = files[self.ENG].replace(" SOV_cml_a_desc:0 \"x\"\n", "")
        f = [x for x in self.run_check(files) if x.rule == 9]
        self.assertEqual(len(f), 1)
        self.assertIn("SOV_cml_a_desc", f[0].msg)

    def test_loc_missing_idea_and_event_keys(self):
        files = good_files()
        for p in (self.GER, self.ENG):
            files[p] = "\n".join(
                l for l in files[p].split("\n") if "cml_idea_a" not in l and "sov_cml.1.a" not in l
            )
        msgs = " ".join(x.msg for x in self.run_check(files) if x.rule == 9)
        self.assertIn("cml_idea_a", msgs)
        self.assertIn("sov_cml.1.a", msgs)

    def test_loc_missing_decision_and_category_keys(self):
        files = good_files()
        files["base/common/decisions/cml_feedback_decisions.txt"] = "cml_cat = { cml_dec = { } }\n"
        files["base/common/decisions/categories/cml_decision_categories.txt"] = "cml_cat = { }\n"
        msgs = " ".join(x.msg for x in self.run_check(files) if x.rule == 9)
        for k in ("cml_dec", "cml_dec_desc", "cml_cat"):
            self.assertIn(k, msgs)


class TestRule10(CheckBase):
    def test_r10_ok(self):
        self.assertNotIn(10, self.rules(self.run_check(good_files())))

    def test_r10_fail(self):
        files = good_files()
        key = "md/common/scripted_effects/cml_adapter_md_effects.txt"
        files[key] = files[key].replace("cml_adapter_reduce_corruption = { log = \"x\" }\n", "")
        f = [x for x in self.run_check(files) if x.rule == 10]
        self.assertEqual(len(f), 1)
        self.assertIn("cml_adapter_reduce_corruption", f[0].msg)

    def test_r10_empty_repo_reports_all_twelve(self):
        f = [x for x in self.run_check({"README.txt": "x"}) if x.rule == 10]
        self.assertEqual(len(f), 12)


class TestFindingAndCli(CheckBase):
    def test_finding_has_line(self):
        files = good_files()
        files["base/common/scripted_effects/cml_effects.txt"] = (
            "cml_core_effect = {\n  log = \"x\"\n  add_ideas = ghost_idea\n}\n"
        )
        f = [x for x in self.run_check(files) if x.rule == 3]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].line, 3)
        self.assertEqual(f[0].path, "base/common/scripted_effects/cml_effects.txt")

    def test_format_finding(self):
        self.assertEqual(
            check.format_finding(check.Finding(3, "base/a.txt", 7, "kaputt")),
            "base/a.txt:7: [R3] kaputt",
        )

    def test_includes_checked_only_base_and_md(self):
        files = good_files()
        files["docs/other.txt"] = "{{{ kaputt"
        self.assertEqual(self.run_check(files), [])


if __name__ == "__main__":
    unittest.main()
