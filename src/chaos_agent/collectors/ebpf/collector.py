"""eBPF telemetry collector — kernel counters during fault window."""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any, Optional

from chaos_agent.config import get_settings
from chaos_agent.executors.ebpf.executor import _ACTIVE_HANDLES

logger = logging.getLogger(__name__)


class EbpfCollector:
    async def collect(
        self,
        experiment_id: str,
        *,
        fault_type: Optional[str] = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        active = [
            meta
            for meta in _ACTIVE_HANDLES.values()
            if meta.get("experiment_id") == experiment_id
        ]

        if settings.simulate_execution or not active:
            return self._simulated(fault_type or "network_latency")

        live = await self._collect_bpftrace_snapshot()
        if live:
            live["source"] = "bpftrace"
            live["active_programs"] = len(active)
            return live

        return self._simulated(fault_type or active[0].get("fault_type", "network_latency"))

    def _simulated(self, fault_type: str) -> dict[str, Any]:
        base = {
            "source": "simulated",
            "fault_type": fault_type,
            "tcp_retransmits": 12 if fault_type == "network_latency" else 4,
            "dropped_packets": 8 if fault_type == "packet_loss" else 1,
            "connect_errors": 3 if fault_type == "connect_block" else 0,
            "syscall_delay_us_p99": 450 if fault_type == "syscall_delay" else 80,
        }
        return base

    async def _collect_bpftrace_snapshot(self) -> Optional[dict[str, Any]]:
        if not shutil.which("bpftrace"):
            return None

        script = (
            "BEGIN { printf('retrans=%d\\n', @retrans); printf('drops=%d\\n', @drops); exit(); }"
            "kprobe:tcp_retransmit_skb { @retrans = count(); }"
            "kprobe:skb_drop_reason { @drops = count(); }"
        )
        try:
            proc = await asyncio.create_subprocess_exec(
                "bpftrace",
                "-e",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
            if proc.returncode != 0:
                return None
            retrans = 0
            drops = 0
            for line in stdout.decode().splitlines():
                if line.startswith("retrans="):
                    retrans = int(line.split("=", 1)[1])
                if line.startswith("drops="):
                    drops = int(line.split("=", 1)[1])
            return {
                "tcp_retransmits": retrans,
                "dropped_packets": drops,
                "connect_errors": 0,
                "syscall_delay_us_p99": 0,
            }
        except Exception as exc:
            logger.debug("bpftrace_collect_skipped", extra={"error": str(exc)})
            return None
