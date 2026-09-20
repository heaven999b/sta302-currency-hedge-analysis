# Figures / 图表

本目录只保存自动生成的可视化证据。主要绘图代码在
`code/analysis/run_analysis.R`；中文 proposal 图由 PDF 构建脚本生成。

```text
figures/
├── inference/      # 系数、斜率和 HAC 推断图
├── prediction/     # 切分、rolling-origin、候选模型和最终测试图
├── diagnostics/    # 残差、影响点和综合稳健性图
└── README.md
```

## `inference/`：解释主模型

- `fx_slope_by_period.png`：疫情前后日元斜率。
- `coefficient_intervals_hac5.png`：完整模型 HAC(5) 系数区间。
- `hac_lag_sensitivity.png`：不同 HAC lag 下的交互项。
- `fx_slope_by_period_zh.png`：中文 proposal 使用的对应图。

## `prediction/`：展示严格预测流程

- `chronological_split.png`：development 与不参与拟合/选模的 final test。
- `rolling_origin_folds.png`：三个扩展训练窗口与验证年度。
- `rolling_origin_model_comparison.png`：三个候选模型总比较。
- `model_fx_interaction_rolling_rmse.png`：最终选中的汇率交互模型。
- `model_macro_controls_rolling_rmse.png`：宏观控制模型。
- `model_full_factor_rolling_rmse.png`：初始完整因子模型。
- `heldout_test_predictions.png`：锁定模型的最终测试表现。

## `diagnostics/`：检查模型风险

- `residual_diagnostics.png`：六联图检查残差与影响点。
- `robustness_sensitivity.png`：函数形式、影响点、断点和变换参数。
- `influence_diagnostics.png`：Cook 距离随时间的筛查。
- `time_and_return_definition_sensitivity.png`：同日/Dimson/周度时钟修正及 log/普通收益测试波动对比。
- `residual_diagnostics_zh.png`：中文 proposal 使用的诊断图。
