# Contributing to RepoCred

Thanks for helping make repository health auditable!

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a PR

- Run the tests: `pytest`
- Run the linter: `ruff check .`
- RepoCred must keep scoring itself near-perfect: `repocred score .`

## Changing the rubric

Any change to weights, checks, triggers, profiles or the applicability matrix is a **rubric
change**: update [SCORING.md](SCORING.md), bump `RUBRIC_VERSION` in `repocred/rubric.py`, and
update the calibration fixtures so the regression tests still pass. The rubric and the code
must never disagree.

## Reporting bugs

Open an issue using the bug report template, including the repo type and the `--json` output.
