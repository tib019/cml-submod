# Stand

Aktualisiert 31.10.2026. Technisch grün ist keine Abnahme; Kriterium 3 der Spec (Spieltest) bleibt offen.

| Paket | Inhalt | Status |
| --- | --- | --- |
| AP0 | Recherche P1–P7 (`docs/md-referenz/pruefpunkte.md`) | erledigt (a3f83d7: Prüfpunkte P1–P7, Entscheidungen in Spec und Plan) |
| AP1 | Gerüst, Parser, MD-Verzeichnis | erledigt (f36c369: Gerüst, Paradox-Parser und MD-Verzeichnis v2.0.3) |
| AP2 | Prüfskript `tools/check.py` | erledigt (a5e4c75: Prüfskript mit zehn Regeln) |
| AP3 | Werte, Build, Rechnung | erledigt (841e2f9: Werte, Build und Balancing-Rechnung) |
| AP4 | MD-Adapter | erledigt (0587a35: zwölf Namen aus Spec 4.1) |
| AP5 | Kern: Variablen, Schleife, Geister, Einstieg | erledigt (17311b8) |
| AP6 | Fokusbaum | erledigt (c203d40: AP6 und AP8 gemeinsam) |
| AP7 | Entscheidungen | erledigt (55aa300: Kategorie Große Rückkopplung mit fünf Entscheidungen) |
| AP8 | Ereignisse | erledigt (c203d40: AP6 und AP8 gemeinsam) |
| AP9 | Testprotokoll, CI, Stand | erledigt (`docs/testprotokoll.md`, `.github/workflows/check.yml`, README; Commit steht aus) |
| AP10 | Gesamtabnahme | offen |

**Nächster Schritt:** Gesamtabnahme (AP10) und Spieltest durch den Nutzer nach `docs/testprotokoll.md`.

## Offene Punkte

- **P1 `on_add` (T4):** Ob beim `swap_ideas` der Interessengruppen `on_add` läuft und die Parteikader eine Startmeinung haben, ist nicht belegt. Fällt T4 durch, gilt der Fallback „nur Meinungsänderung“.
- **Porträt (T5):** Darja Wolnowa nutzt den Platzhalter `GFX_portrait_generic_europe_female_01`; Sichtbarkeit im Spiel ungeprüft.
- **MD-Name im Launcher (T1):** Der genaue Name von MD v2.0.3 im Launcher ist zu notieren und gegen die Abhängigkeiten in `md/descriptor.mod` zu prüfen (Spec 11 P5).
- **Icon „Kult um die Führung“:** zeigt Zyuganov (Platzhalter).

## Hinweise aus AP1
- `descriptor.mod` von MD v2.0.3 trägt `version="2.0.2"`; `md_index.json` übernimmt den Wert wörtlich.
- Vanilla-Sprites (z. B. `GFX_goal_generic_political_pressure`) stehen nicht im MD-Verzeichnis; `check.py` (Regel 3) lässt sie gesondert zu.
- MD benutzt `add_namespace = …`; der Index sammelt `add_namespace` und `namespace`.
