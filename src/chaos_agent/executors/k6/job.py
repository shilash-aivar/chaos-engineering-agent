"""Launch k6 as a Kubernetes Job."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from chaos_agent.config import get_settings
from chaos_agent.executors.base import AppliedResource

logger = logging.getLogger(__name__)


def _k8s_batch_api(kube_context: str | None = None) -> Any:
    from kubernetes import client
    from chaos_agent.platform.kube import load_kubernetes_config

    load_kubernetes_config(kube_context)
    return client.BatchV1Api(), client.CoreV1Api()


async def launch_k6_job(
    experiment_id: str,
    namespace: str,
    script: str,
    *,
    vus: int,
    duration: str,
    kube_context: str | None = None,
) -> tuple[bool, list[AppliedResource]]:
    settings = get_settings()
    safe_id = experiment_id.replace("_", "-").lower()[:20]
    job_name = f"k6-{safe_id}"[:63]
    cm_name = f"k6-script-{safe_id}"[:63]

    def _create() -> None:
        batch, core = _k8s_batch_api(kube_context)
        core.create_namespaced_config_map(
            namespace=namespace,
            body={
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": cm_name, "labels": {"app": "chaos-agent-k6"}},
                "data": {"script.js": script},
            },
        )
        batch.create_namespaced_job(
            namespace=namespace,
            body={
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {"name": job_name, "labels": {"app": "chaos-agent-k6"}},
                "spec": {
                    "ttlSecondsAfterFinished": 600,
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [
                                {
                                    "name": "k6",
                                    "image": settings.k8s_load_test_image,
                                    "command": ["k6", "run", "/scripts/script.js"],
                                    "volumeMounts": [{"name": "script", "mountPath": "/scripts"}],
                                    "env": [
                                        {"name": "K6_VUS", "value": str(vus)},
                                        {"name": "K6_DURATION", "value": duration},
                                    ],
                                },
                            ],
                            "volumes": [
                                {
                                    "name": "script",
                                    "configMap": {"name": cm_name},
                                },
                            ],
                        },
                    },
                },
            },
        )

    try:
        await asyncio.to_thread(_create)
        resources = [
            AppliedResource(api_version="batch/v1", kind="Job", namespace=namespace, name=job_name),
            AppliedResource(api_version="v1", kind="ConfigMap", namespace=namespace, name=cm_name),
        ]
        return True, resources
    except Exception as exc:
        logger.warning("k6_job_launch_failed", extra={"experiment_id": experiment_id, "error": str(exc)})
        return False, []


async def delete_k6_job(
    namespace: str,
    job_name: str,
    cm_name: str,
    *,
    kube_context: str | None = None,
) -> None:
    def _delete() -> None:
        batch, core = _k8s_batch_api(kube_context)
        try:
            batch.delete_namespaced_job(name=job_name, namespace=namespace, propagation_policy="Background")
        except Exception:
            pass
        try:
            core.delete_namespaced_config_map(name=cm_name, namespace=namespace)
        except Exception:
            pass

    await asyncio.to_thread(_delete)
