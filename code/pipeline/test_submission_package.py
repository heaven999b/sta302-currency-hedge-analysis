#!/usr/bin/env python3
"""Knit the staged CSV-only submission in a clean temporary directory."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    rscript = shutil.which("Rscript")
    if not rscript:
        raise RuntimeError("Rscript is not on PATH; activate the project environment first")

    with tempfile.TemporaryDirectory(prefix="sta302-submission-") as temporary:
        package = Path(temporary) / "package"
        shutil.copytree(ROOT / "submission", package)
        subprocess.run(
            [
                rscript,
                "-e",
                'rmarkdown::render("code/STA302_Project_Analysis.Rmd", '
                'output_file="isolated_submission_test.html", quiet=TRUE)',
            ],
            cwd=package,
            check=True,
        )
        required = [
            package / "code" / "isolated_submission_test.html",
            package / "data" / "cleaned" / "sta302_daily_analysis.csv",
            package / "results" / "heldout_test_metrics.csv",
            package / "figures" / "chronological_split.png",
        ]
        for target in required:
            if not target.is_file() or target.stat().st_size < 100:
                raise AssertionError(f"Isolated submission output missing: {target}")

    print("ISOLATED SUBMISSION TEST PASSED: CSV-only package knits without repository data/raw.")


if __name__ == "__main__":
    main()
