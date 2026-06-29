"""Area 10 — Badges."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import result

_CATEGORIES = {
    "build": re.compile(r"(actions/workflow|/badge\.svg|github\.com/.+/workflows|travis|circleci|appveyor|build)", re.I),
    "coverage": re.compile(r"(codecov|coveralls|coverage)", re.I),
    "version": re.compile(r"(pypi|npm|crates\.io|version|release|packagist|gem)", re.I),
    "license": re.compile(r"(license)", re.I),
}
_BADGE_LINE = re.compile(r"(!\[[^\]]*\]\([^)]*\)|img\.shields\.io|badge)", re.I)


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    readme = ctx.find("README.md", "README.rst", "README", "readme.md")
    text = ctx.read(readme) if readme else None
    if not text:
        return [result("badges.present", 0, "no README to scan for badges")]

    badge_lines = [ln for ln in text.splitlines() if _BADGE_LINE.search(ln)]
    found: list[str] = []
    blob = "\n".join(badge_lines)
    for cat, pat in _CATEGORIES.items():
        if pat.search(blob):
            found.append(cat)

    points = min(3, len(found))
    if points:
        ev = f"{readme}: badges for {', '.join(found[:3])}"
    else:
        ev = f"{readme}: no recognizable badges"
    return [result("badges.present", points, ev)]
