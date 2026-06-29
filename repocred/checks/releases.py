"""Area 6 — Releases / versioning (SemVer + Keep a Changelog)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import not_found, read_manifest, result, unknown

_CHANGELOG_NAMES = ("CHANGELOG.md", "CHANGELOG", "CHANGELOG.rst", "HISTORY.md", "NEWS.md", "CHANGES.md")
_SEMVER_TAG = re.compile(r"^v?\d+\.\d+\.\d+")
_SEMVER_VALUE = re.compile(r'(?i)version\s*[:=]\s*["\']?(\d+\.\d+\.\d+)')
_KAC = re.compile(r"keepachangelog\.com|^\s*##\s*\[?\d+\.\d+\.\d+", re.I | re.M)


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    out: list[CheckResult] = []

    # tags / releases (hybrid)
    if ctx.git is None:
        out.append(unknown("releases.tags", "not a git repository; cannot read tags"))
    else:
        tags = ctx.git.tags
        if tags:
            out.append(result("releases.tags", 3, f"{len(tags)} git tag(s), e.g. {tags[-1]}"))
        else:
            out.append(result("releases.tags", 0, "no git tags / releases"))

    # changelog
    cl = ctx.find(*_CHANGELOG_NAMES)
    if cl:
        text = ctx.read(cl) or ""
        note = "Keep a Changelog shape" if _KAC.search(text) else "present"
        out.append(result("releases.changelog", 3, f"{cl} ({note})"))
    else:
        out.append(result("releases.changelog", 0, not_found("CHANGELOG.md")))

    # semver coherence
    semver_ev = None
    if ctx.git and ctx.git.tags:
        matching = [t for t in ctx.git.tags if _SEMVER_TAG.match(t)]
        if matching and len(matching) >= max(1, len(ctx.git.tags) // 2):
            semver_ev = f"{len(matching)}/{len(ctx.git.tags)} tags follow SemVer"
    if not semver_ev:
        manifest = read_manifest(ctx)
        if manifest:
            m = _SEMVER_VALUE.search(manifest[1])
            if m:
                semver_ev = f"{manifest[0]}: version {m.group(1)}"
    out.append(result("releases.semver", 2 if semver_ev else 0,
                      semver_ev or "no SemVer-shaped version found"))

    return out
