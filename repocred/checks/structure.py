"""Area 7 — Structure / hygiene (stack conventions)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import not_found, result

_LAYOUT_DIRS = ("src", "lib", "app", "cmd", "pkg", "packages", "internal", "core")
_CRUFT = re.compile(
    r"(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)$"
    r"|(^|/)(node_modules|__pycache__|\.idea|\.vscode|build|dist|target|\.pytest_cache|\.mypy_cache)/"
    r"|\.(pyc|pyo|class|o|log|swp|tmp|bak|orig)$",
    re.I,
)
_GITIGNORE_MEANINGFUL = 3


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    out: list[CheckResult] = []

    # layout coherent (judgment baseline; the subagent may refine)
    top_dirs = {f.split("/", 1)[0] for f in ctx.files if "/" in f}
    has_layout = bool(top_dirs & set(_LAYOUT_DIRS))
    small_repo = len(ctx.files) <= 15
    if has_layout:
        marker = next(d for d in _LAYOUT_DIRS if d in top_dirs)
        out.append(result("structure.layout", 3, f"recognized source dir: {marker}/"))
    elif small_repo:
        out.append(result("structure.layout", 3, f"small repo ({len(ctx.files)} files), flat layout acceptable"))
    else:
        out.append(result("structure.layout", 0, "no recognizable source layout"))

    # no cruft
    cruft = [f for f in ctx.files if _CRUFT.search(f)]
    if cruft:
        out.append(result("structure.no_cruft", 0, f"committed cruft: {cruft[0]}"
                          + (f" (+{len(cruft)-1} more)" if len(cruft) > 1 else "")))
    else:
        out.append(result("structure.no_cruft", 2, "no committed cruft detected"))

    # .gitignore
    gi = ctx.find(".gitignore")
    if gi:
        patterns = [ln for ln in (ctx.read(gi) or "").splitlines()
                    if ln.strip() and not ln.strip().startswith("#")]
        if len(patterns) >= _GITIGNORE_MEANINGFUL:
            out.append(result("structure.gitignore", 3, f"{gi} ({len(patterns)} patterns)"))
        else:
            out.append(result("structure.gitignore", 0, f"{gi} present but minimal"))
    else:
        out.append(result("structure.gitignore", 0, not_found(".gitignore")))

    return out
