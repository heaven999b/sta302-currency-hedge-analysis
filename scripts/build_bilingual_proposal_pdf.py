from __future__ import annotations

import csv
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
EN_SOURCE = ROOT / "docs" / "proposal" / "STA302_Research_Proposal_EN.md"
ZH_SOURCE = ROOT / "docs" / "proposal" / "STA302_Research_Proposal_ZH.md"
OUTPUT_EN = ROOT / "output" / "pdf" / "STA302_Research_Proposal_Official_EN.pdf"
OUTPUT_BILINGUAL = ROOT / "output" / "pdf" / "STA302_Bilingual_Research_Proposal.pdf"
OUTPUT_ZH = ROOT / "output" / "pdf" / "STA302_Research_Proposal_Official_ZH.pdf"
SCATTER = ROOT / "figures" / "fx_slope_by_period.png"
DIAGNOSTICS = ROOT / "figures" / "residual_diagnostics.png"

NAVY = colors.HexColor("#15324B")
BLUE = colors.HexColor("#1F6AA5")
LIGHT = colors.HexColor("#EAF1F7")
PALE = colors.HexColor("#F5F7F9")
MID = colors.HexColor("#5D6B78")


def register_fonts() -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def clean_inline(text: str) -> str:
    text = text.strip().removeprefix("> ")
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("—", "-").replace("–", "-").replace("‑", "-")
    replacements = {
        "\\Delta": "Delta ",
        "\\beta": "beta ",
        "\\gamma": "gamma ",
        "\\times": " x ",
        "\\varepsilon": "epsilon ",
        "\\log": "log",
        "\\%": "%",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return html.escape(text)


def parse_sections(markdown: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"front": []}
    current = "front"
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif not line.startswith("# "):
            sections[current].append(line)
    return sections


def paragraph_blocks(lines: list[str], body_style, bullet_style, equation_style, paragraph_space=6):
    blocks = []
    buffer: list[str] = []
    equation: list[str] = []
    in_equation = False

    def flush() -> None:
        if buffer:
            blocks.extend([Paragraph(clean_inline(" ".join(buffer)), body_style), Spacer(1, paragraph_space)])
            buffer.clear()

    for raw in lines:
        line = raw.strip()
        if line == "\\[":
            flush()
            equation = []
            in_equation = True
        elif line == "\\]":
            blocks.extend([Paragraph(clean_inline(" ".join(equation)), equation_style), Spacer(1, 5)])
            in_equation = False
        elif in_equation:
            equation.append(line)
        elif not line:
            flush()
        elif re.match(r"^\d+\. ", line):
            flush()
            number, value = line.split(". ", 1)
            blocks.extend([Paragraph(clean_inline(value), bullet_style, bulletText=f"{number}."), Spacer(1, 3)])
        elif line.startswith("|"):
            flush()
        else:
            buffer.append(line)
    flush()
    return blocks


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class ProposalDoc(BaseDocTemplate):
    def __init__(self, filename: str, title: str):
        super().__init__(
            filename,
            pagesize=letter,
            rightMargin=.66 * inch,
            leftMargin=.66 * inch,
            topMargin=.70 * inch,
            bottomMargin=.82 * inch,
            title=title,
            author="Haiwen Yi and group members",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=self.draw_page))

    def draw_page(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor("#D9E0E6"))
            canvas.line(doc.leftMargin, letter[1] - .45 * inch,
                        letter[0] - doc.rightMargin, letter[1] - .45 * inch)
            canvas.setFillColor(MID)
            canvas.setFont("STSong-Light", 7.6)
            canvas.drawString(doc.leftMargin, letter[1] - .34 * inch,
                              "STA302 | Currency-Hedged Japan ETF Study | 日元对冲研究")
        canvas.setFillColor(MID)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(letter[0] - doc.rightMargin, .36 * inch, f"Page {doc.page}")
        canvas.restoreState()


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=23, leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8),
        "title_zh": ParagraphStyle("TitleZH", parent=base["Title"], fontName="STSong-Light",
                                   fontSize=19, leading=25, textColor=BLUE, alignment=TA_LEFT, spaceAfter=12),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Heading2"], fontName="Helvetica",
                                   fontSize=13, leading=18, textColor=BLUE, alignment=TA_LEFT, spaceAfter=16),
        "subtitle_zh": ParagraphStyle("SubtitleZH", parent=base["Heading2"], fontName="STSong-Light",
                                      fontSize=12, leading=17, textColor=BLUE, alignment=TA_LEFT, spaceAfter=14),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14,
                             leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=7, keepWithNext=True),
        "h1_zh": ParagraphStyle("H1ZH", parent=base["Heading1"], fontName="STSong-Light", fontSize=13.2,
                                leading=17, textColor=NAVY, spaceBefore=8, spaceAfter=5, keepWithNext=True),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11,
                             leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=6, keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75,
                               leading=12.0, textColor=colors.HexColor("#1D252C"), alignment=TA_LEFT),
        "body_zh": ParagraphStyle("BodyZH", parent=base["BodyText"], fontName="STSong-Light", fontSize=8.5,
                                  leading=12.4, textColor=colors.HexColor("#1D252C"), alignment=TA_LEFT),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75,
                                 leading=12.0, leftIndent=16, firstLineIndent=-12, bulletIndent=0),
        "bullet_zh": ParagraphStyle("BulletZH", parent=base["BodyText"], fontName="STSong-Light", fontSize=8.5,
                                    leading=12.4, leftIndent=18, firstLineIndent=-14, bulletIndent=0),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica-Oblique",
                                  fontSize=7.6, leading=9.4, textColor=MID, spaceBefore=3, spaceAfter=8),
        "caption_zh": ParagraphStyle("CaptionZH", parent=base["BodyText"], fontName="STSong-Light",
                                     fontSize=7.7, leading=10.2, textColor=MID, spaceBefore=3, spaceAfter=8),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.6,
                                leading=9.5, textColor=MID),
        "small_zh": ParagraphStyle("SmallZH", parent=base["BodyText"], fontName="STSong-Light", fontSize=7.7,
                                   leading=10.5, textColor=MID),
        "equation": ParagraphStyle("Equation", parent=base["BodyText"], fontName="Helvetica-Oblique",
                                   fontSize=9.0, leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4),
        "equation_zh": ParagraphStyle("EquationZH", parent=base["BodyText"], fontName="STSong-Light",
                                      fontSize=9.0, leading=13, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4),
    }


def wrap_table(data, widths, styles, font_size=7.1, repeat_rows=1, chinese=False):
    cell_style = ParagraphStyle(
        "CellZH" if chinese else "Cell",
        parent=styles["small_zh" if chinese else "small"],
        fontName="STSong-Light" if chinese else "Helvetica",
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.HexColor("#1D252C"),
    )
    header_style = ParagraphStyle(
        "CellHeaderZH" if chinese else "CellHeader",
        parent=cell_style,
        fontName="STSong-Light" if chinese else "Helvetica-Bold",
        textColor=colors.white,
    )
    wrapped = []
    for row_index, row in enumerate(data):
        style = header_style if row_index == 0 else cell_style
        wrapped.append([Paragraph(clean_inline(str(value)), style) for value in row])
    table = Table(wrapped, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#C7D1DA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def contribution_table(styles, chinese=False):
    if chinese:
        data = [
            ["成员", "计划贡献"],
            ["Haiwen Yi", "研究设计、数据构建、R 分析、诊断检验和初稿"],
            ["[成员 2]", "文献核验、结果解释和文字修订"],
            ["[成员 3]", "可复现性检查、海报制作和演示录制"],
            ["[成员 4，如适用]", "最终模型敏感性分析与演示审核"],
        ]
    else:
        data = [
            ["Member", "Proposed contribution"],
            ["Haiwen Yi", "Research design, data construction, R analysis, diagnostics, and first draft"],
            ["[Member 2]", "Literature verification, interpretation, and written revision"],
            ["[Member 3]", "Reproducibility check, poster development, and presentation recording"],
            ["[Member 4, if applicable]", "Final-model sensitivity analysis and presentation review"],
        ]
    return wrap_table(data, [1.48 * inch, 4.92 * inch], styles, font_size=7.6, chinese=chinese)


def variable_summary_table(styles, chinese=False):
    summary = {row["variable"]: row for row in read_csv(ROOT / "results" / "predictor_summary.csv")}
    diagnostics = {row["metric"]: row["value"] for row in read_csv(ROOT / "results" / "diagnostics.csv")}
    labels = {
        "Y": ("Response spread", "Extreme days; heavy tails"),
        "JPY_app": ("Yen appreciation", "Wide daily extremes"),
        "Nikkei_ret": ("Nikkei return", "Large crash/rebound days"),
        "SMB": ("Japan SMB", "Moderate spread"),
        "HML": ("Japan HML", "Relatively wide factor range"),
        "RMW": ("Japan RMW", "Moderate spread"),
        "CMA": ("Japan CMA", "Moderate spread"),
        "MOM": ("Japan MOM", "Wide factor extremes"),
        "dlog_VIX": ("VIX log change", "Largest dispersion and right extreme"),
        "rate_diff": ("Lagged rate difference", "Slow-moving monthly series"),
    }
    if chinese:
        labels = {
            "Y": ("响应变量收益差", "存在极端日与厚尾"),
            "JPY_app": ("日元升值", "日度极端值较宽"),
            "Nikkei_ret": ("日经收益", "存在大跌与反弹日"),
            "SMB": ("日本 SMB", "离散程度中等"),
            "HML": ("日本 HML", "因子范围较宽"),
            "RMW": ("日本 RMW", "离散程度中等"),
            "CMA": ("日本 CMA", "离散程度中等"),
            "MOM": ("日本 MOM", "存在较宽极端值"),
            "dlog_VIX": ("VIX 对数变化", "离散最大且右侧极端"),
            "rate_diff": ("滞后利差", "按月更新、变化缓慢"),
        }
    header = ["Variable", "Type", "Mean", "SD", "Range", "Important feature"]
    if chinese:
        header = ["变量", "类型", "均值", "标准差", "范围", "主要特征"]
    rows = [header]
    for name in ["Y", "JPY_app", "Nikkei_ret", "SMB", "HML", "RMW", "CMA", "MOM", "dlog_VIX", "rate_diff"]:
        row = summary[name]
        label, feature = labels[name]
        rows.append([
            label,
            "Numerical" if not chinese else "数值",
            f"{float(row['mean']):.3f}",
            f"{float(row['sd']):.3f}",
            f"{float(row['min']):.3f} to {float(row['max']):.3f}",
            feature,
        ])
    rows.append([
        "Post period" if not chinese else "疫情后时期",
        "Categorical" if not chinese else "分类",
        f"Pre: {int(diagnostics['pre_observations']):,}" if not chinese else f"疫情前：{int(diagnostics['pre_observations']):,}",
        f"Post: {int(diagnostics['post_observations']):,}" if not chinese else f"疫情后：{int(diagnostics['post_observations']):,}",
        "2 levels" if not chinese else "2 个水平",
        "WHO-defined break" if not chinese else "WHO 事件定义断点",
    ])
    return wrap_table(rows, [.92 * inch, .62 * inch, .68 * inch, .64 * inch, 1.05 * inch, 2.49 * inch],
                      styles, font_size=6.45, chinese=chinese)


def coefficient_table(styles, chinese=False):
    rows = read_csv(ROOT / "results" / "coefficients_classical.csv")
    term_labels = {
        "(Intercept)": "Intercept", "JPY_app": "Yen appreciation", "PostPost": "Post indicator",
        "Nikkei_ret": "Nikkei return", "SMB": "SMB", "HML": "HML", "RMW": "RMW", "CMA": "CMA",
        "MOM": "MOM", "dlog_VIX": "VIX log change", "rate_diff": "Lagged rate difference",
        "JPY_app:PostPost": "Yen x Post",
    }
    if chinese:
        term_labels.update({
            "(Intercept)": "截距", "JPY_app": "日元升值", "PostPost": "疫情后指标",
            "Nikkei_ret": "日经收益", "dlog_VIX": "VIX 对数变化",
            "rate_diff": "滞后利差", "JPY_app:PostPost": "日元 x 疫情后",
        })
    table_rows = [["Term", "Estimate", "Classical SE", "95% CI", "p"]]
    if chinese:
        table_rows = [["变量", "估计值", "经典标准误", "95% 区间", "p"]]
    for row in rows:
        p = float(row["p_value"])
        p_text = "<0.001" if p < .001 else f"{p:.3f}"
        table_rows.append([
            term_labels[row["term"]],
            f"{float(row['estimate']):.4f}",
            f"{float(row['std_error']):.4f}",
            f"[{float(row['conf_low']):.4f}, {float(row['conf_high']):.4f}]",
            p_text,
        ])
    return wrap_table(table_rows, [1.55 * inch, .88 * inch, .92 * inch, 1.55 * inch, .70 * inch],
                      styles, font_size=6.65, chinese=chinese)


def schedule_table(styles, chinese=False):
    if chinese:
        rows = [
            ["日期", "里程碑", "负责人", "可检查输出"],
            ["11 月 9-15 日", "复核清理数据与诊断", "Haiwen + 成员 3", "冻结数据、问题日志"],
            ["11 月 16-22 日", "模型修订与敏感性分析", "Haiwen + 成员 2", "最终模型表与图"],
            ["11 月 23-27 日", "制作并审核海报", "成员 2 + 成员 3", "完整海报草稿"],
            ["11 月 28-30 日", "录制、字幕与复核", "全组", "最终视频"],
            ["12 月 1-2 日", "文件与链接最终检查", "Haiwen + 全组", "可提交包"],
        ]
    else:
        rows = [
            ["Dates", "Milestone", "Owner(s)", "Checkable output"],
            ["Nov 9-15", "Audit cleaned data and diagnostics", "Haiwen + Member 3", "Frozen data; issue log"],
            ["Nov 16-22", "Revise model and run sensitivities", "Haiwen + Member 2", "Final model tables/figures"],
            ["Nov 23-27", "Create and review poster", "Member 2 + Member 3", "Complete poster draft"],
            ["Nov 28-30", "Record, caption, and review", "All members", "Final recording"],
            ["Dec 1-2", "Final file and link audit", "Haiwen + all members", "Submission-ready package"],
        ]
    return wrap_table(rows, [1.0 * inch, 2.15 * inch, 1.45 * inch, 1.8 * inch], styles, font_size=6.8, chinese=chinese)


def cover(styles, bilingual=False, chinese_only=False):
    diagnostics = {row["metric"]: row["value"] for row in read_csv(ROOT / "results" / "diagnostics.csv")}
    data_line = (f"{int(diagnostics['observations']):,} daily observations | "
                 f"{diagnostics['start_date']} to {diagnostics['end_date']}")
    if chinese_only:
        story = [Spacer(1, .18 * inch), Paragraph("货币对冲能否抵消日元的日度风险敞口？", styles["title_zh"])]
    else:
        story = [Spacer(1, .18 * inch), Paragraph("Does a Currency Hedge Neutralize Daily Yen Exposure?", styles["title"])]
    if bilingual:
        story.append(Paragraph("货币对冲能否抵消日元的日度风险敞口？", styles["title_zh"]))
    if chinese_only:
        story.append(Paragraph("疫情前后 HEWJ 与 EWJ 的多因子比较研究", styles["subtitle_zh"]))
    else:
        story.append(Paragraph("A Multi-Factor Study of HEWJ versus EWJ Before and After the COVID-19 Break", styles["subtitle"]))
    if bilingual:
        story.append(Paragraph("疫情前后 HEWJ 与 EWJ 的多因子比较研究", styles["subtitle_zh"]))
    story.extend([HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=18)])
    meta = [
        ["Course", "STA302 Final Project - Part 1"],
        ["Prepared", "September 21, 2026"],
        ["Group", "Haiwen Yi; [add all other members before submission]"],
        ["Data", data_line],
    ]
    if bilingual:
        meta = [
            ["Course / 课程", "STA302 Final Project - Part 1 / STA302 期末项目第一部分"],
            ["Prepared / 日期", "September 21, 2026 / 2026 年 9 月 21 日"],
            ["Group / 小组", "Haiwen Yi; [add all other members / 补充其他成员]"],
            ["Data / 数据", data_line],
        ]
    elif chinese_only:
        meta = [
            ["课程", "STA302 期末项目第一部分"],
            ["日期", "2026 年 9 月 21 日"],
            ["小组", "Haiwen Yi；[提交前补充所有其他成员]"],
            ["数据", data_line.replace("daily observations", "个日度观测").replace(" to ", " 至 ")],
        ]
    story.extend([
        wrap_table(meta, [1.25 * inch, 5.15 * inch], styles, font_size=8.2, repeat_rows=0, chinese=bilingual),
        Spacer(1, 24),
        Paragraph(
            "完整中文版" if chinese_only else
            ("English proposal followed by a Chinese study copy / 英文正式提案及中文组内版本" if bilingual else "Official English course version"),
            styles["subtitle_zh" if (bilingual or chinese_only) else "subtitle"]
        ),
        PageBreak(),
    ])
    return story


def english_content(sections, styles, official_heading=True):
    story = []
    if official_heading:
        story.append(Paragraph("Official English proposal", styles["h1"]))
    story.extend([
        Paragraph("Contribution statement", styles["h1"]),
        contribution_table(styles),
        Spacer(1, 4),
        Paragraph("Names and responsibilities must match the separately submitted Group Teamwork Agreement.", styles["small"]),
    ])
    order = [
        "Introduction (388 words)",
        "Data description (276 words)",
        "Ethics discussion (189 words)",
        "Preliminary results (351 words)",
        "Plan for the remaining analysis (275 words)",
        "References",
        "Data and product documentation",
        "Submission items requiring group confirmation",
    ]
    for section in order:
        story.append(Paragraph(section, styles["h1"]))
        if section.startswith("Data description"):
            story.extend([
                variable_summary_table(styles),
                Paragraph("Table 1. Numerical summary of the response and every model predictor. Units are percentage points except the categorical period indicator.", styles["caption"]),
            ])
        if section.startswith("Preliminary results"):
            story.extend([
                Image(str(SCATTER), width=6.38 * inch, height=4.25 * inch),
                Paragraph("Figure 1. Daily HEWJ-minus-EWJ return spread versus yen appreciation, with controlled period-specific OLS slopes.", styles["caption"]),
                coefficient_table(styles),
                Paragraph("Table 2. Complete preliminary OLS coefficient table with classical standard errors and 95% confidence intervals.", styles["caption"]),
            ])
        story.extend(paragraph_blocks(sections[section], styles["body"], styles["bullet"], styles["equation"]))
        if section.startswith("Plan for"):
            story.extend([
                schedule_table(styles),
                Paragraph("Table 3. Proposed team schedule. Member placeholders must be replaced with the signed roster.", styles["caption"]),
            ])
    story.extend([
        PageBreak(),
        Paragraph("Residual diagnostics", styles["h2"]),
        Image(str(DIAGNOSTICS), width=6.38 * inch, height=5.67 * inch),
        Paragraph("Figure 2. Residual-versus-fitted, Q-Q, time-order, and autocorrelation plots for the uncorrected preliminary OLS model.", styles["caption"]),
    ])
    return story


def chinese_content(sections, styles, start_new_page=True, standalone=False, include_figures=False):
    story = []
    if start_new_page:
        story.append(PageBreak())
    story.extend([
        Paragraph("完整中文提案" if standalone else "第二部分 - 中文提案（组内讨论与理解版本）", styles["h1_zh"]),
        Paragraph("本版本完整保留研究设计、数据、数值结果、诊断、限制与参考文献。" if standalone else
                  "正式课程提交请使用独立英文 PDF；本部分与英文版采用相同研究设计、数值与限制。", styles["body_zh"]),
        Paragraph("成员贡献说明", styles["h1_zh"]),
        contribution_table(styles, chinese=True),
        Spacer(1, 4),
        Paragraph("姓名与职责必须和单独提交的小组协议一致。", styles["small_zh"]),
    ])
    order = ["研究背景与问题", "数据说明", "伦理声明", "初步结果", "后续分析计划", "参考文献", "提交前仍需确认"]
    for section in order:
        story.append(Paragraph(section, styles["h1_zh"]))
        if section == "数据说明":
            story.extend([
                variable_summary_table(styles, chinese=True),
                Paragraph("表 1：响应变量及全部入模预测变量的数值汇总。", styles["caption_zh"]),
            ])
        if section == "初步结果":
            if include_figures:
                story.extend([
                    Image(str(SCATTER), width=6.25 * inch, height=4.16 * inch),
                    Paragraph("图 1：日元升值与 HEWJ-EWJ 日度收益差，以及分时期 OLS 斜率。", styles["caption_zh"]),
                ])
            story.extend([
                coefficient_table(styles, chinese=True),
                Paragraph("表 2：完整初步 OLS 系数、经典标准误与 95% 置信区间。", styles["caption_zh"]),
            ])
        story.extend(paragraph_blocks(sections[section], styles["body_zh"], styles["bullet_zh"],
                                      styles["equation_zh"], paragraph_space=3))
        if section == "后续分析计划":
            story.extend([
                schedule_table(styles, chinese=True),
                Paragraph("表 3：拟定团队进度。提交前必须替换成员占位符。", styles["caption_zh"]),
            ])
    if include_figures:
        story.extend([
            PageBreak(),
            Paragraph("残差诊断", styles["h1_zh"]),
            Image(str(DIAGNOSTICS), width=6.25 * inch, height=5.55 * inch),
            Paragraph("图 2：未修正初步 OLS 模型的残差-拟合值、Q-Q、时间顺序与自相关图。", styles["caption_zh"]),
        ])
    return story


def build() -> None:
    register_fonts()
    styles = make_styles()
    en_sections = parse_sections(EN_SOURCE.read_text(encoding="utf-8"))
    zh_sections = parse_sections(ZH_SOURCE.read_text(encoding="utf-8"))
    OUTPUT_EN.parent.mkdir(parents=True, exist_ok=True)

    official_story = cover(styles, bilingual=False) + english_content(en_sections, styles)
    ProposalDoc(str(OUTPUT_EN), "STA302 Research Proposal - Official English Version").build(official_story)

    bilingual_story = cover(styles, bilingual=True) + english_content(en_sections, styles) + chinese_content(zh_sections, styles)
    ProposalDoc(str(OUTPUT_BILINGUAL), "STA302 Bilingual Research Proposal").build(bilingual_story)

    chinese_story = cover(styles, chinese_only=True) + chinese_content(
        zh_sections, styles, start_new_page=False, standalone=True, include_figures=True
    )
    ProposalDoc(str(OUTPUT_ZH), "STA302 Research Proposal - Chinese Version").build(chinese_story)

    print(OUTPUT_EN)
    print(OUTPUT_BILINGUAL)
    print(OUTPUT_ZH)


if __name__ == "__main__":
    build()
