"""Area 8 — Governance / community (GitHub Community Standards)."""

from __future__ import annotations

from ..context import RepoContext
from ..model import CheckResult
from ._util import first_existing, not_found, result


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    out: list[CheckResult] = []

    contributing = first_existing(ctx, "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md")
    out.append(result("governance.contributing", 3 if contributing else 0,
                      contributing or not_found("CONTRIBUTING.md")))

    coc = first_existing(ctx, "CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md", "docs/CODE_OF_CONDUCT.md")
    out.append(result("governance.coc", 2 if coc else 0, coc or not_found("CODE_OF_CONDUCT.md")))

    templates = (
        ctx.glob(".github/ISSUE_TEMPLATE/*")
        + ([f] if (f := first_existing(ctx, ".github/ISSUE_TEMPLATE.md")) else [])
        + ([f] if (f := first_existing(ctx, ".github/PULL_REQUEST_TEMPLATE.md", ".github/pull_request_template.md")) else [])
    )
    out.append(result("governance.templates", 2 if templates else 0,
                      templates[0] if templates else not_found("issue/PR templates")))

    codeowners = first_existing(ctx, "CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS")
    out.append(result("governance.codeowners", 1 if codeowners else 0,
                      codeowners or not_found("CODEOWNERS")))

    return out
