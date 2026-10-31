"""Minimaler Parser für Paradox-Skript (HOI4). Nur Standardbibliothek."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class PdxSyntaxError(Exception):
    def __init__(self, line: int, msg: str) -> None:
        super().__init__(f"Zeile {line}: {msg}")
        self.line = line
        self.msg = msg


@dataclass
class Node:
    key: str
    op: str
    value: "str | list[Node]"
    line: int


_TOKEN = re.compile(
    r"""
    (?P<nl>\n)
  | (?P<ws>[ \t\r\f\v﻿]+)
  | (?P<comment>\#[^\n]*)
  | (?P<string>"[^"\n]*"?)
  | (?P<op><=|>=|!=|==|=|<|>)
  | (?P<lbrace>\{)
  | (?P<rbrace>\})
  | (?P<word>[^\s{}=<>!"\#]+|!)
    """,
    re.VERBOSE,
)


def _tokens(text: str) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    line = 1
    for m in _TOKEN.finditer(text):
        kind = m.lastgroup
        if kind == "nl":
            line += 1
        elif kind in ("ws", "comment"):
            continue
        else:
            out.append((kind, m.group(), line))
    return out


def parse(text: str) -> list[Node]:
    toks = _tokens(text)
    root: list[Node] = []
    # Stapel: (aktuelle Liste, Zeile der öffnenden Klammer)
    stack: list[tuple[list[Node], int]] = []
    cur = root
    i, n = 0, len(toks)
    while i < n:
        kind, tx, line = toks[i]
        if kind == "rbrace":
            if not stack:
                raise PdxSyntaxError(line, "überzählige schließende Klammer }")
            cur, _ = stack.pop()
            i += 1
        elif kind == "lbrace":
            node = Node("", "", [], line)
            cur.append(node)
            stack.append((cur, line))
            cur = node.value  # type: ignore[assignment]
            i += 1
        elif kind == "op":
            i += 1  # verirrter Operator: ignorieren
        else:  # word oder string
            if i + 1 < n and toks[i + 1][0] == "op":
                op = toks[i + 1][1]
                if i + 2 >= n or toks[i + 2][0] == "rbrace":
                    raise PdxSyntaxError(line, f"Wert nach '{tx} {op}' fehlt")
                vkind, vtx, _ = toks[i + 2]
                if vkind == "lbrace":
                    node = Node(tx, op, [], line)
                    cur.append(node)
                    stack.append((cur, toks[i + 2][2]))
                    cur = node.value  # type: ignore[assignment]
                    i += 3
                elif vkind == "op":
                    raise PdxSyntaxError(line, f"unerwarteter Operator nach '{tx} {op}'")
                else:
                    cur.append(Node(tx, op, vtx, line))
                    i += 3
            else:
                cur.append(Node("", "", tx, line))
                i += 1
    if stack:
        raise PdxSyntaxError(stack[-1][1], "nicht geschlossene Klammer {")
    return root


def parse_file(path: Path) -> list[Node]:
    return parse(Path(path).read_text(encoding="utf-8-sig"))


def walk(nodes: list[Node]) -> Iterator[Node]:
    stack = [iter(nodes)]
    while stack:
        for node in stack[-1]:
            yield node
            if isinstance(node.value, list):
                stack.append(iter(node.value))
                break
        else:
            stack.pop()
