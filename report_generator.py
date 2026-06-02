"""
report_generator.py
-------------------
Generates downloadable CSV and summary statistics from verification results.
"""

import csv
import io
from datetime import datetime


def generate_csv_report(verdicts: list[dict], document_name: str = "document") -> bytes:
    """
    Generate a CSV report from a list of verdict dictionaries.

    Args:
        verdicts:      List of verdict dicts (claim, status, explanation, source).
        document_name: Name of the source document for the report header.

    Returns:
        CSV content as bytes, ready for Streamlit download button.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Header metadata rows
    writer.writerow(["Fact-Check Report"])
    writer.writerow(["Document", document_name])
    writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Total Claims", len(verdicts)])
    writer.writerow([])  # Blank separator row

    # Column headers
    writer.writerow(["#", "Claim", "Status", "Explanation", "Source"])

    # Data rows
    for i, v in enumerate(verdicts, 1):
        writer.writerow([
            i,
            v.get("claim", ""),
            v.get("status", ""),
            v.get("explanation", ""),
            v.get("source", ""),
        ])

    # Summary section
    writer.writerow([])
    writer.writerow(["--- Summary ---"])
    stats = compute_summary_stats(verdicts)
    for label, count in stats.items():
        writer.writerow([label, count])

    return output.getvalue().encode("utf-8")


def compute_summary_stats(verdicts: list[dict]) -> dict:
    """
    Compute summary counts for each verdict status.

    Args:
        verdicts: List of verdict dictionaries.

    Returns:
        Dictionary mapping status labels to counts and percentage.
    """
    total = len(verdicts)
    if total == 0:
        return {}

    counts = {"Verified": 0, "Inaccurate": 0, "False": 0, "Unverifiable": 0}
    for v in verdicts:
        status = v.get("status", "Unverifiable")
        if status in counts:
            counts[status] += 1
        else:
            counts["Unverifiable"] += 1

    stats = {}
    for status, count in counts.items():
        pct = round((count / total) * 100, 1)
        stats[f"{status} ({pct}%)"] = count

    return stats


def get_status_emoji(status: str) -> str:
    """Return an emoji badge for a given status string."""
    return {
        "Verified":      "✅",
        "Inaccurate":    "⚠️",
        "False":         "❌",
        "Unverifiable":  "❓",
    }.get(status, "❓")


def get_status_color(status: str) -> str:
    """Return a CSS hex color for a given status string."""
    return {
        "Verified":     "#22c55e",   # Green
        "Inaccurate":   "#f97316",   # Orange
        "False":        "#ef4444",   # Red
        "Unverifiable": "#94a3b8",   # Slate
    }.get(status, "#94a3b8")
