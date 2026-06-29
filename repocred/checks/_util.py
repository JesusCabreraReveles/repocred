"""Shared helpers for check evaluators."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult, CheckSpec, State
from ..rubric import AREAS

CHECK_BY_KEY: dict[str, CheckSpec] = {c.key: c for a in AREAS for c in a.checks}


def spec(key: str) -> CheckSpec:
    return CHECK_BY_KEY[key]


def result(key: str, points: int, *evidence: str) -> CheckResult:
    """Build a verified result; state is inferred from points vs the spec's levels."""
    s = spec(key)
    if points <= 0:
        state = State.ZERO
        points = 0
    elif points >= s.weight:
        state = State.FULL
        points = s.weight
    else:
        state = State.PARTIAL
    return CheckResult(s, state, points, [e for e in evidence if e])


def unknown(key: str, *evidence: str) -> CheckResult:
    return CheckResult(spec(key), State.UNKNOWN, 0, [e for e in evidence if e])


def na(key: str, *evidence: str) -> CheckResult:
    return CheckResult(spec(key), State.NA, 0, [e for e in evidence if e])


# --- text helpers -----------------------------------------------------------

def line_of(text: str, pattern: re.Pattern[str]) -> int | None:
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            return i
    return None


def evidence_at(path: str, text: str | None, pattern: re.Pattern[str]) -> str:
    if text is not None:
        ln = line_of(text, pattern)
        if ln is not None:
            return f"{path}:{ln}"
    return path


def not_found(*names: str) -> str:
    return "not found: " + ", ".join(names)


def first_existing(ctx: RepoContext, *paths: str) -> str | None:
    for p in paths:
        if ctx.exists(p):
            return p
    return None


CODE_FENCE = re.compile(r"^```")


def has_code_block(text: str) -> bool:
    return text.count("```") >= 2


def headings(text: str) -> list[tuple[int, str]]:
    out = []
    in_fence = False
    for line in text.splitlines():
        if CODE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


def workflow_files(ctx: RepoContext) -> list[str]:
    return ctx.glob(".github/workflows/*.yml") + ctx.glob(".github/workflows/*.yaml")


def read_manifest(ctx: RepoContext) -> tuple[str, str] | None:
    """Return (path, text) of the primary package manifest, if any."""
    for name in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "composer.json", "setup.py"):
        f = ctx.find(name)
        if f:
            text = ctx.read(f)
            if text is not None:
                return f, text
    return None
