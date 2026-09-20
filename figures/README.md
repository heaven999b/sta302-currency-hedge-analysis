# Figures / 图表

All files in this directory are generated visual evidence. The generating code
is `code/analysis/run_analysis.R` except for Chinese proposal variants produced
by the PDF builder.

本目录只保存图表；主要生成代码位于 `code/analysis/run_analysis.R`。

## Study design and model selection / 研究设计与选模

- `chronological_split.png`: development versus untouched final test.
- `rolling_origin_folds.png`: three expanding training windows and validation years.
- `rolling_origin_model_comparison.png`: combined comparison of all three candidates.
- `model_fx_interaction_rolling_rmse.png`: selected FX-interaction model only.
- `model_macro_controls_rolling_rmse.png`: macro-control candidate only.
- `model_full_factor_rolling_rmse.png`: initial full-factor model only.
- `heldout_test_predictions.png`: selected-model performance on the final test.

## Inference and diagnostics / 推断与诊断

- `fx_slope_by_period.png`: yen slope before and after the pandemic break.
- `coefficient_intervals_hac5.png`: full-model HAC(5) coefficient intervals.
- `residual_diagnostics.png`: six-panel assumption and influence diagnostics.
- `hac_lag_sensitivity.png`: interaction estimate under alternative HAC lags.
- `robustness_sensitivity.png`: functional-form, influence and break-date checks.
- `influence_diagnostics.png`: Cook-distance screening over time.

Files ending in `_zh.png` are Chinese-labelled versions used in the Chinese PDF.
