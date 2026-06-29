"""Actionable, impact-ordered suggestions keyed by check.

Used by the scorecard's "Top improvements" block and (later) by ``--suggest``.
Keep each suggestion short, concrete and standard-aligned.
"""

from __future__ import annotations

SUGGESTIONS: dict[str, str] = {
    "readme.exists": "Add a README describing the project.",
    "readme.tagline": "Open the README with a one-line tagline: what it does and who it's for.",
    "readme.install": "Add an Install section with a copy-pasteable command block.",
    "readme.usage": "Add a Usage section with a runnable example in a code block.",
    "readme.sections": "Structure the README with clear section headings.",
    "security.policy": "Add SECURITY.md with a vulnerability disclosure policy.",
    "security.deps_mgmt": "Enable Dependabot or Renovate (commit the config file).",
    "security.no_secrets": "Remove the committed secret and rotate it; add a secret scanner.",
    "security.branch_protection": "Enable branch protection on the default branch.",
    "security.token_perms": "Add a scoped `permissions:` block to CI workflows (least privilege).",
    "security.pinned_deps": "Commit a lockfile so dependencies are pinned.",
    "tests.exist": "Add an automated test suite.",
    "tests.documented": "Document the test command (manifest script or README).",
    "tests.in_ci": "Run the tests in CI on every push/PR.",
    "tests.coverage": "Collect and report test coverage.",
    "ci.workflows": "Add a CI workflow (e.g. .github/workflows/ci.yml).",
    "ci.lint": "Add a linter and run it in CI.",
    "ci.build_test": "Add a build/test job to CI.",
    "ci.green": "Fix the failing CI run on the default branch.",
    "license.present": "Add a LICENSE file (MIT is the common default).",
    "license.spdx": "Use a recognized SPDX license and declare it in the manifest.",
    "releases.tags": "Cut a first tagged release (e.g. v0.1.0).",
    "releases.changelog": "Add a CHANGELOG.md following Keep a Changelog.",
    "releases.semver": "Adopt SemVer for version tags.",
    "structure.layout": "Organize sources into a conventional layout (e.g. src/).",
    "structure.no_cruft": "Remove committed build artifacts / OS cruft and gitignore them.",
    "structure.gitignore": "Add a meaningful .gitignore for your stack.",
    "governance.contributing": "Add CONTRIBUTING.md with how to contribute.",
    "governance.coc": "Add a CODE_OF_CONDUCT.md.",
    "governance.templates": "Add issue and pull-request templates under .github/.",
    "governance.codeowners": "Add a CODEOWNERS file.",
    "metadata.description": "Set the repository description on GitHub.",
    "metadata.topics": "Add topics to improve discoverability.",
    "metadata.homepage": "Set the repository homepage URL.",
    "badges.present": "Add status badges (build, coverage, version, license) to the README.",
    "docker.present": "Add a Dockerfile following basics (pinned base, non-root, .dockerignore).",
}


def suggestion_for(key: str) -> str:
    return SUGGESTIONS.get(key, "Improve this check.")
