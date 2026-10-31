# CLAUDE.md – CML-Submod für Millennium Dawn

Submod für Millennium Dawn (MD) v2.0.3: Russland bekommt nach `SOV_zyuganov` den CML-Einstieg und Phase 1 „Die Große Rückkopplung“. Keine MD-Datei wird überschrieben. Sprache im Repo: Deutsch.

## Maßgebliche Dokumente
- Spec (verbindlich): `docs/specs/2026-10-31-tp1-md-phase1-design.md`
- Umsetzungsplan: `docs/plans/2026-10-31-tp1-md-phase1.md`
- Konzept: `docs/konzept.md` · Stand und offene Punkte: `docs/stand.md`

## Aufbau
- `base/` gemeinsamer Inhalt, `md/` MD-Adapter (zwölf Namen, Spec 4.1)
- `base/werte.toml` einzige Quelle aller Zahlen; Skripte nutzen `@@name@@`
- `tools/` pdx.py (Parser), md_index.py (+ `md_index.json`), check.py, build.py, sim.py

## Befehle (vom Repo-Root, nur Python-Standardbibliothek)
- Tests: `python -m unittest discover -s tests -v`
- Prüfung: `python tools/check.py` · Rechnung: `python tools/sim.py` · Build: `python tools/build.py` (nach `dist/`)
- MD-Verzeichnis neu erzeugen: `python tools/md_index.py <md_root> --rev v2.0.3 --out tools/md_index.json`

## Regeln
- Eigene IDs `cml_`/`SOV_cml_`, eigene Dateien `cml_*`; kein Pfad gleicht einem MD-Pfad.
- Lokalisierung UTF-8 mit BOM, je Bereich eine Datei, Deutsch vollständig, Englisch kurz.
- `ai_will_do = { base = 0 }` für Einstieg und alle CML-Fokusse.
- MD-Quelle ist ein Sparse-/Partial-Checkout: nur über `git show v2.0.3:<pfad>` lesen.
- Tests zuerst, Fehlschlag sehen, dann umsetzen. Spec und Plan nicht ändern; Abweichungen an die Hauptsitzung melden.

## Arbeitsweise
- Rollen: Opus plant und nimmt ab, Sonnet baut nach Plan, Haiku recherchiert; jeder Subagent mit ausdrücklicher Modellvorgabe.
- Subagenten: kein Push, kein `git stash`/`checkout`/`reset`, keine Hintergrundläufe. Commit und Push macht die Hauptsitzung nach Abnahme.
- Arbeitszweig: `claude/new-session-x14s26`.
