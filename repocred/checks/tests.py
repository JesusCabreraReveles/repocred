"""Area 3 — Tests."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import not_found, read_manifest, result, workflow_files

_TEST_GLOBS = (
    "test/**", "tests/**", "spec/**", "__tests__/**",
    "**/*_test.go", "**/*_test.py", "**/test_*.py",
    "**/*.test.js", "**/*.test.ts", "**/*.spec.js", "**/*.spec.ts",
    "**/*Test.java", "**/*Tests.cs",
)
_TEST_RUNNER = re.compile(
    r"\b(pytest|tox|nox|unittest|npm test|yarn test|pnpm test|jest|vitest|mocha|"
    r"go test|cargo test|mvn test|gradle test|rspec|phpunit|make test|ctest)\b", re.I)
_COVERAGE_FILES = (
    "coverage.xml", "lcov.info", ".coveragerc", "codecov.yml", ".codecov.yml",
    "coverage.json", ".nycrc", ".nycrc.json",
)
_COVERAGE_CONFIG = re.compile(r"(\[tool\.coverage|collectCoverage|--cov|coverage run)", re.I)
_COVERAGE_BADGE = re.compile(r"(codecov\.io|coveralls\.io|/coverage)", re.I)


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    out: list[CheckResult] = []

    # tests exist
    test_paths: list[str] = []
    for g in _TEST_GLOBS:
        test_paths.extend(ctx.glob(g))
    has_tests = bool(test_paths)
    out.append(result("tests.exist", 5 if has_tests else 0,
                      test_paths[0] if has_tests else not_found("test files/dirs")))

    # test command documented
    documented_ev = None
    manifest = read_manifest(ctx)
    if manifest:
        mpath, mtext = manifest
        if re.search(r'"test"\s*:', mtext) or _COVERAGE_CONFIG.search(mtext) or "pytest" in mtext:
            documented_ev = f"{mpath} (test config)"
    if not documented_ev:
        for mk in ("Makefile", "Taskfile.yml", "justfile", "tox.ini", "noxfile.py"):
            f = ctx.find(mk)
            if f and _TEST_RUNNER.search(ctx.read(f) or ""):
                documented_ev = f
                break
    out.append(result("tests.documented", 3 if documented_ev else 0,
                      documented_ev or not_found("documented test command")))

    # tests run in CI
    in_ci_ev = None
    for wf in workflow_files(ctx):
        t = ctx.read(wf) or ""
        if _TEST_RUNNER.search(t):
            in_ci_ev = wf
            break
    out.append(result("tests.in_ci", 3 if in_ci_ev else 0,
                      in_ci_ev or "no test step found in CI"))

    # coverage signal
    cov_file = None
    for c in _COVERAGE_FILES:
        if ctx.find(c) or ctx.exists(c):
            cov_file = ctx.find(c) or c
            break
    cov_signal = bool(cov_file)
    if not cov_signal and manifest and _COVERAGE_CONFIG.search(manifest[1]):
        cov_signal, cov_file = True, f"{manifest[0]} (coverage config)"
    if not cov_signal:
        readme = ctx.find("README.md", "README.rst", "README")
        if readme and _COVERAGE_BADGE.search(ctx.read(readme) or ""):
            cov_signal, cov_file = True, f"{readme} (coverage badge)"

    if cov_signal:
        out.append(result("tests.coverage", 2, str(cov_file)))
    elif has_tests:
        out.append(result("tests.coverage", 1, "tests present, no coverage signal"))
    else:
        out.append(result("tests.coverage", 0, "no tests / no coverage signal"))

    return out
