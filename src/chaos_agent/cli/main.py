"""CLI entrypoint — `chaos` command."""

from __future__ import annotations

import json
import os

import httpx
import typer

app = typer.Typer(
    name="chaos",
    help="Chaos Engineering Agent — internal resilience CLI",
    no_args_is_help=True,
)

DEFAULT_API = os.environ.get("CHAOS_AGENT_API_URL", "http://127.0.0.1:8000")


def _client() -> httpx.Client:
    return httpx.Client(base_url=DEFAULT_API, timeout=60.0)


@app.command()
def status() -> None:
    """Show API health and agent runtime status."""
    with _client() as client:
        health = client.get("/health").json()
        agents = client.get("/agents/status").json()
    typer.echo(f"API: {health.get('status', 'unknown')}")
    typer.echo(f"Agents: {json.dumps(agents.get('agents', {}), indent=2)}")


@app.command()
def compose(
    scenario: str = typer.Argument(..., help="Natural language scenario"),
    namespace: str = typer.Option("staging", "--namespace", "-n"),
) -> None:
    """Compose an experiment plan from a scenario."""
    with _client() as client:
        resp = client.post("/experiments/compose", json={"scenario": scenario, "namespace": namespace})
        resp.raise_for_status()
        data = resp.json()
    typer.echo(f"Composer: {data.get('composer', 'rules')}")
    typer.echo(json.dumps(data["plan"], indent=2))


@app.command()
def run(
    scenario: str = typer.Argument(..., help="Natural language scenario"),
    namespace: str = typer.Option("staging", "--namespace", "-n"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Compose and run a chaos experiment."""
    with _client() as client:
        composed = client.post(
            "/experiments/compose",
            json={"scenario": scenario, "namespace": namespace},
        ).json()
        if dry_run:
            typer.echo(json.dumps(composed["plan"], indent=2))
            return
        created = client.post("/experiments", json=composed["plan"]).json()
    typer.echo(f"Started experiment {created['id']} — state={created['state']}")


@app.command()
def abort(experiment_id: str = typer.Argument(...)) -> None:
    """Abort a running experiment and trigger rollback."""
    with _client() as client:
        resp = client.post(f"/experiments/{experiment_id}/abort")
        resp.raise_for_status()
    typer.echo(f"Abort requested for {experiment_id}")


@app.command(name="compose-full")
def compose_full_cmd(
    scenario: str = typer.Argument(..., help="Natural language scenario"),
    namespace: str = typer.Option("staging", "--namespace", "-n"),
) -> None:
    """Compose plan + pre-mortem + referee validation."""
    with _client() as client:
        resp = client.post(
            "/experiments/compose-full",
            json={"scenario": scenario, "namespace": namespace},
        )
        resp.raise_for_status()
        data = resp.json()
    typer.echo(f"Composer: {data.get('composer')} · Referee: {data.get('referee')}")
    typer.echo(json.dumps(data["plan"], indent=2))


@app.command()
def approve(experiment_id: str = typer.Argument(...)) -> None:
    """Approve a production experiment awaiting referee sign-off."""
    with _client() as client:
        resp = client.post(f"/experiments/{experiment_id}/approve")
        resp.raise_for_status()
    typer.echo(f"Approved {experiment_id}")


@app.command()
def verify(
    experiment_id: str = typer.Argument(...),
    finding_id: str = typer.Argument(...),
) -> None:
    """Re-run experiment to verify a remediation finding."""
    with _client() as client:
        resp = client.post(f"/remediation/experiments/{experiment_id}/findings/{finding_id}/verify")
        resp.raise_for_status()
        data = resp.json()
    typer.echo(json.dumps(data, indent=2))


@app.command(name="ci-gate")
def ci_gate(
    pr_number: int = typer.Argument(...),
    files: str = typer.Option("", "--files", help="Comma-separated changed files"),
    services: str = typer.Option("checkout", "--services", help="Comma-separated services"),
) -> None:
    """Evaluate PR resilience gate (local script, no API required)."""
    import asyncio

    from chaos_agent.ci_gate.evaluator import evaluate_pr

    changed_files = [f.strip() for f in files.split(",") if f.strip()]
    changed_services = [s.strip() for s in services.split(",") if s.strip()]
    result = asyncio.run(
        evaluate_pr(
            pr_number=pr_number,
            changed_files=changed_files,
            changed_services=changed_services,
            execute_probes=False,
        ),
    )
    typer.echo(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise typer.Exit(code=1)


@app.command(name="posture-scan")
def posture_scan(namespace: str = typer.Option("staging", "--namespace", "-n")) -> None:
    """Scan K8s + AWS posture gaps in current context."""
    with _client() as client:
        data = client.get("/posture/scan", params={"namespace": namespace}).json()
    typer.echo(f"Gaps: {len(data.get('gaps', []))}")
    for gap in data.get("gaps", [])[:10]:
        typer.echo(f"  [{gap['severity']}] {gap['service']}: {gap['message']}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
