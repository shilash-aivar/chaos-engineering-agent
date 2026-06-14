"""eBPF fault program catalog."""

from __future__ import annotations

from typing import Any

EBPF_FAULT_TYPES = [
    {
        "type": "network_latency",
        "description": "TC/netem or BPF cgroup skb latency on target interface",
        "params": ["latency_ms", "interface", "target"],
    },
    {
        "type": "packet_loss",
        "description": "Random packet drop percentage via netem or BPF",
        "params": ["loss_pct", "interface", "target"],
    },
    {
        "type": "connect_block",
        "description": "Block outbound connects to target host:port via BPF cgroup",
        "params": ["target_host", "target_port", "target"],
    },
    {
        "type": "syscall_delay",
        "description": "Tracepoint delay probe on connect/sendmsg (simulated in dev)",
        "params": ["delay_us", "syscall", "target"],
    },
]


def program_spec(fault_type: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "fault_type": fault_type,
        "latency_ms": int(params.get("latency_ms", 100)),
        "loss_pct": float(params.get("loss_pct", 5)),
        "interface": params.get("interface", "eth0"),
        "target": params.get("target", "checkout"),
        "target_host": params.get("target_host", "payments-api"),
        "target_port": int(params.get("target_port", 443)),
        "delay_us": int(params.get("delay_us", 500)),
        "syscall": params.get("syscall", "connect"),
    }
