"""Command-line entry point `aerialrange`. Sub-commands mirror the Makefile targets."""

from __future__ import annotations

import runpy

import typer

from aerialrange.utils.config import REPO_ROOT

app = typer.Typer(help="Aerial tracking and ranging.", no_args_is_help=True)


def _run_script(name: str) -> None:
    runpy.run_path(str(REPO_ROOT / "scripts" / name), run_name="__main__")


@app.command("data-check")
def data_check() -> None:
    """Check dataset presence and schemas."""
    _run_script("check_data.py")


@app.command("env")
def env() -> None:
    """Write results/env.json."""
    _run_script("env_report.py")


if __name__ == "__main__":
    app()
