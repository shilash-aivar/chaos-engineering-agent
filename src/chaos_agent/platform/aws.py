"""AWS client config — profile/region from connectors and target context."""

from __future__ import annotations

from typing import Optional

from chaos_agent.config import get_settings


def aws_region_for_namespace(namespace: str) -> Optional[str]:
    from chaos_agent.platform.target_context_service import list_target_contexts

    match = next((c for c in list_target_contexts() if c.get("namespace") == namespace), None)
    if match is None:
        return None
    return match.get("aws_region")


def aws_profile_for_namespace(namespace: str) -> Optional[str]:
    from chaos_agent.platform.target_context_service import list_target_contexts

    match = next((c for c in list_target_contexts() if c.get("namespace") == namespace), None)
    if match is None:
        return None
    return match.get("aws_profile")


def resolve_aws_config(
    *,
    profile: Optional[str] = None,
    region: Optional[str] = None,
    namespace: Optional[str] = None,
) -> tuple[Optional[str], str]:
    """Return (profile, region) merging explicit args, target context, and settings."""
    from chaos_agent.platform.connector_store import apply_connectors_to_settings

    apply_connectors_to_settings()
    settings = get_settings()

    resolved_profile = profile or (aws_profile_for_namespace(namespace) if namespace else None) or settings.aws_profile or None
    resolved_region = (
        region
        or (aws_region_for_namespace(namespace) if namespace else None)
        or settings.aws_region
        or "us-east-1"
    )
    return resolved_profile or None, resolved_region


def boto_session(*, profile: Optional[str] = None, region: Optional[str] = None, namespace: Optional[str] = None):
    import boto3

    prof, reg = resolve_aws_config(profile=profile, region=region, namespace=namespace)
    if prof:
        return boto3.Session(profile_name=prof, region_name=reg)
    return boto3.Session(region_name=reg)
