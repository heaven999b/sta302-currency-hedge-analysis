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

## Purpose and protocol / 研究目的与流程

This standalone file imports the frozen source data, computes every price return
on its native calendar before merging, enforces a common return interval, fits
OLS with Newey-West HAC inference, runs diagnostics, and performs a strict
expanding-window rolling-origin evaluation. Calendar years 2021, 2022, and 2023
are successive validation windows; the 2024-01-24 onward test period is used once.

本文件可独立读取冻结数据、在各数据自身交易日历内计算收益、执行严格同期合并、
拟合 OLS 并使用 Newey-West HAC 推断，同时完成诊断、非线性检验、异常值敏感性、
断点日期敏感性和扩展窗口 rolling-origin 验证。2021、2022、2023 年依次作为验证窗，
2024-01-24 之后的最终测试集只评估一次，不参与选模。

## Complete analysis code

```{{r complete-analysis, echo=TRUE, message=TRUE, warning=TRUE}}
{analysis_code}
```

## From the initial full model to the final predictive model / 从初始全变量模型到最终预测模型

The initial model uses every proposal predictor:
`Y ~ JPY_app * Post + Nikkei_ret + SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff`.
It remains the pre-specified inferential model for the hedge slopes and period
interaction. Model optimization is a separate, secondary prediction exercise.

初始模型纳入 proposal 中的全部预测变量，并继续作为日元斜率和时期交互项的预设
推断模型。模型精简只用于次要的样本外条件拟合检查，两种职责不混用。

```{{r model-selection-table, echo=FALSE}}
knitr::kable(rolling_origin_fold_metrics, digits = 6,
             caption = "Fold-level rolling-origin validation metrics")
knitr::kable(model_selection_rolling_origin, digits = 6,
             caption = "Three predeclared candidates ranked by mean validation RMSE")
```

`selected_model_name` records the candidate with the lowest mean RMSE across the
three rolling-origin folds. It is refitted on every development observation
through 2024-01-23 and evaluated exactly once on the untouched test set.
Variables are therefore removed by a predeclared out-of-sample rule, not by
individual p-values or by inspecting the test result.

最终预测模型由三个滚动验证窗的平均 RMSE 决定，再用截至 2024-01-23 的全部开发
数据重新拟合，并只在未接触测试集上评估一次。删减依据是预设样本外规则，而不是
单个 p 值或测试集结果。

## Main results / 主要结果

```{{r main-results, echo=FALSE}}
main_interaction <- coef_hac5[coef_hac5$term == "JPY_app:PostPost", ]
main_slopes <- hypothesis_tests[hypothesis_tests$inference == "Newey-West HAC(5)",
                                c("period", "estimate", "std_error", "p_value")]
main_table <- data.frame(
  result = c("Pre-period slope", "Post-period slope", "Slope change (Post interaction)",
             "Full-model R-squared", "Held-out selected-model RMSE", "Held-out mean-benchmark RMSE"),
  estimate = c(main_slopes$estimate[main_slopes$period == "Pre-pandemic"],
               main_slopes$estimate[main_slopes$period == "Post-pandemic"],
               main_interaction$estimate, summary(full_model)$r.squared,
               test_metrics$RMSE[1], test_metrics$RMSE[2]),
  p_value = c(main_slopes$p_value[main_slopes$period == "Pre-pandemic"],
              main_slopes$p_value[main_slopes$period == "Post-pandemic"],
              main_interaction$p_value, NA, NA, NA)
)
knitr::kable(main_table, digits = 6,
             caption = "Primary inference and locked held-out evaluation")
```

The HAC(5) interaction is not significant at 5%, so the primary model does not
establish a stable pandemic slope change. Both period-specific slopes differ
from the complete-hedge benchmark of -1. The selected conditional-fit model
substantially outperforms the naive held-out benchmarks, but it uses same-day
observed predictors and is not a tradable ahead-of-time forecast.

HAC(5) 下交互项在 5% 水平不显著，因此主模型不足以证明疫情前后斜率稳定改变；
两个分时期斜率都显著不同于完全对冲基准 -1。锁定模型在留出集上优于朴素基准，
但使用了当日已观测变量，不是可交易的提前预测。

## Assumption diagnostics / 假设诊断

```{{r diagnostic-table, echo=FALSE}}
diagnostic_display <- diagnostics[diagnostics$metric %in% c(
  "durbin_watson", "breusch_pagan_p", "breusch_godfrey_lag5_p",
  "jarque_bera_p", "reset_p", "max_vif", "cooks_over_4_over_n"
), ]
knitr::kable(diagnostic_display, caption = "Primary-model diagnostics")
```

Residual heteroskedasticity, serial dependence, heavy tails, and functional-form
evidence remain. HAC addresses covariance-based inference only; it does not make
these residual features disappear.

残差仍显示异方差、序列相关、厚尾与函数形式问题。HAC 只修正协方差推断，不能让
这些残差特征消失。

## Completed robustness analysis / 已完成稳健性分析

```{{r robustness-tables, echo=FALSE}}
knitr::kable(functional_form_sensitivity, digits = 6,
             caption = "Functional-form sensitivity under rolling-origin validation")
knitr::kable(influence_sensitivity, digits = 6,
             caption = "Influential-observation sensitivity")
knitr::kable(break_date_sensitivity, digits = 6,
             caption = "Declared pandemic-break window")
```

The quadratic terms are jointly significant under HAC(5), but predictive form
is judged by rolling-origin RMSE rather than in-sample significance. The
Yeo-Johnson lambda is reselected inside every fold; it does not resolve the
diagnostic rejections and makes the hedge
slope less directly interpretable. The sign and incomplete-hedge conclusion are
stable, but the 5% significance of the pandemic slope change is not: it changes
under winsorization, Cook's-distance deletion, and the earliest declared break
date. Therefore the honest final statement is that the post-period slope is
numerically more negative, while evidence for a discrete pandemic change is
sensitive to defensible analysis choices.

二次项在 HAC(5) 下联合显著，但预测函数形式按 rolling-origin RMSE 判断。
Yeo-Johnson 参数在每个折内重新选择；它没有消除诊断拒绝，并削弱斜率
的直接对冲比率解释。方向和“不完全对冲”结论稳定，但疫情斜率变化是否在 5%
水平显著会随缩尾、Cook 距离删除和最早备选断点而改变。因此最终结论应写为：
疫情后斜率在数值上更负，但“疫情造成离散改变”的统计证据对合理分析选择敏感。

## Data quality and reproducibility / 数据质量与复现

```{{r reproducibility-table, echo=FALSE}}
knitr::kable(data_quality_audit, caption = "Machine-checked data and split audit")
```

The raw snapshots are hash-bound, every source has a deterministic CSV export,
the processed variables have a machine-readable dictionary, and the repository
stores a hash manifest for core artifacts. See `REPRODUCIBILITY.md` for the exact
one-command workflow and interpretation limits.

原始快照有 SHA-256 绑定，每个数据源都有确定性的 CSV 导出，处理后变量有机器可读
字典，核心产物有完整哈希清单。具体一键复现方法见 `REPRODUCIBILITY.md`。

## Generated visual evidence / 结果图形

```{{r generated-figures, echo=FALSE, out.width="95%", fig.align="center"}}
figure_files <- file.path(figures_dir, c(
  "chronological_split.png",
  "rolling_origin_folds.png",
  "fx_slope_by_period.png",
  "coefficient_intervals_hac5.png",
  "hac_lag_sensitivity.png",
  "rolling_origin_model_comparison.png",
  "heldout_test_predictions.png",
  "residual_diagnostics.png",
  "robustness_sensitivity.png",
  "influence_diagnostics.png"
))
knitr::include_graphics(figure_files)
```

## Final conclusion / 最终结论

OLS estimates the conditional slopes; Newey-West changes the covariance matrix,
standard errors, confidence intervals, and p-values because the residuals are
heteroskedastic and serially dependent. The pandemic coefficient is an
associational structural-break estimate, not a causal COVID-19 effect. The
strongest reproducible conclusion is incomplete daily yen hedging in both
periods. Evidence of a discrete post-pandemic change is not robust across all
declared sensitivity analyses.

OLS 估计条件斜率；Newey-West 针对异方差和序列相关调整标准误、置信区间与 p 值。
疫情系数是相关性断点，不是 COVID-19 的因果效应。最稳健、可复现的结论是两个时期
都存在不完全日元对冲；疫情后是否发生离散变化，不能在全部已声明敏感性分析下保持。
'''
    TARGET.write_text(document, encoding="utf-8")
    print(f"Synchronized standalone Rmd: {TARGET}")


if __name__ == "__main__":
    main()
