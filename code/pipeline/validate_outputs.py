#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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


def validate_original_csv_exports() -> None:
    manifest_path = ROOT / "data" / "original_csv" / "SHA256SUMS.csv"
    require(manifest_path.is_file(), "Missing original-source CSV manifest")
    rows = read_rows(manifest_path)
    require(len(rows) == 7, f"Expected seven original-source CSV exports, found {len(rows)}")
    for row in rows:
        source = ROOT / row["source_relative_path"]
        exported = ROOT / row["csv_relative_path"]
        require(source.is_file() and exported.is_file(), f"Missing CSV export pair: {row}")
        require(hashlib.sha256(source.read_bytes()).hexdigest() == row["source_sha256"],
                f"Source hash mismatch in CSV manifest: {source.name}")
        require(hashlib.sha256(exported.read_bytes()).hexdigest() == row["csv_sha256"],
                f"Export hash mismatch: {exported.name}")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_analysis() -> None:
    data = read_rows(ROOT / "data" / "processed" / "sta302_daily_analysis.csv")
    require(len(data) == 2655, f"Expected 2655 rows, found {len(data)}")
    require(data[0]["date"] == "2014-02-06", f"Unexpected first date: {data[0]['date']}")
    require(data[-1]["date"] == "2026-07-31", f"Unexpected last date: {data[-1]['date']}")

    coefficients = read_rows(ROOT / "results" / "inference" / "coefficients_hac5.csv")
    by_term = {row["term"]: row for row in coefficients}
    require(abs(float(by_term["JPY_app"]["estimate"]) - (-0.850936443698603)) < 1e-6,
            "JPY_app estimate changed")
    require(abs(float(by_term["JPY_app:PostPost"]["estimate"]) - (-0.0612064199953553)) < 1e-6,
            "interaction estimate changed")
    require(abs(float(by_term["JPY_app:PostPost"]["p_value"]) - 0.104391107292676) < 1e-6,
            "interaction HAC p-value changed")

    diagnostics = {row["metric"]: row["value"] for row in read_rows(ROOT / "results" / "inference" / "diagnostics.csv")}
    require(abs(float(diagnostics["r_squared_full"]) - 0.703818792797337) < 1e-6,
            "full-model R-squared changed")
    require(float(diagnostics["max_vif"]) < 5, "maximum VIF is unexpectedly high")

    splits = read_rows(ROOT / "results" / "prediction" / "split_summary.csv")
    require([row["split"] for row in splits] == ["development", "test"],
            "Chronological split order changed")
    require(sum(int(row["rows"]) for row in splits) == len(data), "Split rows do not cover data")
    require(splits[1]["start_date"] == "2024-01-24", "Final-test cutoff changed")

    rolling = read_rows(ROOT / "results" / "prediction" / "model_selection_rolling_origin.csv")
    folds = read_rows(ROOT / "results" / "prediction" / "rolling_origin_fold_metrics.csv")
    require(len(folds) == 9 and len({row["fold"] for row in folds}) == 3,
            "Rolling-origin fold results are incomplete")
    selected = min(rolling, key=lambda row: float(row["mean_RMSE"]))["model"]
    test = read_rows(ROOT / "results" / "prediction" / "heldout_test_metrics.csv")
    require(test[0]["model"] == f"Selected: {selected}",
            "Held-out model was not locked on rolling-origin validation")
    require(float(test[0]["RMSE"]) < min(float(row["RMSE"]) for row in test[1:]),
            "Selected model does not beat held-out benchmarks")
    require({"Static FX regression benchmark", "Theoretical minus-one spot benchmark",
             "Historical-mean benchmark", "Zero-return benchmark"}.issubset(
                {row["model"] for row in test}),
            "Held-out benchmark set is incomplete")

    alignment = read_rows(ROOT / "results" / "audit" / "data_alignment_audit.csv")
    require({row["series"] for row in alignment} ==
            {"JPY_app", "Nikkei_ret", "dlog_VIX", "Japan_FF5", "Japan_MOM"},
            "Clock audit does not cover every source family")
    require(all(int(row["final_joint_interval_rows"]) == len(data) for row in alignment),
            "Clock audit final-sample count changed")

    nonsync = read_rows(ROOT / "results" / "robustness" / "nonsynchronous_fx_sensitivity.csv")
    require(len(nonsync) == 5 and {row["specification"] for row in nonsync} ==
            {"Current-date full model", "Dimson adjacent-return full model",
             "Last-common-date weekly FX model"},
            "Time-clock sensitivity is incomplete")
    return_def = read_rows(ROOT / "results" / "robustness" / "return_definition_sensitivity.csv")
    require([row["definition"] for row in return_def] == ["Log returns", "Arithmetic returns"],
            "Return-definition sensitivity is incomplete")
    return_sds = [float(row["test_response_sd"]) for row in return_def]
    require(max(return_sds) / min(return_sds) < 1.01,
            "Log/arithmetic test volatility diverges unexpectedly")

    functional = read_rows(ROOT / "results" / "robustness" / "functional_form_sensitivity.csv")
    require(len(functional) == 3, "Functional-form sensitivity must contain three specifications")
    by_spec = {row["specification"]: row for row in functional}
    require(-2 <= float(by_spec["Yeo-Johnson response"]["yeo_johnson_lambda"]) <= 2,
            "Development-selected Yeo-Johnson lambda is invalid")
    require(float(by_spec["Quadratic yen sensitivity"]["nonlinear_terms_hac5_joint_p"]) < 0.05,
            "Quadratic-term sensitivity conclusion changed")
    require(all(float(row["rolling_mean_RMSE_original_scale"]) > 0 for row in functional),
            "Rolling functional-form metrics are invalid")

    influence = read_rows(ROOT / "results" / "robustness" / "influence_sensitivity.csv")
    require(len(influence) == 3, "Influence sensitivity must contain three analyses")
    influence_p = [float(row["interaction_hac5_p"]) for row in influence]
    require(influence_p[0] > 0.05 and min(influence_p[1:]) < 0.05,
            "Influence fragility conclusion changed")
    audit = read_rows(ROOT / "results" / "audit" / "influence_audit.csv")
    require(sum(row["flagged"].upper() == "TRUE" for row in audit) == 134,
            "Cook's-distance flagged count changed")

    breaks = read_rows(ROOT / "results" / "robustness" / "break_date_sensitivity.csv")
    require([row["transition_date"] for row in breaks] ==
            ["2020-03-06", "2020-03-11", "2020-03-16"],
            "Declared break-date window changed")
    break_p = [float(row["interaction_hac5_p"]) for row in breaks]
    require(min(break_p) < 0.05 < max(break_p), "Break-date sensitivity no longer crosses 5%")

    quality = read_rows(ROOT / "results" / "audit" / "data_quality_audit.csv")
    for row in quality:
        require(row["status"].upper() == row["expected"].upper() or
                (row["check"] == "processed_rows" and row["status"].upper() == "TRUE" and
                 row["expected"] == "2655"), f"Failed data-quality check: {row['check']}")


def validate_artifacts() -> None:
    required = [
        ROOT / "reports" / "analysis" / "STA302_Project_Analysis.html",
        ROOT / "reports" / "proposal" / "STA302_Research_Proposal_Official_EN.pdf",
        ROOT / "reports" / "proposal" / "STA302_Bilingual_Research_Proposal.pdf",
        ROOT / "reports" / "proposal" / "STA302_Research_Proposal_Official_ZH.pdf",
        ROOT / "figures" / "inference" / "fx_slope_by_period.png",
        ROOT / "figures" / "diagnostics" / "residual_diagnostics.png",
        ROOT / "figures" / "inference" / "coefficient_intervals_hac5.png",
        ROOT / "figures" / "prediction" / "chronological_split.png",
        ROOT / "figures" / "prediction" / "rolling_origin_folds.png",
        ROOT / "figures" / "prediction" / "rolling_origin_model_comparison.png",
        ROOT / "figures" / "prediction" / "model_fx_interaction_rolling_rmse.png",
        ROOT / "figures" / "prediction" / "model_macro_controls_rolling_rmse.png",
        ROOT / "figures" / "prediction" / "model_full_factor_rolling_rmse.png",
        ROOT / "figures" / "prediction" / "heldout_test_predictions.png",
        ROOT / "figures" / "inference" / "hac_lag_sensitivity.png",
        ROOT / "figures" / "diagnostics" / "robustness_sensitivity.png",
        ROOT / "figures" / "diagnostics" / "influence_diagnostics.png",
        ROOT / "figures" / "diagnostics" / "time_and_return_definition_sensitivity.png",
        ROOT / "results" / "audit" / "R_run_log.txt",
        ROOT / "results" / "audit" / "ARTIFACT_MANIFEST.csv",
    ]
    for target in required:
        require(target.is_file() and target.stat().st_size > 1000, f"Missing or empty artifact: {target}")

    official_pdf = ROOT / "reports" / "proposal" / "STA302_Research_Proposal_Official_EN.pdf"
    bilingual_pdf = ROOT / "reports" / "proposal" / "STA302_Bilingual_Research_Proposal.pdf"
    chinese_pdf = ROOT / "reports" / "proposal" / "STA302_Research_Proposal_Official_ZH.pdf"
    if shutil.which("pdftotext"):
        text = subprocess.check_output(["pdftotext", str(official_pdf), "-"], text=True)
        for phrase in [
            "Official English proposal",
            "Abstract",
            "Introduction (400 words)",
            "Related work and research gap",
            "Table 1. Summary and missingness",
            "Table 2. Preliminary OLS estimates",
            "Table 3. Proposed team schedule",
            "three hierarchy-respecting candidates",
            "the reduced winner is the final predictive model",
            "Glen, J., & Jorion, P. (1993)",
            "Six-panel diagnostics",
            "diagnose but do not correct violations",
        ]:
            require(phrase in text, f"Expected official PDF text not found: {phrase}")
        require("第二部分" not in text, "Official English PDF unexpectedly contains the Chinese section")

        bilingual_text = subprocess.check_output(["pdftotext", str(bilingual_pdf), "-"], text=True)
        for phrase in ["Official English proposal", "第二部分", "摘要", "研究背景与问题", "三个遵守层级原则的候选模型", "数据与产品文档", "提交前仍需确认"]:
            require(phrase in bilingual_text, f"Expected bilingual PDF text not found: {phrase}")

        chinese_text = subprocess.check_output(["pdftotext", str(chinese_pdf), "-"], text=True)
        for phrase in ["完整中文提案", "摘要", "研究背景与问题", "三个遵守层级原则的候选模型", "数据与产品文档", "残差诊断", "提交前仍需确认"]:
            require(phrase in chinese_text, f"Expected Chinese PDF text not found: {phrase}")

    manifest_rows = read_rows(ROOT / "results" / "audit" / "ARTIFACT_MANIFEST.csv")
    require(len(manifest_rows) >= 45, "Core artifact manifest is unexpectedly incomplete")
    manifest_paths = {row["relative_path"] for row in manifest_rows}
    for required_path in [
        "code/analysis/run_analysis.R",
        "config/analysis_protocol.yml",
        "data/processed/sta302_daily_analysis.csv",
        "data/TIME_ALIGNMENT.csv",
        "results/robustness/functional_form_sensitivity.csv",
        "results/robustness/nonsynchronous_fx_sensitivity.csv",
        "results/robustness/return_definition_sensitivity.csv",
        "results/robustness/factor_interval_sensitivity.csv",
        "results/prediction/rolling_origin_fold_metrics.csv",
        "results/prediction/model_selection_rolling_origin.csv",
        "results/robustness/influence_sensitivity.csv",
        "results/robustness/break_date_sensitivity.csv",
        "reports/analysis/STA302_Project_Analysis.html",
    ]:
        require(required_path in manifest_paths, f"Artifact manifest omits {required_path}")
    for row in manifest_rows:
        target = ROOT / row["relative_path"]
        require(target.is_file(), f"Manifest target missing: {target}")
        require(hashlib.sha256(target.read_bytes()).hexdigest() == row["sha256"],
                f"Artifact hash mismatch: {row['relative_path']}")


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
    require('source("code/analysis/run_analysis.R")' not in rmd, "Submission Rmd still sources an external R script")
    for phrase in ["read_yahoo_adjusted <- function", "native_log_return <- function", "full_formula <-",
                   "rolling-origin evaluation", "residual_diagnostics.png"]:
        require(phrase in rmd, f"Standalone Rmd is missing analysis code: {phrase}")


def main() -> None:
    validate_raw_hashes()
    if "--raw-only" in sys.argv[1:]:
        print("RAW VALIDATION PASSED: all frozen SHA-256 hashes match.")
        return
    validate_original_csv_exports()
    validate_analysis()
    validate_artifacts()
    validate_submission()
    print("VALIDATION PASSED: raw/CSV hashes, interval/clock alignment, rolling-origin selection, locked held-out results, time/return-definition/nonlinear/influence/break sensitivity, figures, PDFs, standalone Rmd, and artifact manifest are consistent.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise
