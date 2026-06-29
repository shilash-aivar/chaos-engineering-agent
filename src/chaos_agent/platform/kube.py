"""Kubernetes client config — per-target kube context."""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def kube_context_for_namespace(namespace: str) -> Optional[str]:
    from chaos_agent.platform.target_context_service import list_target_contexts

    match = next((c for c in list_target_contexts() if c.get("namespace") == namespace), None)
    if match is None:
        return None
    return match.get("kube_context") or match.get("cluster")


def load_kubernetes_config(kube_context: Optional[str] = None) -> None:
    from kubernetes import config
    from kubernetes.config.config_exception import ConfigException

    try:
        config.load_incluster_config()
        return
    except ConfigException:
        pass

    from chaos_agent.config import get_settings

    settings = get_settings()
    context = kube_context or settings.kube_context or None
    kubeconfig_path = settings.kubeconfig_path or os.environ.get("KUBECONFIG")

    if not kubeconfig_path and not os.path.exists(os.path.expanduser("~/.kube/config")):
        raise RuntimeError("no kubeconfig")

    kwargs: dict[str, str] = {}
    if context:
        kwargs["context"] = context
    if kubeconfig_path:
        kwargs["config_file"] = os.path.expanduser(kubeconfig_path)
    config.load_kube_config(**kwargs)
