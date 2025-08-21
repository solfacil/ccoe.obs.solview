#!/usr/bin/env python3
"""
Traffic Generator for Solview Demo Stack

Purpose:
  - Generate HTTP traffic across both applications (demo-app at :8000 and backend-processor at :8001)
  - Produce a realistic mix of successful and error responses to exercise logs, metrics and traces

Usage:
  - python scripts/traffic_generator.py --duration 300 --concurrency 16

Environment variables:
  DEMO_APP_URL               Default: http://localhost:8000
  BACKEND_PROCESSOR_URL      Default: http://localhost:8001
  TG_DURATION_SECONDS        Default: 300
  TG_CONCURRENCY             Default: 12
  TG_REQUESTS_PER_WORKER     Optional target requests per worker (soft)

Notes:
  - All code comments in English as requested; messages/log lines are minimal
  - Endpoints reflect current repo routes; adjust via code if your app differs
"""

import asyncio
import os
import random
import string
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


def _env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value.strip()


DEMO_APP_URL = _env("DEMO_APP_URL", "http://localhost:8000")
BACKEND_URL = _env("BACKEND_PROCESSOR_URL", "http://localhost:8001")

DURATION_SECONDS = int(os.getenv("TG_DURATION_SECONDS", "300"))
CONCURRENCY = int(os.getenv("TG_CONCURRENCY", "12"))
REQS_PER_WORKER = int(os.getenv("TG_REQUESTS_PER_WORKER", "0"))  # 0 = unlimited during duration


@dataclass
class Endpoint:
    method: str
    url: str
    weight: int = 1
    params: Optional[Dict[str, Any]] = None


def random_query(n: int = 6) -> str:
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(n))


def build_endpoint_catalog() -> Dict[str, List[Endpoint]]:
    """Define weighted endpoint mixes for both services."""
    demo = [
        Endpoint("GET", f"{DEMO_APP_URL}/", 4),
        Endpoint("GET", f"{DEMO_APP_URL}/health", 6),
        Endpoint("GET", f"{DEMO_APP_URL}/ready", 2),
        Endpoint("GET", f"{DEMO_APP_URL}/info", 2),
        Endpoint("GET", f"{DEMO_APP_URL}/api/catalog/products", 8, params={"limit": 10}),
        Endpoint("GET", f"{DEMO_APP_URL}/api/catalog/search", 5, params={"q": random_query()}),
        Endpoint("GET", f"{DEMO_APP_URL}/api/errors/400", 2),
        Endpoint("GET", f"{DEMO_APP_URL}/api/errors/500", 2),
        Endpoint("GET", f"{DEMO_APP_URL}/api/errors/random", 3),
    ]

    backend = [
        Endpoint("GET", f"{BACKEND_URL}/health", 6),
        Endpoint("GET", f"{BACKEND_URL}/ready", 3),
        Endpoint("GET", f"{BACKEND_URL}/info", 3),
        Endpoint("GET", f"{BACKEND_URL}/api/v1/errors/400", 2),
        Endpoint("GET", f"{BACKEND_URL}/api/v1/errors/500", 2),
        Endpoint("GET", f"{BACKEND_URL}/api/v1/errors/random", 3),
        Endpoint("GET", f"{BACKEND_URL}/api/v1/errors/cascade-error", 1),
    ]

    return {"demo": demo, "backend": backend}


def _weighted_choice(endpoints: List[Endpoint]) -> Endpoint:
    population = endpoints
    weights = [e.weight for e in endpoints]
    return random.choices(population, weights=weights, k=1)[0]


async def _issue_request(client: httpx.AsyncClient, ep: Endpoint) -> None:
    start = time.perf_counter()
    try:
        if ep.method == "GET":
            resp = await client.get(ep.url, params=ep.params, timeout=15.0)
        elif ep.method == "POST":
            resp = await client.post(ep.url, json=ep.params or {}, timeout=15.0)
        else:
            resp = await client.request(ep.method, ep.url, params=ep.params, timeout=15.0)
        # Lightweight output for quick feedback
        status = resp.status_code
    except Exception:
        status = -1
    finally:
        _ = (time.perf_counter() - start)
    # Optional: print one in N to avoid flooding stdout
    if random.random() < 0.02:
        print(f"{ep.method} {ep.url} -> {status}")


async def _worker(name: str, endpoints: List[Endpoint], stop_time: float, req_limit: int) -> None:
    async with httpx.AsyncClient(http2=False) as client:
        sent = 0
        while time.time() < stop_time:
            ep = _weighted_choice(endpoints)
            await _issue_request(client, ep)
            sent += 1
            if req_limit and sent >= req_limit:
                break
            # Jitter between 10–120 ms to vary pacing
            await asyncio.sleep(random.uniform(0.01, 0.12))


async def run(duration_seconds: int, concurrency: int, reqs_per_worker: int) -> None:
    catalog = build_endpoint_catalog()
    endpoints = catalog["demo"] + catalog["backend"]

    stop_time = time.time() + duration_seconds
    tasks = [
        asyncio.create_task(_worker(f"w{i+1}", endpoints, stop_time, reqs_per_worker))
        for i in range(concurrency)
    ]
    await asyncio.gather(*tasks)


def main() -> None:
    print(
        f"TrafficGen starting | demo={DEMO_APP_URL} backend={BACKEND_URL} "
        f"duration={DURATION_SECONDS}s concurrency={CONCURRENCY} per_worker={REQS_PER_WORKER or 'unlimited'}"
    )
    try:
        asyncio.run(run(DURATION_SECONDS, CONCURRENCY, REQS_PER_WORKER))
    except KeyboardInterrupt:
        print("Interrupted")
    print("TrafficGen finished")


if __name__ == "__main__":
    main()


