# RepoCred — Scoring Methodology (`rubric v1`)

> This document is the **single source of truth** for how RepoCred computes a score.
> The CLI implements exactly what is written here; the subagent narrates it. If the CLI
> and this document ever disagree, **this document wins** and the CLI is a bug.
>
> Every score RepoCred emits declares the rubric version (`rubric v1`), the scoring
> **mode**, the detected **profile**, and the **verification coverage**. Change the rubric →
> bump the version. Reproducibility over time depends on this.

## Architecture note (read this first)

RepoCred is **two pieces that must not be confused**:

1. **A deterministic CLI** (Python). It runs the checks, computes the score, emits
   `--json`, returns a CI exit code, and generates the badge. *All numbers come from here.*
   Same input → same score, byte-for-byte. There is no model in the scoring path.
2. **A Claude Code subagent** (`agent/repocred.md`). It orchestrates the CLI, interprets
   the few judgment checks, and renders the human-facing scorecard and the prioritized
   improvements. It never invents numbers.

This split is the whole credibility story: the score is **code**, the prose is the agent.

---

## 1. The scoring model

Each **area** has a fixed point weight. Each area contains **checks**. Each check resolves
to one of a small set of discrete levels (e.g. `0 / partial / full`) — never a continuous
"4.5 because roughly". A check earns points **only with evidence** (a `path:line`, a `gh`
API field, or an explicit "not found").

```
score = (points_earned / points_applicable) × 10
```

Rounded to **1 decimal, half-up** (`6.185 → 6.2`).

- `points_applicable` is the sum of weights of all checks that are **APPLICABLE and VERIFIED**
  (states `full`, `partial`, or `0`). See §2.
- `points_earned` is the sum of points actually awarded.

### Worked example

```
README        16/18   Security       4/15   Tests        11/13
CI            12/12   License        0/8    Releases      0/8
Structure      7/8    Governance     3/8    Metadata      4/4
Badges         3/3    Docker         N/A

Applicable: 97   Earned: 60   Score: 60 / 97 × 10 = 6.185 → 6.2
```

---

## 2. The three check states (the credibility core)

A check is never just "pass/fail". It is one of:

| State | Meaning | In denominator? | In numerator? |
|---|---|---|---|
| `full` / `partial` / `0` | Applicable, **verified**, earned full / some / no points | ✅ yes | yes / some / no |
| `N/A` | **Does not apply** to this profile (e.g. Docker for a pure library) | ❌ no | no |
| `unknown` | Applies, but **could not be verified** in this run (e.g. `--local` can't see branch protection) | ❌ no | no |

The difference between `N/A` and `unknown` is the heart of honest scoring:

- `N/A` removes a check we *deliberately don't grade*. Safe to exclude.
- `unknown` removes a check we *wanted to grade but couldn't*. Excluding it keeps the score
  from being unfairly penalized — **but it silently inflates the score unless we disclose it.**

So every report carries a **verification coverage**: the share of the *applicable* rubric
that was actually verified.

```
coverage = verified_points / (verified_points + unknown_points)
```

Reported as, e.g., `local — 84/100 pts verified`. A run with low coverage is loudly flagged.

### Hard rules derived from this

1. **A `--local` run and a `gh`-enabled run are NOT comparable.** Same as modes: the report,
   badge, and JSON always declare the verification mode.
2. **The badge is NEVER generated from a run with `unknown` checks** (i.e. never from `--local`,
   or from any run where remote-only checks couldn't be resolved). A partial score may not be
   published as if it were complete. `repocred badge` refuses and tells the user to run with `gh`.
3. **Modes are not comparable to each other** (a repo scores differently in `security` vs
   `balanced`). The mode is always declared.

---

## 3. Verification modes: `--local` vs `gh`

Some checks cannot be answered from a filesystem clone alone. RepoCred tags every check as
`local`, `remote`, or `hybrid`:

- **`local`** — answerable from the working tree / git history. Always evaluated.
- **`remote`** — needs the GitHub API (`gh`). In `--local` → `unknown`.
- **`hybrid`** — has a *local signal* and a *stronger remote signal*. In `--local` we grade the
  local signal and note the limitation; with `gh` we use the authoritative remote signal.

Default: RepoCred uses `gh` if it is installed **and** authenticated **and** a GitHub remote is
detected; otherwise it runs `--local` automatically and says so. `--local` forces local-only.

The genuinely **remote-only** checks (→ `unknown` in `--local`) are just:
`branch protection`, `secret scanning enabled`, `CI status (green on last commit)`,
and `repo metadata (description / topics / homepage)`. Everything else has a local answer.

---

## 4. Scoring modes (weight presets)

A mode is a named preset of area weights. **Every preset sums to exactly 100.** Raising one
area lowers the rest proportionally, so N/A/`unknown` renormalization always holds.

| Area | `balanced` | `security` | `tests` | `ci` |
|---|---:|---:|---:|---:|
| 1 README | 18 | 14 | 15 | 15 |
| 2 Security / supply-chain | 15 | **30** | 12 | 13 |
| 3 Tests | 13 | 10 | **26** | 12 |
| 4 CI | 12 | 10 | 11 | **24** |
| 5 License | 8 | 6 | 7 | 7 |
| 6 Releases / versioning | 8 | 6 | 6 | 6 |
| 7 Structure / hygiene | 8 | 7 | 7 | 7 |
| 8 Governance / community | 8 | 7 | 7 | 7 |
| 9 Metadata | 4 | 4 | 3 | 3 |
| 10 Badges | 3 | 3 | 3 | 3 |
| 11 Docker | 3 | 3 | 3 | 3 |
| **Total** | **100** | **100** | **100** | **100** |

> The non-`balanced` presets above are the **calibration starting point**, not final. They are
> tuned against the fixtures (§9): a known-excellent repo must land 9+ in each mode. See "Open
> calibration" at the end.

### Sub-check rescaling (resolved)

When an area's weight changes (via a mode or a `weights:` override), its checks keep their
**relative proportions** and are rescaled to the new area total, then rounded half-up with the
largest-remainder method so the sub-checks still sum to the area weight. Example: README's
`18 = 4/4/3/4/3`; under `security` (14) it becomes `3/3/2/3/3 = 14`. The CLI does this
deterministically; the breakdown table always shows the *effective* sub-weights used.

---

## 5. Profiles and the applicability matrix

The profile decides **which areas apply**; the mode decides **how they're weighted**. Two
independent axes.

### Detection (deterministic, first match wins)

1. **`monorepo`** — multiple independent package manifests in sibling subdirectories
   (e.g. `packages/*/package.json`, `apps/*/`, a `pnpm-workspace.yaml`, `go.work`, Cargo
   workspace, Nx/Turbo config).
2. **`service`** — a deployable: `Dockerfile`/`compose`, a `Procfile`, k8s/helm manifests, or a
   web framework entrypoint, **and** no library publish manifest.
3. **`cli`** — declares a binary/console entrypoint (`[project.scripts]`, `bin` in
   `package.json`, `cmd/` in Go, etc.) and is not primarily a service.
4. **`library`** — publishable package manifest with no service/CLI markers (default fallback).

Profile is overridable in `.repocred.yml`. The chosen profile is always declared in the report.

### Applicability matrix (default; overridable per-repo)

| Area | library | service | cli | monorepo |
|---|:--:|:--:|:--:|:--:|
| 1 README | ✓ | ✓ | ✓ | ✓ |
| 2 Security | ✓ | ✓ | ✓ | ✓ |
| 3 Tests | ✓ | ✓ | ✓ | ✓ |
| 4 CI | ✓ | ✓ | ✓ | ✓ |
| 5 License | ✓ | ✓ | ✓ | ✓ |
| 6 Releases / versioning | ✓ | ✓ | ✓ | ✓ |
| 7 Structure | ✓ | ✓ | ✓ | ✓ |
| 8 Governance | ✓ | ✓ | ✓ | ✓ |
| 9 Metadata | ✓ | ✓ | ✓ | ✓ |
| 10 Badges | ✓ | ✓ | ✓ | ✓ |
| 11 Docker | **N/A** | ✓ | **N/A** | ✓ |

Only **Docker** flips by profile in v1 (N/A for `library` and `cli`, since a container is not
expected there). This is intentionally conservative: a repo is graded on what its kind of
project genuinely needs, and nothing more. `.repocred.yml` can mark any area `off` → `N/A`.

---

## 6. The rubric — areas, checks, triggers, tags

Notation per check: `points [level set] (tag)`. `tag` ∈ `local` / `remote` / `hybrid`.
Each awarded level requires **evidence**; "not found" is itself valid evidence for `0`.

### 1. README — 18 (GitHub Community Standards)
```
├─ Exists and is non-trivial (> 10 non-blank lines)      4  [0 / 4]   (local)
├─ Clear tagline on first heading/line ("what for")      4  [0 / 2 / 4](local, judgment)
├─ Install section with an executable block               3  [0 / 3]   (local)
├─ Usage + runnable examples                              4  [0 / 2 / 4](local, judgment)
└─ Structured sections (≥3 meaningful headings)           3  [0 / 3]   (local)
```
Triggers: tagline `4` = first non-title line states what the project is *and* who it's for;
`2` = a description exists but vague. Usage `4` = a fenced code block showing real invocation;
`2` = prose-only usage.

### 2. Security / supply-chain — 15 (OpenSSF Scorecard)
```
├─ SECURITY.md (disclosure policy)                        3  [0 / 3]   (local)
├─ Dependency management config present                   3  [0 / 3]   (local)   ← .github/dependabot.yml | renovate.json | mend
├─ No secrets committed                                   3  [0 / 3]   (local)   ← gitleaks-style scan of tree + history
├─ Branch protection on default branch                    2  [0 / 2]   (remote)
├─ Minimal token permissions in CI workflows              2  [0 / 2]   (local)   ← `permissions:` blocks scoped down
└─ Pinned deps / lockfile present                         2  [0 / 2]   (local)
```
> Note: "secret **scanning** enabled" (a GitHub setting) is folded into branch-protection-tier
> remote posture and is *not* a separate point in v1, to avoid over-weighting one GitHub toggle.
> The committed-secrets check above is local and always evaluated.

### 3. Tests — 13
```
├─ Tests exist (test dir / *_test.* / test_*.*)          5  [0 / 5]   (local)
├─ Test command documented (manifest scripts / README)   3  [0 / 3]   (local)
├─ Tests run in CI                                        3  [0 / 3]   (local)   ← test invocation in a workflow
└─ Coverage signal present                                2  [0 / 1 / 2](local)
```
Coverage trigger (resolved — no fragile percentage parsing): `2` = a coverage report or config
exists (`coverage.xml`, `lcov.info`, `.coveragerc`, `codecov.yml`, jest `collectCoverage`, etc.)
**or** a coverage badge in README; `1` = tests exist but no coverage signal; `0` = no tests.

### 4. CI — 12 (OpenSSF CI-Tests)
```
├─ Workflows present (.github/workflows/*)               4  [0 / 4]   (local)
├─ Lint configured (in CI or repo linter config)         3  [0 / 3]   (local)
├─ Build/test automated in CI                            3  [0 / 3]   (local)
└─ CI green on last commit                               2  [0 / 2]   (remote)
```

### 5. License — 8 (GitHub / SPDX) — binary and critical
```
├─ LICENSE file present                                  6  [0 / 6]   (local)
└─ Recognized SPDX license, declared                     2  [0 / 2]   (local)
```

### 6. Releases / versioning — 8 (SemVer + Keep a Changelog)
```
├─ Tags / releases exist                                 3  [0 / 3]   (hybrid)  ← git tags (local) ∪ GitHub Releases (remote)
├─ CHANGELOG (Keep a Changelog shape)                    3  [0 / 3]   (local)
└─ Consistent versioning (SemVer)                        2  [0 / 2]   (local)
```

### 7. Structure / hygiene — 8 (stack conventions)
```
├─ Layout coherent with the stack                        3  [0 / 3]   (local, judgment)
├─ No cruft (build artifacts, temp, .DS_Store…)          2  [0 / 2]   (local)
└─ Adequate .gitignore                                   3  [0 / 3]   (local)
```
> The old "no sensitive config committed" 1-pt check was **removed to avoid double-counting**
> with Security §2 "No secrets committed". Its point was reallocated to `.gitignore` (2→3),
> keeping the area at 8.

### 8. Governance / community — 8 (GitHub Community Standards)
```
├─ CONTRIBUTING.md                                       3  [0 / 3]   (local)
├─ CODE_OF_CONDUCT.md                                    2  [0 / 2]   (local)
├─ Issue/PR templates                                    2  [0 / 2]   (local)
└─ CODEOWNERS                                            1  [0 / 1]   (local)
```

### 9. Metadata — 4 (GitHub discoverability)
```
├─ Repo description                                      2  [0 / 2]   (remote)
├─ Topics                                                1  [0 / 1]   (remote)
└─ Homepage                                              1  [0 / 1]   (remote)
```
Entirely remote → `unknown` under `--local`.

### 10. Badges — 3
```
└─ build / coverage / version / license badges in README   [0 / 1 / 2 / 3]  (local)
```
One point per distinct category present, capped at 3.

### 11. Docker — 3 (N/A for library & cli by default)
```
└─ Dockerfile/compose present + basic good practices       [0 / 1 / 3]  (local)
```
`1` = a Dockerfile exists; `3` = also follows basics (pinned base image, non-root user,
`.dockerignore`, multi-stage or slim base).

---

## 7. Evidence (the anti-arbitrariness rule)

- Every awarded or denied point ships with evidence: `path:line`, a `gh` field name, or
  an explicit `not found`.
- No evidence → no points. A check that *can't* gather evidence in this run is `unknown`,
  not `0`.
- The `--json` output carries the full evidence list so a reviewer can audit every cell.

---

## 8. Configuration (`.repocred.yml`)

```yaml
profile: library            # library | service | cli | monorepo  (default: autodetect)
mode: balanced              # balanced | security | tests | ci
fail_under: 7.0             # CI gate: exit ≠ 0 below this

weights:                    # fine override on top of the mode (optional)
  security: 20              # see renormalization rule below

checks:
  docker: off               # force an area to N/A
  badges: off

ignore:
  - "examples/**"           # paths excluded from analysis
  - "vendor/**"
```

### `weights:` override semantics (resolved)

An override sets the *target* weight for the named area(s). The CLI then **renormalizes all
other (non-overridden, applicable) areas proportionally so the total returns to 100.** This
preserves the "every configuration sums to 100" invariant and keeps N/A/`unknown`
renormalization consistent. The effective weights (post-renormalization) are printed in the
report so the math is never hidden.

---

## 9. Calibration & regression (why it won't drift)

- **Fixture repos with expected scores** (`fixtures/`): known repos with a target score and a
  tolerance. Excellent → 9+, empty → 2–3, intermediate cases bounded. `pytest` fails the build
  if the score drifts outside tolerance. This is the scoring regression test.
- **Determinism**: because scoring is pure code with no model in the path, the tolerance is
  **exact** (±0.0) for a given rubric version, profile, mode, and verification mode. The ±0.1
  tolerance only ever covers half-up rounding boundaries.
- **Public calibration**: this file plus the fixture results are the published proof.

## 10. Versioning

`rubric v1`. Any change to weights, checks, triggers, profiles, or the matrix bumps the rubric
version. Every report prints `RepoCred vX / rubric vY` so a score is reproducible and comparable
across time.

## Open calibration (not yet locked)

- Final weights for the `security` / `tests` / `ci` presets. The `balanced` base and the presets
  in §4 are a proposal; they get tuned once the fixtures exist so a known-excellent repo lands
  9+ in every mode. The CLI reads weights from a versioned table, so retuning = a rubric bump,
  not a code rewrite.
