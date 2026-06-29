"""Rubric v1 — the versioned definition of areas, checks, modes and profiles.

This is the data side of SCORING.md. Changing anything here is a rubric change and
MUST bump ``RUBRIC_VERSION``.
"""

from __future__ import annotations

from .model import AreaSpec, CheckSpec, Tag

RUBRIC_VERSION = "v1"

# --- Areas and checks -------------------------------------------------------
# Order matches SCORING.md §6. ``levels`` mirror the [0 / .. / full] notation.

AREAS: tuple[AreaSpec, ...] = (
    AreaSpec(
        "readme",
        "README",
        "GitHub Community Standards",
        (
            CheckSpec("readme.exists", "Exists and non-trivial (>10 lines)", 4, (0, 4), Tag.LOCAL),
            CheckSpec("readme.tagline", "Clear tagline (what for)", 4, (0, 2, 4), Tag.LOCAL),
            CheckSpec("readme.install", "Install section with executable block", 3, (0, 3), Tag.LOCAL),
            CheckSpec("readme.usage", "Usage + runnable examples", 4, (0, 2, 4), Tag.LOCAL),
            CheckSpec("readme.sections", "Structured sections (>=3 headings)", 3, (0, 3), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "security",
        "Security / supply-chain",
        "OpenSSF Scorecard",
        (
            CheckSpec("security.policy", "SECURITY.md (disclosure policy)", 3, (0, 3), Tag.LOCAL),
            CheckSpec("security.deps_mgmt", "Dependency management config", 3, (0, 3), Tag.LOCAL),
            CheckSpec("security.no_secrets", "No secrets committed", 3, (0, 3), Tag.LOCAL),
            CheckSpec("security.branch_protection", "Branch protection on default branch", 2, (0, 2), Tag.REMOTE),
            CheckSpec("security.token_perms", "Minimal token permissions in CI", 2, (0, 2), Tag.LOCAL),
            CheckSpec("security.pinned_deps", "Pinned deps / lockfile present", 2, (0, 2), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "tests",
        "Tests",
        "—",
        (
            CheckSpec("tests.exist", "Tests exist", 5, (0, 5), Tag.LOCAL),
            CheckSpec("tests.documented", "Test command documented", 3, (0, 3), Tag.LOCAL),
            CheckSpec("tests.in_ci", "Tests run in CI", 3, (0, 3), Tag.LOCAL),
            CheckSpec("tests.coverage", "Coverage signal present", 2, (0, 1, 2), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "ci",
        "CI",
        "OpenSSF (CI-Tests)",
        (
            CheckSpec("ci.workflows", "Workflows present", 4, (0, 4), Tag.LOCAL),
            CheckSpec("ci.lint", "Lint configured", 3, (0, 3), Tag.LOCAL),
            CheckSpec("ci.build_test", "Build/test automated", 3, (0, 3), Tag.LOCAL),
            CheckSpec("ci.green", "CI green on last commit", 2, (0, 2), Tag.REMOTE),
        ),
    ),
    AreaSpec(
        "license",
        "License",
        "GitHub / SPDX",
        (
            CheckSpec("license.present", "LICENSE file present", 6, (0, 6), Tag.LOCAL),
            CheckSpec("license.spdx", "Recognized SPDX license, declared", 2, (0, 2), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "releases",
        "Releases / versioning",
        "SemVer + Keep a Changelog",
        (
            CheckSpec("releases.tags", "Tags / releases exist", 3, (0, 3), Tag.HYBRID),
            CheckSpec("releases.changelog", "CHANGELOG (Keep a Changelog)", 3, (0, 3), Tag.LOCAL),
            CheckSpec("releases.semver", "Consistent versioning (SemVer)", 2, (0, 2), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "structure",
        "Structure / hygiene",
        "Stack conventions",
        (
            CheckSpec("structure.layout", "Layout coherent with the stack", 3, (0, 3), Tag.LOCAL),
            CheckSpec("structure.no_cruft", "No cruft (artifacts, temp, .DS_Store)", 2, (0, 2), Tag.LOCAL),
            CheckSpec("structure.gitignore", "Adequate .gitignore", 3, (0, 3), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "governance",
        "Governance / community",
        "GitHub Community Standards",
        (
            CheckSpec("governance.contributing", "CONTRIBUTING.md", 3, (0, 3), Tag.LOCAL),
            CheckSpec("governance.coc", "CODE_OF_CONDUCT.md", 2, (0, 2), Tag.LOCAL),
            CheckSpec("governance.templates", "Issue/PR templates", 2, (0, 2), Tag.LOCAL),
            CheckSpec("governance.codeowners", "CODEOWNERS", 1, (0, 1), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "metadata",
        "Metadata",
        "GitHub discoverability",
        (
            CheckSpec("metadata.description", "Repo description", 2, (0, 2), Tag.REMOTE),
            CheckSpec("metadata.topics", "Topics", 1, (0, 1), Tag.REMOTE),
            CheckSpec("metadata.homepage", "Homepage", 1, (0, 1), Tag.REMOTE),
        ),
    ),
    AreaSpec(
        "badges",
        "Badges",
        "—",
        (
            CheckSpec("badges.present", "build / coverage / version / license badges", 3, (0, 1, 2, 3), Tag.LOCAL),
        ),
    ),
    AreaSpec(
        "docker",
        "Docker",
        "Container best practices",
        (
            CheckSpec("docker.present", "Dockerfile/compose + basic good practices", 3, (0, 1, 3), Tag.LOCAL),
        ),
    ),
)

AREA_BY_KEY = {a.key: a for a in AREAS}

# --- Scoring modes (SCORING.md §4) ------------------------------------------
# Each preset assigns a weight per area; every preset sums to exactly 100.

MODE_WEIGHTS: dict[str, dict[str, int]] = {
    "balanced": {
        "readme": 18, "security": 15, "tests": 13, "ci": 12, "license": 8,
        "releases": 8, "structure": 8, "governance": 8, "metadata": 4,
        "badges": 3, "docker": 3,
    },
    "security": {
        "readme": 14, "security": 30, "tests": 10, "ci": 10, "license": 6,
        "releases": 6, "structure": 7, "governance": 7, "metadata": 4,
        "badges": 3, "docker": 3,
    },
    "tests": {
        "readme": 15, "security": 12, "tests": 26, "ci": 11, "license": 7,
        "releases": 6, "structure": 7, "governance": 7, "metadata": 3,
        "badges": 3, "docker": 3,
    },
    "ci": {
        "readme": 15, "security": 13, "tests": 12, "ci": 24, "license": 7,
        "releases": 6, "structure": 7, "governance": 7, "metadata": 3,
        "badges": 3, "docker": 3,
    },
}

MODES = tuple(MODE_WEIGHTS.keys())

# --- Profiles and applicability (SCORING.md §5) -----------------------------

PROFILES = ("library", "service", "cli", "monorepo")

# Areas that are N/A by default per profile. Only Docker flips in v1.
PROFILE_NA: dict[str, frozenset[str]] = {
    "library": frozenset({"docker"}),
    "service": frozenset(),
    "cli": frozenset({"docker"}),
    "monorepo": frozenset(),
}


def validate_rubric() -> None:
    """Fail loudly if the rubric is internally inconsistent. Called on import."""
    base = MODE_WEIGHTS["balanced"]
    for area in AREAS:
        if base[area.key] != area.base_weight:
            raise ValueError(
                f"balanced weight for {area.key} ({base[area.key]}) "
                f"!= sum of check weights ({area.base_weight})"
            )
    for mode, weights in MODE_WEIGHTS.items():
        total = sum(weights.values())
        if total != 100:
            raise ValueError(f"mode {mode!r} weights sum to {total}, expected 100")
        missing = {a.key for a in AREAS} - set(weights)
        if missing:
            raise ValueError(f"mode {mode!r} missing areas: {missing}")


validate_rubric()
