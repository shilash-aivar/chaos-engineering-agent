"""Load test scenario library."""

from __future__ import annotations

from typing import Any

LOAD_TEST_TYPES = [
    {
        "type": "load",
        "title": "Load test",
        "question": "Does the system handle expected peak traffic under fault?",
        "description": "Sustained traffic at expected peak VUs while a fault is active.",
        "when_to_use": "Before major releases, SLO validation",
        "typical_duration": "5–15 min",
        "chaos_pairing": "pod_kill or network_latency on critical path",
    },
    {
        "type": "stress",
        "title": "Stress test",
        "question": "Where does the system break under overload + fault?",
        "description": "Ramp VUs beyond normal capacity to find breaking point.",
        "when_to_use": "Capacity planning, autoscaling validation",
        "typical_duration": "10–20 min",
        "chaos_pairing": "dependency_blackhole during ramp",
    },
    {
        "type": "performance",
        "title": "Performance test",
        "question": "Do p99 and error rate stay within SLO during inject?",
        "description": "Fixed moderate load with strict latency thresholds.",
        "when_to_use": "Regression after dependency changes",
        "typical_duration": "3–10 min",
        "chaos_pairing": "network_latency on upstream service",
    },
    {
        "type": "soak",
        "title": "Soak test",
        "question": "Are there memory leaks or queue buildup over time?",
        "description": "Long-running moderate load with periodic faults.",
        "when_to_use": "Weekly game days, queue/backlog validation",
        "typical_duration": "30–60 min",
        "chaos_pairing": "intermittent timeout on cache/queue",
    },
]

SCENARIOS = [
    {
        "id": "checkout-peak-load",
        "name": "Checkout peak load",
        "type": "load",
        "vus": 50,
        "duration": "10m",
        "target": "checkout",
        "status": "ready",
        "hypothesis": "Checkout sustains 50 VUs with <1% errors during pod kill",
    },
    {
        "id": "payments-stress",
        "name": "Payments stress ramp",
        "type": "stress",
        "vus": 200,
        "duration": "15m",
        "target": "payments-api",
        "status": "ready",
        "hypothesis": "Payments API degrades gracefully when DB blackholed under ramp",
    },
    {
        "id": "inventory-perf",
        "name": "Inventory p99 guard",
        "type": "performance",
        "vus": 30,
        "duration": "5m",
        "target": "inventory-api",
        "status": "ready",
        "hypothesis": "p99 stays under 500ms with 300ms injected latency",
    },
    {
        "id": "order-soak",
        "name": "Order pipeline soak",
        "type": "soak",
        "vus": 20,
        "duration": "45m",
        "target": "checkout",
        "status": "ready",
        "hypothesis": "SQS backlog stable over 45m with intermittent Redis timeout",
    },
]

PAIRINGS = [
    {
        "id": "peak-pod-kill",
        "name": "Peak traffic + pod kill",
        "load_type": "load",
        "recommended_vus": 50,
        "hypothesis": "HPA recovers checkout within 2 min under load",
        "fault": "chaos_mesh/pod_kill → checkout",
    },
    {
        "id": "stress-db-blackhole",
        "name": "Stress ramp + DB blackhole",
        "load_type": "stress",
        "recommended_vus": 150,
        "hypothesis": "Circuit breaker opens before connection pool exhaustion",
        "fault": "toxiproxy/dependency_blackhole → payments-db",
    },
]

K6_TEMPLATES = {
    "load": """import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 50,
  duration: '10m',
  thresholds: { http_req_failed: ['rate<0.01'], http_req_duration: ['p(99)<500'] },
};

export default function () {
  const res = http.get('http://checkout.staging.svc/health');
  check(res, { 'status 200': (r) => r.status === 200 });
}""",
    "stress": """import http from 'k6/http';

export const options = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '5m', target: 200 },
    { duration: '5m', target: 0 },
  ],
};

export default function () {
  http.get('http://payments-api.staging.svc/orders');
}""",
    "performance": """import http from 'k6/http';

export const options = {
  vus: 30,
  duration: '5m',
  thresholds: { http_req_duration: ['p(99)<500'] },
};

export default function () {
  http.get('http://inventory-api.staging.svc/items');
}""",
    "soak": """import http from 'k6/http';

export const options = {
  vus: 20,
  duration: '45m',
};

export default function () {
  http.get('http://checkout.staging.svc/checkout');
}""",
}


def get_load_tests_catalog() -> dict[str, Any]:
    return {
        "types": LOAD_TEST_TYPES,
        "scenarios": SCENARIOS,
        "pairings": PAIRINGS,
        "templates": K6_TEMPLATES,
    }
