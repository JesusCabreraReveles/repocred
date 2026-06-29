"""Command-line interface.

Exit codes:
  0  success (and, if a gate is set, score >= fail_under)
  1  score below fail_under (CI gate)
  2  configuration or usage error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, badge, jsonout, render
from .analyze import analyze
from .config import ConfigError
from .rubric import MODES, PROFILES

EXIT_OK = 0
EXIT_GATE = 1
EXIT_ERROR = 2


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("path", nargs="?", default=".", help="repository path (default: .)")
    p.add_argument("--mode", choices=MODES, help="scoring mode (overrides config)")
    p.add_argument("--profile", choices=PROFILES, help="project profile (overrides autodetect)")
    p.add_argument("--local", action="store_true", help="skip all remote (gh) checks")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repocred",
        description="Auditable repository health scorecard, aligned with OpenSSF / GitHub standards.",
    )
    parser.add_argument("--version", action="version", version=f"repocred {__version__}")
    sub = parser.add_subparsers(dest="command")

    score = sub.add_parser("score", help="analyze a repo and print its scorecard (default)")
    _add_common(score)
    score.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    score.add_argument("--audit", action="store_true", help="also print the auditable table")
    score.add_argument("--evidence", action="store_true", help="include per-check evidence (implies --audit)")
    score.add_argument("--fail-under", type=float, metavar="N",
                       help="exit 1 if score < N (CI gate; overrides config)")

    bdg = sub.add_parser("badge", help="generate a badge (refuses on incomplete verification)")
    _add_common(bdg)
    group = bdg.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true",
                       help="write .repocred/badge.json (endpoint badge; default)")
    group.add_argument("--print", dest="print_json", action="store_true",
                       help="print the endpoint badge.json to stdout")
    group.add_argument("--static", action="store_true",
                       help="print a frozen static badge markdown snippet")
    bdg.add_argument("--endpoint-url", metavar="RAW_URL",
                     help="print endpoint badge markdown for this committed badge.json raw URL")
    return parser


def _run_score(args: argparse.Namespace) -> int:
    analysis = analyze(
        Path(args.path), __version__,
        mode_override=args.mode, profile_override=args.profile, local=args.local,
    )
    report = analysis.report

    if args.json:
        print(jsonout.to_json(report, files_read=analysis.context.read_files))
    else:
        print(render.render_scorecard(report))
        if args.audit or args.evidence:
            print("\n" + render.render_audit(report, show_evidence=args.evidence))

    fail_under = args.fail_under if args.fail_under is not None else analysis.config.fail_under
    if fail_under is not None and float(report.score) < fail_under:
        if not args.json:
            print(f"\n✗ score {report.score} is below fail_under {fail_under}", file=sys.stderr)
        return EXIT_GATE
    return EXIT_OK


def _run_badge(args: argparse.Namespace) -> int:
    analysis = analyze(
        Path(args.path), __version__,
        mode_override=args.mode, profile_override=args.profile, local=args.local,
    )
    report = analysis.report
    try:
        if args.static:
            print(badge.static_markdown(report))
        elif args.endpoint_url:
            print(badge.endpoint_markdown(report, args.endpoint_url))
        elif args.print_json:
            print(badge.endpoint_json(report))
        else:  # default: write
            content = badge.endpoint_json(report)
            out_dir = Path(args.path) / ".repocred"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "badge.json"
            out_path.write_text(content + "\n", encoding="utf-8")
            print(f"wrote {out_path}")
            print("Embed in your README (public repos):")
            print("  " + badge.endpoint_markdown(
                report,
                "https://raw.githubusercontent.com/OWNER/REPO/BRANCH/.repocred/badge.json",
            ))
    except badge.BadgeRefused as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    # Default to the `score` subcommand when none is given.
    passthrough = {"score", "badge", "-h", "--help", "--version"}
    if not raw:
        raw = ["score"]
    elif raw[0] not in passthrough:
        raw = ["score", *raw]

    parser = build_parser()
    args = parser.parse_args(raw)

    try:
        if args.command == "badge":
            return _run_badge(args)
        return _run_score(args)
    except ConfigError as exc:
        print(f"✗ config error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except FileNotFoundError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
