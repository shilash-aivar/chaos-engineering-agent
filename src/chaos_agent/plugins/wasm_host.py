"""Wasm plugin host — wasmtime with Python fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from chaos_agent.config import get_settings
from chaos_agent.plugins.builtin import POSTURE_GAP_WAT, REFEREE_BLAST_WAT, BuiltinPlugins
from chaos_agent.plugins.types import PluginResult

logger = logging.getLogger(__name__)

_WASM_RUNTIME: Optional[str] = None


def _wasmtime_available() -> bool:
    global _WASM_RUNTIME
    if _WASM_RUNTIME is not None:
        return _WASM_RUNTIME == "wasmtime"
    try:
        import wasmtime  # noqa: F401

        _WASM_RUNTIME = "wasmtime"
        return True
    except ImportError:
        _WASM_RUNTIME = "none"
        return False


class WasmHost:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def available(self) -> bool:
        return self.settings.wasm_plugins_enabled

    @property
    def runtime(self) -> str:
        if not self.settings.wasm_plugins_enabled:
            return "disabled"
        return "wasmtime" if _wasmtime_available() else "python"

    def _run_wat_i32_fn(self, wat: str, export_name: str, arg: int) -> Optional[int]:
        try:
            import wasmtime

            engine = wasmtime.Engine()
            module = wasmtime.Module(engine, wat)
            store = wasmtime.Store(engine)
            instance = wasmtime.Instance(store, module, [])
            func = instance.exports(store)[export_name]
            result = func(store, arg)
            return int(result)
        except Exception as exc:
            logger.warning("wasm_exec_failed", extra={"export": export_name, "error": str(exc)})
            return None

    def _load_file_module(self, path: Path) -> Optional[bytes]:
        if not path.exists():
            return None
        return path.read_bytes()

    def validate_blast_radius(self, max_replicas_pct: int, cap: int = 20) -> PluginResult:
        if not self.settings.wasm_plugins_enabled:
            return PluginResult(passed=True, plugin="referee_blast", runtime="disabled")

        if _wasmtime_available():
            failed = self._run_wat_i32_fn(REFEREE_BLAST_WAT, "validate_blast_radius", max_replicas_pct)
            if failed is not None:
                return PluginResult(
                    passed=failed == 0,
                    message=(
                        f"wasm: blast radius {max_replicas_pct}% exceeds cap {cap}%"
                        if failed
                        else f"wasm: blast radius {max_replicas_pct}% within cap"
                    ),
                    plugin="referee_blast",
                    runtime="wasmtime",
                )

        return BuiltinPlugins.validate_blast_radius(max_replicas_pct, cap=cap)

    def validate_gap_count(self, gap_count: int, threshold: int = 50) -> PluginResult:
        if not self.settings.wasm_plugins_enabled:
            return PluginResult(passed=True, plugin="posture_gaps", runtime="disabled")

        if _wasmtime_available():
            failed = self._run_wat_i32_fn(POSTURE_GAP_WAT, "validate_gap_count", gap_count)
            if failed is not None:
                return PluginResult(
                    passed=failed == 0,
                    message=(
                        f"wasm: {gap_count} posture gaps exceeds {threshold}"
                        if failed
                        else f"wasm: {gap_count} posture gaps ok"
                    ),
                    plugin="posture_gaps",
                    runtime="wasmtime",
                )

        return BuiltinPlugins.validate_gap_count(gap_count, threshold=threshold)

    def list_plugins(self) -> list[dict[str, Any]]:
        plugin_dir = Path(self.settings.wasm_plugins_dir)
        external = []
        if plugin_dir.is_dir():
            external = [p.name for p in plugin_dir.glob("*.wasm")]
        return [
            {
                "id": "referee_blast",
                "name": "Referee blast radius cap",
                "runtime": self.runtime,
                "builtin": True,
                "description": "Rejects plans with blast radius > 20%",
            },
            {
                "id": "posture_gaps",
                "name": "Posture gap threshold",
                "runtime": self.runtime,
                "builtin": True,
                "description": "Flags scans with excessive gap counts",
            },
            *[{"id": p, "name": p, "runtime": "wasmtime", "builtin": False} for p in external],
        ]
