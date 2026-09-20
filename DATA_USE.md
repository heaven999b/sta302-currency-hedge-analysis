# Data use and redistribution notes / 数据使用与再分发说明

This private educational repository contains frozen snapshots from third-party providers so the submitted analysis can be reproduced exactly. The repository does not claim ownership of those files.

本私有教学仓库保存第三方数据快照，以便精确复现课程分析；仓库不主张拥有这些数据。

Sources:

- Yahoo Finance: HEWJ and EWJ adjusted-price histories.
- Federal Reserve Bank of St. Louis FRED: DEXJPUS, NIKKEI225, VIXCLS, IRSTCI01USM156N, and IRSTCI01JPM156N.
- Kenneth French Data Library: Japan 5 Factors Daily and Japan Momentum Daily.
- iShares: product descriptions used to interpret HEWJ and EWJ.

The provider pages and frozen-file checksums are listed in `SOURCE_MANIFEST.md` and `data/raw/SHA256SUMS.txt`. Keep the repository private unless each provider's redistribution terms have been reviewed. If the repository is later made public, consider replacing raw third-party files with a documented download script when required by provider terms.

各数据入口和冻结文件校验值记录在 `SOURCE_MANIFEST.md` 与 `data/raw/SHA256SUMS.txt` 中。在逐一确认提供方的再分发条款前，请保持仓库为 private。若未来需要公开，可根据条款把原始文件替换为可复现下载脚本。
