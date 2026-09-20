#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python3 scripts/validate_outputs.py --raw-only
Rscript analysis/run_analysis.R
Rscript -e 'rmarkdown::render("analysis/STA302_Project_Analysis.Rmd", output_dir="output", quiet=TRUE)'
python3 scripts/build_bilingual_proposal_pdf.py
python3 scripts/validate_outputs.py
