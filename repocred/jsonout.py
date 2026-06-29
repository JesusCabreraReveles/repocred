"""Machine-readable output (``--json``). Stable schema for downstream tooling."""

from __future__ import annotations

import json
from decimal import Decimal

from .scoring import Report

SCHEMA_VERSION = 1


def _num(value: Decimal) -> float:
    return float(value)


def to_dict(report: Report) -> dict:
    return {
        "tool": "repocred",
        "tool_version": report.tool_version,
        "rubric_version": report.rubric_version,
        "schema": SCHEMA_VERSION,
        "mode": report.mode,
        "profile": report.profile,
        "score": _num(report.score),
        "earned": _num(report.earned),
        "applicable": _num(report.applicable),
        "verification": {
            "local_only": report.local_only,
            "fully_verified": report.fully_verified,
            "coverage": _num(report.coverage),
            "unknown_points": _num(report.unknown_points),
        },
        "effective_weights": report.effective_weights,
        "areas": [
            {
                "key": area.area.spec.key,
                "title": area.area.spec.title,
                "standard": area.area.spec.standard,
                "effective_weight": area.effective_weight,
                "earned": _num(area.earned),
                "applicable": _num(area.applicable),
                "state": area.state_summary.value,
                "checks": [
                    {
                        "key": c.result.spec.key,
                        "title": c.result.spec.title,
                        "tag": c.result.spec.tag.value,
                        "state": c.result.state.value,
                        "points": _num(c.earned),
                        "max": _num(c.effective_weight),
                        "evidence": c.result.evidence,
                    }
                    for c in area.checks
                ],
            }
            for area in report.areas
        ],
    }


def to_json(report: Report, files_read: list[str] | None = None, indent: int = 2) -> str:
    data = to_dict(report)
    if files_read is not None:
        data["files_read"] = files_read
    return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=False)
