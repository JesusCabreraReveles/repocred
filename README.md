# RepoCred

> **Point it at a repo, get an auditable health scorecard** — a defensible `Score: X/10` with
> evidence for every point, what's missing, what's weak, and the highest-impact fixes. A Claude
> Code agent plus a deterministic CLI. Zero-friction, CI-ready.

![build](https://img.shields.io/badge/build-passing-brightgreen)
![coverage](https://img.shields.io/badge/coverage-tracked-brightgreen)
![license](https://img.shields.io/badge/license-MIT-blue)
![RepoCred](https://img.shields.io/badge/RepoCred-self--scored-brightgreen)

RepoCred is **not** a star-chaser. It's a repository-health auditor aligned with
[OpenSSF Scorecard](https://github.com/ossf/scorecard), [GitHub Community Standards],
and [SemVer] — usable as a CI quality gate. Three principles separate it from a homemade linter:

1. **Reproducible** — the score is a traceable sum of checks against a versioned rubric, not an opinion. Same input → same score.
2. **Auditable** — every point awarded or withheld cites evidence (`path:line`).
3. **Configurable** — each team tunes profile, weights and thresholds to its own bar.

[GitHub Community Standards]: https://docs.github.com/communities
[SemVer]: https://semver.org

## How it works

RepoCred is **two pieces**:

- A **deterministic CLI** (`repocred`) that runs the checks, computes the score, emits `--json`,
  returns a CI exit code, and generates badges. *All numbers come from here* — there is no model
  in the scoring path, so it's exactly reproducible.
- A **Claude Code subagent** (`agent/repocred.md`) that orchestrates the CLI and renders the
  human-facing scorecard and improvements. It never invents numbers.

See [SCORING.md](SCORING.md) for the full, versioned methodology.

## Installation

```bash
pipx install repocred      # or: pip install repocred
```

Install the Claude Code agent (zero-friction, language-agnostic — it's just a file):

```bash
mkdir -p ~/.claude/agents && cp agent/repocred.md ~/.claude/agents/
```

Then in Claude Code: *"score this repo with RepoCred"*.

## Usage

```bash
repocred score .                 # human scorecard for the current repo
repocred score . --audit         # also print the auditable table
repocred score . --json          # machine-readable output
repocred score . --mode security # re-weight for a security audit
repocred score . --local         # filesystem only, skip remote (gh) checks
```

Example scorecard:

```
📊 RepoCred: 8.7 / 10  ███████████░░     (rubric v1 · profile: library · mode: balanced)

✅ README (16/18)
✅ CI (12/12)
⚠️  Security / supply-chain (8/15)
❌ License (0/8)

💡 Top improvements (by impact):
   1. Add a LICENSE file (MIT is the common default).  [+8 pts]
   2. Add SECURITY.md + enable Dependabot.             [+6 pts]
```

## CI integration

Fail the build below a threshold (a real exit code, not a vibe):

```yaml
- run: pipx install repocred && repocred score . --fail-under 7.0
```

Set the bar (and profile, mode, weights) per repo with `.repocred.yml` — see the example in
this repo.

## Verification modes: `--local` vs `gh`

Some checks (branch protection, CI status, repo metadata) can only be answered via the GitHub
API. RepoCred uses `gh` automatically when available; otherwise it runs `--local` and marks
those checks `unknown` — **excluded from the score and disclosed**, never silently counted as
failures. A `--local` score and a full score are not comparable, and a badge is never generated
from an incompletely-verified run.

## Badge

```bash
repocred badge .            # writes .repocred/badge.json (shields endpoint badge)
repocred badge . --static   # prints a frozen static badge snippet
```

## License

MIT — see [LICENSE](LICENSE). RepoCred scores itself; that's the point.
