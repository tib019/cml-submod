# Testprotokoll Teilprojekt 1 (MD v2.0.3, Phase 1)

Grundlage: Spec Abschnitt 8.4 und 11. Dieses Protokoll füllt der Nutzer im Spiel aus. Technisch grün (Tests, `check.py`, `sim.py`) ist keine Abnahme; Erfolgskriterium 3 der Spec ist dieser Spieltest.

## Vorbereitung

1. Im Repo-Root `python tools/build.py` ausführen. Ergebnis liegt in `dist/`.
2. Den Inhalt von `dist/` (Ordner `cml_md` und Datei `cml_md.mod`) in den HOI4-Mod-Ordner kopieren:
   - Windows: `Dokumente\Paradox Interactive\Hearts of Iron IV\mod\`
   - Linux: `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`
3. Im Launcher Millennium Dawn (v2.0.3) und „CML – Russland (MD)“ aktivieren. CML muss **nach** MD geladen werden.
4. **Notieren (Spec 11, P5):** den genauen Namen von Millennium Dawn im Launcher: `______________________`. Er muss zu einem der beiden Abhängigkeitsnamen in `md/descriptor.mod` passen („Millennium Dawn: Developer Version“ oder „Millennium Dawn: A Modern Day Mod“); sonst meldet der Launcher eine fehlende Abhängigkeit.

## Konsolenhinweise

- Konsole im Spiel mit `^` bzw. `~` öffnen; `debug_mode` zeigt Skriptfehler im Spiel.
- `tag SOV` wechselt in die Rolle Russlands, falls nicht ohnehin gespielt.
- `focus.autocomplete` schließt alle aktuell laufenden Fokusse sofort ab (nacheinander wiederholen).
- `event sov_cml.<nr>` löst ein Ereignis aus (z. B. `event sov_cml.10`). Die CML-Ereignisse sind `is_triggered_only`, der Befehl funktioniert trotzdem.
- Variablen setzen: `set_variable SOV_cml_oscillation 49` kann je nach Spielstand/Syntax als Länderbereich scheitern. **Alternative:** per `event`-Befehl testen, z. B. `event sov_cml.10` (Schwelle 1), `event sov_cml.11`, `event sov_cml.12`, `event sov_cml.13` (Zusammenbruch), `event sov_cml.20` (Ausgang verstärkter Weg). Variablenstand ablesen mit `debug_mode` bzw. dem Tooltip der Ereignisse und Entscheidungen.

## Protokoll

| Nr | Schritt | Konsolenbefehle | Erwartung | Datum | Ergebnis | Fehlerauszug |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Spiel als Russland starten; Launcher-Name von MD notiert (siehe Vorbereitung 4) | `tag SOV`, `debug_mode` | keine Fehler aus `cml_`-Dateien in `error.log` | | | |
| T2 | ohne CML: Fokus `SOV_zyuganov`, dann `SOV_communist_party_dominance` | `focus.autocomplete` (mehrfach, bis beide Fokusse fertig sind) | Russland-Baum wie gewohnt, Einstiegsentscheidung verschwindet | | | |
| T3 | neues Spiel, `SOV_zyuganov` abschließen | `tag SOV`, `focus.autocomplete` (bis `SOV_zyuganov` fertig, dann nicht weiter) | Kategorie „Die Partei und ihre Basis“ mit der Einstiegsentscheidung (`SOV_cml_signal_to_the_centre`) sichtbar | | | |
| T4 | Entscheidung nehmen, 21 Tage warten; **Interessengruppen prüfen** (Spec 11 P1) | Entscheidung `SOV_cml_signal_to_the_centre` anklicken; Spiel 21 Tage laufen lassen; Alternative bei Problemen: `event sov_cml.1`, `event sov_cml.2` | CML-Baum geladen, Ereignis 1 und nach 14 Tagen Ereignis 2, Geist „Große Rückkopplung“ sichtbar. Interessengruppe: Parteikader statt Rohstoffindustrie. **Zusätzlich:** Haben die Parteikader eine Startmeinung (nicht 0 bzw. nicht leer)? Falls nein: `on_add` läuft beim Tausch nicht, es gilt der Fallback „nur Meinungsänderung“ (Spec 11 P1). Bitte Wert notieren: ______ **Hinweis:** Der MD-Russland-Fokusbaum wird durch den CML-Baum ersetzt, ein laufender Fokus geht verloren. **Prüfpunkt:** `has_completed_focus = SOV_zyuganov` bleibt wahr (`keep_completed`). | | | |
| T5 | Ereignis 2 Option B wählen; **Porträt prüfen** | Ereignis 2 abwarten oder `event sov_cml.2` | Darja Wolnowa ist Staatsoberhaupt. **Zusätzlich:** Ist ihr Porträt sichtbar (Platzhalter `GFX_portrait_generic_europe_female_01`), oder fehlt das Bild? | | | |
| T6 | Fokusse 2–7 nacheinander | `focus.autocomplete` (je Fokus einmal; Reihenfolge: offene Kanäle, kader vor die Basis, Oligarchen-Verbindungen, Silowiki, neue Kader, Zentrale antwortet) | Wirkungen laut Tooltips, Ereignisse 3, 4, 6 erscheinen (Alternative: `event sov_cml.3`, `event sov_cml.4`, `event sov_cml.6`), Entscheidungskategorie „Die Große Rückkopplung“ sichtbar | | | |
| T7 | Aufschaukeln auf 49 setzen, einen Monat warten | `set_variable SOV_cml_oscillation 49` (Alternative: `event sov_cml.10` und `event sov_cml.11` direkt auslösen) | Ereignis 10 und 11 | | | |
| T8 | „Kader überprüfen“ (`SOV_cml_review_cadres`) mehrfach nehmen | – | Treffer und Fehlurteile kommen vor; ab 3 Fehlurteilen erscheint „Rehabilitierung“ (`SOV_cml_rehabilitation`) | | | |
| T9 | Fokus 8a „Den Regelkreis schließen“ | `focus.autocomplete` | Geist wechselt zu „Demokratischer Zentralismus“, Entscheidungskategorie verschwindet | | | |
| T10 | neues Spiel, bis Fokus 7, dann Fokus 8b „Die Rückkopplung verstärken“, Aufschaukeln per Konsole auf 99 | `focus.autocomplete` bis Fokus 7, danach 8b wählen; `set_variable SOV_cml_oscillation 99` (Alternative: `event sov_cml.20` bzw. `event sov_cml.13` zum Vergleich der Texte) | Ereignis 20 statt 13 | | | |
| T11 | Spiel auf Deutsch und auf Englisch starten | Spracheinstellung im Launcher wechseln, Schritte T3–T6 kurz wiederholen | keine sichtbaren Lokalisierungsschlüssel (`SOV_cml_…`, `sov_cml.…`) | | | |

Ergebnis je Schritt mit Datum eintragen (OK / Fehler / nicht prüfbar). Bei Fehlern den Auszug aus `error.log` in die letzte Spalte.

## error.log

- Windows: `Dokumente\Paradox Interactive\Hearts of Iron IV\logs\error.log`
- Linux: `~/.local/share/Paradox Interactive/Hearts of Iron IV/logs/error.log`

**Bitte zurückschicken:** alle Zeilen mit „cml“ oder „sov_cml“ sowie alles, was im Zusammenhang auffällt (Zeilen davor und danach, Fehler zu Fokussen, Entscheidungen, Ereignissen, Ideen oder Lokalisierung, die zeitgleich auftreten). Das Log vor dem Testlauf löschen oder die Spielstartzeit notieren, damit die Zeilen zuzuordnen sind.

## Bekannte Platzhalter

- Icon „Kult um die Führung“ zeigt das Bild von Zyuganov (Platzhalter).
- Porträt Wolnowa nutzt `GFX_portrait_generic_europe_female_01` (Platzhalter).
