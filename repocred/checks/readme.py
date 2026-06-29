"""Area 1 — README (GitHub Community Standards)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import has_code_block, headings, not_found, result

_README_NAMES = ("README.md", "README.rst", "README.txt", "README", "readme.md")
_INSTALL = re.compile(r"\b(install|installation|setup|getting started)\b", re.I)
_INSTALL_CMD = re.compile(r"\b(pip install|pipx|uv add|npm i|npm install|yarn add|pnpm add|cargo add|go install|brew install|docker (run|pull)|apt install)\b", re.I)
_USAGE = re.compile(r"\b(usage|example|examples|quick ?start|getting started|how to use)\b", re.I)
_BADGE_OR_TITLE = re.compile(r"^\s*(#|!\[|\[!\[|<|=+$|-+$)")


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    path = ctx.find(*_README_NAMES)
    text = ctx.read(path) if path else None

    if not path or text is None:
        nf = not_found(*_README_NAMES)
        return [
            result("readme.exists", 0, nf),
            result("readme.tagline", 0, nf),
            result("readme.install", 0, nf),
            result("readme.usage", 0, nf),
            result("readme.sections", 0, nf),
        ]

    lines = text.splitlines()
    non_blank = [ln for ln in lines if ln.strip()]

    # exists & non-trivial
    exists = result("readme.exists", 4 if len(non_blank) > 10 else 0,
                    f"{path} ({len(non_blank)} non-blank lines)")

    # tagline: first descriptive line that isn't a title/badge/separator
    tagline_pts, tagline_ev = 0, f"{path}: no clear tagline near the top"
    for i, ln in enumerate(lines[:8], start=1):
        s = ln.strip()
        if not s or _BADGE_OR_TITLE.match(s):
            continue
        if len(s) >= 40:
            tagline_pts, tagline_ev = 4, f"{path}:{i}"
        else:
            tagline_pts, tagline_ev = 2, f"{path}:{i} (short)"
        break
    tagline = result("readme.tagline", tagline_pts, tagline_ev)

    # install section
    install_pts = 0
    install_ev = f"{path}: no install section/command"
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("#") and _INSTALL.search(ln):
            install_pts, install_ev = 3, f"{path}:{i}"
            break
    if not install_pts:
        for i, ln in enumerate(lines, start=1):
            if _INSTALL_CMD.search(ln):
                install_pts, install_ev = 3, f"{path}:{i}"
                break
    install = result("readme.install", install_pts, install_ev)

    # usage + runnable example
    usage_heading_line = None
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("#") and _USAGE.search(ln):
            usage_heading_line = i
            break
    if usage_heading_line and has_code_block(text):
        usage = result("readme.usage", 4, f"{path}:{usage_heading_line} (+ code example)")
    elif usage_heading_line:
        usage = result("readme.usage", 2, f"{path}:{usage_heading_line} (no code block)")
    else:
        usage = result("readme.usage", 0, f"{path}: no usage/examples section")

    # structured sections
    n_headings = len([1 for lvl, _ in headings(text) if lvl >= 2])
    sections = result("readme.sections", 3 if n_headings >= 3 else 0,
                      f"{path}: {n_headings} section headings")

    return [exists, tagline, install, usage, sections]
