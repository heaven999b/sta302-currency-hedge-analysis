#!/usr/bin/env python3
"""Create deterministic, analysis-ready CSV copies of every frozen source file."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "original_csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_yahoo(source: Path, destination: Path, ticker: str) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    adjusted = result["indicators"]["adjclose"][0]["adjclose"]
    if len(timestamps) != len(adjusted):
        raise ValueError(f"Timestamp/value length mismatch in {source.name}")
    source_digest = sha256(source)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["date", "adjusted_close", "ticker", "source_snapshot_sha256"])
        for timestamp, value in zip(timestamps, adjusted):
            if value is None:
                continue
            date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
            writer.writerow([date, value, ticker, source_digest])


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = {}
    for line in (RAW / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, filename = line.split(maxsplit=1)
            expected[filename.strip()] = digest

    rows: list[list[str | int]] = []
    for source in sorted(RAW.glob("*.csv")):
        destination = OUTPUT / source.name
        shutil.copyfile(source, destination)
        rows.append([
            f"data/raw/{source.name}",
            f"data/original_csv/{destination.name}",
            expected[source.name],
            sha256(destination),
            destination.stat().st_size,
            "byte-for-byte copy",
        ])

    yahoo_sources = [
        ("Yahoo_HEWJ_chart.json", "Yahoo_HEWJ_original_export.csv", "HEWJ"),
        ("Yahoo_EWJ_chart.json", "Yahoo_EWJ_original_export.csv", "EWJ"),
    ]
    for source_name, output_name, ticker in yahoo_sources:
        source = RAW / source_name
        destination = OUTPUT / output_name
        export_yahoo(source, destination, ticker)
        rows.append([
            f"data/raw/{source.name}",
            f"data/original_csv/{destination.name}",
            expected[source.name],
            sha256(destination),
            destination.stat().st_size,
            "Yahoo chart JSON to date/adjusted_close CSV; null prices omitted",
        ])

    manifest = OUTPUT / "SHA256SUMS.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "source_relative_path",
            "csv_relative_path",
            "source_sha256",
            "csv_sha256",
            "csv_bytes",
            "transformation",
        ])
        writer.writerows(rows)

    print(f"Exported {len(rows)} frozen sources as CSV under {OUTPUT}")


if __name__ == "__main__":
    main()
