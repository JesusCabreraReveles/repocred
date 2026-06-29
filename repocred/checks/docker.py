"""Area 11 — Docker (N/A for library & cli by default; see applicability matrix)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import result

_DOCKERFILES = ("Dockerfile", "dockerfile", "docker/Dockerfile")
_COMPOSE = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
_FROM_LATEST = re.compile(r"^\s*FROM\s+\S+:latest", re.I | re.M)
_FROM_PINNED = re.compile(r"^\s*FROM\s+\S+[:@]\S+", re.I | re.M)
_NONROOT = re.compile(r"^\s*USER\s+(?!root\b)\S+", re.I | re.M)
_MULTISTAGE = re.compile(r"^\s*FROM\s+\S+\s+AS\s+\S+", re.I | re.M)


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    dockerfile = next((d for d in _DOCKERFILES if ctx.exists(d)), None)
    compose = next((c for c in _COMPOSE if ctx.exists(c)), None)

    if not dockerfile and not compose:
        return [result("docker.present", 0, "no Dockerfile/compose")]

    if not dockerfile:
        return [result("docker.present", 1, f"{compose} (compose only, no Dockerfile)")]

    text = ctx.read(dockerfile) or ""
    good = 0
    notes = []
    if _FROM_PINNED.search(text) and not _FROM_LATEST.search(text):
        good += 1
        notes.append("pinned base")
    if _NONROOT.search(text):
        good += 1
        notes.append("non-root USER")
    if ctx.exists(".dockerignore"):
        good += 1
        notes.append(".dockerignore")
    if _MULTISTAGE.search(text):
        good += 1
        notes.append("multi-stage")

    if good >= 2:
        return [result("docker.present", 3, f"{dockerfile} ({', '.join(notes)})")]
    return [result("docker.present", 1, f"{dockerfile} (basic; missing best practices)")]
