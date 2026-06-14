"""Build fault-window evidence by correlating Prometheus, Loki, and Tempo."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from chaos_agent.collectors.loki.client import LokiClient
from chaos_agent.collectors.ebpf.collector import EbpfCollector
from chaos_agent.collectors.prometheus.client import PrometheusClient, promql_for_metric
from chaos_agent.collectors.tempo.client import TempoClient
from chaos_agent.models import ExperimentPlan, FaultExecutor
from chaos_agent.observability.catalog import (
    load_catalog,
    resolve_metrics_for_services,
    resolve_services_for_plan,
)
from chaos_agent.observability.types import (
    FaultWindowEvidence,
    LogSummary,
    MetricWindowSample,
    ObservabilityBackendStatus,
    TraceSummary,
)


class ObservabilityCorrelator:
    def __init__(
        self,
        prom: Optional[PrometheusClient] = None,
        loki: Optional[LokiClient] = None,
        tempo: Optional[TempoClient] = None,
    ) -> None:
        self.prom = prom or PrometheusClient()
        self.loki = loki or LokiClient()
        self.tempo = tempo or TempoClient()
        self.catalog = load_catalog()

    async def backend_status(self) -> ObservabilityBackendStatus:
        prom_ok, loki_ok, tempo_ok = await asyncio.gather(
            self.prom.is_available(),
            self.loki.is_available(),
            self.tempo.is_available(),
        )
        return ObservabilityBackendStatus(
            prometheus="ok" if prom_ok else "gap",
            loki="ok" if loki_ok else "gap",
            tempo="ok" if tempo_ok else "gap",
            detail={
                "prometheus": None if prom_ok else "Unreachable",
                "loki": None if loki_ok else "Unreachable",
                "tempo": None if tempo_ok else "Unreachable",
            },
        )

    async def build_evidence(
        self,
        experiment_id: str,
        plan: ExperimentPlan,
        *,
        baseline: dict[str, float],
        window_start: datetime,
        window_end: datetime,
        slo_breached: bool = False,
        force_simulate: bool = False,
    ) -> FaultWindowEvidence:
        status = await self.backend_status()
        simulate = force_simulate or status.prometheus == "gap"

        target_services = [t.service for t in plan.targets]
        fault_targets = [f.target for f in plan.faults if f.target]
        services = resolve_services_for_plan(target_services, fault_targets, plan.watch_metrics, self.catalog)
        metrics = resolve_metrics_for_services(services, plan.watch_metrics, self.catalog)
        ebpf_faults = [f for f in plan.faults if f.executor == FaultExecutor.EBPF]
        ebpf_metrics: dict = {}
        if ebpf_faults:
            fault_type = ebpf_faults[0].type
            ebpf_metrics = await EbpfCollector().collect(experiment_id, fault_type=fault_type)

        if simulate:
            evidence = self._simulate_evidence(
                experiment_id,
                plan,
                baseline,
                window_start,
                window_end,
                metrics,
                services,
                slo_breached,
            )
            if ebpf_metrics:
                evidence.ebpf_metrics = ebpf_metrics
                evidence.correlations.extend(self._ebpf_correlations(ebpf_metrics))
            return evidence

        metric_samples, log_summaries, trace_summaries = await asyncio.gather(
            self._fetch_metrics(metrics, baseline, window_start, window_end),
            self._fetch_logs(services, window_start, window_end),
            self._fetch_traces(services, window_start, window_end),
        )
        correlations = self._correlate(metric_samples, log_summaries, slo_breached)
        correlations.extend(self._ebpf_correlations(ebpf_metrics))
        return FaultWindowEvidence(
            experiment_id=experiment_id,
            window_start=window_start,
            window_end=window_end,
            simulated=False,
            metrics=metric_samples,
            logs=log_summaries,
            traces=trace_summaries,
            correlations=correlations,
            ebpf_metrics=ebpf_metrics,
        )

    async def _fetch_metrics(
        self,
        metrics: list[str],
        baseline: dict[str, float],
        window_start: datetime,
        window_end: datetime,
    ) -> list[MetricWindowSample]:
        mid = window_start + (window_end - window_start) / 2
        after_start = max(mid, window_end - timedelta(seconds=30))

        async def one_metric(name: str) -> MetricWindowSample:
            promql = promql_for_metric(name)
            during_samples, after_samples = await asyncio.gather(
                self.prom.query_range(promql, window_start, window_end),
                self.prom.query_range(promql, after_start, window_end),
            )
            base = baseline.get(name)
            during_peak = self.prom.peak_in_window(during_samples)
            after = self.prom.last_in_window(after_samples)
            delta = None
            if base and during_peak is not None and base > 0:
                delta = during_peak / base
            unit = "seconds" if name.endswith("p99") or "latency" in name else "ratio"
            return MetricWindowSample(
                name=name,
                baseline=base,
                during_peak=during_peak,
                after=after,
                delta_ratio=delta,
                unit=unit,
            )

        return list(await asyncio.gather(*[one_metric(m) for m in metrics]))

    async def _fetch_logs(
        self,
        services: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> list[LogSummary]:
        async def one_service(service: str) -> LogSummary:
            spec = self.catalog.services.get(service)
            selector = spec.log_selector if spec and spec.log_selector else f'{{app="{service}"}}'
            lines = await self.loki.query_range(selector, window_start, window_end)
            count, patterns, samples = LokiClient.summarize_lines(lines)
            return LogSummary(
                service=service,
                error_count=count,
                top_patterns=patterns,
                sample_lines=samples,
            )

        return list(await asyncio.gather(*[one_service(s) for s in services]))

    async def _fetch_traces(
        self,
        services: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> list[TraceSummary]:
        summaries: list[TraceSummary] = []

        for path_name, path_spec in self.catalog.paths.items():
            if not any(s in services for s in path_spec.services):
                continue
            query = path_spec.trace_query or (
                f'{{ resource.service.name = "{path_spec.services[0]}" }}'
            )
            traces = await self.tempo.search(query, window_start, window_end)
            trace_ids = [t.get("traceID", t.get("traceId", "")) for t in traces if t]
            trace_ids = [tid for tid in trace_ids if tid][:5]
            error_spans = sum(int(t.get("errorSpans", 0) or 0) for t in traces)
            durations = [float(t.get("durationMs", 0) or 0) for t in traces if t.get("durationMs")]
            p99 = max(durations) if durations else None
            summaries.append(
                TraceSummary(
                    path=path_name,
                    trace_count=len(traces),
                    error_spans=error_spans,
                    p99_ms=p99,
                    sample_trace_ids=trace_ids,
                ),
            )

        if not summaries and services:
            for svc in services[:2]:
                query = f'{{ resource.service.name = "{svc}" }}'
                traces = await self.tempo.search(query, window_start, window_end)
                trace_ids = [t.get("traceID", t.get("traceId", "")) for t in traces if t]
                trace_ids = [tid for tid in trace_ids if tid][:5]
                summaries.append(
                    TraceSummary(
                        path=svc,
                        trace_count=len(traces),
                        error_spans=sum(int(t.get("errorSpans", 0) or 0) for t in traces),
                        sample_trace_ids=trace_ids,
                    ),
                )
        return summaries

    def _correlate(
        self,
        metrics: list[MetricWindowSample],
        logs: list[LogSummary],
        slo_breached: bool,
    ) -> list[str]:
        lines: list[str] = []
        for m in metrics:
            if m.delta_ratio and m.delta_ratio >= 2.0:
                lines.append(
                    f"{m.name} peaked at {m.during_peak:.4f} ({m.delta_ratio:.1f}x baseline)",
                )
        for log in logs:
            if log.error_count > 0 and log.top_patterns:
                lines.append(
                    f"{log.service} logged {log.error_count} errors — pattern: {log.top_patterns[0][:80]}",
                )
        if slo_breached and not lines:
            lines.append("SLO breach flagged by steady-state guard during fault window")
        if metrics and logs and lines:
            breached = [m.name for m in metrics if m.delta_ratio and m.delta_ratio >= 2.0]
            noisy = [lg.service for lg in logs if lg.error_count > 0]
            if breached and noisy:
                lines.append(f"Metric spikes ({', '.join(breached)}) align with log errors in {', '.join(noisy)}")
        return lines

    def _ebpf_correlations(self, ebpf_metrics: dict) -> list[str]:
        if not ebpf_metrics:
            return []
        lines: list[str] = []
        source = ebpf_metrics.get("source", "unknown")
        if ebpf_metrics.get("tcp_retransmits", 0) > 5:
            lines.append(
                f"eBPF ({source}): {ebpf_metrics['tcp_retransmits']} TCP retransmits during fault window",
            )
        if ebpf_metrics.get("dropped_packets", 0) > 0:
            lines.append(
                f"eBPF ({source}): {ebpf_metrics['dropped_packets']} dropped packets observed",
            )
        if ebpf_metrics.get("connect_errors", 0) > 0:
            lines.append(
                f"eBPF ({source}): {ebpf_metrics['connect_errors']} connect errors blocked",
            )
        return lines

    def _simulate_evidence(
        self,
        experiment_id: str,
        plan: ExperimentPlan,
        baseline: dict[str, float],
        window_start: datetime,
        window_end: datetime,
        metrics: list[str],
        services: list[str],
        slo_breached: bool,
    ) -> FaultWindowEvidence:
        metric_samples: list[MetricWindowSample] = []
        for name in metrics:
            base = baseline.get(name, 0.01 if "error" in name else 0.2)
            multiplier = 4.0 if slo_breached and "error" in name else 1.5
            if "p99" in name or "latency" in name:
                multiplier = 2.5 if slo_breached else 1.2
            during = base * multiplier
            metric_samples.append(
                MetricWindowSample(
                    name=name,
                    baseline=base,
                    during_peak=during,
                    after=base * 1.05,
                    delta_ratio=during / base if base > 0 else None,
                    unit="seconds" if "p99" in name else "ratio",
                ),
            )

        fault_type = plan.faults[0].type if plan.faults else "unknown"
        fault_target = plan.faults[0].target if plan.faults and plan.faults[0].target else "service"
        log_summaries = [
            LogSummary(
                service=svc,
                error_count=42 if slo_breached else 3,
                top_patterns=[
                    f"connection timeout to {fault_target}",
                    f"{fault_type} induced degradation",
                ],
                sample_lines=[
                    f'ERROR upstream {fault_target} unreachable during {fault_type}',
                    f'WARN retry exhausted calling {fault_target}',
                ],
            )
            for svc in services[:3]
        ]

        trace_summaries = [
            TraceSummary(
                path="checkout-payments",
                trace_count=18,
                error_spans=6 if slo_breached else 1,
                p99_ms=4200.0 if slo_breached else 320.0,
                sample_trace_ids=[f"sim-{experiment_id[:8]}-001", f"sim-{experiment_id[:8]}-002"],
            ),
        ]

        correlations = self._correlate(metric_samples, log_summaries, slo_breached)
        return FaultWindowEvidence(
            experiment_id=experiment_id,
            window_start=window_start,
            window_end=window_end,
            simulated=True,
            metrics=metric_samples,
            logs=log_summaries,
            traces=trace_summaries,
            correlations=correlations,
        )


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
