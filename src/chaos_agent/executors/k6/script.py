"""Generate k6 scripts from fault params."""

from __future__ import annotations

from chaos_agent.config import get_settings
from chaos_agent.models import Fault
from chaos_agent.platform.load_tests_data import K6_TEMPLATES


def build_k6_script(fault: Fault, namespace: str) -> str:
    target = fault.target or "checkout"
    vus = int(fault.params.get("vus", 30))
    duration = fault.params.get("duration", "5m")
    fault_type = fault.type if fault.type in K6_TEMPLATES else "load"
    template = K6_TEMPLATES[fault_type]
    settings = get_settings()
    base_url = settings.staging_base_url.rstrip("/")
    service_url = f"http://{target}.{namespace}.svc"
    return (
        template.replace(f"http://{target}.staging.svc", service_url)
        .replace("vus: 50", f"vus: {vus}")
        .replace("vus: 30", f"vus: {vus}")
        .replace("vus: 20", f"vus: {vus}")
        .replace("duration: '10m'", f"duration: '{duration}'")
        .replace("duration: '5m'", f"duration: '{duration}'")
        .replace("duration: '45m'", f"duration: '{duration}'")
        .replace("http://checkout.staging.svc", service_url)
        .replace("http://payments-api.staging.svc", service_url)
        .replace("http://inventory-api.staging.svc", service_url)
        .replace("http://localhost:8080", base_url)
    )
