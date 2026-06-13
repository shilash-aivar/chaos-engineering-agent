"""CLI entrypoint — `chaos` command."""

import typer

app = typer.Typer(
    name="chaos",
    help="Chaos Engineering Agent — internal resilience CLI",
    no_args_is_help=True,
)


@app.command()
def status() -> None:
    """Show active context, cluster, and agent health."""
    typer.echo("Chaos Agent v0.1.0 — status: not connected")


@app.command()
def run(
    scenario: str = typer.Argument(..., help="Natural language scenario or plan name"),
    namespace: str = typer.Option("staging", "--namespace", "-n"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Describe or run a chaos experiment."""
    typer.echo(f"Scenario: {scenario}")
    typer.echo(f"Namespace: {namespace}")
    if dry_run:
        typer.echo("Dry run — plan only, no fault injection")


@app.command()
def abort(experiment_id: str = typer.Argument(...)) -> None:
    """Abort a running experiment and trigger rollback."""
    typer.echo(f"Aborting experiment {experiment_id}")


@app.command()
def posture_scan() -> None:
    """Scan K8s + AWS posture gaps in current context."""
    typer.echo("Posture scan — not implemented")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
