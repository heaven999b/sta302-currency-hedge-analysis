# Code / 代码

Everything executable is kept under this directory. Start with
`pipeline/run_all.sh` for a complete verified rebuild.

所有可执行代码集中在本目录。需要完整复现时，从 `pipeline/run_all.sh` 开始。

## Analysis / 分析代码

| File | Purpose |
|---|---|
| `analysis/run_analysis.R` | Reads frozen sources, constructs calendar-interval-matched data, audits market clocks, fits OLS/HAC and Dimson/weekly models, reruns arithmetic returns, performs rolling-origin evaluation and other sensitivities, and writes every CSV/RDS/figure result. |
| `analysis/STA302_Project_Analysis.Rmd` | Standalone course-facing R Markdown containing the complete analysis code plus interpretation and figures. |

## Pipeline / 构建与验证代码

| File | Purpose |
|---|---|
| `pipeline/run_all.sh` | One-command entry: validates inputs, reruns analysis, rebuilds reports/PDFs/submission, and checks every artifact. |
| `pipeline/export_original_csv.py` | Converts or copies all frozen source files into deterministic CSV exports. |
| `pipeline/sync_analysis_rmd.py` | Inserts the tested R pipeline into the standalone R Markdown report. |
| `pipeline/build_bilingual_proposal_pdf.py` | Builds the English, Chinese, and bilingual proposal PDFs. |
| `pipeline/prepare_submission_package.py` | Creates the Quercus-ready `submission/` package. |
| `pipeline/test_submission_package.py` | Knits the submission package in isolation to prove it does not depend on hidden repository files. |
| `pipeline/build_artifact_manifest.py` | Records SHA-256 hashes for core code, data, results, figures, and reports. |
| `pipeline/validate_outputs.py` | Independently checks expected numbers, files, PDF text, hashes, and submission completeness. |

## Tests / 测试代码

| File | Purpose |
|---|---|
| `tests/test_pipeline.R` | End-to-end R assertions for dates, alignment, rolling-origin selection, held-out testing, HAC conclusions, sensitivities, and figures. |

Run from the repository root:

```bash
bash code/pipeline/run_all.sh
```
