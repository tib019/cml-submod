# Spec Teilprojekt 1: Grundgerüst und Phase 1 „Die Große Rückkopplung“ in Millennium Dawn

Stand 31.10.2026 · Status: Entwurf zur Freigabe · Konzept: `docs/konzept.md`

## 1. Ziel und Erfolgskriterien

Russland (`SOV`) bekommt in Millennium Dawn einen spielbaren Einstieg in den CML-Pfad und die vollständige Phase 1. Der Mod ist zunächst für den eigenen Gebrauch (Entscheidung 31.10.2026), Workshop-Veröffentlichung ist ein späteres Teilprojekt.

Teilprojekt 1 ist fertig, wenn:

1. `python tools/check.py` grün ist (Abschnitt 8.2).
2. `python tools/sim.py` die Balancing-Ziele aus Abschnitt 7 erfüllt.
3. Der Nutzer das Testprotokoll (Abschnitt 8.4) in seinem Spiel mit MD v2.0.3 durchgespielt hat, ohne Fehler aus unseren Dateien in `error.log`, und der restliche Russland-Baum ohne CML-Wahl unverändert funktioniert.

Kriterium 3 ist die eigentliche Abnahme. 1 und 2 belegen nur Struktur und Rechnung.

## 2. Getroffene Entscheidungen

| Datum | Entscheidung |
| --- | --- |
| 31.10.2026 | CML zweigt nach `SOV_zyuganov` als vierte Option neben den drei Gabelungsfokussen ab. |
| 31.10.2026 | Phase 1 heißt „Die Große Rückkopplung“ (nicht Kulturrevolution). |
| 31.10.2026 | Umsetzung als eigener Fokusbaum, Einstieg per Entscheidung (Weg 1). Keine MD-Datei wird überschrieben. |
| 31.10.2026 | Zielgruppe zunächst nur der Nutzer selbst: Deutsch vollständig, Englisch kurz, Icons aus dem MD-Bestand. |
| 31.10.2026 | Referenzstand ist MD **v2.0.3** (Tag `04d6210`, 27.10.2026), die dem Workshop nächste Version. |
| 31.10.2026 | Neue Führungsfigur: **Darja Iljinitschna Wolnowa**, erfunden, Gewerkschafterin aus einem Autowerk an der Wolga. Swjasin und Sarjowa sind für spätere Phasen reserviert. |
| 31.10.2026 | Arbeitsweise Agentur: Opus plant und nimmt ab, Sonnet baut nach Plan, Haiku recherchiert und erstellt Zuordnungen. Jeder Subagent mit ausdrücklicher Modellvorgabe. |

## 3. Umfang

**Enthalten:** Repo-Grundgerüst mit Werkzeugen, Einstiegsentscheidung, eigener Fokusbaum mit den acht Fokussen von Phase 1, drei Variablen mit monatlicher Eigendynamik, fünf Geister, fünf Entscheidungen, elf Ereignisse, Führungsfigur Wolnowa, Lokalisierung Deutsch und Englisch, Testprotokoll.

**Nicht enthalten:** Planungskapazität, technokratische Drift, Phasen 2–4, TFR-Adapter, eigene Grafiken, KI-Verhalten über `ai_will_do = { base = 0 }` hinaus (die KI wählt den Pfad nicht), Balancing über die Startwerte hinaus, Workshop-Veröffentlichung.

## 4. Aufbau des Repos

```
CLAUDE.md                       Arbeitsregeln, Rollen, Prüfbefehle
docs/konzept.md  docs/stand.md  docs/specs/  docs/plans/  docs/testprotokoll.md
docs/md-referenz/               lesbare Zuordnung: genutzte MD-Stellen mit Datei:Zeile (v2.0.3)
base/
  werte.toml                    alle Zahlenwerte (Abschnitt 6), Quelle für Mod und sim.py
  common/national_focus/cml_russia_focus.txt
  common/ideas/cml_ideas.txt
  common/dynamic_modifiers/cml_dynamic_modifiers.txt
  common/decisions/cml_entry_decisions.txt  common/decisions/cml_feedback_decisions.txt
  common/decisions/categories/cml_decision_categories.txt
  common/scripted_effects/cml_effects.txt
  common/scripted_triggers/cml_triggers.txt
  common/scripted_localisation/cml_scripted_loc.txt
  common/opinion_modifiers/cml_opinion_modifiers.txt
  events/cml_sov_loop_events.txt  events/cml_sov_events.txt
  localisation/german/cml_<bereich>_l_german.yml   (je Bereich eine Datei)
  localisation/english/cml_<bereich>_l_english.yml
md/
  common/scripted_effects/cml_adapter_md_effects.txt
  common/scripted_triggers/cml_adapter_md_triggers.txt
  descriptor.mod
tools/
  md_index.py   build.py   check.py   sim.py
  md_index.json                 erzeugtes ID-Verzeichnis von MD v2.0.3 (eingecheckt)
.github/workflows/check.yml     check.py und sim.py bei jedem Push
```

**Regeln:** Alle eigenen IDs beginnen mit `cml_` oder `SOV_cml_`, alle eigenen Dateien mit `cml_`. Kein Pfad in `base/` oder `md/` darf einem Pfad in MD v2.0.3 gleichen.

### 4.1 Adapter-Schnittstelle

`base/` ruft MD-spezifische Dinge nur über diese Namen auf. `md/` implementiert sie. Ein späterer TFR-Adapter implementiert dieselben Namen.

| Name | Art | MD-Umsetzung |
| --- | --- | --- |
| `cml_adapter_entry_visible` | Trigger | `has_completed_focus = SOV_zyuganov` und keiner von `SOV_communist_party_dominance`, `SOV_honor_gorbachevs_legacy`, `SOV_national_patriotic_alliance` abgeschlossen, und nicht `has_country_flag = SOV_cml_path` |
| `cml_adapter_entry_blocked` | Trigger | einer der drei Gabelungsfokusse abgeschlossen |
| `cml_adapter_cml_in_power` | Trigger | `emerging_communist_state_are_in_power = yes` oder `neutrality_neutral_communism_are_in_power = yes` (wie im KPRF-Ast) |
| `cml_adapter_install_cadres` | Effekt | wenn `fossil_fuel_industry` vorhanden: `swap_ideas` zu `communist_cadres` (wie `SOV_communist_purges` es mit `oligarchs` macht) |
| `cml_adapter_purge_oligarchs` | Effekt | wenn `oligarchs` vorhanden: `swap_ideas` zu `labour_unions`, danach Gewerkschaften +`unions_after_swap` |
| `cml_adapter_cadres_opinion` | Effekt | liest `temp_opinion`, ruft `change_communist_cadres_opinion = yes` |
| `cml_adapter_unions_opinion` | Effekt | liest `temp_opinion`, ruft `change_labour_unions_opinion = yes` |
| `cml_adapter_siloviki_opinion` | Effekt | liest `temp_opinion`, ruft `change_intelligence_community_opinion = yes` |
| `cml_adapter_reduce_corruption` | Effekt | `decrease_corruption = yes` |
| `cml_adapter_treasury` | Effekt | liest `cml_treasury_change` (Mrd. $), setzt `treasury_change` und ruft `modify_treasury_effect = yes` |
| `cml_adapter_install_leader` | Effekt | `create_country_leader` mit Name „Darja Wolnowa“, `picture = GFX_portrait_generic_europe_female_01`, `ideology = communist_state`, Trait `emerging_communist_state` (Muster `events/Russia.txt:1631`) |
| `cml_adapter_rename_party` | Effekt | in Teilprojekt 1 leer (nur `log`), siehe Abschnitt 9: MD benennt Parteien ideologiebezogen, nicht je Slot |

Die MD-Effekte `change_<gruppe>_opinion` erwarten die Variable `temp_opinion` (so im KPRF-Ast verwendet). Die Adapter reichen sie durch.

### 4.2 Werte und Build

`base/werte.toml` enthält jeden Zahlenwert aus Abschnitt 6. In den Skriptdateien stehen statt Zahlen Platzhalter `@@name@@`. `tools/build.py` ersetzt sie, fügt `base/` und `md/` zusammen und schreibt `dist/cml_md/` plus `dist/cml_md.mod`. `dist/` ist in `.gitignore`. `tools/sim.py` liest dieselbe Datei.

`md/descriptor.mod`: `name = "CML – Russland (MD)"`, `dependencies = { "Millennium Dawn: Developer Version" "Millennium Dawn: A Modern Day Mod" }` (Entwickler- und Workshop-Name; nicht vorhandene Einträge ignoriert der Launcher), `supported_version = "1.19.*"` (wie MD v2.0.3), `tags = { "Alternative History" "National Focuses" }`. Den Workshop-Namen bestätigt der Nutzer im Launcher (Testschritt T1).

## 5. Spielablauf

### 5.1 Einstieg

Entscheidungskategorie `cml_feedback_entry_category` („Die Partei und ihre Basis“), sichtbar wenn `cml_adapter_entry_visible`.

Entscheidung `SOV_cml_signal_to_the_centre` („Das Signal an die Zentrale“):
- Kosten `entry_pp` Politische Macht, Laufzeit `entry_days` Tage, einmalig.
- `available`: `cml_adapter_cml_in_power`.
- `cancel_trigger`: `cml_adapter_entry_blocked`. Abbruch ohne Wirkung.
- `remove_effect`, nur wenn nicht `cml_adapter_entry_blocked`:
  1. `set_country_flag = SOV_cml_path`
  2. `SOV_cml_party_base` = `base_start`, `SOV_cml_oscillation` = `osc_start`, `SOV_cml_wrongful_verdicts` = 0
  3. dynamischer Modifier `SOV_cml_feedback_modifier`, Flag `SOV_cml_campaign_active`
  4. `cml_adapter_install_cadres`, `cml_adapter_rename_party`
  5. `load_focus_tree = { tree = cml_russia_focus keep_completed = no }`
  6. Ereignis `sov_cml.1` sofort, `sov_cml.2` nach `event2_delay_days` Tagen
  7. Start der Monatsschleife: verstecktes Ereignis `sov_cml.100` nach 30 Tagen
- `ai_will_do = { base = 0 }`.

### 5.2 Monatsschleife

Verstecktes Ereignis `sov_cml.100` (`hidden = yes`, `is_triggered_only = yes`). Solange `SOV_cml_campaign_active`:
1. Parteibasis +`monthly_base`, Aufschaukeln +`monthly_osc` (mit Flag `SOV_cml_amplified` +`monthly_osc_amplified`). Beide Werte auf 0–100 begrenzen.
2. Schwellen prüfen, jede feuert einmal pro Kampagne (Flag `SOV_cml_threshold_<n>_fired`): ≥25 `sov_cml.10`, ≥50 `sov_cml.11`, ≥75 `sov_cml.12`, =100 `sov_cml.13`.
3. Mit `SOV_cml_amplified`: Zähler `SOV_cml_amplified_days` +30; ab `amplify_duration_days` oder bei Aufschaukeln 100 `sov_cml.20` (statt `sov_cml.13`).
4. Sich selbst nach 30 Tagen erneut aufrufen.

Ohne `SOV_cml_campaign_active` endet die Schleife (kein erneuter Aufruf). Die Schwellen- und Korrekturereignisse rufen außerdem `cml_check_thresholds` nach jeder Änderung durch Fokus oder Entscheidung auf, damit sie nicht bis zum Monatsende warten.

Hilfseffekte in `base/common/scripted_effects/cml_effects.txt`: `cml_add_party_base` und `cml_add_oscillation` (lesen `cml_delta`, begrenzen auf 0–100, rufen `cml_check_thresholds`), `cml_end_campaign` (entfernt Modifier und Flag `SOV_cml_campaign_active`, setzt Aufschaukeln 0, vergibt `SOV_cml_democratic_centralism`, setzt `SOV_cml_phase1_done`).

### 5.3 Fokusbaum `cml_russia_focus`

`focus_tree = { id = cml_russia_focus  country = { factor = 0 } ... }`. Jeder Fokus: `available = { cml_adapter_cml_in_power = yes has_country_flag = SOV_cml_path }`, `ai_will_do = { base = 0 }`. Positionen absolut:

| # | ID | Name | Kosten (Wochen) | x, y | Voraussetzung | Ausschluss | Wirkung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | `SOV_cml_open_channels` | Offene Kanäle in den Betrieben | `f2_cost` | 4, 0 | – | – | Basis +`f2_base`, Aufschaukeln +`f2_osc`, Stabilität −`f2_stab`; Flag `SOV_cml_decisions_unlocked` |
| 3 | `SOV_cml_cadres_before_the_base` | Die Kader vor die Basis | `f3_cost` | 8, 0 | – | – | Kader-Meinung −`f3_cadres`; Basis +`f3_base`, Aufschaukeln +`f3_osc`; Korruption −1; Ereignis `sov_cml.3` |
| 4 | `SOV_cml_cut_oligarch_ties` | Die Oligarchen-Verbindungen kappen | `f4_cost` | 6, 1 | 3 | – | `cml_adapter_purge_oligarchs`; Kasse +`f4_treasury`; Korruption −1; Stabilität −`f4_stab`, Aufschaukeln +`f4_osc`; `sov_cml.4` nach 7–14 Tagen |
| 5 | `SOV_cml_untie_siloviki` | Die Silowiki-Seilschaften lösen | `f5_cost` | 10, 1 | 3 | – | Silowiki-Meinung −`f5_siloviki`; Basis +`f5_base`, Aufschaukeln +`f5_osc`; PP +`f5_pp`; mit `f5_event_chance` % `sov_cml.5` innerhalb von 30 Tagen |
| 6 | `SOV_cml_new_cadres` | Neue Kader aus den Betrieben | `f6_cost` | 7, 2 | 2 **und** (4 **oder** 5) | – | Basis +`f6_base`, Aufschaukeln −`f6_osc_reduce`; Kader-Meinung +`f6_cadres`; Flag `SOV_cml_cadre_school_discount` (für Phase 2) |
| 7 | `SOV_cml_centre_replies` | Die Zentrale antwortet | `f7_cost` | 7, 3 | 6 | – | Korruption −1; Ereignis `sov_cml.6` |
| 8a | `SOV_cml_close_the_loop` | Den Regelkreis schließen | `f8a_cost` | 5, 4 | 7 | 8b | `available` zusätzlich: Aufschaukeln < `f8a_osc_max`. Basis +`f8a_base`; `cml_end_campaign` |
| 8b | `SOV_cml_amplify_the_feedback` | Die Rückkopplung verstärken | `f8b_cost` | 9, 4 | 7 | 8a | Basis +`f8b_base`, Aufschaukeln +`f8b_osc`; Flag `SOV_cml_amplified` |

Ausschluss 8a/8b steht in beiden Fokussen. Icons laut Tabelle P4 in `docs/md-referenz/pruefpunkte.md` (Fokus-Icons ohne `GFX_`-Präfix wie im Russland-Baum), Ersatz `political_pressure`.

### 5.4 Geister

| ID | Art | Wirkung |
| --- | --- | --- |
| `SOV_cml_feedback_modifier` | dynamischer Modifier | `stability_factor` −`spirit_feedback_stab`, `political_power_factor` −`spirit_feedback_pp`, `drift_defence_factor` +`spirit_feedback_drift_def`, `communism_drift` +`spirit_feedback_comm_drift` |
| `SOV_cml_democratic_centralism` | Idee (Land) | `stability_factor` +`spirit_dc_stab`, `political_power_factor` +`spirit_dc_pp` |
| `SOV_cml_exhausted_movement` | Idee, `add_timed_idea` `spirit_exhausted_days` Tage | `stability_factor` −`spirit_exhausted_stab`, `industrial_capacity_factory` −`spirit_exhausted_factory`, `political_power_factor` −`spirit_exhausted_pp` |
| `SOV_cml_factory_standstill` | Idee, `add_timed_idea` `spirit_standstill_days` Tage | `industrial_capacity_factory` −`spirit_standstill_factory`, `consumer_goods_factor` +`spirit_standstill_cg` |
| `SOV_cml_leader_cult` | Idee, bis entfernt | `stability_factor` +`spirit_cult_stab`; Flag `SOV_cml_leader_cult` (sperrt in Phase 3 die Räteordnung) |

Ob MD `consumer_goods_factor` und `industrial_capacity_factory` unverändert nutzt, prüft Haiku (Prüfpunkt P2); MD hat ein eigenes Wirtschaftssystem.

### 5.5 Entscheidungen

Kategorie `cml_feedback_category` („Die Große Rückkopplung“), sichtbar mit `SOV_cml_decisions_unlocked` und `SOV_cml_campaign_active`.

| ID | Kosten | Wiederholung | Wirkung |
| --- | --- | --- | --- |
| `SOV_cml_review_cadres` | `review_pp` PP, `review_days` Tage | ja, Abklingzeit `review_cooldown` | Zufallszahl 0–99 per `set_temp_variable_to_random`. Fehlurteil, wenn Zahl < `review_wrong_base` + Aufschaukeln × `review_wrong_per_osc`. Treffer: Basis +`review_hit_base`, Kader-Meinung −`review_hit_cadres`, mit `review_hit_corruption_chance` % Korruption −1. Fehlurteil: Aufschaukeln +`review_wrong_osc`, Stabilität −`review_wrong_stab`, Fehlurteile +1 |
| `SOV_cml_damp_the_feedback` | `damp_pp` PP | ja, Abklingzeit `damp_cooldown` | Aufschaukeln −`damp_osc`, Basis −`damp_base` |
| `SOV_cml_workplace_assemblies` | Kasse −`assemblies_treasury` | ja, Abklingzeit `assemblies_cooldown` | Basis +`assemblies_base`, Aufschaukeln +`assemblies_osc`, Gewerkschafts-Meinung +`assemblies_unions` |
| `SOV_cml_rehabilitation` | `rehab_pp` PP | sichtbar ab Fehlurteile ≥ 3 | Basis +`rehab_base`, Aufschaukeln −`rehab_osc`, Fehlurteile −3 |
| `SOV_cml_end_the_cult` | `endcult_pp` PP | einmalig, nur mit `SOV_cml_leader_cult` | entfernt die Idee und das Flag, Stabilität −`endcult_stab`, Basis +`endcult_base` |

`SOV_cml_end_the_cult` bleibt auch nach Kampagnenende sichtbar (eigene Sichtbarkeitsbedingung).

### 5.6 Ereignisse (Namespace `sov_cml`)

| ID | Titel | Auslöser | Optionen und Wirkung |
| --- | --- | --- | --- |
| 1 | Brief an das Zentralkomitee | Einstieg | A Basis +5, Aufschaukeln +3 · B Aufschaukeln −3, PP +25 |
| 2 | Der Generalsekretär unter Druck | Einstieg + `event2_delay_days` | A Zyuganov bleibt: Stabilität +3 %, Basis −3 · B Rücktritt: Basis +8, Stabilität −5 %, `cml_adapter_install_leader` |
| 3 | Der Fall des Gebietssekretärs | Fokus 3 | A öffentliches Verfahren: Basis +5, Aufschaukeln +5 · B stille Abberufung: PP −25, Aufschaukeln −3 |
| 4 | Kapitalflucht | 7–14 Tage nach Fokus 4 | A Kapitalverkehr schließen: Kasse −3, Meinung von USA, Großbritannien, Frankreich, Deutschland −10 · B ziehen lassen: Kasse −8, Stabilität +2 % |
| 5 | Gegenschlag der Dienste | Chance nach Fokus 5 | A durchstehen: Aufschaukeln +10, Stabilität −5 %, Silowiki-Meinung −10 · B einigen: PP −50, Silowiki-Meinung +10, Basis −5 |
| 6 | Die Parteikonferenz | Fokus 7 | Text mit aktuellen Werten (scripted localisation), eine Option „Verstanden“, keine Wirkung |
| 10 | Fraktionen in den Komitees | Aufschaukeln ≥ 25 | A dämpfen: PP −50, Aufschaukeln −10 · B laufen lassen: Basis +5, Aufschaukeln +5 |
| 11 | Ein Gesicht für die Bewegung | Aufschaukeln ≥ 50 | A zurückweisen: Basis −5, Aufschaukeln −15, Stabilität −3 % · B annehmen: Idee `SOV_cml_leader_cult`, Aufschaukeln +10 |
| 12 | Stillstand in den Werken | Aufschaukeln ≥ 75 | einzige Option: Idee `SOV_cml_factory_standstill`, Basis −10 |
| 13 | Die Bewegung frisst ihre Basis | Aufschaukeln = 100 ohne `SOV_cml_amplified` | einzige Option: Basis halbieren, Stabilität −10 %, Idee `SOV_cml_exhausted_movement`, `cml_end_campaign` |
| 20 | Die Korrektur | nach 8b: `amplify_duration_days` oder Aufschaukeln 100 | A auffangen: Basis −15, `cml_end_campaign` · B brechen: wie Ereignis 13 |
| 100 | (versteckt) | Monatsschleife | siehe 5.2 |

Die Werte in dieser Tabelle stehen ebenfalls in `werte.toml` (Schlüssel `e<id>_<option>_<wert>`); hier sind sie zur Lesbarkeit ausgeschrieben.

### 5.7 Führungsfigur

Kein eigener Charakter-Eintrag: MD setzt russische Staatsoberhäupter per `create_country_leader` in Ereignissen (`events/Russia.txt:1631`). `cml_adapter_install_leader` macht das genauso, nur über Ereignis 2 B. Porträt ist ein generisches MD-Porträt (Platzhalter).

## 6. Startwerte (`base/werte.toml`)

| Schlüssel | Wert | | Schlüssel | Wert |
| --- | --- | --- | --- | --- |
| `entry_pp` | 50 | | `f6_cost` | 5 |
| `entry_days` | 21 | | `f6_base` | 15 |
| `event2_delay_days` | 14 | | `f6_osc_reduce` | 5 |
| `base_start` | 20 | | `f6_cadres` | 15 |
| `osc_start` | 5 | | `f7_cost` | 3 |
| `monthly_base` | 1 | | `f8a_cost` | 7 |
| `monthly_osc` | 2 | | `f8a_osc_max` | 60 |
| `monthly_osc_amplified` | 4 | | `f8a_base` | 10 |
| `amplify_duration_days` | 180 | | `f8b_cost` | 5 |
| `f2_cost` | 3 | | `f8b_base` | 20 |
| `f2_base` | 8 | | `f8b_osc` | 20 |
| `f2_osc` | 5 | | `review_pp` | 25 |
| `f2_stab` | 0.02 | | `review_days` | 30 |
| `f3_cost` | 5 | | `review_cooldown` | 30 |
| `f3_cadres` | 20 | | `review_wrong_base` | 20 |
| `f3_base` | 10 | | `review_wrong_per_osc` | 0.5 |
| `f3_osc` | 10 | | `review_hit_base` | 3 |
| `f4_cost` | 5 | | `review_hit_cadres` | 5 |
| `f4_treasury` | 10 | | `review_hit_corruption_chance` | 25 |
| `f4_stab` | 0.03 | | `review_wrong_osc` | 5 |
| `f4_osc` | 5 | | `review_wrong_stab` | 0.01 |
| `unions_after_swap` | 15 | | `damp_pp` | 50 |
| `f5_cost` | 5 | | `damp_cooldown` | 60 |
| `f5_siloviki` | 25 | | `damp_osc` | 10 |
| `f5_base` | 5 | | `damp_base` | 3 |
| `f5_osc` | 10 | | `assemblies_treasury` | 2 |
| `f5_pp` | 50 | | `assemblies_cooldown` | 45 |
| `f5_event_chance` | 50 | | `assemblies_base` | 5 |
| `spirit_feedback_stab` | 0.05 | | `assemblies_osc` | 3 |
| `spirit_feedback_pp` | 0.15 | | `assemblies_unions` | 5 |
| `spirit_feedback_drift_def` | 0.20 | | `rehab_pp` | 30 |
| `spirit_feedback_comm_drift` | 0.03 | | `rehab_base` | 5 |
| `spirit_dc_stab` | 0.10 | | `rehab_osc` | 5 |
| `spirit_dc_pp` | 0.10 | | `endcult_pp` | 75 |
| `spirit_exhausted_days` | 365 | | `endcult_stab` | 0.05 |
| `spirit_exhausted_stab` | 0.10 | | `endcult_base` | 5 |
| `spirit_exhausted_factory` | 0.05 | | `spirit_standstill_days` | 90 |
| `spirit_exhausted_pp` | 0.10 | | `spirit_standstill_factory` | 0.10 |
| `spirit_cult_stab` | 0.05 | | `spirit_standstill_cg` | 0.05 |

Fokuskosten sind Wochen (HOI4: `cost × 7` Tage).

## 7. Balancing-Ziele (geprüft von `tools/sim.py`)

`sim.py` rechnet monatlich mit den Werten aus `werte.toml` und festen Annahmen je Weg. Fokusse werden nacheinander mit ihrer Dauer abgearbeitet, Ereignisoptionen sind je Weg festgelegt.

| Weg | Annahmen | Ziel |
| --- | --- | --- |
| Sauber | 2 → 3 → 4 → 6 → 7 → 8a; Ereignisse 1A, 2A, 3A, 4B, 10A; einmal dämpfen vor 8a; keine Kaderprüfung | Abschluss 6–9 Monate nach Einstieg; Parteibasis bei Abschluss 70–85; Aufschaukeln vor 8a 10–45; Ereignis 10 höchstens einmal, kein Ereignis 11–13 |
| Radikal | 2 → 3 → 4 → 5 → 6 → 7 → 8b; Ereignisse 1A, 2B, 3A, 4A, 5A, 10B, 11B; alle 30 Tage Kaderprüfung (Erwartungswert) | Parteibasis erreicht 100; mindestens Ereignis 10 und 11 ausgelöst; Ereignis 20 wird erreicht |
| Nichts tun | nur Einstieg (Ereignis 1A, 2A), danach keine Fokusse und Entscheidungen; Schwellenereignisse 10B, 11B, 12 | Aufschaukeln 100 nach 34–50 Monaten |

Verfehlt ein Weg sein Ziel, wird `werte.toml` angepasst, nicht die Annahmen.

## 8. Prüfung und Test

### 8.1 `tools/md_index.py`

Liest einen MD-Checkout (Pfad als Argument, Stand v2.0.3) und schreibt `tools/md_index.json` mit: allen Fokus-IDs, Ideen, Charakteren, scripted effects, scripted triggers, Ereignis-Namespaces, Sprite-Namen (`GFX_…`), Entscheidungskategorien, dynamischen Modifiern, Dateipfaden unter `common/`, `events/`, `localisation/`, `gfx/`, `interface/`, und der MD-Version aus `descriptor.mod`. Die JSON-Datei wird eingecheckt, damit `check.py` ohne MD-Checkout läuft.

### 8.2 `tools/check.py`

Läuft über `base/` und `md/` und schlägt fehl bei:
1. nicht geschlossenen oder überzähligen geschweiften Klammern (Kommentare und Strings beachtet)
2. Platzhaltern `@@name@@`, die nicht in `werte.toml` stehen, und Werten in `werte.toml`, die nirgends genutzt werden
3. aufgerufenen fremden IDs (Fokus, Idee, Charakter, scripted effect/trigger, Sprite), die weder in `md_index.json` noch in unseren Dateien definiert sind
4. eigenen IDs ohne Präfix `cml_`/`SOV_cml_` und doppelten eigenen IDs
5. Dateipfaden, die in `md_index.json` vorkommen
6. Fokus-Voraussetzungen oder -Ausschlüssen auf unbekannte Fokusse und einseitigen Ausschlüssen
7. aufgerufenen Ereignissen, die nicht definiert sind
8. Variablen, die gelesen, aber nirgends gesetzt werden
9. Lokalisierung: Datei nicht UTF-8 mit BOM, falsche Kopfzeile (`l_german:`/`l_english:`), Schlüssel nur in einer Sprache, fehlende Schlüssel für Fokusse (`<id>` und `<id>_desc`), Ideen, Entscheidungen (`<id>` und `<id>_desc`), Kategorien, Ereignistitel, -texte und -optionen
10. jeder Adapter-Name aus 4.1, der in `md/` nicht definiert ist

Ausgabe je Fehler mit Datei:Zeile. Exit-Code 0 nur ohne Fehler.

### 8.3 `tools/sim.py`

Rechnet die drei Wege aus Abschnitt 7 und gibt je Weg die Kennzahlen und „erfüllt/verfehlt“ aus. Exit-Code 0 nur, wenn alle Ziele erfüllt sind.

### 8.4 Test im Spiel (`docs/testprotokoll.md`)

Vorbereitung: `python tools/build.py`, `dist/cml_md/` und `dist/cml_md.mod` in den HOI4-Mod-Ordner kopieren, im Launcher MD und CML aktivieren.

| # | Schritt | Erwartung |
| --- | --- | --- |
| T1 | Spiel als Russland starten, `debug_mode` | keine Fehler aus `cml_`-Dateien in `error.log` |
| T2 | ohne CML: Fokus `SOV_zyuganov`, dann `SOV_communist_party_dominance` (Konsole `focus.autocomplete`) | Russland-Baum wie gewohnt, Einstiegsentscheidung verschwindet |
| T3 | neues Spiel, `SOV_zyuganov` abschließen | Kategorie „Die Partei und ihre Basis“ mit der Einstiegsentscheidung sichtbar |
| T4 | Entscheidung nehmen, 21 Tage warten | CML-Baum geladen, Ereignis 1 und nach 14 Tagen Ereignis 2, Geist „Große Rückkopplung“ sichtbar, Interessengruppe Parteikader statt Rohstoffindustrie |
| T5 | Ereignis 2 Option B | Darja Wolnowa ist Staatsoberhaupt |
| T6 | Fokusse 2–7 nacheinander (`focus.autocomplete`) | Wirkungen laut Tooltips, Ereignisse 3, 4, 6 erscheinen, Entscheidungskategorie sichtbar |
| T7 | Konsole: `set_variable SOV_cml_oscillation 49`, einen Monat warten | Ereignis 10 und 11 |
| T8 | „Kader überprüfen“ mehrfach | Treffer und Fehlurteile kommen vor; ab 3 Fehlurteilen erscheint „Rehabilitierung“ |
| T9 | Fokus 8a | Geist wechselt zu „Demokratischer Zentralismus“, Entscheidungskategorie verschwindet |
| T10 | neues Spiel, bis Fokus 7, dann 8b, Aufschaukeln per Konsole auf 99 | Ereignis 20 statt 13 |
| T11 | Spiel auf Deutsch und auf Englisch starten | keine sichtbaren Lokalisierungsschlüssel |

Ergebnis je Schritt mit Datum ins Protokoll. Fehler mit Auszug aus `error.log`.

### 8.5 Abnahme je Arbeitspaket

Sonnet baut nach Plan und lässt `check.py` (und, wo betroffen, `sim.py`) laufen. Opus prüft den Diff gegen Spec und Plan. Erst dann Commit und Push auf den Arbeitszweig.

## 9. Prüfpunkte für die Recherche (Haiku, erstes Arbeitspaket)

Jeder Prüfpunkt wird mit Datei:Zeile aus MD v2.0.3 in `docs/md-referenz/` belegt. Gibt es keinen Beleg, gilt der Fallback.

| # | Frage | Fallback |
| --- | --- | --- |
| P1 | Funktioniert `swap_ideas` zwischen Interessengruppen per Effekt, wie in `SOV_communist_purges`, und wird dabei `on_add` der neuen Gruppe ausgeführt? | Statt Tausch nur Meinungsänderung der vorhandenen Gruppen |
| P2 | Welche Modifier-Namen nutzt MD für Fabrikleistung und Konsumgüter? | Wirkung über `stability_factor` und `political_power_factor` ersetzen |
| P3 | Wie benennt MD Parteien um (`set_party_name` oder eigenes System), und lässt sich das nur für `SOV` und Slot 4 machen? | Keine Umbenennung in Teilprojekt 1, Hinweis im Ereignis 1 |
| P4 | Passende vorhandene Sprites für die acht Fokusse, fünf Geister, Entscheidungskategorien, und ein generisches Porträt für Wolnowa | `GFX_goal_generic_political_pressure`, `GFX_idea_generic_political_advisor`, Standard-Porträt |
| P5 | Genauer Name von MD in `descriptor.mod` und `supported_version` | Werte aus der Spec, Nutzer prüft im Launcher |
| P6 | Ist der Namespace `sov_cml` frei, und wie heißen MD-Ereignisdateien, damit wir keinen Pfad doppeln? | Namespace `cml_sov` |
| P7 | Welche Effekte setzt MD für Staatsoberhaupt-Wechsel (`promote_character`, `set_politics`, eigenes System)? | `promote_character` |

## 10. Arbeitsweise

- Opus (Hauptsitzung) schreibt Plan und Briefe, nimmt jedes Paket ab und committet.
- Sonnet-Subagenten bauen je ein Arbeitspaket nach Brief. Haiku-Subagenten recherchieren (Abschnitt 9) und erstellen Zuordnungen.
- Jeder Subagent bekommt sein Modell ausdrücklich vorgegeben.
- Briefe verbieten: Push, `git stash`/`checkout`/`reset`, Arbeiten außerhalb des genannten Pfads, Änderungen an Spec und Plan.
- Der Stand liegt in `docs/stand.md`: abgeschlossene Pakete, nächstes Paket, offene Prüfpunkte.

## 11. Entscheidungen nach der Recherche (AP0, 31.10.2026)

Belege: `docs/md-referenz/pruefpunkte.md`.

| # | Entscheidung |
| --- | --- |
| P1 | Interessengruppen werden per `swap_ideas` getauscht wie in MD (`05_russia.txt:12680`, `05_ENG_decisions.txt:104`). Ob dabei `on_add` der neuen Gruppe läuft (Startmeinung), ist nicht belegt und wird in Testschritt T4 geprüft. Fällt T4 durch, gilt der Fallback „nur Meinungsänderung“. |
| P2 | `industrial_capacity_factory` und `consumer_goods_factor` werden wie in MD direkt genutzt. |
| P3 | Keine Parteiumbenennung in Teilprojekt 1 (MD benennt per `set_party_name` je Ideologie, nicht je Slot). `cml_adapter_rename_party` bleibt als leerer Adapter bestehen. |
| P4 | Icons laut Tabelle P4. Die Vanilla-Fallbacks der Spec gibt es in MD nicht; Ersatz `political_pressure` bzw. `GFX_idea_generic_political_pressure`. Porträt Wolnowa: `GFX_portrait_generic_europe_female_01` (eigentlich ein Wissenschaftlerinnen-Porträt, Platzhalter). |
| P5 | Abhängigkeit auf beide MD-Namen, `supported_version = "1.19.*"`. Der Tag v2.0.3 trägt in `descriptor.mod` die Version 2.0.2. |
| P6 | Namespace `sov_cml` ist frei und wird genutzt. |
| P7 | Staatsoberhaupt per `create_country_leader` statt `promote_character`; kein Charakter-Eintrag. |
| AP3 | Fokus 8b setzt **zuerst** das Flag `SOV_cml_amplified` und erhöht danach das Aufschaukeln. So führt ein Erreichen von 100 durch 8b zu Ereignis 20, nicht zu 13. Die Rechnung in `tools/sim.py` folgt derselben Reihenfolge. |
