# Config / 分析规则

本目录保存“实验开始前决定的规则”，避免在看到结果后随意更改方案。

```text
config/
├── analysis_protocol.yml   # 主分析、切分、候选模型和敏感性规则
└── README.md
```

`analysis_protocol.yml` 是机器可读的单一规则来源，记录研究问题、主 OLS
模型、Newey-West HAC(5)、严格日期对齐、rolling-origin 折、最终测试边界、
候选模型、函数形式、影响点和断点敏感性。修改它意味着修改研究设计，不能只为
获得更好 p 值或测试成绩而改。
