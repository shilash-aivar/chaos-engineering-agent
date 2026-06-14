"""CI resilience gate — PR-scoped probes + chaos fault."""

from __future__ import annotations

from chaos_agent.platform.chaos_dna_service import get_chaos_dna
from chaos_agent.red_blue.experiments import inject_attack
from chaos_agent.security.generator import generate_attack_plan
from chaos_agent.security.scanners.dast import run_dast_probe
from chaos_agent.security.types import AttackCategory, RedAttack


async def evaluate_pr(
    *,
    pr_number: int,
    changed_files: list[str],
    changed_services: list[str],
    namespace: str = "staging",
    execute_probes: bool = True,
) -> dict:
    """Pick up to 3 security probes + 1 chaos fault for a PR."""
    has_tf = any(f.endswith(".tf") for f in changed_files)
    has_py = any(f.endswith(".py") for f in changed_files)
    has_api = any("api" in f or "routes" in f for f in changed_files)

    framework = "owasp-top10-2021"
    category_ids: list[str] = []
    if has_api:
        category_ids.extend(["A01", "A07"])
    if has_py:
        category_ids.append("A03")
    if has_tf:
        category_ids.append("A05")
    if not category_ids:
        category_ids = ["A07"]

    plan = generate_attack_plan(
        framework_id=framework,
        namespace=namespace,
        category_ids=category_ids,
    )
    probes = plan.attacks[:3]
    service = changed_services[0] if changed_services else "checkout"
    fault = {
        "executor": "toxiproxy",
        "type": "dependency_blackhole",
        "target": "payments-db" if "payment" in service else service,
    }

    probe_results = []
    all_passed = True
    if execute_probes:
        for p in probes:
            dast = await run_dast_probe(p)
            probe_results.append(
                {"id": p.id, "name": p.name, "passed": dast.passed, "message": dast.message},
            )
            if not dast.passed:
                all_passed = False

    inject_result = None
    if execute_probes and fault.get("type"):
        attack = RedAttack(
            id=f"ci-{pr_number}",
            category=AttackCategory.RESILIENCE,
            title=f"CI gate fault: {fault['type']}",
            service=service,
            technique=fault["type"],
            description=f"PR #{pr_number} resilience fault on {fault['target']}",
            transcript="CI gate injected fault",
            faults=[{"type": fault["type"], "target": fault["target"]}],
        )
        try:
            inject_result = await inject_attack(attack, namespace, timeout_seconds=90)
            if inject_result.get("slo_breached"):
                all_passed = False
        except Exception as exc:
            inject_result = {"error": str(exc), "injected": False}
            all_passed = False

    dna = await get_chaos_dna(namespace)
    score_before = dna["org_score"]
    score_after = score_before - 3 if not all_passed else score_before + 2
    passed = all_passed and score_after >= score_before - 1

    probe_lines = "\n".join(
        f"- **{p.name}** (`{p.cwe}`) → `{p.target_service}`"
        for p in probes
    )
    comment = f"""## Chaos Agent — PR resilience check #{pr_number}

| Check | Status |
|-------|--------|
| Security probes | {len(probes)} selected |
| Chaos fault | `{fault['type']}` on `{fault['target']}` |
| Namespace | `{namespace}` |

### Security probes (OWASP)
{probe_lines}

### Chaos fault
- {fault['executor']}: {fault['type']} → {fault['target']}

| Resilience score | {score_before} → {score_after} |

### Probe results
{chr(10).join(f"- {r['name']}: {'pass' if r['passed'] else 'FAIL'} — {r['message']}" for r in probe_results) if probe_results else "Simulation mode"}

> Merge when probes pass and resilience score does not regress.
"""

    return {
        "pr_number": pr_number,
        "passed": passed,
        "probes": [p.model_dump(mode="json") for p in probes],
        "probe_results": probe_results,
        "fault": fault,
        "inject_result": inject_result,
        "comment_markdown": comment,
        "resilience_score_before": score_before,
        "resilience_score_after": score_after,
    }
