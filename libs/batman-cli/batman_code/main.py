"""CLI entry point for bat-code."""

from __future__ import annotations

import argparse


def cli_main() -> None:
    """Entry point for the `bat-code` console script."""
    parser = argparse.ArgumentParser(
        prog="bat-code",
        description="Batman-themed AI coding assistant.",
    )
    parser.add_argument(
        "--no-splash",
        action="store_true",
        default=False,
        help="Skip the Batcave loading animation.",
    )
    args = parser.parse_args()

    from batman_code.app import BatmanApp  # noqa: PLC0415

    app = BatmanApp(no_splash=args.no_splash)
    app.run()
