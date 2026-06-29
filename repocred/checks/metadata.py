"""Area 9 — Metadata (GitHub discoverability). Entirely remote."""

from __future__ import annotations

from ..context import RepoContext
from ..model import CheckResult
from ._util import result, unknown


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    if not ctx.gh:
        reason = "requires gh (remote check)"
        return [
            unknown("metadata.description", reason),
            unknown("metadata.topics", reason),
            unknown("metadata.homepage", reason),
        ]

    data = ctx.gh.repo_view()
    if data is None:
        reason = "gh: could not read repo metadata"
        return [
            unknown("metadata.description", reason),
            unknown("metadata.topics", reason),
            unknown("metadata.homepage", reason),
        ]

    description = (data.get("description") or "").strip()
    topics = data.get("topics") or []
    homepage = (data.get("homepage") or "").strip()

    return [
        result("metadata.description", 2 if description else 0,
               "gh: description set" if description else "gh: no description"),
        result("metadata.topics", 1 if topics else 0,
               f"gh: {len(topics)} topic(s)" if topics else "gh: no topics"),
        result("metadata.homepage", 1 if homepage else 0,
               "gh: homepage set" if homepage else "gh: no homepage"),
    ]
