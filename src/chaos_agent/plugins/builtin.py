"""Built-in plugin logic and embedded WAT modules."""

from __future__ import annotations

from chaos_agent.plugins.types import PluginResult

# Referee: returns 1 if blast radius exceeds cap (fail), else 0 (pass)
REFEREE_BLAST_WAT = """
(module
  (func (export "validate_blast_radius") (param $pct i32) (result i32)
    local.get $pct
    i32.const 20
    i32.gt_u
  )
)
"""

# Posture: returns 1 if gap count exceeds threshold
POSTURE_GAP_WAT = """
(module
  (func (export "validate_gap_count") (param $count i32) (result i32)
    local.get $count
    i32.const 50
    i32.gt_u
  )
)
"""


class BuiltinPlugins:
    @staticmethod
    def validate_blast_radius(max_replicas_pct: int, cap: int = 20) -> PluginResult:
        failed = max_replicas_pct > cap
        return PluginResult(
            passed=not failed,
            message=(
                f"blast radius {max_replicas_pct}% exceeds wasm cap {cap}%"
                if failed
                else f"blast radius {max_replicas_pct}% within cap"
            ),
            plugin="referee_blast",
            runtime="python",
        )

    @staticmethod
    def validate_gap_count(gap_count: int, threshold: int = 50) -> PluginResult:
        failed = gap_count > threshold
        return PluginResult(
            passed=not failed,
            message=(
                f"posture gap count {gap_count} exceeds threshold {threshold}"
                if failed
                else f"posture gap count {gap_count} ok"
            ),
            plugin="posture_gaps",
            runtime="python",
        )
