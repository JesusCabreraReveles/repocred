"""Area 2 — Security / supply-chain (OpenSSF Scorecard)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import na, not_found, result, unknown, workflow_files

# High-precision secret patterns. Conservative on purpose: a false "secret found!"
# is worse for credibility than a miss. Entropy-based detection is intentionally
# excluded to avoid false positives.
_SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("Stripe live key", re.compile(r"\bsk_live_[0-9A-Za-z]{24,}\b")),
    ("generic assigned secret", re.compile(
        r"(?i)(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]")),
]
_SCANNABLE = re.compile(
    r"\.(py|js|ts|tsx|jsx|go|rb|java|kt|php|env|cfg|conf|ini|yaml|yml|json|toml|sh|txt|md|properties)$"
    r"|(^|/)\.env"
)
_BINARY_HINT = re.compile(r"\.(png|jpg|jpeg|gif|pdf|zip|gz|tar|woff2?|ttf|ico|lock)$")

_DEP_CONFIGS = (
    ".github/dependabot.yml", ".github/dependabot.yaml",
    "renovate.json", ".renovaterc", ".renovaterc.json", ".github/renovate.json",
    ".mend.config", ".whitesource",
)
_LOCKFILES = (
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json",
    "poetry.lock", "Pipfile.lock", "uv.lock", "pdm.lock",
    "go.sum", "Cargo.lock", "composer.lock", "Gemfile.lock",
)
_WRITE_ALL = re.compile(r"permissions:\s*write-all")
_PERMISSIONS = re.compile(r"^\s*permissions:", re.M)


def _scan_secrets(ctx: RepoContext) -> tuple[int, str]:
    scanned = 0
    for f in ctx.files:
        if _BINARY_HINT.search(f) or not _SCANNABLE.search(f):
            continue
        text = ctx.read(f)
        if text is None:
            continue
        scanned += 1
        for i, line in enumerate(text.splitlines(), start=1):
            for label, pat in _SECRET_PATTERNS:
                if pat.search(line):
                    return 0, f"potential {label} at {f}:{i}"
    return scanned, ""


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    out: list[CheckResult] = []

    # SECURITY.md
    sec = ctx.find("SECURITY.md") or _first(ctx, ".github/SECURITY.md", "docs/SECURITY.md")
    out.append(result("security.policy", 3 if sec else 0, sec or not_found("SECURITY.md")))

    # dependency management
    dep = _first(ctx, *_DEP_CONFIGS)
    out.append(result("security.deps_mgmt", 3 if dep else 0, dep or not_found("dependabot/renovate config")))

    # no secrets committed
    bad_scan, finding = _scan_secrets(ctx)
    if finding:
        out.append(result("security.no_secrets", 0, finding))
    else:
        out.append(result("security.no_secrets", 3, f"no secrets detected ({bad_scan} files scanned)"))

    # branch protection (remote)
    if ctx.gh and ctx.git and ctx.git.default_branch:
        prot = ctx.gh.branch_protection(ctx.git.default_branch)
        if prot is None:
            out.append(unknown("security.branch_protection", "gh: could not read branch protection"))
        else:
            out.append(result("security.branch_protection", 2 if prot else 0,
                              f"gh: branch {ctx.git.default_branch} {'protected' if prot else 'unprotected'}"))
    else:
        out.append(unknown("security.branch_protection", "requires gh (remote check)"))

    # minimal token permissions in CI
    wfs = workflow_files(ctx)
    if not wfs:
        out.append(na("security.token_perms", "no CI workflows"))
    else:
        scoped = []
        write_all = []
        for wf in wfs:
            t = ctx.read(wf) or ""
            if _WRITE_ALL.search(t):
                write_all.append(wf)
            elif _PERMISSIONS.search(t):
                scoped.append(wf)
        if scoped and not write_all:
            out.append(result("security.token_perms", 2, f"scoped permissions in {scoped[0]}"))
        elif write_all:
            out.append(result("security.token_perms", 0, f"write-all permissions in {write_all[0]}"))
        else:
            out.append(result("security.token_perms", 0, f"no permissions: block in {wfs[0]}"))

    # pinned deps / lockfile
    lock = _first(ctx, *_LOCKFILES)
    if not lock:
        for req in ctx.glob("requirements*.txt") + ctx.glob("**/requirements*.txt"):
            if "==" in (ctx.read(req) or ""):
                lock = f"{req} (pinned)"
                break
    out.append(result("security.pinned_deps", 2 if lock else 0, lock or not_found("lockfile / pinned requirements")))

    return out


def _first(ctx: RepoContext, *paths: str) -> str | None:
    for p in paths:
        if ctx.exists(p):
            return p
    return None
