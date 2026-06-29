"""Core data types for RepoCred.

These types are intentionally small and pure. Scoring math lives in ``scoring.py``;
nothing here touches the filesystem or the network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    """The five states a check can resolve to (see SCORING.md §2)."""

    FULL = "full"
    PARTIAL = "partial"
    ZERO = "0"
    NA = "N/A"
    UNKNOWN = "unknown"

    @property
    def is_verified(self) -> bool:
        """Verified states count toward the score denominator."""
        return self in (State.FULL, State.PARTIAL, State.ZERO)


class Tag(str, Enum):
    """Where a check can be answered from (see SCORING.md §3)."""

    LOCAL = "local"
    REMOTE = "remote"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class CheckSpec:
    """Static definition of a single check, independent of any repo.

    ``levels`` are the allowed integer point values at *base* weight, ascending,
    with ``levels[-1] == weight``. This mirrors the ``[0 / 2 / 4]`` notation in
    SCORING.md exactly.
    """

    key: str
    title: str
    weight: int
    levels: tuple[int, ...]
    tag: Tag

    def __post_init__(self) -> None:
        if not self.levels:
            raise ValueError(f"{self.key}: levels must be non-empty")
        if list(self.levels) != sorted(self.levels):
            raise ValueError(f"{self.key}: levels must be ascending")
        if self.levels[0] != 0:
            raise ValueError(f"{self.key}: lowest level must be 0")
        if self.levels[-1] != self.weight:
            raise ValueError(f"{self.key}: top level must equal weight ({self.weight})")


@dataclass(frozen=True)
class AreaSpec:
    """An area is a named group of checks with a base weight."""

    key: str
    title: str
    standard: str
    checks: tuple[CheckSpec, ...]

    @property
    def base_weight(self) -> int:
        return sum(c.weight for c in self.checks)


@dataclass
class CheckResult:
    """The outcome of evaluating one check against a repo."""

    spec: CheckSpec
    state: State
    points: int  # earned points at base weight; meaningful only when state.is_verified
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state.is_verified and self.points not in self.spec.levels:
            raise ValueError(
                f"{self.spec.key}: points {self.points} not in levels {self.spec.levels}"
            )


@dataclass
class AreaResult:
    spec: AreaSpec
    results: list[CheckResult]
    effective_weight: int  # area weight after mode/override (display); base for balanced
