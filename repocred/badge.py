"""Badge generation.

Two flavours, both without any hosted service (SCORING.md "growth" section):
- **static**: a frozen shields.io badge URL embedded in the README.
- **endpoint**: a ``.repocred/badge.json`` committed to the user's repo and rendered by
  shields' endpoint badge. The user's CI rewrites it on every push.

Hard rule: a badge is NEVER generated from a run with ``unknown`` checks (e.g. ``--local``).
A partial score may not be published as if it were complete.
"""

from __future__ import annotations

import json
from urllib.parse import quote

from .scoring import Report


class BadgeRefused(RuntimeError):
    """Raised when a badge is requested from an incompletely-verified run."""


def _color(score: float) -> str:
    if score >= 9:
        return "brightgreen"
    if score >= 7.5:
        return "green"
    if score >= 6:
        return "yellowgreen"
    if score >= 4:
        return "yellow"
    if score >= 2:
        return "orange"
    return "red"


def _label(report: Report) -> str:
    return "RepoCred" if report.mode == "balanced" else f"RepoCred ({report.mode})"


def _guard(report: Report) -> None:
    if not report.fully_verified:
        raise BadgeRefused(
            "Refusing to generate a badge from an incompletely-verified run "
            f"({report.unknown_points:g} pts unverified). Run with `gh` available so every "
            "remote check resolves, then generate the badge."
        )


def endpoint_json(report: Report) -> str:
    """The ``.repocred/badge.json`` payload for shields' endpoint badge."""
    _guard(report)
    score = float(report.score)
    payload = {
        "schemaVersion": 1,
        "label": _label(report),
        "message": f"{report.score}/10",
        "color": _color(score),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def static_markdown(report: Report) -> str:
    """A frozen shields badge for the README. Notes that it reflects the last analysis."""
    _guard(report)
    label = quote(_label(report))
    message = quote(f"{report.score}/10")
    url = f"https://img.shields.io/badge/{label}-{message}-{_color(float(report.score))}"
    return f"![RepoCred]({url})"


def endpoint_markdown(report: Report, raw_json_url: str) -> str:
    """Endpoint badge markdown given the public raw URL of the committed badge.json.

    Only works for public repos (shields cannot fetch a private raw URL)."""
    _guard(report)
    endpoint = f"https://img.shields.io/endpoint?url={quote(raw_json_url, safe='')}"
    return f"![RepoCred]({endpoint})"
