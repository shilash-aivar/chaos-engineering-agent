"""Terraform parser — HCL-first with lightweight regex fallback."""

from __future__ import annotations

import re
from typing import Any

from chaos_agent.context.types import TerraformResource

RESOURCE_RE = re.compile(
    r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{',
    re.MULTILINE,
)
ATTR_RE = re.compile(r'^\s*([a-zA-Z0-9_]+)\s*=\s*(.+)$', re.MULTILINE)


def _parse_value(raw: str) -> Any:
    raw = raw.strip().rstrip(",")
    if raw in ("true", "false"):
        return raw == "true"
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    return raw


def _extract_block_attrs(block: str) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for match in ATTR_RE.finditer(block):
        key, val = match.group(1), match.group(2)
        if key in ("resource", "data", "provider", "module"):
            continue
        if val.startswith("{"):
            continue
        attrs[key] = _parse_value(val)
    return attrs


def parse_terraform(content: str, source_file: str = "main.tf") -> list[TerraformResource]:
    parsed = _parse_with_hcl2(content, source_file)
    if parsed:
        return parsed
    return _parse_with_regex(content, source_file)


def _parse_with_hcl2(content: str, source_file: str) -> list[TerraformResource]:
    try:
        import hcl2
    except Exception:
        return []

    try:
        document = hcl2.loads(content)
    except Exception:
        return []

    resources: list[TerraformResource] = []
    for item in document.get("resource", []) or []:
        if not isinstance(item, dict):
            continue
        for rtype, named in item.items():
            if not isinstance(named, dict):
                continue
            for rname, attrs in named.items():
                if not isinstance(attrs, dict):
                    attrs = {}
                resources.append(
                    TerraformResource(
                        type=_unquote(str(rtype)),
                        name=_unquote(str(rname)),
                        attributes=_normalize_hcl_value(attrs),
                        source_file=source_file,
                    ),
                )
    return resources


def _unquote(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] == '"':
        return stripped[1:-1]
    return stripped


def _normalize_hcl_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _normalize_hcl_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_hcl_value(v) for v in value]
    if isinstance(value, str):
        return _unquote(value)
    return value


def _parse_with_regex(content: str, source_file: str = "main.tf") -> list[TerraformResource]:
    resources: list[TerraformResource] = []
    for match in RESOURCE_RE.finditer(content):
        rtype, rname = match.group(1), match.group(2)
        start = match.end()
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
            i += 1
        block = content[start : i - 1]
        attrs = _extract_block_attrs(block)
        resources.append(
            TerraformResource(
                type=rtype,
                name=rname,
                attributes=attrs,
                source_file=source_file,
            ),
        )
    return resources
