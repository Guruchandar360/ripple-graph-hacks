"""Verify a real model investigation through the running HTTP API, not a test double."""

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx


async def verify(restart_database=False):
    destination = Path("artifacts/http-proof")
    destination.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=20) as client:
        for _ in range(30):
            try:
                health = (await client.get("/api/health")).json()
                if health["database"] == "connected":
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError("The actual database did not become ready.")
        response = await client.post("/api/scenarios/memory/load")
        response.raise_for_status()
        loaded = response.json()
        response = await client.post("/api/runs", json={"mode": "graph"})
        response.raise_for_status()
        run_id = response.json()["id"]
        deadline = time.monotonic() + 360
        while time.monotonic() < deadline:
            response = await client.get(f"/api/runs/{run_id}")
            response.raise_for_status()
            run = response.json()
            if run["status"] != "investigating":
                break
            await asyncio.sleep(1)
        if run["status"] != "awaiting_approval":
            (destination / "failed-run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
            raise RuntimeError(f"Actual model did not produce an approvable proposal: {run['status']}")
        proposal = next(p for p in reversed(run["proposals"]) if not p["blocked_reason"] and not p["stale"])
        path = f"/api/runs/{run_id}/actions/{proposal['id']}/execute"
        response = await client.post(path)
        response.raise_for_status()
        result = response.json()
        assert result["verified"] and all(p["healthy"] for p in result["after"])
        duplicate = await client.post(path)
        duplicate.raise_for_status()
        assert duplicate.json() == result
        memory = (await client.get("/api/memory")).json()
        assert len(memory) == 1 and memory[0]["verified"]
        await client.post("/api/scenarios/memory/load")
        assert (await client.get("/api/workspace")).json()["memory_count"] == 1
        database_restart_verified = False
        if restart_database:
            # Only the verification driver can run this fixed local infrastructure command.
            # No subprocess operation is exposed through agent tools or the application API.
            from ripple.config import Settings

            if Settings().graph_host not in {"localhost", "127.0.0.1"}:
                raise RuntimeError("Database restart verification is restricted to local Docker.")
            process = await asyncio.create_subprocess_exec(
                "docker",
                "compose",
                "restart",
                "falkordb",
                cwd=Path(__file__).resolve().parent.parent,
            )
            if await process.wait() != 0:
                raise RuntimeError("The local verification database did not restart.")
            for _ in range(30):
                if (await client.get("/api/health")).json()["database"] == "connected":
                    break
                await asyncio.sleep(1)
            restarted = await client.get("/api/memory")
            restarted.raise_for_status()
            assert restarted.json()[0]["id"] == memory[0]["id"]
            database_restart_verified = True
        async with httpx.AsyncClient(base_url=str(client.base_url)) as visitor:
            isolated = await visitor.get(f"/api/runs/{run_id}")
            assert isolated.status_code == 404
        report = {
            "passed": True,
            "health": health,
            "run_id": run_id,
            "model_calls": run["model_calls"],
            "elapsed_ms": run["elapsed_ms"],
            "verified_result": result,
            "duplicate_result_identical": True,
            "memory_survived_scenario_reload": True,
            "foreign_visitor_status": isolated.status_code,
            "scenario": loaded["scenario"]["id"],
            "transport": "actual HTTP requests to Uvicorn",
            "database_restart_verified": database_restart_verified,
        }
        (destination / "http-proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--restart-database",
        action="store_true",
        help="Verify the documented local Docker Compose persistence",
    )
    asyncio.run(verify(parser.parse_args().restart_database))
