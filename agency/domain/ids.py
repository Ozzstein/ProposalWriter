"""Identifier conventions shared by the whole agency.

IDs keep the prefixes users already know from the previous system so that
drafts, wiki pages and exported JSONL stay readable. IDs are allocated by
the store (never by a model) so parallel jobs cannot collide.
"""
from __future__ import annotations

import re
from enum import Enum


class Prefix(str, Enum):
    SOURCE = "SRC"
    CLAIM = "CLM"
    FIN_CLAIM = "CLM-FIN"
    GAP = "GAP"
    NOVELTY = "NOV"
    DECISION = "DEC"
    FEEDBACK = "FBK"
    PATCH = "PATCH"
    FIGURE = "F"
    FRAMING = "FRM"
    CRITERION = "CRIT"
    REQUIREMENT = "REQ"
    SECTION = "SEC"
    FINDING = "FND"
    SCORE = "SCR"
    TASK = "TASK"
    WIKI_SOURCE = "WIKI-SRC"
    WIKI_CLAIM = "WIKI-CLM"


_ID_RE = re.compile(r"^(?P<prefix>[A-Z]+(?:-[A-Z]+)*)-(?P<num>\d+)$")

# Width used when formatting numeric parts. F-01 keeps the old two-digit style.
_WIDTH = {Prefix.FIGURE: 2}


def format_id(prefix: Prefix | str, number: int) -> str:
    p = prefix.value if isinstance(prefix, Prefix) else prefix
    width = _WIDTH.get(Prefix(p), 3) if p in {x.value for x in Prefix} else 3
    return f"{p}-{number:0{width}d}"


def parse_id(value: str) -> tuple[str, int] | None:
    m = _ID_RE.match(value.strip())
    if not m:
        return None
    return m.group("prefix"), int(m.group("num"))


CLAIM_REF_RE = re.compile(r"\b(?:WIKI-)?CLM(?:-FIN)?-\d+\b")
SOURCE_REF_RE = re.compile(r"\b(?:WIKI-)?SRC-\d+\b")
