"""Human-facing rendering: the scorecard and the auditable table."""

from __future__ import annotations

from decimal import Decimal

from .advice import suggestion_for
from .model import State
from .scoring import CheckScore, Report

_ICON = {
    State.FULL: "✅",
    State.PARTIAL: "⚠️ ",
    State.ZERO: "❌",
    State.UNKNOWN: "❓",
    State.NA: "•",
}


def _fmt(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return f"{value:.1f}"


def _bar(score: Decimal, width: int = 13) -> str:
    filled = int((score / 10 * width).to_integral_value())
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _coverage_note(report: Report) -> str:
    verified_mode = "local" if report.local_only else "full"
    if report.fully_verified:
        return verified_mode
    applicable = report.applicable
    total = applicable + report.unknown_points
    return f"{verified_mode} — {_fmt(applicable)}/{_fmt(total)} pts verified"


def _improvements(report: Report, limit: int = 3) -> list[tuple[CheckScore, Decimal]]:
    candidates = [
        (c, c.recoverable)
        for area in report.areas
        for c in area.checks
        if c.result.state.is_verified and c.recoverable > 0
    ]
    candidates.sort(key=lambda t: (t[1], t[0].result.spec.key), reverse=True)
    return candidates[:limit]


def render_scorecard(report: Report) -> str:
    lines: list[str] = []
    score = report.score
    meta = f"rubric {report.rubric_version} · profile: {report.profile} · mode: {report.mode}"
    lines.append(f"📊 RepoCred: {score} / 10  {_bar(score)}     ({meta})")
    lines.append("")

    if not report.fully_verified:
        unknown_areas = sorted({
            c.result.spec.title
            for area in report.areas
            for c in area.checks
            if c.result.state == State.UNKNOWN
        })
        lines.append(f"ℹ️  verification: {_coverage_note(report)}")
        lines.append(f"   not verified ({_fmt(report.unknown_points)} pts): {', '.join(unknown_areas)}")
        if report.local_only:
            lines.append("   run with `gh` available for full coverage.")
        lines.append("")

    for area in report.areas:
        summary = area.state_summary
        if summary == State.NA:
            continue
        icon = _ICON[summary]
        score_txt = (
            "not verified" if summary == State.UNKNOWN
            else f"{_fmt(area.earned)}/{_fmt(area.applicable)}"
        )
        lines.append(f"{icon} {area.area.spec.title} ({score_txt})")

    improvements = _improvements(report)
    if improvements:
        lines.append("")
        lines.append("💡 Top improvements (by impact):")
        for i, (cs, rec) in enumerate(improvements, start=1):
            tip = suggestion_for(cs.result.spec.key)
            lines.append(f"   {i}. {tip}  [+{_fmt(rec)} pts]")

    return "\n".join(lines)


def render_audit(report: Report, show_evidence: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"RepoCred audit — rubric {report.rubric_version} · {report.profile} · {report.mode} · {_coverage_note(report)}")
    lines.append("")
    name_w = max(len(a.area.spec.title) for a in report.areas)
    for area in report.areas:
        summary = area.state_summary
        if summary == State.NA:
            cell = "N/A"
        elif summary == State.UNKNOWN:
            cell = "unknown"
        else:
            cell = f"{_fmt(area.earned)}/{_fmt(area.applicable)}"
        lines.append(f"  {area.area.spec.title.ljust(name_w)}  {cell}")

    lines.append("")
    lines.append(
        f"  Applicable: {_fmt(report.applicable)}   "
        f"Earned: {_fmt(report.earned)}   "
        f"Score: {_fmt(report.earned)} / {_fmt(report.applicable)} × 10 = {report.score}"
    )

    if show_evidence:
        lines.append("")
        lines.append("Evidence:")
        for area in report.areas:
            for c in area.checks:
                state = c.result.state.value
                ev = "; ".join(c.result.evidence) or "—"
                lines.append(f"  [{state:>7}] {c.result.spec.key}: {ev}")
    return "\n".join(lines)
