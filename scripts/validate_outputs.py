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
    require(len(data) == 2655, f"Expected 2655 rows, found {len(data)}")
    require(data[0]["date"] == "2014-02-06", f"Unexpected first date: {data[0]['date']}")
    require(data[-1]["date"] == "2026-07-31", f"Unexpected last date: {data[-1]['date']}")

    coefficients = read_rows(ROOT / "results" / "coefficients_hac5.csv")
    by_term = {row["term"]: row for row in coefficients}
    require(abs(float(by_term["JPY_app"]["estimate"]) - (-0.850936443698603)) < 1e-6,
            "JPY_app estimate changed")
    require(abs(float(by_term["JPY_app:PostPost"]["estimate"]) - (-0.0612064199953553)) < 1e-6,
            "interaction estimate changed")
    require(abs(float(by_term["JPY_app:PostPost"]["p_value"]) - 0.104391107292676) < 1e-6,
            "interaction HAC p-value changed")

    diagnostics = {row["metric"]: row["value"] for row in read_rows(ROOT / "results" / "diagnostics.csv")}
    require(abs(float(diagnostics["r_squared_full"]) - 0.703818792797337) < 1e-6,
            "full-model R-squared changed")
    require(float(diagnostics["max_vif"]) < 5, "maximum VIF is unexpectedly high")

    splits = read_rows(ROOT / "results" / "split_summary.csv")
    require([row["split"] for row in splits] == ["train", "tuning", "test"],
            "Chronological split order changed")
    require(sum(int(row["rows"]) for row in splits) == len(data), "Split rows do not cover data")

    tuning = read_rows(ROOT / "results" / "model_selection_tuning.csv")
    selected = min(tuning, key=lambda row: float(row["RMSE"]))["model"]
    test = read_rows(ROOT / "results" / "heldout_test_metrics.csv")
    require(test[0]["model"] == f"Selected: {selected}", "Held-out model was not locked on tuning")
    require(float(test[0]["RMSE"]) < min(float(row["RMSE"]) for row in test[1:]),
            "Selected model does not beat held-out benchmarks")


def validate_artifacts() -> None:
    required = [
        ROOT / "output" / "STA302_Project_Analysis.html",
        ROOT / "output" / "pdf" / "STA302_Research_Proposal_Official_EN.pdf",
        ROOT / "output" / "pdf" / "STA302_Bilingual_Research_Proposal.pdf",
        ROOT / "figures" / "fx_slope_by_period.png",
        ROOT / "figures" / "residual_diagnostics.png",
        ROOT / "figures" / "coefficient_intervals_hac5.png",
        ROOT / "figures" / "chronological_split.png",
        ROOT / "figures" / "tuning_model_comparison.png",
        ROOT / "figures" / "heldout_test_predictions.png",
        ROOT / "figures" / "hac_lag_sensitivity.png",
        ROOT / "results" / "R_run_log.txt",
    ]
    for target in required:
        require(target.is_file() and target.stat().st_size > 1000, f"Missing or empty artifact: {target}")

    official_pdf = ROOT / "output" / "pdf" / "STA302_Research_Proposal_Official_EN.pdf"
    bilingual_pdf = ROOT / "output" / "pdf" / "STA302_Bilingual_Research_Proposal.pdf"
    if shutil.which("pdftotext"):
        text = subprocess.check_output(["pdftotext", str(official_pdf), "-"], text=True)
        for phrase in [
            "Official English proposal",
            "Introduction (388 words)",
            "Table 1. Numerical summary",
            "Table 2. Complete preliminary OLS coefficient table",
            "Table 3. Proposed team schedule",
            "diagnose but do not correct violations",
        ]:
            require(phrase in text, f"Expected official PDF text not found: {phrase}")
        require("第二部分" not in text, "Official English PDF unexpectedly contains the Chinese section")

        bilingual_text = subprocess.check_output(["pdftotext", str(bilingual_pdf), "-"], text=True)
        for phrase in ["Official English proposal", "第二部分", "研究背景与问题", "提交前仍需确认"]:
            require(phrase in bilingual_text, f"Expected bilingual PDF text not found: {phrase}")


def validate_submission() -> None:
    package = ROOT / "submission"
    required = [
        package / "proposal" / "STA302_Research_Proposal_Official_EN.pdf",
        package / "code" / "STA302_Project_Analysis.Rmd",
        package / "data" / "cleaned" / "sta302_daily_analysis.csv",
        package / "data" / "original" / "Yahoo_HEWJ_original_export.csv",
        package / "data" / "original" / "Yahoo_EWJ_original_export.csv",
        package / "SHA256SUMS.csv",
    ]
    for target in required:
        require(target.is_file() and target.stat().st_size > 100, f"Missing submission file: {target}")
    for target in (package / "data").rglob("*"):
        if target.is_file():
            require(target.suffix.lower() == ".csv", f"Submission data file is not CSV: {target}")

    rmd = (package / "code" / "STA302_Project_Analysis.Rmd").read_text(encoding="utf-8")
    require('source("analysis/run_analysis.R")' not in rmd, "Submission Rmd still sources an external R script")
    for phrase in ["read_yahoo_adjusted <- function", "native_log_return <- function", "full_formula <-",
                   "Strict chronological evaluation", "residual_diagnostics.png"]:
        require(phrase in rmd, f"Standalone Rmd is missing analysis code: {phrase}")


def main() -> None:
    validate_raw_hashes()
    if "--raw-only" in sys.argv[1:]:
        print("RAW VALIDATION PASSED: all frozen SHA-256 hashes match.")
        return
    validate_analysis()
    validate_artifacts()
    validate_submission()
    print("VALIDATION PASSED: raw hashes, aligned analysis, strict splits, held-out results, figures, PDFs, standalone Rmd, and CSV package are consistent.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise
