"""Ready-to-paste file templates for the `suggest` / `--apply` flow.

Each artifact is tied to the check whose gap it closes. ``suggest`` only offers artifacts
for checks that actually failed (state ``0``), so the output is always relevant to the repo.
Snippets (``path is None``) are paste-only; they are never written to disk.
"""

from __future__ import annotations

import datetime
import subprocess
from dataclasses import dataclass
from typing import Callable

from .context import RepoContext


def _git_author(ctx: RepoContext) -> str:
    try:
        out = subprocess.run(
            ["git", "config", "user.name"], cwd=str(ctx.root),
            capture_output=True, text=True, timeout=10, check=False,
        )
        name = out.stdout.strip()
        if name:
            return name
    except (OSError, subprocess.SubprocessError):
        pass
    return "<copyright holder>"


def _project_name(ctx: RepoContext) -> str:
    return ctx.root.name or "this project"


@dataclass
class Artifact:
    key: str                       # the check key this closes
    path: str | None               # target path; None => paste-only snippet
    title: str
    render: Callable[[RepoContext], str]


def _license_mit(ctx: RepoContext) -> str:
    year = datetime.date.today().year
    holder = _git_author(ctx)
    return f"""MIT License

Copyright (c) {year} {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _security(ctx: RepoContext) -> str:
    return """# Security Policy

## Reporting a vulnerability

Please report security issues **privately** via GitHub Security Advisories
("Report a vulnerability" on the repository's Security tab), not through public issues.
We aim to acknowledge reports within 72 hours.
"""


def _dependabot(ctx: RepoContext) -> str:
    ecosystem = "pip"
    if ctx.find("package.json"):
        ecosystem = "npm"
    elif ctx.find("go.mod"):
        ecosystem = "gomod"
    elif ctx.find("Cargo.toml"):
        ecosystem = "cargo"
    return f"""version: 2
updates:
  - package-ecosystem: "{ecosystem}"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
"""


def _contributing(ctx: RepoContext) -> str:
    return f"""# Contributing to {_project_name(ctx)}

Thanks for contributing!

## Getting started
1. Fork and clone the repo.
2. Create a branch for your change.
3. Add tests and make sure they pass.
4. Open a pull request describing the change.

## Before you submit
- Run the test suite.
- Run the linter/formatter.
"""


def _coc(ctx: RepoContext) -> str:
    return """# Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org)
version 2.1. Be respectful, welcoming and constructive. Report unacceptable behavior to the
maintainers.
"""


def _changelog(ctx: RepoContext) -> str:
    today = datetime.date.today().isoformat()
    return f"""# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org).

## [Unreleased]

## [0.1.0] - {today}

### Added
- Initial release.
"""


def _issue_template(ctx: RepoContext) -> str:
    return """---
name: Bug report
about: Report a problem
labels: bug
---

## Description

## Steps to reproduce

## Expected vs actual
"""


def _pr_template(ctx: RepoContext) -> str:
    return """## Summary

<!-- What does this change and why? -->

## Checklist
- [ ] Tests added/updated
- [ ] Docs updated
"""


def _codeowners(ctx: RepoContext) -> str:
    return "# Default owners for everything in the repo.\n* @your-team\n"


def _gitignore(ctx: RepoContext) -> str:
    common = "# OS / editors\n.DS_Store\nThumbs.db\n.idea/\n.vscode/\n\n"
    if ctx.find("package.json"):
        return common + "# Node\nnode_modules/\ndist/\nbuild/\n*.log\n.env\n"
    if ctx.find("go.mod"):
        return common + "# Go\nbin/\n*.exe\n*.test\n*.out\n"
    if ctx.find("Cargo.toml"):
        return common + "# Rust\n/target/\n"
    return common + "# Python\n__pycache__/\n*.py[cod]\n*.egg-info/\n.venv/\nbuild/\ndist/\n.pytest_cache/\n.coverage\n"


def _badge_snippet(ctx: RepoContext) -> str:
    return """Add status badges near the top of your README:

```markdown
![build](https://img.shields.io/badge/build-passing-brightgreen)
![coverage](https://img.shields.io/badge/coverage-tracked-brightgreen)
![license](https://img.shields.io/badge/license-MIT-blue)
```

For a live RepoCred badge, run: `repocred badge .` (needs full verification via `gh`).
"""


ARTIFACTS: list[Artifact] = [
    Artifact("license.present", "LICENSE", "MIT license", _license_mit),
    Artifact("security.policy", "SECURITY.md", "Security policy", _security),
    Artifact("security.deps_mgmt", ".github/dependabot.yml", "Dependabot config", _dependabot),
    Artifact("releases.changelog", "CHANGELOG.md", "Changelog (Keep a Changelog)", _changelog),
    Artifact("structure.gitignore", ".gitignore", ".gitignore", _gitignore),
    Artifact("governance.contributing", "CONTRIBUTING.md", "Contributing guide", _contributing),
    Artifact("governance.coc", "CODE_OF_CONDUCT.md", "Code of Conduct", _coc),
    Artifact("governance.templates", ".github/ISSUE_TEMPLATE/bug_report.md", "Issue template", _issue_template),
    Artifact("governance.templates", ".github/PULL_REQUEST_TEMPLATE.md", "Pull request template", _pr_template),
    Artifact("governance.codeowners", ".github/CODEOWNERS", "CODEOWNERS", _codeowners),
    Artifact("badges.present", None, "README badges", _badge_snippet),
]
