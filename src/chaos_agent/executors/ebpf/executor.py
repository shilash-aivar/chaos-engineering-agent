"""eBPF / TC-netem fault executor."""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from typing import Any

from chaos_agent.config import get_settings
from chaos_agent.executors.base import AppliedResource, RollbackHandle
from chaos_agent.executors.ebpf.programs import program_spec
from chaos_agent.models import Fault

logger = logging.getLogger(__name__)

_ACTIVE_HANDLES: dict[str, dict[str, Any]] = {}


class EbpfExecutor:
    def __init__(self, simulate: bool | None = None) -> None:
        self.simulate = simulate if simulate is not None else get_settings().simulate_execution
        self.settings = get_settings()

    async def apply(
        self,
        experiment_id: str,
        fault: Fault,
        namespace: str,
        max_replica_percent: float,
    ) -> RollbackHandle:
        spec = program_spec(fault.type, fault.params)
        handle_id = f"ebpf-{experiment_id[:12]}-{uuid.uuid4().hex[:6]}"
        interface = spec["interface"]

        applied_via = "simulated"
        if (
            not self.simulate
            and self.settings.ebpf_enabled
            and self.settings.ebpf_use_tc
            and fault.type in ("network_latency", "packet_loss")
        ):
            ok = await self._apply_tc_netem(handle_id, interface, fault.type, spec)
            if ok:
                applied_via = "tc_netem"

        if applied_via == "simulated":
            logger.info(
                "ebpf_simulated_apply",
                extra={"experiment_id": experiment_id, "type": fault.type, "spec": spec},
            )

        _ACTIVE_HANDLES[handle_id] = {
            "experiment_id": experiment_id,
            "interface": interface,
            "fault_type": fault.type,
            "spec": spec,
            "applied_via": applied_via,
        }

        return RollbackHandle(
            experiment_id=experiment_id,
            executor="ebpf",
            resources=[
                AppliedResource(
                    api_version="chaos.agent/v1",
                    kind="EbpfProgram",
                    namespace=namespace,
                    name=handle_id,
                ),
            ],
            simulated=applied_via == "simulated",
        )

    async def _apply_tc_netem(
        self,
        handle_id: str,
        interface: str,
        fault_type: str,
        spec: dict[str, Any],
    ) -> bool:
        if not shutil.which("tc"):
            return False

        args: list[str] = ["tc", "qdisc", "add", "dev", interface, "root", "netem"]
        if fault_type == "network_latency":
            args.extend(["delay", f"{spec['latency_ms']}ms"])
        elif fault_type == "packet_loss":
            args.extend(["loss", f"{spec['loss_pct']}%"])
        else:
            return False

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode != 0:
                logger.warning("tc_netem_failed", extra={"stderr": stderr.decode()[:200]})
                return False
            return True
        except Exception as exc:
            logger.warning("tc_netem_error", extra={"error": str(exc)})
            return False

    async def rollback(self, handle: RollbackHandle) -> None:
        resource = handle.resources[0] if handle.resources else None
        name = resource.name if resource else None
        meta = _ACTIVE_HANDLES.pop(name or "", None)
        if meta is None:
            return

        if meta.get("applied_via") == "tc_netem" and shutil.which("tc"):
            interface = meta["interface"]
            try:
                proc = await asyncio.create_subprocess_exec(
                    "tc",
                    "qdisc",
                    "del",
                    "dev",
                    interface,
                    "root",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=5)
            except Exception as exc:
                logger.warning("tc_netem_rollback_failed", extra={"error": str(exc)})

        logger.info("ebpf_rollback", extra={"handle": name, "via": meta.get("applied_via")})
