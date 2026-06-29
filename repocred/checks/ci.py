"""Area 4 — CI (OpenSSF CI-Tests)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import first_existing, result, unknown, workflow_files

_OTHER_CI = (
    ".gitlab-ci.yml", ".circleci/config.yml", "azure-pipelines.yml",
    "Jenkinsfile", ".travis.yml", "bitbucket-pipelines.yml",
)
_LINT_CONFIGS = (
    ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", "eslint.config.js",
    ".flake8", ".pylintrc", "ruff.toml", ".ruff.toml", ".golangci.yml", ".golangci.yaml",
    ".rubocop.yml", ".pre-commit-config.yaml", "biome.json",
)
_LINT_IN_CI = re.compile(r"\b(ruff|flake8|pylint|eslint|golangci-lint|rubocop|black --check|prettier|biome|clippy)\b", re.I)
_BUILD_TEST = re.compile(r"\b(test|build|pytest|go test|cargo (test|build)|npm (run )?(test|build)|make|gradle|mvn|tox)\b", re.I)


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    out: list[CheckResult] = []
    wfs = workflow_files(ctx)
    other = first_existing(ctx, *_OTHER_CI)
    workflow_texts = [(w, ctx.read(w) or "") for w in wfs]

    # workflows present
    if wfs:
        out.append(result("ci.workflows", 4, f"{wfs[0]} ({len(wfs)} workflow(s))"))
    elif other:
        out.append(result("ci.workflows", 4, f"{other} (non-GitHub CI)"))
    else:
        out.append(result("ci.workflows", 0, "no CI workflows found"))

    # lint configured
    lint_cfg = first_existing(ctx, *_LINT_CONFIGS)
    lint_in_ci = next((w for w, t in workflow_texts if _LINT_IN_CI.search(t)), None)
    if lint_cfg:
        out.append(result("ci.lint", 3, lint_cfg))
    elif lint_in_ci:
        out.append(result("ci.lint", 3, f"{lint_in_ci} (lint step)"))
    else:
        out.append(result("ci.lint", 0, "no lint config or CI lint step"))

    # build/test automated
    bt = next((w for w, t in workflow_texts if _BUILD_TEST.search(t)), None)
    if not bt and other:
        bt = other if _BUILD_TEST.search(ctx.read(other) or "") else None
    out.append(result("ci.build_test", 3 if bt else 0,
                      f"{bt} (build/test step)" if bt else "no build/test step in CI"))

    # CI green on last commit (remote)
    if ctx.gh and ctx.git and ctx.git.default_branch:
        concl = ctx.gh.latest_run_conclusion(ctx.git.default_branch)
        if concl is None:
            out.append(unknown("ci.green", "gh: could not read CI runs"))
        elif concl == "success":
            out.append(result("ci.green", 2, "gh: last run succeeded"))
        elif concl == "":
            out.append(result("ci.green", 0, "gh: no CI runs found"))
        else:
            out.append(result("ci.green", 0, f"gh: last run = {concl}"))
    else:
        out.append(unknown("ci.green", "requires gh (remote check)"))

    return out
