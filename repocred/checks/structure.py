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
    conventional = top_dirs & set(_LAYOUT_DIRS)
    # A top-level package (flat layout) is just as valid as src/: e.g. mypkg/__init__.py.
    flat_packages = {f.split("/", 1)[0] for f in ctx.glob("*/__init__.py")}
    go_dirs = {f.split("/", 1)[0] for f in ctx.glob("*/*.go")}
    small_repo = len(ctx.files) <= 15
    if conventional:
        out.append(result("structure.layout", 3, f"recognized source dir: {sorted(conventional)[0]}/"))
    elif flat_packages:
        out.append(result("structure.layout", 3, f"top-level package: {sorted(flat_packages)[0]}/"))
    elif go_dirs:
        out.append(result("structure.layout", 3, f"package dir: {sorted(go_dirs)[0]}/"))
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
