"""Steady-state guard — baseline capture and breach detection."""

from __future__ import annotations

from dataclasses import dataclass

from typing import Optional

from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.config import get_settings


@dataclass
class BreachResult:
    breached: bool
    metric: Optional[str] = None
    baseline: Optional[float] = None
    current: Optional[float] = None
    reason: Optional[str] = None


class SteadyStateGuard:
    def __init__(self, prom: Optional[PrometheusClient] = None) -> None:
        self.prom = prom or PrometheusClient()
        self.settings = get_settings()

    async def capture_baseline(self, watch_metrics: list[str], samples: int = 3) -> dict[str, float]:
        """Average a few Prometheus samples for baseline."""
        accumulated: dict[str, list[float]] = {m: [] for m in watch_metrics}
        import asyncio

        for _ in range(samples):
            snap = await self.prom.snapshot(watch_metrics)
            for key, value in snap.items():
                accumulated.setdefault(key, []).append(value)
            await asyncio.sleep(min(5, self.settings.guard_interval_seconds))

        baseline: dict[str, float] = {}
        for metric, values in accumulated.items():
            if values:
                baseline[metric] = sum(values) / len(values)
        return baseline

    def check(self, baseline: dict[str, float], current: dict[str, float]) -> BreachResult:
        for metric, base_value in baseline.items():
            current_value = current.get(metric)
            if current_value is None:
                continue

            if metric.endswith("error_rate") or "error" in metric:
                threshold = base_value * self.settings.steady_state_error_multiplier
                if base_value == 0 and current_value > 0.01:
                    return BreachResult(
                        breached=True,
                        metric=metric,
                        baseline=base_value,
                        current=current_value,
                        reason="error rate above zero baseline",
                    )
                if base_value > 0 and current_value > threshold:
                    return BreachResult(
                        breached=True,
                        metric=metric,
                        baseline=base_value,
                        current=current_value,
                        reason=f"error rate > {self.settings.steady_state_error_multiplier}x baseline",
                    )

            if metric.endswith("p99") or "latency" in metric:
                threshold = base_value * self.settings.steady_state_latency_multiplier
                if base_value > 0 and current_value > threshold:
                    return BreachResult(
                        breached=True,
                        metric=metric,
                        baseline=base_value,
                        current=current_value,
                        reason=f"latency > {self.settings.steady_state_latency_multiplier}x baseline",
                    )

        return BreachResult(breached=False)

    async def wait_for_recovery(
        self,
        baseline: dict[str, float],
        watch_metrics: list[str],
        timeout_seconds: int = 120,
    ) -> bool:
        import asyncio

        elapsed = 0
        while elapsed < timeout_seconds:
            current = await self.prom.snapshot(watch_metrics)
            breach = self.check(baseline, current)
            if not breach.breached:
                return True
            await asyncio.sleep(self.settings.guard_interval_seconds)
            elapsed += self.settings.guard_interval_seconds
        return False
