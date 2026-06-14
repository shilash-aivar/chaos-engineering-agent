"""Red vs Blue campaign orchestration — DB-backed with optional security/DAST."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from chaos_agent.blue.service import defend_red_attack
from chaos_agent.blue.remediation import open_blue_pr, verify_round
from chaos_agent.config import get_settings
from chaos_agent.posture.scanner import PostureScanner
from chaos_agent.red.service import plan_red_attack
from chaos_agent.red_blue.experiments import inject_attack
from chaos_agent.referee.scorer import score_round
from chaos_agent.security.catalog import list_security_attacks
from chaos_agent.security.generator import generate_attack_plan
from chaos_agent.security.scanners.dast import run_dast_probe
from chaos_agent.security.types import CampaignDetail, GeneratedAttackPlan, SecurityAttackSpec
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.campaign import CampaignRepository

MAX_ROUNDS = 3
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def list_campaigns() -> list[dict[str, Any]]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        rows = await repo.list_campaigns()
        return [r.model_dump(mode="json") for r in rows]


async def get_campaign(campaign_id: str) -> Optional[CampaignDetail]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        return await repo.get_campaign(campaign_id)


async def _camp_dict_from_row(repo: CampaignRepository, campaign_id: str) -> Optional[dict[str, Any]]:
    detail = await repo.get_campaign(campaign_id)
    if detail is None:
        return None
    return {
        "id": detail.id,
        "name": detail.name,
        "namespace": detail.namespace,
        "state": detail.state,
        "round": detail.round,
        "max_rounds": detail.max_rounds,
        "red_score": detail.red_score,
        "blue_score": detail.blue_score,
        "leader": detail.leader,
        "include_security": detail.include_security,
        "security_mix_pct": detail.security_mix_pct,
        "attack_framework_id": detail.attack_framework_id,
        "attack_plan_id": detail.attack_plan_id,
        "planned_attack_count": detail.planned_attack_count,
        "last_round_at": detail.last_round_at,
        "rounds": [r.model_dump(mode="json") for r in detail.rounds],
    }


async def start_campaign(
    name: str,
    namespace: str = "staging",
    include_security: bool = False,
    security_mix_pct: int = 50,
    attack_framework_id: Optional[str] = None,
    attack_category_ids: Optional[list[str]] = None,
    attack_plan_id: Optional[str] = None,
) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        await repo.seed_if_empty()

        plan_id = attack_plan_id
        planned_count = 0
        if plan_id:
            plan = await repo.get_attack_plan(plan_id)
            if plan:
                planned_count = len(plan.attacks)
                include_security = True
                security_mix_pct = max(security_mix_pct, 80)
        elif attack_framework_id:
            plan = generate_attack_plan(
                framework_id=attack_framework_id,
                namespace=namespace,
                category_ids=attack_category_ids,
            )
            plan_id = await repo.save_attack_plan(plan)
            planned_count = len(plan.attacks)
            include_security = True
            security_mix_pct = max(security_mix_pct, 80)

        mix = security_mix_pct if include_security else 0
        max_rounds = MAX_ROUNDS
        if planned_count > MAX_ROUNDS:
            max_rounds = min(planned_count, 10)

        now = _utcnow().isoformat()
        camp = {
            "id": f"camp-{uuid.uuid4().hex[:8]}",
            "name": name,
            "namespace": namespace,
            "state": "active",
            "round": 0,
            "max_rounds": max_rounds,
            "red_score": 0,
            "blue_score": 0,
            "leader": "draw",
            "include_security": include_security,
            "security_mix_pct": mix,
            "attack_framework_id": attack_framework_id,
            "attack_plan_id": plan_id,
            "planned_attack_count": planned_count,
            "last_round_at": now,
            "rounds": [],
        }
        await repo.save_campaign(camp)
        summary = (await repo.get_campaign(camp["id"])).model_dump(mode="json")
        return summary


async def store_attack_plan(plan: GeneratedAttackPlan) -> str:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        return await repo.save_attack_plan(plan)


async def get_attack_plan(plan_id: str) -> Optional[GeneratedAttackPlan]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        return await repo.get_attack_plan(plan_id)


async def _attack_pool(repo: CampaignRepository, camp: dict[str, Any]) -> Optional[list[SecurityAttackSpec]]:
    plan_id = camp.get("attack_plan_id")
    if not plan_id:
        return None
    plan = await repo.get_attack_plan(plan_id)
    if plan is None:
        return None
    return plan.attacks


def _leader(red: int, blue: int) -> str:
    if red > blue:
        return "red"
    if blue > red:
        return "blue"
    return "draw"


async def run_round(campaign_id: str) -> Optional[dict[str, Any]]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        camp = await _camp_dict_from_row(repo, campaign_id)
        if camp is None:
            return None
        if camp["state"] != "active":
            return None
        if camp["round"] >= camp["max_rounds"]:
            camp["state"] = "complete"
            await repo.update_campaign(camp)
            return None

        round_num = camp["round"] + 1
        scanner = PostureScanner(camp["namespace"])
        posture = await scanner.scan()
        gaps = posture.get("gaps", [])
        prior = [r["attack"]["technique"] for r in camp.get("rounds", [])]
        pool = await _attack_pool(repo, camp)
        settings = get_settings()

        attack = await plan_red_attack(
            round_num=round_num,
            namespace=camp["namespace"],
            include_security=camp["include_security"],
            security_mix_pct=camp["security_mix_pct"],
            prior_techniques=prior,
            posture_gaps=gaps,
            attack_pool=pool,
            use_llm=settings.llm_enabled,
        )

        inject_result = None
        if settings.inject_red_blue_faults:
            try:
                inject_result = await inject_attack(attack, camp["namespace"])
                attack.transcript += (
                    f" Fault injected via experiment {inject_result['experiment_id']} "
                    f"({inject_result['state']})."
                )
            except Exception as exc:
                attack.transcript += f" Fault inject skipped: {exc}"

        dast_note = ""
        if camp["include_security"] and pool:
            spec = next((s for s in pool if s.technique == attack.technique), None)
            if spec:
                dast = await run_dast_probe(spec)
                if not dast.passed:
                    attack.transcript += f" DAST: {dast.message}"
                    dast_note = dast.message

        evidence_summary: list[str] = []
        if dast_note:
            evidence_summary.append(f"DAST: {dast_note}")
        if inject_result:
            evidence_summary.append(
                f"Inject {inject_result['experiment_id']}: slo_breached={inject_result.get('slo_breached')}",
            )

        defense = await defend_red_attack(
            attack,
            posture_gaps=gaps,
            evidence_summary=evidence_summary or None,
            namespace=camp["namespace"],
            use_llm=settings.llm_enabled,
        )
        result = score_round(
            round_num=round_num,
            attack=attack,
            defense=defense,
            posture_gaps=gaps,
            inject_result=inject_result,
        )
        if dast_note:
            result.red_transcript.append(f"DAST confirmed: {dast_note}")

        camp["rounds"].append(result.model_dump(mode="json"))
        camp["round"] = round_num
        total_red = sum(r["red_points"] for r in camp["rounds"])
        total_blue = sum(r["blue_points"] for r in camp["rounds"])
        camp["red_score"] = total_red
        camp["blue_score"] = total_blue
        camp["leader"] = _leader(total_red, total_blue)
        camp["last_round_at"] = _utcnow().isoformat()
        if result.outcome == "draw":
            try:
                from chaos_agent.referee.service import export_equilibrium_round

                await export_equilibrium_round(campaign_id, round_num)
            except Exception as exc:
                logger.warning("equilibrium_export_failed", extra={"campaign_id": campaign_id, "error": str(exc)})
        if round_num >= camp["max_rounds"]:
            camp["state"] = "complete"
            try:
                from chaos_agent.integrations.slack.client import SlackClient

                slack = SlackClient()
                if slack.available:
                    await slack.notify_campaign_complete(campaign_id, camp["name"], camp["leader"])
            except Exception:
                pass

        await repo.update_campaign(camp)
        summary = (await repo.get_campaign(campaign_id)).model_dump(mode="json")
        return {"campaign": summary, "round": result.model_dump(mode="json")}


async def remediate_round(campaign_id: str, round_num: int) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        detail = await repo.get_campaign(campaign_id)
        if detail is None:
            raise ValueError("Campaign not found")
        rnd = next((r for r in detail.rounds if r.round == round_num), None)
        if rnd is None:
            raise ValueError("Round not found")
        pr = await open_blue_pr(rnd.defense)
        row = await repo.save_remediation(
            campaign_id=campaign_id,
            round_num=round_num,
            defense_json=rnd.defense.model_dump_json(),
            pr_url=pr.get("url"),
            pr_number=pr.get("number"),
            status="pr_opened" if pr.get("url") else "draft",
        )
        return {
            "remediation_id": row.id,
            "pr_url": row.pr_url,
            "pr_number": row.pr_number,
            "dry_run": pr.get("dry_run", False),
            "title": pr.get("title"),
        }


async def verify_round_remediation(campaign_id: str, round_num: int) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        rem = await repo.get_remediation(campaign_id, round_num)
        detail = await repo.get_campaign(campaign_id)
        if detail is None or rem is None:
            raise ValueError("Remediation not found")
        rnd = next((r for r in detail.rounds if r.round == round_num), None)
        if rnd is None:
            raise ValueError("Round not found")
        outcome = await verify_round(rnd.attack, rnd.defense)
        if outcome["verified"]:
            await repo.mark_verified(rem.id)
        return outcome


def security_attack_catalog() -> list[dict[str, Any]]:
    return [s.model_dump(mode="json") for s in list_security_attacks()]
