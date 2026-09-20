# Reproducibility guide / 可复现性说明

## What is frozen / 已冻结内容

- `data/raw/` contains the seven source snapshots used by the analysis.
- `data/raw/SHA256SUMS.txt` binds the exact source bytes.
- `data/SOURCE_MANIFEST.csv` records provider, URL, retrieval date, variables, and SHA-256.
- `config/analysis_protocol.yml` records the primary estimator, covariance rule, split, candidate models, and every robustness setting.
- `data/DATA_DICTIONARY.csv` defines every field in the processed table.

The pipeline does not fetch live data. This avoids silent revisions and makes the
reported numbers reproducible. Provider ownership and redistribution conditions
remain in force; see `DATA_USE.md`.

原始数据、来源、抓取日期、哈希值、变量定义和分析规则全部固定。流水线不抓取
实时数据，避免供应商修订导致结果漂移。

## Environment / 环境

The verified run used:

- macOS on Apple silicon;
- R 4.4.3;
- jsonlite 2.0.0, knitr 1.52, rmarkdown 2.32;
- Python 3.12 from the project conda environment;
- the dependencies declared in `environment.yml`.

Create the environment in a path without spaces:

```bash
conda env create -p /private/tmp/sta302_r_env -f environment.yml
conda activate /private/tmp/sta302_r_env
bash scripts/run_all.sh
```

## What `run_all.sh` proves / 一键流程验证内容

1. Recomputes all seven raw-file SHA-256 digests.
2. Exports all original sources to deterministic CSV copies in `data/original_csv/`.
3. Rebuilds the processed exact-interval table from frozen raw inputs.
4. Re-estimates OLS, HAC(1/5/10), diagnostics, chronological validation, nonlinear checks, influence checks, and break-date checks.
5. Runs R assertions for dates, row counts, split isolation, model-selection lock, conclusions, and figures.
6. Rebuilds the standalone R Markdown HTML and the three proposal PDFs.
7. Runs the standalone CSV-only R Markdown in an isolated temporary directory.
8. Hashes all core inputs, code, results, figures, and rendered outputs in `results/ARTIFACT_MANIFEST.csv`.
9. Runs independent Python validation of the expected numerical and documentary outputs.

## Leakage and randomness / 数据泄漏与随机性

- Dates are strictly increasing and never shuffled.
- Candidate prediction models use expanding training windows ending in 2020, 2021, and 2022, followed by validation in 2021, 2022, and 2023.
- The 2024-01-24 onward final test was evaluated once after the winner was locked by mean rolling-origin RMSE.
- Nonlinear sensitivity work uses the same folds and does not reopen the final-test choice.
- No stochastic estimator, bootstrap, random initialization, or random split is used, so a random seed is not applicable.
- Yeo-Johnson lambda selection is repeated inside each training fold.

## Output map / 输出对应关系

| Question | Evidence |
|---|---|
| Can the raw bytes be verified? | `data/raw/SHA256SUMS.txt` |
| Can every source be opened as CSV? | `data/original_csv/` and its `SHA256SUMS.csv` |
| What does each processed field mean? | `data/DATA_DICTIONARY.csv` |
| Are dates, missingness, intervals, and splits valid? | `results/data_quality_audit.csv` |
| Was model selection time-respecting? | `results/rolling_origin_fold_metrics.csv` and `results/model_selection_rolling_origin.csv` |
| Are conclusions robust to HAC lag? | `results/hac_lag_sensitivity.csv` |
| Do nonlinear forms help? | `results/functional_form_sensitivity.csv` |
| Are influential observations driving the result? | `results/influence_audit.csv` and `results/influence_sensitivity.csv` |
| Does the COVID cutoff matter? | `results/break_date_sensitivity.csv` |
| Can every artifact be tied to a hash? | `results/ARTIFACT_MANIFEST.csv` |
| What software actually ran? | `results/R_run_log.txt` |

## Interpretation boundary / 解释边界

The main coefficient is an associational conditional slope, not a causal COVID
effect. Newey-West changes uncertainty estimates; it does not repair functional
form, heavy tails, or omitted variables. Sensitivity analyses are reported even
when they weaken the preferred conclusion.

主系数是条件相关斜率，不是 COVID-19 的因果效应。Newey-West 修正协方差估计，
不能自动修复函数形式、厚尾或遗漏变量。敏感性分析无论是否支持主结论都完整保留。
