# Time alignment / 时间对齐说明

相同日期不代表相同盘中时刻。本项目先在每条序列自己的交易日历内计算收益，
再要求主要价格序列的收益起止日期一致；这能解决节假日和跨多日收益混合问题，
但不能把纽约中午汇率变成纽约收盘汇率。

## Source clocks / 数据时钟

- HEWJ/EWJ 使用美国交易日调整后收盘价。Yahoo JSON 时间戳只用作交易日标签，
  不被解释为调整后收盘价的实际采样时刻。
- DEXJPUS 是纽约中午买入汇率，因此其日收益是 noon-to-noon。
- Nikkei 225 是东京市场 close-to-close；VIX 是美国市场 close-to-close。
- 日本 FF5 和 MOM 是日本交易日因子收益。代码推断每行的前一因子交易日并审计，
  但数据没有提供盘中换算时刻。
- 月度美日利差滞后一个月后才进入日度表。

机器可读版本见 `TIME_ALIGNMENT.csv`。

## Three-layer treatment / 三层处理

1. **Calendar interval:** 各序列先独立计算收益，只保留结束日和起始日一致的主要
   价格收益；因子的推断起始日另外报告严格敏感性样本。
2. **Intraday clock:** 日度稳健性模型加入相邻一期、当期和相邻下一期日元收益，
   按 Dimson 非同步交易方法报告三个系数之和。lead 只用于解释性时钟校正，绝不
   进入预测模型。
3. **Lower-frequency check:** 每个周五标签周选择 HEWJ、EWJ 和 DEXJPUS 最后一个
   共同观测日，计算共同端点周收益，降低几小时时点差异相对于整周窗口的影响。

日度模型同时报告 HAC(5) 和覆盖约一个交易月的 HAC(22)；周度模型使用 HAC(4)。
这些分析不会声称从日频数据恢复了不存在的盘中价格。

## Return definition / 收益定义

主分析的 log return 是精确的连续复利价格比变化，不是近似计算。近似只发生在把
log 百分比直接口头解释为普通百分比时。项目使用完全相同的样本、模型候选、
rolling-origin 折和最终时期，再以 arithmetic return 重跑一次，用实际结果衡量
log 对尾部波动和测试 RMSE 的影响。

## References / 方法依据

- Federal Reserve DEXJPUS notes: https://fred.stlouisfed.org/series/DEXJPUS
- Scholes, M., & Williams, J. (1977). *Estimating betas from nonsynchronous data*.
  https://doi.org/10.1016/0304-405X(77)90041-1
- Dimson, E. (1979). *Risk measurement when shares are subject to infrequent trading*.
  https://doi.org/10.1016/0304-405X(79)90013-8
