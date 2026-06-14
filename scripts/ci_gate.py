#!/usr/bin/env python3
"""Run CI resilience gate locally or in GitHub Actions."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from chaos_agent.ci_gate.evaluator import evaluate_pr


async def main() -> int:
    parser = argparse.ArgumentParser(description="Chaos Agent CI gate")
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--services", nargs="*", default=[])
    parser.add_argument("--namespace", default="staging")
    parser.add_argument("--no-execute", action="store_true", help="Skip live probes/fault inject")
    args = parser.parse_args()

    result = await evaluate_pr(
        pr_number=args.pr_number,
        changed_files=args.files,
        changed_services=args.services,
        namespace=args.namespace,
        execute_probes=not args.no_execute,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
