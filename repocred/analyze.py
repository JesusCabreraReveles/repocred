"""Orchestration: build context, detect profile, run checks, score."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .checks import EVALUATORS
from .config import Config
from .context import RepoContext
from .model import AreaResult, CheckResult, State
from .profile import detect_profile
from .rubric import AREAS, PROFILE_NA
from .scoring import Report, score_report


@dataclass
class Analysis:
    report: Report
    config: Config
    context: RepoContext
    profile: str


def analyze(
    root: Path,
    tool_version: str,
    config: Config | None = None,
    mode_override: str | None = None,
    profile_override: str | None = None,
    local: bool = False,
) -> Analysis:
    cfg = config if config is not None else Config.discover(root)
    mode = mode_override or cfg.mode
    ctx = RepoContext.build(root, local_only=local, ignore=cfg.ignore)
    profile = profile_override or cfg.profile or detect_profile(ctx)

    na_areas = set(PROFILE_NA.get(profile, frozenset())) | cfg.checks_off

    area_results: list[AreaResult] = []
    for area in AREAS:
        if area.key in na_areas:
            reason = "disabled in .repocred.yml" if area.key in cfg.checks_off else f"N/A for {profile} profile"
            results = [CheckResult(c, State.NA, 0, [reason]) for c in area.checks]
        else:
            results = EVALUATORS[area.key](ctx)
            _validate(area.key, results)
        area_results.append(AreaResult(spec=area, results=results, effective_weight=area.base_weight))

    report = score_report(
        area_results,
        mode=mode,
        profile=profile,
        tool_version=tool_version,
        local_only=ctx.local_only,
        override=cfg.weights,
    )
    return Analysis(report=report, config=cfg, context=ctx, profile=profile)


def _validate(area_key: str, results: list[CheckResult]) -> None:
    expected = [c.key for c in next(a for a in AREAS if a.key == area_key).checks]
    got = [r.spec.key for r in results]
    if got != expected:
        raise RuntimeError(f"area {area_key}: evaluator returned {got}, expected {expected}")
