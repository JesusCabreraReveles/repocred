# Changelog

All notable changes to RepoCred are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org).

## [Unreleased]

## [0.1.0] - 2026-06-28

### Added
- Deterministic scoring CLI implementing rubric v1 (11 areas, 100 points).
- Three check states: verified (`0/partial/full`), `N/A`, and `unknown` with disclosed
  verification coverage.
- Scoring modes (`balanced`, `security`, `tests`, `ci`) and profile autodetection
  (`library`, `service`, `cli`, `monorepo`).
- `--json` output, `--audit` table, and `--fail-under` CI gate (exit codes).
- `.repocred.yml` configuration (profile, mode, weights override, disabled areas, ignore globs).
- Badge generation (static + shields endpoint), refused on incomplete verification.
- `suggest` command: prints ready-to-paste files for a repo's gaps; `--apply` writes them
  (never overwriting existing files).
- Working-tree analysis (tracked + untracked-not-ignored files) so newly added files score immediately.
- Calibration fixtures and a scoring regression test suite.
- Claude Code subagent definition (`agent/repocred.md`).
- `examples/` with real, regenerable CLI output and a `vhs` demo script.

[Unreleased]: https://github.com/JesusCabreraReveles/repocred/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JesusCabreraReveles/repocred/releases/tag/v0.1.0
