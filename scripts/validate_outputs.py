#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_raw_hashes() -> None:
    raw_dir = ROOT / "data" / "raw"
    checksum_file = raw_dir / "SHA256SUMS.txt"
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, filename = line.split(maxsplit=1)
        target = raw_dir / filename.strip()
        require(target.is_file(), f"Missing raw file: {target}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        require(actual == expected, f"SHA-256 mismatch: {filename}")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_analysis() -> None:
    data = read_rows(ROOT / "data" / "processed" / "sta302_daily_analysis.csv")
    require(len(data) == 2753, f"Expected 2753 rows, found {len(data)}")
    require(data[0]["date"] == "2014-02-06", f"Unexpected first date: {data[0]['date']}")
    require(data[-1]["date"] == "2026-07-31", f"Unexpected last date: {data[-1]['date']}")

    coefficients = read_rows(ROOT / "results" / "coefficients_hac5.csv")
    by_term = {row["term"]: row for row in coefficients}
    require(abs(float(by_term["JPY_app"]["estimate"]) - (-0.851968889752887)) < 1e-6,
            "JPY_app estimate changed")
    require(abs(float(by_term["JPY_app:PostPost"]["estimate"]) - (-0.064808531)) < 1e-6,
            "interaction estimate changed")
    require(abs(float(by_term["JPY_app:PostPost"]["p_value"]) - 0.0683468628773935) < 1e-6,
            "interaction HAC p-value changed")

    diagnostics = {row["metric"]: row["value"] for row in read_rows(ROOT / "results" / "diagnostics.csv")}
    require(abs(float(diagnostics["r_squared_full"]) - 0.712119863255427) < 1e-6,
            "full-model R-squared changed")
    require(float(diagnostics["max_vif"]) < 5, "maximum VIF is unexpectedly high")


def validate_artifacts() -> None:
    required = [
        ROOT / "output" / "STA302_Project_Analysis.html",
        ROOT / "output" / "pdf" / "STA302_Bilingual_Research_Proposal.pdf",
        ROOT / "figures" / "fx_slope_by_period.png",
        ROOT / "figures" / "residual_diagnostics.png",
        ROOT / "figures" / "coefficient_intervals_hac5.png",
        ROOT / "results" / "R_run_log.txt",
    ]
    for target in required:
        require(target.is_file() and target.stat().st_size > 1000, f"Missing or empty artifact: {target}")

    pdf = ROOT / "output" / "pdf" / "STA302_Bilingual_Research_Proposal.pdf"
    if shutil.which("pdftotext"):
        text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
        for phrase in [
            "Part I - English proposal",
            "第二部分",
            "Introduction (341 words)",
            "研究背景与问题",
            "0.0683",
        ]:
            require(phrase in text, f"Expected PDF text not found: {phrase}")


def main() -> None:
    validate_raw_hashes()
    if "--raw-only" in sys.argv[1:]:
        print("RAW VALIDATION PASSED: all frozen SHA-256 hashes match.")
        return
    validate_analysis()
    validate_artifacts()
    print("VALIDATION PASSED: raw hashes, analysis results, and bilingual artifacts are consistent.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise
