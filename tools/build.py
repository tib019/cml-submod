"""Build: base/ und md/ zusammenfuehren, @@name@@ aus base/werte.toml einsetzen."""
from __future__ import annotations

import re
import shutil
import sys
import tomllib
from pathlib import Path

PLACEHOLDER = re.compile(r"@@([A-Za-z0-9_]+)@@")
RENDERED_SUFFIXES = {".txt", ".yml", ".mod"}
MOD_NAME = "cml_md"


def load_values(path: Path) -> dict[str, int | float]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _fmt(value: int | float) -> str:
    # int ohne ".0"; float mit Punkt, so wie in werte.toml geschrieben (repr)
    if isinstance(value, bool):
        raise TypeError("bool ist kein Zahlenwert")
    return str(value) if isinstance(value, int) else repr(value)


def render(text: str, values: dict) -> str:
    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name not in values:
            raise KeyError(name)
        return _fmt(values[name])

    return PLACEHOLDER.sub(sub, text)


def _copy_tree(src: Path, dst: Path, values: dict) -> None:
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        if rel.as_posix() in ("werte.toml", "descriptor.mod"):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix in RENDERED_SUFFIXES:
            # utf-8 (nicht utf-8-sig): ein vorhandenes BOM bleibt erhalten
            text = p.read_bytes().decode("utf-8")
            target.write_bytes(render(text, values).encode("utf-8"))
        else:
            shutil.copyfile(p, target)


def build(repo_root: Path, out: Path) -> None:
    values = load_values(repo_root / "base" / "werte.toml")
    mod_dir = out / MOD_NAME
    if mod_dir.exists():
        shutil.rmtree(mod_dir)
    mod_dir.mkdir(parents=True)
    _copy_tree(repo_root / "base", mod_dir, values)
    _copy_tree(repo_root / "md", mod_dir, values)
    descriptor = render(
        (repo_root / "md" / "descriptor.mod").read_bytes().decode("utf-8"), values)
    (mod_dir / "descriptor.mod").write_bytes(descriptor.encode("utf-8"))
    launcher = descriptor.rstrip("\n") + f'\npath="mod/{MOD_NAME}"\n'
    (out / f"{MOD_NAME}.mod").write_bytes(launcher.encode("utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    build(root, root / "dist")
    print(f"gebaut: {root / 'dist' / (MOD_NAME + '.mod')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
