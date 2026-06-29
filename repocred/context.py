"""Repository context: the filesystem / git / GitHub facts that checks read from.

A check never shells out on its own; it asks the context. This keeps checks pure and
makes ``--local`` vs ``gh`` behaviour live in exactly one place.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_IGNORE_ALWAYS = (".git/**", ".git")
_UNSET = object()


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a gitignore-ish glob (supporting ``**``) to a regex."""
    i, n, out = 0, len(pattern), []
    while i < n:
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def _run(args: list[str], cwd: Path) -> str | None:
    try:
        proc = subprocess.run(
            args, cwd=str(cwd), capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


@dataclass
class GitInfo:
    tags: list[str]
    default_branch: str | None
    owner: str | None
    repo: str | None

    @property
    def slug(self) -> str | None:
        if self.owner and self.repo:
            return f"{self.owner}/{self.repo}"
        return None


def _parse_remote(url: str) -> tuple[str | None, str | None]:
    url = url.strip()
    m = re.search(r"github\.com[:/]+([^/]+)/(.+?)(?:\.git)?/?$", url)
    if m:
        return m.group(1), m.group(2)
    return None, None


def load_git_info(root: Path) -> GitInfo | None:
    if not shutil.which("git"):
        return None
    inside = _run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if not inside or inside.strip() != "true":
        return None
    tags_out = _run(["git", "tag", "--list"], root) or ""
    tags = [t for t in tags_out.splitlines() if t.strip()]
    head = _run(["git", "symbolic-ref", "--short", "-q", "HEAD"], root)
    default_branch = head.strip() if head else None
    remote = _run(["git", "remote", "get-url", "origin"], root)
    owner = repo = None
    if remote:
        owner, repo = _parse_remote(remote)
    return GitInfo(tags=tags, default_branch=default_branch, owner=owner, repo=repo)


class GhClient:
    """Thin wrapper over the ``gh`` CLI for remote checks. Construct via :meth:`maybe`."""

    def __init__(self, slug: str):
        self.slug = slug
        self._repo_view: dict | None | object = _UNSET

    @classmethod
    def maybe(cls, git: GitInfo | None) -> GhClient | None:
        if git is None or git.slug is None:
            return None
        if not shutil.which("gh"):
            return None
        # Confirm authentication without leaking anything to stdout.
        try:
            status = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, timeout=15, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if status.returncode != 0:
            return None
        return cls(git.slug)

    def _api(self, path: str) -> object | None:
        try:
            proc = subprocess.run(
                ["gh", "api", path], capture_output=True, text=True, timeout=30, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if proc.returncode != 0:
            return None
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return None

    def repo_view(self) -> dict | None:
        if self._repo_view is _UNSET:
            data = self._api(f"repos/{self.slug}")
            self._repo_view = data if isinstance(data, dict) else None
        return self._repo_view  # type: ignore[return-value]

    def branch_protection(self, branch: str) -> bool | None:
        data = self._api(f"repos/{self.slug}/branches/{branch}/protection")
        if data is None:
            # Could be "not protected" (404) or an access error; treat as unprotected
            # only if we can otherwise reach the repo.
            return False if self.repo_view() is not None else None
        return isinstance(data, dict)

    def latest_run_conclusion(self, branch: str) -> str | None:
        data = self._api(f"repos/{self.slug}/actions/runs?branch={branch}&per_page=1")
        if not isinstance(data, dict):
            return None
        runs = data.get("workflow_runs") or []
        if not runs:
            return ""  # reachable, but no runs
        return str(runs[0].get("conclusion") or "")


@dataclass
class RepoContext:
    root: Path
    local_only: bool
    ignore: list[str] = field(default_factory=list)
    git: GitInfo | None = None
    gh: GhClient | None = None
    files: list[str] = field(default_factory=list)
    read_files: list[str] = field(default_factory=list)  # audit trail (SECURITY.md)

    @classmethod
    def build(cls, root: Path, local_only: bool, ignore: list[str]) -> RepoContext:
        root = root.resolve()
        git = load_git_info(root)
        gh = None if local_only else GhClient.maybe(git)
        ctx = cls(root=root, local_only=local_only or gh is None, ignore=list(ignore), git=git, gh=gh)
        ctx.files = ctx._list_files()
        return ctx

    # --- file discovery -----------------------------------------------------
    def _ignored(self, rel: str) -> bool:
        for pat in (*_IGNORE_ALWAYS, *self.ignore):
            if _glob_to_regex(pat).match(rel):
                return True
        return False

    def _list_files(self) -> list[str]:
        out = _run(["git", "ls-files"], self.root) if self.git else None
        if out is not None:
            rels = [line for line in out.splitlines() if line]
        else:
            rels = [
                p.relative_to(self.root).as_posix()
                for p in self.root.rglob("*")
                if p.is_file()
            ]
        return sorted(r for r in rels if not self._ignored(r))

    # --- queries used by checks ---------------------------------------------
    def exists(self, rel: str) -> bool:
        return rel in self._fileset

    @property
    def _fileset(self) -> set[str]:
        return set(self.files)

    def find(self, *names: str) -> str | None:
        """Return the first top-level file matching any name, case-insensitively."""
        lower = {n.lower() for n in names}
        for f in self.files:
            if "/" not in f and f.lower() in lower:
                return f
        return None

    def glob(self, pattern: str) -> list[str]:
        rx = _glob_to_regex(pattern)
        return [f for f in self.files if rx.match(f)]

    def read(self, rel: str) -> str | None:
        path = self.root / rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        if rel not in self.read_files:
            self.read_files.append(rel)
        return text
