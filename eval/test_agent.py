#!/usr/bin/env python3
"""
Query the Business Case Writer agent and validate the streaming run.

Usage:
    python3 eval/test_agent.py              # runs test case 01 (happy path)
    python3 eval/test_agent.py 03          # runs test case 03 (contradictory assumptions)
    python3 eval/test_agent.py --all       # runs all 10 test cases sequentially
    python3 eval/test_agent.py --list      # print available cases and agent info

Requires:
    pip install httpx
    docker compose up  (backend must be running on localhost:8000)
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    sys.exit("Missing dependency: pip install httpx")

BASE_URL = "http://localhost:8000"
AGENT_NAME = "Business Case Writer"
CASES_DIR = Path(__file__).parent / "test_cases"
STREAM_TIMEOUT = 600  # 10 min — LLM runs can be slow


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_agent_id() -> str:
    resp = httpx.get(f"{BASE_URL}/api/agents", timeout=15)
    resp.raise_for_status()
    for a in resp.json():
        if a["name"] == AGENT_NAME:
            return a["id"]
    names = [a["name"] for a in resp.json()]
    raise RuntimeError(
        f"Agent '{AGENT_NAME}' not found.\nExisting agents: {names}\n"
        "Did the 0003 migration run? Try: docker compose down && docker compose up --build"
    )


def get_agent_detail(agent_id: str) -> dict:
    resp = httpx.get(f"{BASE_URL}/api/agents/{agent_id}", timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Test case helpers
# ---------------------------------------------------------------------------

def load_case(prefix: str) -> dict:
    matches = sorted(CASES_DIR.glob(f"{prefix}*.json"))
    if not matches:
        available = sorted(p.name for p in CASES_DIR.glob("*.json"))
        raise FileNotFoundError(
            f"No test case matching '{prefix}'. Available: {available}"
        )
    return json.loads(matches[0].read_text())


def build_prompt(tc: dict) -> str:
    return (
        "Please write a comprehensive business case for the following project.\n\n"
        f"{json.dumps(tc['input'], indent=2)}"
    )


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------

def stream_run(agent_id: str, prompt: str) -> tuple[list[dict], str, str | None]:
    """
    POST /api/agents/{id}/run and consume the SSE stream.

    Returns:
        events       — all parsed SSE payloads
        final_output — concatenated model text
        error        — error message string, or None on success
    """
    events: list[dict] = []
    output_parts: list[str] = []
    error: str | None = None

    with httpx.stream(
        "POST",
        f"{BASE_URL}/api/agents/{agent_id}/run",
        json={"input": prompt},
        timeout=STREAM_TIMEOUT,
        headers={"Accept": "text/event-stream"},
    ) as resp:
        if resp.status_code != 200:
            body = resp.read().decode()
            raise RuntimeError(f"HTTP {resp.status_code}: {body}")

        for raw_line in resp.iter_lines():
            if not raw_line.startswith("data: "):
                continue
            try:
                payload = json.loads(raw_line[6:])
            except json.JSONDecodeError as exc:
                print(f"  [WARN] Could not parse SSE line: {exc}", flush=True)
                continue

            events.append(payload)
            kind = payload.get("type", "")

            if kind == "on_chat_model_stream":
                # event["data"]["data"]["chunk"] is the AIMessageChunk
                chunk = payload.get("data", {}).get("data", {}).get("chunk", {})
                content = chunk.get("content", "") if isinstance(chunk, dict) else ""
                if content:
                    output_parts.append(content)
                    print(content, end="", flush=True)

            elif kind == "on_tool_start":
                name = payload.get("data", {}).get("name", "?")
                tool_input = payload.get("data", {}).get("data", {}).get("input", "")
                input_preview = str(tool_input)[:80].replace("\n", " ")
                print(f"\n  [TOOL ▶] {name}  input={input_preview!r}", flush=True)

            elif kind == "on_tool_end":
                name = payload.get("data", {}).get("name", "?")
                output = payload.get("data", {}).get("data", {}).get("output", "")
                out_preview = str(output)[:80].replace("\n", " ")
                print(f"  [TOOL ■] {name}  output={out_preview!r}", flush=True)

            elif kind == "error":
                error = payload.get("message", "Unknown error")
                print(f"\n  [ERROR] {error}", flush=True)

            elif kind == "done":
                run_id = payload.get("run_id", "?")
                print(f"\n  [DONE]  run_id={run_id}", flush=True)

    return events, "".join(output_parts), error


# ---------------------------------------------------------------------------
# Single test case runner
# ---------------------------------------------------------------------------

def run_case(agent_id: str, prefix: str) -> bool:
    tc = load_case(prefix)
    tc_id = tc["id"]
    expected_kpis = tc["expected_kpi_count"]
    expected_hitl = tc.get("expected_hitl_triggered", False)
    expected_flags = tc.get("expected_red_flags", [])
    expected_warns = tc.get("expected_warnings", [])

    banner = f"  TEST: {tc_id}"
    print(f"\n{'='*72}")
    print(banner)
    print(f"  {tc.get('notes', '')}")
    print(f"  Expects  kpis={expected_kpis}  hitl={expected_hitl}  flags={expected_flags}")
    print(f"{'─'*72}\n")

    prompt = build_prompt(tc)
    t0 = time.time()

    try:
        events, output, error = stream_run(agent_id, prompt)
    except Exception as exc:
        print(f"\n  [FATAL] {exc}")
        return False

    elapsed = time.time() - t0

    # ── Analyse events ──────────────────────────────────────────────────────
    tool_starts = [e for e in events if e.get("type") == "on_tool_start"]
    tool_names = [e.get("data", {}).get("name", "?") for e in tool_starts]
    unique_tools = list(dict.fromkeys(tool_names))  # order-preserving dedup

    # Check which bcase tools were called
    bcase_tools_called = [
        t for t in unique_tools
        if t in {
            "financial_calculator", "sensitivity_analyzer", "kpi_generator",
            "validate_bcase", "market_research", "document_parser",
            "template_renderer", "risk_register", "ask_human",
        }
    ]

    # ── Assertions ──────────────────────────────────────────────────────────
    failures: list[str] = []

    if error:
        failures.append(f"Run returned an error: {error}")

    if not output and not error:
        failures.append("No text output produced")

    if "financial_calculator" not in tool_names and expected_kpis > 0:
        failures.append("financial_calculator was never called (expected for non-zero KPIs)")

    if expected_hitl and "ask_human" not in tool_names:
        failures.append("ask_human was expected (HITL case) but was never called")

    # ── Print summary ────────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  SUMMARY  ({elapsed:.1f}s)")
    print(f"  Status         : {'ERROR' if error else 'OK'}")
    print(f"  Output length  : {len(output):,} chars")
    print(f"  Tools called   : {unique_tools or '—'}")
    print(f"  BCase tools    : {bcase_tools_called or '—'}")
    print(f"  Total events   : {len(events)}")

    if failures:
        print(f"\n  FAILURES:")
        for f in failures:
            print(f"    ✗ {f}")
    else:
        print(f"\n  ✓ PASS")

    return not bool(failures)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def list_info(agent_id: str) -> None:
    detail = get_agent_detail(agent_id)
    print(f"\nAgent: {detail['name']}  (id={agent_id})")
    print(f"Model: {detail['model']}  temp={detail['temperature']}")
    print(f"Sub-agents ({len(detail.get('subagents', []))}):")
    for sa in detail.get("subagents", []):
        tools = [t["name"] for t in sa.get("tools", [])]
        print(f"  • {sa['name']}  tools={tools}")
    print(f"\nTools selected ({len(detail.get('tools', []))}):")
    for t in detail.get("tools", []):
        print(f"  • {t['name']}  [{t['tool_type']}]")
    print(f"\nAvailable test cases:")
    for f in sorted(CASES_DIR.glob("*.json")):
        tc = json.loads(f.read_text())
        print(f"  {f.stem[:2]}  {tc['id']}")
        print(f"      {textwrap.shorten(tc.get('notes',''), 65)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", nargs="?", default="01", metavar="CASE",
                        help="Test case prefix, e.g. 01, 03 (default: 01)")
    parser.add_argument("--all", action="store_true", help="Run all 10 test cases")
    parser.add_argument("--list", action="store_true", help="List agent info and test cases")
    args = parser.parse_args()

    print(f"Connecting to {BASE_URL} …", end=" ", flush=True)
    try:
        agent_id = get_agent_id()
        print(f"OK  (agent_id={agent_id})")
    except Exception as exc:
        print(f"FAILED\n{exc}")
        sys.exit(1)

    if args.list:
        list_info(agent_id)
        return

    if args.all:
        prefixes = sorted(p.stem[:2] for p in CASES_DIR.glob("*.json"))
        results: dict[str, bool] = {}
        for prefix in prefixes:
            results[prefix] = run_case(agent_id, prefix)

        print(f"\n{'='*72}")
        print("FINAL RESULTS")
        for prefix, ok in results.items():
            tc = load_case(prefix)
            mark = "✓" if ok else "✗"
            print(f"  {mark}  {prefix}  {tc['id']}")
        failed = sum(1 for ok in results.values() if not ok)
        total = len(results)
        print(f"\n{total - failed}/{total} passed")
        sys.exit(0 if failed == 0 else 1)

    # Single case
    ok = run_case(agent_id, args.case)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
