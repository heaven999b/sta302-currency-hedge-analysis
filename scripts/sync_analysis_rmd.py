#!/usr/bin/env python3
"""Build the standalone course Rmd from the tested R pipeline."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis" / "run_analysis.R"
TARGET = ROOT / "analysis" / "STA302_Project_Analysis.Rmd"


def main() -> None:
    analysis_code = SOURCE.read_text(encoding="utf-8").rstrip()
    document = f'''---
title: "STA302 Final Project: Reproducible Daily Analysis"
author: "Haiwen Yi and group members"
date: "2026-09-21"
output:
  html_document:
    toc: true
    toc_depth: 2
---

## Purpose and protocol

This standalone file imports the frozen source data, computes every price return
on its native calendar before merging, enforces a common return interval, fits
OLS with Newey-West HAC inference, runs diagnostics, and performs a strict
chronological 60%/20%/20% train/tuning/test evaluation. The test period is used
once, after the predictive model is selected on the tuning period.

## Complete analysis code

```{{r complete-analysis, echo=TRUE, message=TRUE, warning=TRUE}}
{analysis_code}
```

## Generated visual evidence

```{{r generated-figures, echo=FALSE, out.width="95%", fig.align="center"}}
figure_files <- file.path(figures_dir, c(
  "chronological_split.png",
  "fx_slope_by_period.png",
  "coefficient_intervals_hac5.png",
  "hac_lag_sensitivity.png",
  "tuning_model_comparison.png",
  "heldout_test_predictions.png",
  "residual_diagnostics.png"
))
knitr::include_graphics(figure_files)
```

## Interpretation boundary

OLS estimates the conditional slopes; Newey-West changes the covariance matrix,
standard errors, confidence intervals, and p-values because the residuals are
heteroskedastic and serially dependent. The pandemic coefficient is an
associational structural-break estimate, not a causal COVID-19 effect.
'''
    TARGET.write_text(document, encoding="utf-8")
    print(f"Synchronized standalone Rmd: {TARGET}")


if __name__ == "__main__":
    main()
