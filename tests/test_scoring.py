"""Unit tests for the deterministic scoring math."""

from __future__ import annotations

from decimal import Decimal

import pytest

from repocred.scoring import effective_area_weights, round_half_up


def test_round_half_up():
    assert round_half_up(Decimal("6.185")) == Decimal("6.2")
    assert round_half_up(Decimal("6.15")) == Decimal("6.2")
    assert round_half_up(Decimal("6.14")) == Decimal("6.1")
    assert round_half_up(Decimal("10")) == Decimal("10.0")


def test_balanced_weights_sum_100():
    w = effective_area_weights("balanced", None)
    assert sum(w.values()) == 100


def test_all_modes_sum_100():
    for mode in ("balanced", "security", "tests", "ci"):
        assert sum(effective_area_weights(mode, None).values()) == 100


def test_override_renormalizes_to_100():
    w = effective_area_weights("balanced", {"security": 20})
    assert w["security"] == 20
    assert sum(w.values()) == 100
    # other areas shrank proportionally relative to each other
    assert w["readme"] < 18


def test_override_too_large_rejected():
    with pytest.raises(ValueError):
        effective_area_weights("balanced", {"security": 120})
