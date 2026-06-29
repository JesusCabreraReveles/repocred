"""Scoring regression: known fixtures must land in their expected score band, and
the same input must always produce the exact same score (SCORING.md §9)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from repocred.analyze import analyze
from repocred.jsonout import to_dict

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GIT = shutil.which("git")


def _materialize(src: Path, dst: Path, tag: str | None = None) -> Path:
    shutil.copytree(src, dst)
    if GIT:
        env = ["-c", "user.email=t@t.t", "-c", "user.name=t"]
        subprocess.run([GIT, "init", "-q", "-b", "main"], cwd=dst, check=True)
        subprocess.run([GIT, *env, "add", "-A"], cwd=dst, check=True)
        subprocess.run([GIT, *env, "commit", "-q", "-m", "init"], cwd=dst, check=True)
        if tag:
            subprocess.run([GIT, "tag", tag], cwd=dst, check=True)
    return dst


def test_excellent_scores_high(tmp_path):
    repo = _materialize(FIXTURES / "excellent", tmp_path / "excellent", tag="v1.0.0")
    analysis = analyze(repo, "test", local=True)
    assert analysis.profile == "library"
    assert float(analysis.report.score) >= 9.5, analysis.report.score


def test_empty_scores_low(tmp_path):
    repo = _materialize(FIXTURES / "empty", tmp_path / "empty")
    analysis = analyze(repo, "test", local=True)
    assert float(analysis.report.score) <= 3.5, analysis.report.score


def test_determinism(tmp_path):
    repo = _materialize(FIXTURES / "excellent", tmp_path / "excellent", tag="v1.0.0")
    first = to_dict(analyze(repo, "test", local=True).report)
    second = to_dict(analyze(repo, "test", local=True).report)
    assert first == second


def test_docker_na_for_library(tmp_path):
    repo = _materialize(FIXTURES / "excellent", tmp_path / "excellent", tag="v1.0.0")
    report = analyze(repo, "test", local=True).report
    docker = next(a for a in report.areas if a.area.spec.key == "docker")
    assert docker.state_summary.value == "N/A"


@pytest.mark.skipif(not GIT, reason="git not available")
def test_excellent_full_marks_components(tmp_path):
    repo = _materialize(FIXTURES / "excellent", tmp_path / "excellent", tag="v1.0.0")
    report = analyze(repo, "test", local=True).report
    by_key = {a.area.spec.key: a for a in report.areas}
    assert float(by_key["license"].earned) == 8
    assert float(by_key["readme"].earned) == 18
