#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "submission"
ORIGINAL = PACKAGE / "data" / "original"
CLEANED = PACKAGE / "data" / "cleaned"
CODE = PACKAGE / "code"
PROPOSAL = PACKAGE / "proposal"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_yahoo_json(source: Path, destination: Path, ticker: str) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    adjusted = result["indicators"]["adjclose"][0]["adjclose"]
    if len(timestamps) != len(adjusted):
        raise ValueError(f"Mismatched timestamp/value lengths in {source.name}")
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "adjusted_close", "ticker", "source_snapshot_sha256"])
        digest = sha256(source)
        for timestamp, value in zip(timestamps, adjusted):
            if value is None:
                continue
            date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
            writer.writerow([date, value, ticker, digest])


def main() -> None:
    for directory in [ORIGINAL, CLEANED, CODE, PROPOSAL]:
        directory.mkdir(parents=True, exist_ok=True)

    raw = ROOT / "data" / "raw"
    for source in sorted(raw.glob("*.csv")):
        shutil.copy2(source, ORIGINAL / source.name)
    export_yahoo_json(raw / "Yahoo_HEWJ_chart.json", ORIGINAL / "Yahoo_HEWJ_original_export.csv", "HEWJ")
    export_yahoo_json(raw / "Yahoo_EWJ_chart.json", ORIGINAL / "Yahoo_EWJ_original_export.csv", "EWJ")

    shutil.copy2(ROOT / "data" / "processed" / "sta302_daily_analysis.csv",
                 CLEANED / "sta302_daily_analysis.csv")
    shutil.copy2(ROOT / "code" / "analysis" / "STA302_Project_Analysis.Rmd",
                 CODE / "STA302_Project_Analysis.Rmd")
    shutil.copy2(ROOT / "reports" / "proposal" / "STA302_Research_Proposal_Official_EN.pdf",
                 PROPOSAL / "STA302_Research_Proposal_Official_EN.pdf")
    shutil.copy2(ROOT / "reports" / "submission" / "QUERCUS_SUBMISSION_CHECKLIST.md",
                 PACKAGE / "QUERCUS_SUBMISSION_CHECKLIST.md")

    manifest_rows = []
    for item in sorted(PACKAGE.rglob("*")):
        if item.is_file() and item.name != "SHA256SUMS.csv":
            manifest_rows.append([str(item.relative_to(PACKAGE)), item.stat().st_size, sha256(item)])
    with (PACKAGE / "SHA256SUMS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "bytes", "sha256"])
        writer.writerows(manifest_rows)

    print(f"Prepared submission package: {PACKAGE}")
    print(f"Files: {len(manifest_rows)}")


if __name__ == "__main__":
    main()
