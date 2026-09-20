# Results / 数值结果

本目录是已经完成实验的机器可读结果。所有文件均由
`code/analysis/run_analysis.R` 自动生成，不要手工修改 CSV 或 RDS。

```text
results/
├── inference/      # 主模型系数、标准误、假设检验和共线性诊断
├── prediction/     # rolling-origin 选模、最终测试和逐日预测
├── robustness/     # 函数形式、HAC、断点、影响点和对齐敏感性
├── audit/          # 数据质量、逐行审计、运行日志和哈希清单
├── models/         # 可供 R 重新载入的模型对象
└── README.md
```

## `inference/`：主推断

| 文件 | 用途 |
|---|---|
| `coefficients_classical.csv` | 完整 OLS 模型的传统标准误结果。 |
| `coefficients_hac5.csv` | 同一组系数的主报告 Newey-West HAC(5) 推断。 |
| `fx_slope_hypothesis_tests.csv` | 疫情前后斜率及其与完全对冲基准 -1 的检验。 |
| `diagnostics.csv` | 线性、独立性、等方差、正态性、异常点等诊断汇总。 |
| `predictor_summary.csv` | 响应变量及初始模型全部数值变量的描述统计。 |
| `vif.csv` | 多重共线性检查。 |

## `prediction/`：时间序列验证与最终测试

| 文件 | 用途 |
|---|---|
| `split_summary.csv` | development 与不参与拟合/选模的 test 日期边界。 |
| `rolling_origin_fold_metrics.csv` | 三个候选模型在 2021、2022、2023 验证折上的 RMSE/MAE。 |
| `model_selection_rolling_origin.csv` | 三折均值、标准差和最终模型排名。 |
| `heldout_test_metrics.csv` | 锁定模型后的一次性 2024–2026 测试结果及基准比较。 |
| `heldout_test_predictions.csv` | 最终测试集逐日真实值和预测值。 |
| `chronological_validation.csv` | 最终测试指标的兼容性副本。 |

## `robustness/`：稳健性与敏感性

| 文件 | 用途 |
|---|---|
| `functional_form_sensitivity.csv` | 线性、二次项和 Yeo-Johnson 比较。 |
| `yeo_johnson_lambda_profile.csv`, `yeo_johnson_rolling_folds.csv` | 变换参数及逐折验证证据。 |
| `hac_lag_sensitivity.csv` | HAC lag 1/5/10 比较。 |
| `influence_sensitivity.csv` | 原始、缩尾及 Cook 删除压力测试。 |
| `break_date_sensitivity.csv` | 2020-03-06/11/16 三个固定断点比较。 |
| `data_alignment_sensitivity.csv` | 较宽松日期对齐规则的敏感性结果。 |
| `factor_interval_sensitivity.csv` | 因子收益区间起点完全匹配与主样本的比较。 |
| `nonsynchronous_fx_sensitivity.csv` | 同日、Dimson 累计暴露与周度共同日期的时钟敏感性。 |
| `return_definition_sensitivity.csv` | log 与普通收益的完整选模、测试和推断重跑。 |

## `audit/`：审计与复现证据

| 文件 | 用途 |
|---|---|
| `data_quality_audit.csv` | 日期、缺失、范围、区间和切分隔离的机器检查。 |
| `data_alignment_audit.csv` | 每个来源的日期区间和日内观测时钟审计。 |
| `influence_audit.csv` | 每个观测的 Cook 距离和标记状态。 |
| `R_run_log.txt` | R/包版本、样本、模型和本次运行摘要。 |
| `ARTIFACT_MANIFEST.csv` | 核心代码、数据、结果、图表和报告的 SHA-256 清单。 |

## `models/`：模型对象

- `models.rds`：完整模型、候选模型、HAC 协方差和锁定的选模元数据。它用于复核，正式结论仍以 CSV 和报告为准。
