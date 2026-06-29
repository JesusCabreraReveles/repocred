"""Check evaluators, one module per rubric area."""

from __future__ import annotations

from . import (
    badges,
    ci,
    docker,
    governance,
    license,
    metadata,
    readme,
    releases,
    security,
    structure,
    tests,
)

# Maps each area key to its evaluator. Order is irrelevant here; the rubric defines it.
EVALUATORS = {
    "readme": readme.evaluate,
    "security": security.evaluate,
    "tests": tests.evaluate,
    "ci": ci.evaluate,
    "license": license.evaluate,
    "releases": releases.evaluate,
    "structure": structure.evaluate,
    "governance": governance.evaluate,
    "metadata": metadata.evaluate,
    "badges": badges.evaluate,
    "docker": docker.evaluate,
}
