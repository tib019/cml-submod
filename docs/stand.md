# Stand

Aktualisiert 31.10.2026. Technisch grün ist keine Abnahme; Kriterium 3 der Spec (Spieltest) bleibt offen.

| Paket | Inhalt | Status |
| --- | --- | --- |
| AP0 | Recherche P1–P7 (`docs/md-referenz/pruefpunkte.md`) | läuft parallel |
| AP1 | Gerüst, Parser, MD-Verzeichnis | gebaut, Abnahme offen |
| AP2 | Prüfskript `tools/check.py` | offen |
| AP3 | Werte, Build, Rechnung | offen |
| AP4 | MD-Adapter | offen |
| AP5 | Kern: Variablen, Schleife, Geister, Einstieg | offen |
| AP6 | Fokusbaum | offen |
| AP7 | Entscheidungen | offen |
| AP8 | Ereignisse | offen |
| AP9 | Testprotokoll, CI, Stand | offen |
| AP10 | Gesamtabnahme | offen |

**Nächstes Paket:** AP2 und AP3 (parallel), nach Abnahme von AP1.

## Offene Prüfpunkte (Spec Abschnitt 9)
P1–P7 warten auf AP0. Bis dahin gilt jeweils der Fallback der Spec.

## Hinweise aus AP1
- `descriptor.mod` von MD v2.0.3 trägt `version="2.0.2"`; `md_index.json` übernimmt den Wert wörtlich.
- Vanilla-Sprites (z. B. `GFX_goal_generic_political_pressure`) stehen nicht im MD-Verzeichnis; `check.py` (Regel 3) muss sie gesondert zulassen.
- MD benutzt `add_namespace = …`; der Index sammelt `add_namespace` und `namespace`.
