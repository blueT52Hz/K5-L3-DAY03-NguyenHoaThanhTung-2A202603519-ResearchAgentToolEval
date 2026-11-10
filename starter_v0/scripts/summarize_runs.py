"""One row per run JSON: version, suite, metrics, failed case ids.

Usage (from starter_v0/):
    python scripts/summarize_runs.py runs/ --output analysis/run_summary.csv
Complements scripts/parse_runs.py (one row per case).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FIELDS = [
    "run_file", "version", "artifact_version", "suite", "model", "total_cases", "provider_error_cases",
    "case_accuracy", "tool_routing_accuracy", "argument_accuracy", "multiturn_accuracy", "failed_cases",
]


def summarize(path: Path) -> dict:
    run = json.loads(path.read_text(encoding="utf-8"))
    summary = run.get("summary", {})
    failed = [r.get("id") or r.get("case_id") for r in run.get("results", []) if not r.get("result", {}).get("passed")]
    suite = "extension" if "_extension_" in path.name else ("group" if "_group_" in path.name else "base")
    return {
        "run_file": f"runs/{path.name}",
        "version": run.get("artifact_version", "").split("+")[0],
        "artifact_version": run.get("artifact_version", ""),
        "suite": suite,
        "model": run.get("model", ""),
        "total_cases": summary.get("total_cases"),
        "provider_error_cases": summary.get("provider_error_cases"),
        "case_accuracy": summary.get("case_accuracy"),
        "tool_routing_accuracy": summary.get("tool_routing_accuracy"),
        "argument_accuracy": summary.get("argument_accuracy"),
        "multiturn_accuracy": summary.get("multiturn_accuracy"),
        "failed_cases": " ".join(str(c) for c in failed),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [summarize(p) for p in sorted(args.runs_dir.glob("*.json"))]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} runs to {args.output}")


if __name__ == "__main__":
    main()
