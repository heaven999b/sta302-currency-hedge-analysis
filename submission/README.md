# Submission package / 提交包

这是由 `code/pipeline/prepare_submission_package.py` 生成的 Quercus/OneDrive
暂存包，不是代码开发区。需要更新时应重跑流水线，不要只改这里的副本。

```text
submission/
├── code/                   # 可独立运行的完整 Rmd
├── data/
│   ├── original/           # 七份原始来源的 CSV 版本
│   └── cleaned/            # 最终建模 CSV
├── proposal/               # 正式英文 proposal PDF
├── QUERCUS_SUBMISSION_CHECKLIST.md
├── SHA256SUMS.csv          # 提交包完整性哈希
└── README.md
```

- `code/`：交给助教检查数据处理、建模、绘图和诊断的完整代码。
- `data/original/`：可上传到 UofT OneDrive 的原始 CSV。
- `data/cleaned/`：可直接重跑分析的清洗后数据。
- `proposal/`：Part 1 正式英文 PDF。
- `QUERCUS_SUBMISSION_CHECKLIST.md`：提交前仍需人工确认的成员、协议和链接。
- `SHA256SUMS.csv`：证明提交包中的文件与生成时一致。
