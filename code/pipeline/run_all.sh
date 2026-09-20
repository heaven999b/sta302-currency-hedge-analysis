#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON_BIN:-python3}"

"$python_bin" code/pipeline/validate_outputs.py --raw-only
"$python_bin" code/pipeline/export_original_csv.py
Rscript code/analysis/run_analysis.R
"$python_bin" code/pipeline/sync_analysis_rmd.py
Rscript code/tests/test_pipeline.R
Rscript -e 'rmarkdown::render("code/analysis/STA302_Project_Analysis.Rmd", output_dir="reports/analysis", quiet=TRUE)'
"$python_bin" code/pipeline/build_bilingual_proposal_pdf.py
"$python_bin" code/pipeline/prepare_submission_package.py
"$python_bin" code/pipeline/test_submission_package.py
"$python_bin" code/pipeline/build_artifact_manifest.py
"$python_bin" code/pipeline/validate_outputs.py
