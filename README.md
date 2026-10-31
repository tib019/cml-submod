# cml-submod

Submod für Millennium Dawn (MD) v2.0.3, der Russland nach `SOV_zyuganov` den Einstieg in den CML-Pfad und die Phase 1 „Die Große Rückkopplung“ gibt, ohne eine MD-Datei zu überschreiben.

## Stand

Teilprojekt 1 ist technisch fertig (Tests, Prüfung, Rechnung und Build laufen); der Spieltest durch den Nutzer ist offen. Siehe `docs/stand.md`.

## Installation

1. `python tools/build.py` (nur Python-Standardbibliothek, ab Python 3.11) erzeugt `dist/`.
2. Inhalt von `dist/` (Ordner `cml_md` und Datei `cml_md.mod`) in den HOI4-Mod-Ordner kopieren:
   - Windows: `Dokumente\Paradox Interactive\Hearts of Iron IV\mod\`
   - Linux: `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`
3. Im Launcher Millennium Dawn und „CML – Russland (MD)“ aktivieren; CML nach MD laden.

## Entwicklung

Vom Repo-Root:

```
python -m unittest discover -s tests -v
python tools/check.py
python tools/sim.py
python tools/build.py
```

## Dokumente

- Konzept: `docs/konzept.md`
- Spec: `docs/specs/2026-10-31-tp1-md-phase1-design.md`
- Plan: `docs/plans/2026-10-31-tp1-md-phase1.md`
- Spieltest: `docs/testprotokoll.md`
- Stand: `docs/stand.md`
