# STA302 Currency-Hedge Effectiveness / STA302 货币对冲有效性研究

Private, reproducible course project studying whether the daily return spread between HEWJ and EWJ behaves like a yen hedge, and whether that relationship changed after the COVID-19 break.

本仓库是一个私有、可复现的 STA302 课程项目，用于研究 HEWJ 与 EWJ 的日度收益差是否体现日元对冲效果，以及这种关系在 COVID-19 断点后是否发生变化。

## Headline results / 核心结果

| Item / 指标 | Result / 结果 |
|---|---:|
| Complete daily observations / 完整日度观测 | 2,753 |
| Sample / 样本区间 | 2014-02-06 to 2026-07-31 |
| Full-model R² / 完整模型 R² | 0.712120 |
| Pre-period yen slope / 疫情前日元斜率 | -0.851969 |
| Yen x Post / 日元 x 疫情后交互项 | -0.064809 |
| Interaction p, classical / 经典 p 值 | 0.00429 |
| Interaction p, HAC(5) / HAC(5) p 值 | 0.06835 |
| Implied post-period slope / 疫情后隐含斜率 | -0.916777 |
| Chronological test RMSE / 时间顺序测试 RMSE | 0.3132 vs 0.6543 benchmark |

The pandemic interaction is significant with conventional OLS standard errors but only marginal with Newey-West HAC(5). The repository preserves both results and does not present the break as causal.

疫情交互项在经典 OLS 标准误下显著，但使用 Newey-West HAC(5) 后仅为边际显著。仓库完整保留两种推断，并且不把该断点解释为因果效应。

## Repository architecture / 仓库架构

```text
.
├── analysis/
│   ├── run_analysis.R                  # complete deterministic R pipeline
│   └── STA302_Project_Analysis.Rmd     # course-facing reproducibility entry
├── data/
│   ├── raw/                            # frozen source snapshots + SHA-256
│   └── processed/                      # cleaned modeling table
├── docs/proposal/
│   ├── STA302_Research_Proposal_EN.md  # official English proposal
│   └── STA302_Research_Proposal_ZH.md  # aligned Chinese translation
├── figures/                            # generated figures
├── results/                            # coefficients, diagnostics, validation, RDS
├── scripts/
│   ├── build_bilingual_proposal_pdf.py
│   ├── prepare_submission_package.py
│   ├── run_all.sh
│   └── validate_outputs.py
├── output/
│   ├── STA302_Project_Analysis.html
│   └── pdf/
│       ├── STA302_Research_Proposal_Official_EN.pdf
│       └── STA302_Bilingual_Research_Proposal.pdf
├── submission/                         # Quercus-ready staging package
│   ├── code/                           # standalone Rmd
│   ├── data/original/                  # all source data as CSV
│   ├── data/cleaned/                   # cleaned modeling CSV
│   └── proposal/                       # official English PDF
├── SOURCE_MANIFEST.md
├── DATA_USE.md
└── environment.yml
```

## Reproduce everything / 完整复现

Create the environment in a path without spaces:

```bash
conda env create -p /private/tmp/sta302_r_env -f environment.yml
conda activate /private/tmp/sta302_r_env
```

Run the complete pipeline from the repository root:

```bash
bash scripts/run_all.sh
```

This command:

1. verifies all seven frozen raw-file SHA-256 hashes;
2. reruns cleaning, OLS, HAC(5), diagnostics, figures, and chronological validation in R;
3. knits the Rmd to a self-contained HTML file;
4. rebuilds the official English and bilingual proposal PDFs;
5. prepares an all-CSV Quercus staging package; and
6. checks the expected rows, dates, coefficients, outputs, Rmd completeness, and PDF text.

该命令会验证七份原始文件、重新运行完整 R 分析、渲染 Rmd、重建中英双语 PDF，并检查关键数值和输出是否一致。

## Primary deliverables / 主要交付物

- `output/pdf/STA302_Research_Proposal_Official_EN.pdf` - formal English-only course submission.
- `output/pdf/STA302_Bilingual_Research_Proposal.pdf` - English proposal followed by a faithful Chinese study copy.
- `analysis/STA302_Project_Analysis.Rmd` - self-contained course submission containing the full cleaning, modeling, table, and diagnostic code.
- `output/STA302_Project_Analysis.html` - verified knitted analysis.
- `data/processed/sta302_daily_analysis.csv` - final complete-case modeling table.
- `submission/` - staged PDF, standalone Rmd, original CSV exports/copies, cleaned CSV, checklist, and hashes.
- `results/R_run_log.txt` - R version, package versions, sample and results.

## Data and integrity / 数据与诚信

The repository contains frozen third-party data snapshots for private educational reproducibility. Ownership and usage terms remain with Yahoo Finance, FRED, iShares, and the Kenneth French Data Library. Do not make this repository public until the data-provider terms have been reviewed. See `DATA_USE.md` and `SOURCE_MANIFEST.md`.

本仓库为了私有教学复现而保存第三方数据快照。数据所有权和使用条款仍属于 Yahoo Finance、FRED、iShares 与 Kenneth French Data Library。在审查各数据源条款前，请勿把仓库改为公开。

## Manual items before course submission / 课程提交前必须人工补充

1. Replace bracketed group-member names and contribution descriptions.
2. Complete and sign the course-provided Group Teamwork Agreement PDF using the same roster and roles.
3. Upload `submission/data/original/` and `submission/data/cleaned/` to UofT OneDrive, verify the required access setting, and paste the link into the Quercus submission comment.

1. 替换所有带方括号的小组成员姓名和贡献说明。
2. 使用相同名单与职责完成并签署课程提供的 Group Teamwork Agreement PDF。
3. 把 `submission/data/original/` 和 `submission/data/cleaned/` 上传至 UofT OneDrive，核验权限后把链接粘贴到 Quercus 提交评论。
