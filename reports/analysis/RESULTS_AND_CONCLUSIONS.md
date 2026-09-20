# Results and conclusions / 结果与结论

## Method / 方法

All price returns are computed inside their original series before merging. The
primary sample then requires HEWJ/EWJ, USD/JPY, Nikkei 225, and VIX returns to
share the same interval start and end dates. This produces 2,655 observations.
The less strict same-end-date rule produces 2,925 observations and is retained
only as a sensitivity analysis.

所有价格序列先在各自原始交易日历内计算收益，再合并。主样本要求
HEWJ/EWJ、美元兑日元、日经 225 和 VIX 的收益区间起止日期完全一致，得到
2,655 条观测；仅要求结束日期相同的 2,925 条样本只作为敏感性分析。

The main conditional-mean model uses OLS coefficients. Since residual tests
reject iid errors, its primary confidence intervals and p-values use Newey-West
HAC(5). HAC(1) and HAC(10) are reported as prespecified sensitivity checks.

主条件均值模型仍用 OLS 估计系数；由于残差检验拒绝 iid，主要置信区间和
p 值使用 Newey-West HAC(5)，并报告 HAC(1) 与 HAC(10) 敏感性结果。

## Initial and final model roles / 初始模型与最终模型职责

The analysis deliberately keeps inference and prediction separate. The initial
full model is
`Y ~ JPY_app * Post + Nikkei_ret + SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff`.
It uses all ten predictors required by the proposal and remains the
pre-specified model for the hedge-slope and period-interaction inference.

For secondary conditional prediction, three candidates were compared using
expanding-window rolling-origin validation. Models trained through 2020, 2021,
and 2022 were scored on 2021, 2022, and 2023. Mean RMSE was 0.26665 for the
FX-interaction model, 0.27417 for macro controls, and 0.27637 for the full factor
model. The FX-interaction model therefore won under the locked rule and has
formula `Y ~ JPY_app * Post`. It was refitted on all 2,124 development rows
through 2024-01-23 before one untouched-test evaluation. Reduction was selected
by time-respecting out-of-sample RMSE, not by deleting insignificant coefficients.

本研究刻意区分解释性推断和预测。初始完整模型为
`Y ~ JPY_app * Post + Nikkei_ret + SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff`，
包含 proposal 要求的全部十个预测变量，并继续承担日元斜率和时期交互项的预设推断。
次要预测环节采用扩展窗口 rolling-origin：分别用截至 2020、2021、2022 年的数据
训练，并在 2021、2022、2023 年验证。汇率交互、宏观控制和完整因子模型的三折平均
RMSE 分别为 0.26665、0.27417 和 0.27637，因此锁定汇率交互模型
`Y ~ JPY_app * Post`。该模型用截至 2024-01-23 的 2,124 条开发样本重新拟合后，
只在未接触测试集上评估一次。精简依据是遵守时间顺序的样本外 RMSE，而不是 p 值。

## Main inference / 主要推断

- Pre-period yen slope: -0.85094; HAC(5) test against -1, p = 0.000005.
- Post-period implied slope: -0.91214; HAC(5) test against -1, p = 0.000048.
- Change in slope: -0.06121; classical p = 0.00931, HAC(5) p = 0.10439.
- HAC interaction p-values are 0.10287, 0.10439, and 0.10635 for lags 1, 5, and 10.

因此，疫情后斜率在数值上更接近 -1，但使用适合非 iid 残差的 HAC 推断后，
没有足够证据认定疫情前后斜率发生变化。两个时期的斜率都显著不同于 -1，
所以更稳妥的结论是：两个时期均存在不完全对冲，而不是疫情导致了显著变化。

## Rolling-origin prediction check / 滚动起点预测检验

The three validation windows contain 211, 211, and 217 observations. The
FX-interaction candidate has the lowest mean validation RMSE (0.26665) and is
locked before test evaluation. After refitting on all development data, its
test RMSE is 0.31589 and MAE is 0.21576, compared with 0.65316 and 0.46087 for
the historical-mean benchmark.
This is a held-out conditional-fit check using same-day observed predictors, not
an ahead-of-time return forecast or trading backtest.

三个验证窗分别有 211、211、217 条观测。汇率交互模型的三折平均 RMSE 最低
（0.26665），因此在查看测试结果前锁定；用全部开发数据重拟合后，其测试 RMSE
为 0.31589、MAE 为 0.21576，明显优于历史均值基准的 0.65316 和 0.46087。
该结果是使用当日已观测预测变量的样本外条件拟合检查，不是提前收益预测或交易回测。

## Diagnostics and limits / 诊断与限制

The residuals remain heteroskedastic, serially dependent, heavy-tailed, and show
functional-form evidence. Newey-West addresses covariance-based inference but
does not repair misspecification or establish causality. The pandemic indicator
is a descriptive break, and the results concern one ETF pair.

残差仍存在异方差、序列相关、厚尾和函数形式问题。Newey-West 只修正推断所用
协方差矩阵，并不自动修复模型设定，也不能建立因果关系。疫情变量只是描述性
断点，结论也仅针对这一组 ETF。

## Functional-form sensitivity / 函数形式敏感性

The promised nonlinear checks are now complete. A hierarchy-preserving model
adds `JPY_app^2` and `JPY_app^2 x Post`. The two quadratic terms are jointly
significant under HAC(5) (p = 0.0288), but its mean rolling-origin RMSE is
0.28180, worse than 0.27637 for the corresponding linear full model. It also does not remove RESET,
heteroskedasticity, serial dependence, or heavy-tail rejections.

The Yeo-Johnson response parameter was reselected inside each training fold from
a fixed -2 to 2 grid. Fold lambdas were 0.95, 0.95, and 1.00; its mean
inverse-transformed rolling-origin RMSE is 0.27531, a small improvement,
but the transformed model still fails the same broad diagnostic families and
its slope is no longer a directly interpretable hedge ratio. It is therefore
reported as sensitivity evidence, not substituted for the primary model after
the test set had already been locked.

预先承诺的非线性检验已经完成。保留层级原则的二次模型加入 `JPY_app^2` 及其与
`Post` 的交互项；两个二次项在 HAC(5) 下联合 p = 0.0288，但三折平均 RMSE 为
0.28180，差于对应线性完整模型的 0.27637，也没有消除 RESET、异方差、序列相关
和厚尾问题。Yeo-Johnson 参数在各训练折内重新选择，依次为 0.95、0.95、1.00；
其逆变换平均 RMSE 为 0.27531，只是轻微改善，且斜率不再能直接解释为对冲
比率。因此两者都作为敏感性证据报告，不在测试集已锁定后替换主模型。

## Influence and break-date sensitivity / 影响点与断点日期敏感性

The primary model retains all 2,655 valid observations. There are 134 dates with
Cook's distance above `4/n`; every date and diagnostic is recorded in
`results/audit/influence_audit.csv`. No observation was classified as a confirmed
source error by the automated hash and interval checks.

The focal interaction is not significant in the primary HAC(5) model
(estimate -0.06121, p = 0.10439), but becomes significant after 0.5/99.5
percentile winsorization (estimate -0.08499, p = 0.00489) and after mechanically
removing Cook-flagged rows (estimate -0.04878, p = 0.01121). The latter deletion
is explicitly post-hoc and is not a preferred estimate.

The declared transition dates also matter: March 6 gives p = 0.03028, March 11
gives p = 0.10439, and March 16 gives p = 0.15997. The interaction remains
negative in every run, but its 5% significance is not robust to the break date
or influence rule. Consequently, the evidence supports a numerically more
negative post-period slope, not a stable claim of a discrete pandemic change.

主模型保留全部 2,655 条有效观测；134 个日期超过 Cook 距离 `4/n` 阈值，已逐行
记录。主模型交互项 p = 0.10439；0.5/99.5 分位缩尾后 p = 0.00489，机械删除
Cook 标记行后 p = 0.01121。后者是事后压力测试，不作为首选估计。备选断点
3 月 6 日、3 月 11 日和 3 月 16 日的 p 值分别为 0.03028、0.10439 和 0.15997。
交互项方向始终为负，但其 5% 显著性对断点和影响点规则敏感。因此可以说疫情后
斜率在数值上更负，不能稳健声称发生了离散的疫情结构变化。

## Reproducibility status / 可复现性状态

All seven frozen source files are SHA-256 verified. Each source is also exported
as CSV under `data/original_csv/`; the Yahoo JSON-to-CSV conversion records the
source digest on every row. `data/SOURCE_MANIFEST.csv` records provider URLs,
retrieval dates and hashes, while `data/DATA_DICTIONARY.csv` defines the model
table. The complete pipeline, isolated CSV-only run, data-quality audit, and
artifact hash manifest are generated by `code/pipeline/run_all.sh`.

七份冻结原始文件均通过 SHA-256 校验，并全部在 `data/original_csv/` 中提供 CSV
版本。来源、日期、变量和哈希均为机器可读；处理数据的字段有独立数据字典。
`code/pipeline/run_all.sh` 会执行完整分析、隔离的纯 CSV 复现、数据质量审计和产物哈希。

## Final conclusion / 最终结论

The strongest conclusion is that HEWJ does not deliver a complete one-for-one
daily yen hedge relative to EWJ in either period. The post-period slope is closer
to -1, but evidence that the pandemic break caused or even cleanly marks a slope
change is not robust across the declared influence and date sensitivities. This
is an associational result for one ETF pair, not a causal estimate or trading
recommendation.

最稳健的结论是：相对 EWJ，HEWJ 在疫情前后都没有实现一比一的完整日度日元对冲。
疫情后斜率更接近 -1，但“疫情导致或清晰标记斜率改变”的证据无法通过全部已声明的
影响点与日期敏感性检验。本研究只描述一组 ETF 的条件相关，不是因果估计或交易建议。
