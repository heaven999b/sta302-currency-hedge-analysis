#!/usr/bin/env python3
"""Hash every core research input, script, result and rendered artifact."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "audit" / "ARTIFACT_MANIFEST.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(relative: Path) -> tuple[str, str]:
    path = relative.as_posix()
    if path.startswith("data/raw/"):
        return "frozen_input", "external provider snapshot"
    if path.startswith("data/original_csv/"):
        return "csv_export", "code/pipeline/export_original_csv.py"
    if path.startswith("data/processed/"):
        return "processed_data", "code/analysis/run_analysis.R"
    if path.startswith("results/"):
        return "statistical_result", "code/analysis/run_analysis.R or manifest builder"
    if path.startswith("figures/"):
        return "figure", "code/analysis/run_analysis.R or PDF builder"
    if path.startswith("reports/") and relative.suffix.lower() in {".html", ".pdf"}:
        return "rendered_output", "R Markdown or PDF builder"
    if path.startswith("code/"):
        return "executable_code", "version-controlled source"
    if path.startswith("config/") or path.endswith("environment.yml"):
        return "configuration", "version-controlled source"
    if path.endswith(".md") or path.endswith(".csv"):
        return "documentation", "version-controlled source"
    return "project_file", "version-controlled source"


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    if not path.is_file() or ".git" in parts or parts[0] == "submission" or "tmp" in parts:
        return False
    if path == OUTPUT or "__pycache__" in parts:
        return False
    return (
        parts[0] in {"code", "config", "data", "figures", "reports", "results"}
        or relative.as_posix() in {"README.md", "REPRODUCIBILITY.md", "environment.yml"}
    )


def main() -> None:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not included(path):
            continue
        relative = path.relative_to(ROOT)
        role, producer = classify(relative)
        rows.append([relative.as_posix(), role, producer, path.stat().st_size, sha256(path)])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["relative_path", "role", "producer", "bytes", "sha256"])
        writer.writerows(rows)
    print(f"Wrote core artifact manifest with {len(rows)} files: {OUTPUT}")


if __name__ == "__main__":
    main()
