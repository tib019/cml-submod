# Prüfpunkte MD v2.0.3

Stand v2.0.3 (Tag 27.10.2026, Commit 04d6210). Erstellt von Recherche-Agent AP0.

Alle Pfade beziehen sich auf den Tag v2.0.3 im MD-Repo. Zeilen sind die Zeilen der Datei in v2.0.3. Die Nennungen "Definition" bei Sprites zeigen auf die Zeile `name = "..."`.

## P1 – Tauscht `swap_ideas` Interessengruppen, und läuft dabei `on_add` der neuen Gruppe?

**Antwort:** Ja, MD tauscht Interessengruppen per `swap_ideas`: `oligarchs` gegen `the_military` im Fokus `SOV_communist_purges` sowie `fossil_fuel_industry` bzw. `labour_unions` gegen `international_bankers` in der ENG-Entscheidung. Dass HOI4 dabei `on_add` der neuen Gruppe ausführt, ist im Repo nicht belegt. Die `on_add`-Blöcke setzen `<gruppe>_opinion`-Variablen, was auf Ausführung hindeutet, beweist es aber nicht. OFFEN(P1), bis Test T4 bestätigt.

**Belege:**
- common/national_focus/05_russia.txt:12680-12683 – `swap_ideas` mit `remove_idea = oligarchs` und `add_idea = the_military` im Fokus `SOV_communist_purges` (Fokus-ID Zeile 12651)
- common/decisions/05_ENG_decisions.txt:104-107 und 125-128 – `swap_ideas` von `fossil_fuel_industry` bzw. `labour_unions` zu `international_bankers` (Entscheidung `ENG_bankers_switch_faction`)
- common/ideas/AA_law_internal_factions.txt:381-387 – `on_add` der Gruppe `labour_unions` (setzt `labour_unions_opinion = 60` und Minimum); gleiches Muster bei `the_military` (Zeile 326) und `communist_cadres` (Zeile 465)

**Weg:** Der Tausch ist in MD belegt. Für den Lauf von `on_add` gilt der Fallback der Spec: bis T4 bestätigt, nur Meinungsänderung der vorhandenen Gruppen (`change_*_opinion`), kein Tausch zu `communist_cadres`/`labour_unions`.

## P2 – Welche Modifier-Namen nutzt MD für Fabrikleistung und Konsumgüter?

**Antwort:** MD nutzt die Modifier `industrial_capacity_factory` und `consumer_goods_factor` direkt, sowohl in dynamischen Modifiern als auch in Ideen. Die Werte kommen aus MD-eigenen Variablen (z. B. `inflation_rate_output_var`, `COM_consumer_good_factor_var`). Der Fallback über `stability_factor` und `political_power_factor` ist nicht nötig.

**Belege:**
- common/dynamic_modifiers/00_MD_dynamic_modifiers.txt:92 und 94 – `inflation_dynamic_modifier`: `industrial_capacity_factory = inflation_rate_output_var`, `consumer_goods_factor = inflation_goods_var`
- common/dynamic_modifiers/05_internal_factions_modifiers.txt:146 – `communist_cadres_dynamic_modifier`: `consumer_goods_factor = COM_consumer_good_factor_var`
- common/ideas/05_Australia.txt:296 – Idee mit direktem Modifier `industrial_capacity_factory = 0.15`

**Weg:** Beleg. `industrial_capacity_factory` und `consumer_goods_factor` können wie in der Spec (5.4) verwendet werden.

## P3 – Wie benennt MD Parteien um, und lässt sich nur Slot 4 für SOV umbenennen?

**Antwort:** MD benennt Parteien mit `set_party_name = { ideology = ... name = "[SUBIDEOLOGY_NAME]" ... }` in Meta-Effekten. Der Name kommt aus der scripted localisation `show_ruling_party`, und der Schlüssel wird über die Regierungspartei gewählt. Slot 4 entspricht `ruling_party = 4` (`emerging_communist_state_are_in_power`). Eine Umbenennung nur für Slot 4 bei SOV ist nicht belegt, weil `set_party_name` nach Ideologie wirkt und nicht nach Slot. Das Lokalisierungs-Schlüsselpaar `SOV.communist_state` (localisation/english/MD_politics_view_parties_l_english.yml:8889) gehört MD; eigene Überschreibung wäre eine Änderung an MD-Schlüsseln und ist nicht vorgesehen.

**Belege:**
- common/scripted_effects/00_leader_setup_scripted_effects.txt:95-101 – `set_party_name` mit `ideology = communism` im Meta-Effekt, Name `[SUBIDEOLOGY_NAME]` = `[show_ruling_party]`
- common/scripted_effects/00_MD_politicsview_scripted_effects.txt:710-721 – `update_party_name`: `set_party_name` mit `ideology = THIS`
- common/scripted_triggers/01_political_triggers.txt:197-200 – `emerging_communist_state_are_in_power` prüft `ruling_party = 4`

**Weg:** Fallback der Spec. Keine Umbenennung in Teilprojekt 1, Hinweis im Ereignis 1.

## P4 – Passende vorhandene Sprites (Fokus, Geister, Kategorie, Porträt)

**Antwort:** Fokus-Icons in 05_russia.txt werden ohne `GFX_`-Präfix angegeben (z. B. `icon = sov_anti_oligarch`, definiert in interface/goals.gfx:32163). Die Definitionen mit `name = "..."` in interface/goals.gfx sind die Icon-Namen. Die Ideen-Icons der Geister folgen dem Muster `picture = <Sprite>` (Beispiel common/ideas/05_china.txt:1933, `picture = oligarchs`). Die Fallbacks der Spec sind nicht vollständig belegt: `GFX_goal_generic_political_pressure` und `GFX_idea_generic_political_advisor` sind in interface/ nicht definiert. Ersatz vorhanden sind `political_pressure` (interface/goals.gfx:4413) und `GFX_idea_generic_political_pressure` (interface/MD_ideas.gfx:13728). Auswahl ist eine Haiku-Zuordnung nach Namen und Motiv, kein fachlich geprüftes Icon-Urteil.

| Zweck | Sprite | Definition |
| --- | --- | --- |
| Fokus 2 Offene Kanäle in den Betrieben | Focus_Socialist_Worker | interface/goals.gfx:7165 |
| Fokus 3 Die Kader vor die Basis | communist_purge | interface/goals.gfx:7073 |
| Fokus 4 Oligarchen-Verbindungen kappen | sov_anti_oligarch | interface/goals.gfx:32163 |
| Fokus 5 Silowiki-Seilschaften lösen | communist_spies | interface/goals.gfx:7089 |
| Fokus 6 Neue Kader aus den Betrieben | Focus_Socialist_Worker2 | interface/goals.gfx:7169 |
| Fokus 7 Die Zentrale antwortet | revolutionary_government | interface/goals.gfx:7433 |
| Fokus 8a Den Regelkreis schließen | industry_communism | interface/goals.gfx:7289 |
| Fokus 8b Die Rückkopplung verstärken | Generic_Socialist_Revolution | interface/goals.gfx:7249 |
| Geist SOV_cml_feedback_modifier | generic_communism_focus | interface/goals.gfx:7197 |
| Geist SOV_cml_democratic_centralism | communist_constiution | interface/goals.gfx:7049 |
| Geist SOV_cml_exhausted_movement | people_control | interface/goals.gfx:7417 |
| Geist SOV_cml_factory_standstill | generic_factory | interface/goals.gfx:5849 |
| Geist SOV_cml_leader_cult | Generic_Socialist_Man | interface/goals.gfx:7241 |
| Entscheidungskategorie | GFX_decisions_category_political | interface/MD_decisions.gfx:4045 |
| Porträt Darja Wolnowa (weiblich, generisch) | GFX_portrait_generic_europe_female_01 | interface/MD_portraits.gfx:486 (Textur liegt in gfx/leaders/scientists/generic_scientists/, also Wissenschaftler-Porträt; Hinweis) |

**Weg:** Beleg für alle Einträge der Tabelle. Für die Fallbacks gilt: `political_pressure` (interface/goals.gfx:4413) als Ersatz für `GFX_goal_generic_political_pressure`; für `GFX_idea_generic_political_advisor` gibt es keinen Beleg, daher ohne Icon oder Ersatz `GFX_idea_generic_political_pressure` (interface/MD_ideas.gfx:13728).

## P5 – Name von MD und `supported_version` in `descriptor.mod` und `Millennium_Dawn.mod`

**Antwort:** Beide Dateien nennen den Mod "Millennium Dawn: Developer Version" und `supported_version = "1.19.*"`. Die Spec nennt "Millennium Dawn: A Modern Day Mod" und "1.17.*"; beides ist nicht belegt. Die `version`-Felder lauten 2.0.2 (descriptor.mod) bzw. 2.0.0 (Millennium_Dawn.mod), nicht 2.0.3. Der Dependency-Name in `md/descriptor.mod` muss daher vom Nutzer im Launcher geprüft werden.

**Belege:**
- descriptor.mod:2 – `name = "Millennium Dawn: Developer Version"`
- descriptor.mod:13 – `supported_version = "1.19.*"` (Zeile 1: `version = "2.0.2"`)
- Millennium_Dawn.mod:2 und :13 – gleicher Name und gleiche `supported_version` (Zeile 1: `version = "2.0.0"`)

**Weg:** Beleg. Abschnitt 4 der Spec (Dependency-Name und `supported_version`) ist anzupassen.

## P6 – Ist der Namespace `sov_cml` frei, und wie heißen die MD-Ereignisdateien für Russland?

**Antwort:** Ja, `sov_cml` ist in events/ frei: weder `namespace = sov_cml` noch `add_namespace = sov_cml` noch `sov_cml.<n>` kommen vor. Dateien mit Präfix `cml_` gibt es in events/ nicht. Die Russland-Ereignisse liegen in events/Russia.txt (Namespace-Liste ab Zeile 1, u. a. `sov_communists`) und events/SubjectRussia.txt. Fallback `cml_sov` ist nicht nötig.

**Belege:**
- events/Russia.txt:1-14 – `add_namespace`-Liste (`russia`, `sov_vybory`, `sov_communists`, `sov_final_strike`, ...)
- events/Russia.txt:4037 – `id = sov_communists.1` (Beispiel der Namensnutzung)
- events/ (Dateiliste v2.0.3) – Russland-Ereignisse nur in `Russia.txt` und `SubjectRussia.txt`; keine Datei mit Präfix `cml_`

**Weg:** Beleg. Namespace `sov_cml` verwenden.

## P7 – Wie wechselt MD das Staatsoberhaupt per Effekt, und wie sind russische Charaktere aufgebaut?

**Antwort:** MD setzt Staatsoberhäupter in Ereignissen mit `create_country_leader`, z. B. Gorbatschow als `ideology = communist_state` mit Trait `emerging_communist_state`. Die Umstellung der Regierungspartei geschieht über `set_politics` mit `update_party_name = yes` (Fokus) bzw. `set_variable = { ruling_party = N }` mit `update_set_politics = yes` (Ereignis). `promote_character` nutzt MD nur für Australien (AST), nicht für SOV. `common/characters/SOV.txt` enthält nur Generäle mit `advisor`-Blöcken und kein `country_leader`; Staatsführer sind für SOV in Ereignissen definiert.

Kurzbeispiel (events/Russia.txt:1631-1639):
```
create_country_leader = {
	name = "Mikhail Gorbachev"
	picture = "mikhail_gorbachev.dds"
	ideology = communist_state
	traits = {
		emerging_communist_state
	}
}
```

**Belege:**
- events/Russia.txt:1631-1639 – `create_country_leader` mit `ideology = communist_state` und `emerging_communist_state` (Beispiel oben)
- common/country_leader/00_traits.txt:42 – Trait `emerging_communist_state` definiert (`random = no`)
- events/05_australia_events.txt:2036 – `promote_character = AST_leader_peter_costello`; das Muster mit einem `country_leader`-Block in common/characters/AST.txt:756-770

**Weg:** Für Wolnowa (`cml_adapter_install_leader`): `promote_character = SOV_cml_darja_wolnowa` mit einem `country_leader`-Charakter in `md/common/characters/` nach dem AST-Muster (Beleg: AST.txt:756 und 05_australia_events.txt:2036). Alternativ `create_country_leader` nach dem Gorbatschow-Muster (Beleg: events/Russia.txt:1631). Die SOV-Charakterdatei common/characters/SOV.txt ist für `country_leader` nicht das Vorbild.
