# Examples

Real RepoCred output, captured by running the CLI against the calibration fixtures
(`fixtures/`). Regenerate any time — the scoring is deterministic, so these files are stable.

| File | Command |
|---|---|
| [`scorecard-excellent.txt`](scorecard-excellent.txt) | `repocred score <excellent> --audit` |
| [`audit-excellent-with-evidence.txt`](audit-excellent-with-evidence.txt) | `repocred score <excellent> --evidence` |
| [`excellent.json`](excellent.json) | `repocred score <excellent> --json` |
| [`scorecard-excellent-security-mode.txt`](scorecard-excellent-security-mode.txt) | `repocred score <excellent> --mode security` |
| [`scorecard-empty.txt`](scorecard-empty.txt) | `repocred score <empty>` |

> All runs above use `--local` (no `gh`), so remote-only checks (branch protection, CI status,
> repo metadata) show as `unknown` and are disclosed in the verification line — never counted
> as failures. With `gh` available those resolve and coverage reaches 100%.

## Demo GIF (for the top of the main README)

The ~5s GIF in the project README is recorded manually (RepoCred can't record itself). To make it:

1. Pick a real repo (or the `fixtures/excellent` copy).
2. Record a terminal running:
   ```bash
   repocred score . --audit
   ```
   with a tool like [`vhs`](https://github.com/charmbracelet/vhs) (scriptable, reproducible) or
   [`asciinema`](https://asciinema.org) + [`agg`](https://github.com/asciinema/agg).
3. Save it as `examples/demo.gif` and reference it from the main `README.md`.

A ready-to-use `vhs` script lives in [`demo.tape`](demo.tape).
