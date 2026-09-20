# Results and conclusions / 结果与结论

## Method / 方法

All price returns are computed inside their original series before merging. The
primary sample then requires HEWJ/EWJ, USD/JPY, Nikkei 225, and VIX returns to
share the same calendar interval start and end dates. This produces 2,655 observations.
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

## Time-zone and market-clock design / 时区与市场时钟设计

Calendar alignment is not claimed to be intraday synchronization. HEWJ/EWJ and
VIX are U.S.-close observations; DEXJPUS is measured at New York noon; Nikkei is
a Tokyo-close series; the Japanese factors describe their local trading session.
The repository records these clocks and time zones in `data/TIME_ALIGNMENT.csv`.
No automatic reassignment to another calendar day is performed, because that
would falsely imply one common observation time.

The clock issue is handled in three layers. First, the primary same-calendar-
interval model is retained as the transparent course model. Second, a Dimson
specification includes lagged, current, and leading yen returns and reports their
cumulative exposure; the lead is diagnostic only and is never used in prediction.
Third, a weekly model uses the last date on which HEWJ, EWJ, and DEXJPUS are all
observed within each Friday-labelled week. HAC(5) and HAC(22) are both reported.

日期对齐不等于日内同步。本研究不会把所有序列自动归到某个统一“交易日”，也不会
仅把日期机械转换为 UTC，因为这会虚构一个并不存在的共同观测时点。具体来源时钟与
时区记录在 `data/TIME_ALIGNMENT.csv`。处理分三层：保留透明的同日历区间主模型；
用前一期、当期、后一期日元收益的 Dimson 累计暴露吸收非同步交易；再用每周最后共同
观测日重估。lead 只作诊断，绝不进入预测；同时报告 HAC(5) 与 HAC(22)。

Current-date post-period exposure is -0.91214. Dimson cumulative exposure is
-0.99410 (HAC(22) 95% CI [-1.03465, -0.95356]), and the weekly common-date
estimate is -0.98633 ([-1.01568, -0.95697]). Both are statistically compatible
with -1. Thus the daily current-date model understates full cumulative yen
exposure; an unqualified “incomplete hedge” claim does not survive the clock
correction.

同日模型疫情后斜率为 -0.91214；Dimson 累计暴露为 -0.99410（HAC(22) 95% CI
[-1.03465, -0.95356]），周度共同日期估计为 -0.98633（[-1.01568, -0.95697]），
两者都不能拒绝 -1。因此日度同日模型低估了完整累计日元暴露；“稳定存在不完全对冲”
不能脱离非同步时钟限定来表述。

## Log versus arithmetic returns / 对数与普通收益

Log returns are computed exactly as `100 * log(P_t/P_{t-1})`; they are not a
numerical approximation. The entire selection, held-out evaluation, and
full-model inference workflow is also rerun with exact arithmetic returns.
Test response SD is 0.65378 for log returns and 0.65316 for arithmetic returns;
the 95th-percentile absolute moves are 1.34703 and 1.34734, and maxima are
2.78024 and 2.81234. Selected-model RMSE is 0.31589 versus 0.31673. Therefore
log returns do not materially suppress overall test volatility here; they only
compress the largest extreme very slightly.

log 收益按精确公式计算，另用普通收益完整重跑。测试响应标准差分别为 0.65378 与
0.65316，绝对波动 95% 分位分别为 1.34703 与 1.34734，最大值为 2.78024 与
2.81234，所选模型 RMSE 为 0.31589 与 0.31673。因此 log 没有实质压低整体测试波动，
只对最大极端值产生很小的非线性压缩。

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
through 2024-01-23 before evaluation on data held out from fitting and selection. Reduction was selected
by time-respecting out-of-sample RMSE, not by deleting insignificant coefficients.

本研究刻意区分解释性推断和预测。初始完整模型为
`Y ~ JPY_app * Post + Nikkei_ret + SMB + HML + RMW + CMA + MOM + dlog_VIX + rate_diff`，
包含 proposal 要求的全部十个预测变量，并继续承担日元斜率和时期交互项的预设推断。
次要预测环节采用扩展窗口 rolling-origin：分别用截至 2020、2021、2022 年的数据
训练，并在 2021、2022、2023 年验证。汇率交互、宏观控制和完整因子模型的三折平均
RMSE 分别为 0.26665、0.27417 和 0.27637，因此锁定汇率交互模型
`Y ~ JPY_app * Post`。该模型用截至 2024-01-23 的 2,124 条开发样本重新拟合后，
在未参与拟合或选模的测试集上评估。精简依据是遵守时间顺序的样本外 RMSE，而不是 p 值。

## Main inference / 主要推断

- Pre-period yen slope: -0.85094; HAC(5) test against -1, p = 0.000005.
- Post-period implied slope: -0.91214; HAC(5) test against -1, p = 0.000048.
- Change in slope: -0.06121; classical p = 0.00931, HAC(5) p = 0.10439.
- HAC interaction p-values are 0.10287, 0.10439, and 0.10635 for lags 1, 5, and 10.

因此，疫情后同日斜率在数值上更接近 -1，但使用适合非 iid 残差的 HAC 推断后，
没有足够证据认定疫情前后斜率发生变化。两个时期的同日斜率都显著不同于 -1；
但如上所述，时钟修正后的累计暴露与 -1 相容，不能把同日结论直接推广到完整暴露。

## Rolling-origin prediction check / 滚动起点预测检验

The three validation windows contain 211, 211, and 217 observations. The
FX-interaction candidate has the lowest mean validation RMSE (0.26665) and is
locked before test evaluation. After refitting on all development data, its
test RMSE is 0.31589 and MAE is 0.21576. It is only marginally better than the
static-FX benchmark (RMSE 0.31624, MAE 0.21604) and theoretical -1 spot
benchmark (0.32104, 0.21918), while strongly beating the historical mean.
This is a held-out conditional-fit check using same-day observed predictors, not
an ahead-of-time return forecast or trading backtest.

三个验证窗分别有 211、211、217 条观测。汇率交互模型的三折平均 RMSE 最低
（0.26665），因此在查看测试结果前锁定；用全部开发数据重拟合后，其测试 RMSE
为 0.31589、MAE 为 0.21576，仅略优于静态汇率基准（0.31624、0.21604）和理论
-1 即期暴露基准（0.32104、0.21918），但明显优于历史均值基准。
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

The current-date model shows slopes short of -1, but the Dimson and weekly clock
corrections recover cumulative post-period exposures statistically compatible
with -1. The defensible conclusion is narrower: same-date daily exposure appears
incomplete, while cumulative exposure is close to complete once nonsynchronous
clocks are allowed. Evidence of a discrete pandemic change is not robust. This
is associational evidence for one ETF pair, not a causal estimate or trading recommendation.

同日模型斜率绝对值小于 1，但 Dimson 与周度时钟修正后的疫情后累计暴露与 -1 相容。
因此最终结论必须收窄为：同日暴露看似不完整，但允许非同步观测后，累计暴露接近完整；
疫情离散变化并不稳健。本研究只描述一组 ETF 的条件相关，不是因果估计或交易建议。
