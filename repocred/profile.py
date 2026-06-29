"""Profile autodetection (SCORING.md §5). First match wins: monorepo > service > cli > library."""

from __future__ import annotations

import json
import re

from .context import RepoContext

_WORKSPACE_MARKERS = ("pnpm-workspace.yaml", "go.work", "lerna.json", "nx.json", "turbo.json")
_SERVICE_MARKERS = (
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml",
    "compose.yaml", "Procfile", "Chart.yaml", "fly.toml", "render.yaml",
)
_CARGO_WORKSPACE = re.compile(r"^\s*\[workspace\]", re.M)
_PY_SCRIPTS = re.compile(r"^\s*\[(project\.scripts|tool\.poetry\.scripts)\]", re.M)
_CONSOLE_SCRIPTS = re.compile(r"console_scripts")


def _package_json(ctx: RepoContext) -> dict | None:
    f = ctx.find("package.json")
    if not f:
        return None
    try:
        data = json.loads(ctx.read(f) or "")
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def detect_profile(ctx: RepoContext) -> str:
    # monorepo
    if any(ctx.exists(m) for m in _WORKSPACE_MARKERS):
        return "monorepo"
    cargo = ctx.find("Cargo.toml")
    if cargo and _CARGO_WORKSPACE.search(ctx.read(cargo) or ""):
        return "monorepo"
    sub_manifests = (
        ctx.glob("*/package.json") + ctx.glob("packages/*/package.json")
        + ctx.glob("apps/*/package.json") + ctx.glob("services/*/package.json")
    )
    if len(sub_manifests) >= 2:
        return "monorepo"

    # service
    if any(ctx.exists(m) for m in _SERVICE_MARKERS) or ctx.glob("k8s/**") or ctx.glob("helm/**"):
        return "service"

    # cli
    pkg = _package_json(ctx)
    if pkg and pkg.get("bin"):
        return "cli"
    pyproject = ctx.find("pyproject.toml")
    if pyproject and _PY_SCRIPTS.search(ctx.read(pyproject) or ""):
        return "cli"
    setup = ctx.find("setup.py", "setup.cfg")
    if setup and _CONSOLE_SCRIPTS.search(ctx.read(setup) or ""):
        return "cli"
    if ctx.glob("cmd/*/main.go") or ctx.glob("cmd/*.go"):
        return "cli"

    # library (default)
    return "library"
