# Data / 数据

This directory contains data only; no executable analysis code is stored here.

本目录只保存数据、来源和字段说明，不保存分析代码。

| Location | Contents |
|---|---|
| `raw/` | Seven frozen provider snapshots and their SHA-256 checksum file. |
| `original_csv/` | Deterministic CSV versions of every original source. |
| `processed/sta302_daily_analysis.csv` | Final 2,655-row calendar-interval-matched table; intraday clocks are documented separately. |
| `SOURCE_MANIFEST.csv` | Machine-readable provider, URL, retrieval date, variable and hash information. |
| `SOURCE_MANIFEST.md` | Human-readable source and provenance explanation. |
| `DATA_DICTIONARY.csv` | Definition, unit, source and missing-value rule for every processed field. |
| `TIME_ALIGNMENT.csv` | Machine-readable time zone, observation-clock, interval, and handling policy for every series. |
| `TIME_ALIGNMENT.md` | Bilingual explanation of calendar alignment, intraday mismatch, Dimson/weekly checks, and log-return treatment. |
| `DATA_USE.md` | Data ownership, redistribution and private-repository guidance. |

The pipeline never downloads live replacements. Reproduction always starts from
the frozen files under `raw/`.

流水线不会重新下载实时数据，所有复现都从 `raw/` 中的冻结文件开始。
