"""Deterministic scoring math.

All arithmetic is done with :class:`decimal.Decimal` so a given set of check results,
mode and profile always produces the exact same score on any machine. There is no
model and no float drift in this path (SCORING.md §1, §9).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .model import AreaResult, CheckResult, State
from .rubric import MODE_WEIGHTS, RUBRIC_VERSION


def round_half_up(value: Decimal, places: int = 1) -> Decimal:
    quant = Decimal(1).scaleb(-places)  # e.g. Decimal("0.1")
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def _largest_remainder(weights: dict[str, Decimal], target: int) -> dict[str, int]:
    """Distribute ``target`` integer points across keys proportional to ``weights``,
    using the largest-remainder method so the result sums to exactly ``target``."""
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("cannot distribute weights: total is zero")
    raw = {k: (v / total) * target for k, v in weights.items()}
    floor = {k: int(v) for k, v in raw.items()}
    remainder = target - sum(floor.values())
    order = sorted(raw, key=lambda k: (raw[k] - floor[k], k), reverse=True)
    for k in order[:remainder]:
        floor[k] += 1
    return floor


def effective_area_weights(mode: str, override: dict[str, int] | None) -> dict[str, int]:
    """Area weights after applying a mode preset and an optional fine override.

    The override fixes the named areas and renormalizes the rest proportionally so
    the total stays at exactly 100 (SCORING.md §8). Returns integer weights summing
    to 100.
    """
    base = dict(MODE_WEIGHTS[mode])
    if not override:
        return base

    fixed = {k: v for k, v in override.items() if k in base}
    if not fixed:
        return base
    if any(v < 0 for v in fixed.values()):
        raise ValueError("weight override values must be >= 0")
    fixed_total = sum(fixed.values())
    if fixed_total > 100:
        raise ValueError(f"weight override sums to {fixed_total}, which exceeds 100")

    others = {k: Decimal(v) for k, v in base.items() if k not in fixed}
    remaining = 100 - fixed_total
    if not others:
        if remaining != 0:
            raise ValueError("override fixes every area but does not sum to 100")
        return dict(fixed)
    distributed = _largest_remainder(others, remaining)
    return {**fixed, **distributed}


@dataclass
class CheckScore:
    result: CheckResult
    effective_weight: Decimal  # this check's share of the (integer) area weight
    earned: Decimal           # points earned at effective weight (0 unless verified)

    @property
    def recoverable(self) -> Decimal:
        """Points that would be gained by taking this check to ``full``."""
        if self.result.state.is_verified:
            return self.effective_weight - self.earned
        return Decimal(0)


@dataclass
class AreaScore:
    area: AreaResult
    checks: list[CheckScore]
    effective_weight: int

    @property
    def earned(self) -> Decimal:
        return sum((c.earned for c in self.checks), Decimal(0))

    @property
    def applicable(self) -> Decimal:
        return sum(
            (c.effective_weight for c in self.checks if c.result.state.is_verified),
            Decimal(0),
        )

    @property
    def state_summary(self) -> State:
        """A single rolled-up state for the area, for the human scorecard."""
        states = [c.result.state for c in self.checks]
        if all(s == State.NA for s in states):
            return State.NA
        verified = [c for c in self.checks if c.result.state.is_verified]
        if not verified:
            return State.UNKNOWN
        ratio = self.earned / self.applicable if self.applicable else Decimal(0)
        if ratio >= Decimal("0.85"):
            return State.FULL
        if ratio >= Decimal("0.4"):
            return State.PARTIAL
        return State.ZERO


@dataclass
class Report:
    rubric_version: str
    tool_version: str
    mode: str
    profile: str
    local_only: bool
    areas: list[AreaScore]
    effective_weights: dict[str, int]

    @property
    def earned(self) -> Decimal:
        return sum((a.earned for a in self.areas), Decimal(0))

    @property
    def applicable(self) -> Decimal:
        return sum((a.applicable for a in self.areas), Decimal(0))

    @property
    def unknown_points(self) -> Decimal:
        total = Decimal(0)
        for a in self.areas:
            for c in a.checks:
                if c.result.state == State.UNKNOWN:
                    total += c.effective_weight
        return total

    @property
    def score(self) -> Decimal:
        if self.applicable <= 0:
            return Decimal("0.0")
        return round_half_up((self.earned / self.applicable) * 10)

    @property
    def coverage(self) -> Decimal:
        """Share of the *applicable* rubric that was actually verified (0..1)."""
        denom = self.applicable + self.unknown_points
        if denom <= 0:
            return Decimal(1)
        return self.applicable / denom

    @property
    def fully_verified(self) -> bool:
        return self.unknown_points == 0


def score_report(
    area_results: list[AreaResult],
    mode: str,
    profile: str,
    tool_version: str,
    local_only: bool,
    override: dict[str, int] | None = None,
) -> Report:
    weights = effective_area_weights(mode, override)
    area_scores: list[AreaScore] = []

    for area_result in area_results:
        spec = area_result.spec
        area_weight = weights[spec.key]
        base = spec.base_weight
        check_scores: list[CheckScore] = []
        for cr in area_result.results:
            eff_w = (Decimal(cr.spec.weight) / Decimal(base)) * Decimal(area_weight)
            if cr.state.is_verified:
                earned = (Decimal(cr.points) / Decimal(cr.spec.weight)) * eff_w
            else:
                earned = Decimal(0)
            check_scores.append(CheckScore(cr, eff_w, earned))
        area_scores.append(AreaScore(area_result, check_scores, area_weight))

    return Report(
        rubric_version=RUBRIC_VERSION,
        tool_version=tool_version,
        mode=mode,
        profile=profile,
        local_only=local_only,
        areas=area_scores,
        effective_weights=weights,
    )
