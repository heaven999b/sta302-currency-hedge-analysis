#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON_BIN:-python3}"

"$python_bin" scripts/validate_outputs.py --raw-only
"$python_bin" scripts/export_original_csv.py
Rscript analysis/run_analysis.R
"$python_bin" scripts/sync_analysis_rmd.py
Rscript tests/test_pipeline.R
Rscript -e 'rmarkdown::render("analysis/STA302_Project_Analysis.Rmd", output_dir="output", quiet=TRUE)'
"$python_bin" scripts/build_bilingual_proposal_pdf.py
"$python_bin" scripts/prepare_submission_package.py
"$python_bin" scripts/test_submission_package.py
"$python_bin" scripts/build_artifact_manifest.py
"$python_bin" scripts/validate_outputs.py
