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

## Main inference / 主要推断

- Pre-period yen slope: -0.85094; HAC(5) test against -1, p = 0.000005.
- Post-period implied slope: -0.91214; HAC(5) test against -1, p = 0.000048.
- Change in slope: -0.06121; classical p = 0.00931, HAC(5) p = 0.10439.
- HAC interaction p-values are 0.10287, 0.10439, and 0.10635 for lags 1, 5, and 10.

因此，疫情后斜率在数值上更接近 -1，但使用适合非 iid 残差的 HAC 推断后，
没有足够证据认定疫情前后斜率发生变化。两个时期的斜率都显著不同于 -1，
所以更稳妥的结论是：两个时期均存在不完全对冲，而不是疫情导致了显著变化。

## Chronological prediction check / 时间顺序预测检验

The fixed split is 1,593 train rows, 531 tuning rows, and 531 untouched test
rows. The macro-control candidate has the lowest tuning RMSE (0.30619), narrowly
ahead of the FX-interaction model (0.30662), and is therefore locked before test
evaluation. After refitting on train+tuning, its test RMSE is 0.31159 and MAE is
0.21781, compared with 0.65316 and 0.46087 for the historical-mean benchmark.
This is a held-out conditional-fit check using same-day observed predictors, not
an ahead-of-time return forecast or trading backtest.

固定时间切分为 1,593 条训练、531 条调优、531 条最终测试。宏观控制模型在
调优集 RMSE 最低，因此在查看测试结果前锁定；其测试 RMSE 为 0.31159、MAE
为 0.21781，明显优于历史均值基准的 0.65316 和 0.46087。
该结果是使用当日已观测预测变量的样本外条件拟合检查，不是提前收益预测或交易回测。

## Diagnostics and limits / 诊断与限制

The residuals remain heteroskedastic, serially dependent, heavy-tailed, and show
functional-form evidence. Newey-West addresses covariance-based inference but
does not repair misspecification or establish causality. The pandemic indicator
is a descriptive break, and the results concern one ETF pair.

残差仍存在异方差、序列相关、厚尾和函数形式问题。Newey-West 只修正推断所用
协方差矩阵，并不自动修复模型设定，也不能建立因果关系。疫情变量只是描述性
断点，结论也仅针对这一组 ETF。
