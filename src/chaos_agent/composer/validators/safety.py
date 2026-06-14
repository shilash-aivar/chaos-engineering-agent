"""Plan safety validation — hard limits, not LLM."""

from chaos_agent.config import get_settings
from chaos_agent.executors.ebpf.programs import EBPF_FAULT_TYPES
from chaos_agent.models import ExperimentPlan

_EBPF_TYPES = {item["type"] for item in EBPF_FAULT_TYPES}


class SafetyValidationError(ValueError):
    pass


def validate_plan(plan: ExperimentPlan) -> None:
    settings = get_settings()

    if plan.blast_radius.environment == "production" and not settings.allow_prod:
        raise SafetyValidationError(
            "production experiments require CHAOS_AGENT_ALLOW_PROD=true and approval",
        )

    if plan.blast_radius.max_replicas_pct > settings.max_replica_percent:
        raise SafetyValidationError(
            f"blast radius {plan.blast_radius.max_replicas_pct}% exceeds max "
            f"{settings.max_replica_percent}%",
        )

    if not plan.faults:
        raise SafetyValidationError("experiment plan must include at least one fault")

    for fault in plan.faults:
        if fault.executor.value == "aws_fis":
            if not settings.aws_fis_enabled:
                raise SafetyValidationError("aws_fis executor disabled — set CHAOS_AGENT_AWS_FIS_ENABLED=true")
        if fault.executor.value == "ebpf":
            if not settings.ebpf_enabled:
                raise SafetyValidationError("ebpf executor disabled — set CHAOS_AGENT_EBPF_ENABLED=true")
            if fault.type not in _EBPF_TYPES:
                raise SafetyValidationError(f"unsupported ebpf fault type: {fault.type}")
        if fault.executor.value not in ("chaos_mesh", "toxiproxy", "k6", "aws_fis", "ebpf"):
            raise SafetyValidationError(f"executor not enabled: {fault.executor.value}")

    if not plan.watch_metrics:
        raise SafetyValidationError("watch_metrics required for steady-state guard")

    if plan.rollback.type not in ("delete_chaos_crd", "aws_fis_stop", "delete_ebpf_program"):
        raise SafetyValidationError(f"unsupported rollback type: {plan.rollback.type}")
