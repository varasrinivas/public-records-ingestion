"""
Data Quality Report Generator
Implements: REQ-DQ-002

Generates a summary report of all quality checks across layers.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.quality.checks import QualityResult


def generate_report(results: list[QualityResult], output_path: Optional[str] = None) -> str:
    """Generate a formatted quality report from check results."""
    now = datetime.now(timezone.utc).isoformat()

    # Summary stats
    total = len(results)
    passed = sum(1 for r in results if r.status.value == "PASS")
    warned = sum(1 for r in results if r.status.value == "WARN")
    failed = sum(1 for r in results if r.status.value == "FAIL")

    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║            DATA QUALITY REPORT                           ║",
        f"║  Generated: {now[:19]}                      ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        f"  Total checks: {total}   ✓ PASS: {passed}   ⚠ WARN: {warned}   ✗ FAIL: {failed}",
        "",
        "  ┌─────────────────────┬───────┬──────────┬────────┬──────────┬────────┐",
        "  │ Check               │ Layer │ Table    │ Pass % │ Thresh % │ Status │",
        "  ├─────────────────────┼───────┼──────────┼────────┼──────────┼────────┤",
    ]

    for r in results:
        icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(r.status.value, "?")
        lines.append(
            f"  │ {r.check_name[:19]:<19} │ {r.layer[:5]:<5} │ {r.table_name[:8]:<8} "
            f"│ {r.pass_rate:5.1f}% │ {r.threshold:5.1f}%  │ {icon} {r.status.value:<4} │"
        )

    lines.append(
        "  └─────────────────────┴───────┴──────────┴────────┴──────────┴────────┘"
    )

    # Add details for failures
    failures = [r for r in results if r.status.value in ("FAIL", "WARN")]
    if failures:
        lines.extend(["", "  Details:"])
        for r in failures:
            lines.append(f"    {r.status.value} {r.check_name}: {r.details}")

    report = "\n".join(lines) + "\n"

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)

    # Also save JSON for programmatic access
    if output_path:
        json_path = output_path.replace(".txt", ".json")
        with open(json_path, "w") as f:
            json.dump([r.to_dict() for r in results], f, indent=2)

    return report
