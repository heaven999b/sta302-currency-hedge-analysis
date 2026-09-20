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
    BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
EN_SOURCE = ROOT / "docs" / "proposal" / "STA302_Research_Proposal_EN.md"
ZH_SOURCE = ROOT / "docs" / "proposal" / "STA302_Research_Proposal_ZH.md"
OUTPUT = ROOT / "output" / "pdf" / "STA302_Bilingual_Research_Proposal.pdf"
SCATTER = ROOT / "figures" / "fx_slope_by_period.png"
DIAGNOSTICS = ROOT / "figures" / "residual_diagnostics.png"

NAVY = colors.HexColor("#15324B")
BLUE = colors.HexColor("#1F6AA5")
LIGHT = colors.HexColor("#EAF1F7")
PALE = colors.HexColor("#F5F7F9")
MID = colors.HexColor("#5D6B78")


def register_fonts() -> None:
    # STSong-Light is a ReportLab CID font and keeps the build portable across
    # macOS, Linux, and GitHub Actions without bundling a third-party font file.
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def clean_inline(text: str) -> str:
    text = text.strip().removeprefix("> ")
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("—", "-").replace("–", "-").replace("‑", "-")
    replacements = {
        "\\Delta": "Δ", "\\beta": "β", "\\gamma": "γ",
        "\\times": "×", "\\varepsilon": "ε", "\\%": "%",
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


def paragraph_blocks(lines: list[str], body_style, bullet_style, equation_font: str):
    blocks = []
    buffer: list[str] = []
    equation: list[str] = []
    in_equation = False

    def flush() -> None:
        if buffer:
            blocks.extend([Paragraph(clean_inline(" ".join(buffer)), body_style), Spacer(1, 6)])
            buffer.clear()

    for raw in lines:
        line = raw.strip()
        if line == "\\[":
            flush(); equation = []; in_equation = True
        elif line == "\\]":
            blocks.append(Paragraph(
                clean_inline(" ".join(equation)),
                ParagraphStyle("Equation", parent=body_style, alignment=TA_CENTER,
                               fontName=equation_font, spaceBefore=5, spaceAfter=8),
            ))
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


def term(rows: list[dict[str, str]], name: str) -> dict[str, str]:
    return next(row for row in rows if row["term"] == name)


class ProposalDoc(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(filename, pagesize=letter, rightMargin=.70 * inch, leftMargin=.70 * inch,
                         topMargin=.70 * inch, bottomMargin=.65 * inch,
                         title="STA302 Bilingual Research Proposal",
                         author="Haiwen Yi and group members")
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


def styled_table(data, widths, header_font="Helvetica-Bold", body_font="Helvetica", font_size=7.7):
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), header_font),
        ("FONTNAME", (0, 1), (-1, -1), body_font),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#C7D1DA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def build() -> None:
    register_fonts()
    en_sections = parse_sections(EN_SOURCE.read_text(encoding="utf-8"))
    zh_sections = parse_sections(ZH_SOURCE.read_text(encoding="utf-8"))

    base = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23,
                           leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8)
    title_zh = ParagraphStyle("TitleZH", parent=title, fontName="STSong-Light", fontSize=19,
                              leading=25, textColor=BLUE, spaceAfter=12)
    subtitle = ParagraphStyle("Subtitle", parent=base["Heading2"], fontName="Helvetica", fontSize=13,
                              leading=18, textColor=BLUE, alignment=TA_LEFT, spaceAfter=16)
    subtitle_zh = ParagraphStyle("SubtitleZH", parent=subtitle, fontName="STSong-Light", fontSize=12)
    h1 = ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14,
                        leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=7, keepWithNext=True)
    h1_zh = ParagraphStyle("H1ZH", parent=h1, fontName="STSong-Light", fontSize=13.5)
    h2 = ParagraphStyle("H2", parent=h1, fontSize=11, leading=14, textColor=BLUE)
    body = ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.05,
                          leading=12.5, textColor=colors.HexColor("#1D252C"), alignment=TA_LEFT)
    body_zh = ParagraphStyle("BodyZH", parent=body, fontName="STSong-Light", fontSize=9.0, leading=14.2)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=16, firstLineIndent=-12, bulletIndent=0)
    bullet_zh = ParagraphStyle("BulletZH", parent=body_zh, leftIndent=18, firstLineIndent=-14, bulletIndent=0)
    caption = ParagraphStyle("Caption", parent=body, fontName="Helvetica-Oblique", fontSize=8,
                             leading=10, textColor=MID, spaceBefore=3, spaceAfter=8)
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=10.5, textColor=MID)
    small_zh = ParagraphStyle("SmallZH", parent=body_zh, fontSize=8, leading=11, textColor=MID)
    callout_zh = ParagraphStyle("CalloutZH", parent=body_zh, fontSize=10, leading=15, textColor=NAVY)

    classic = read_csv(ROOT / "results" / "coefficients_classical.csv")
    hac = read_csv(ROOT / "results" / "coefficients_hac5.csv")
    jpy = term(hac, "JPY_app")
    interaction_c = term(classic, "JPY_app:PostPost")
    interaction_h = term(hac, "JPY_app:PostPost")

    story = [Spacer(1, .18 * inch),
             Paragraph("Does a Currency Hedge Neutralize Daily Yen Exposure?", title),
             Paragraph("货币对冲能否抵消日元的日度风险敞口？", title_zh),
             Paragraph("A Multi-Factor Study of HEWJ versus EWJ Before and After the COVID-19 Break", subtitle),
             Paragraph("疫情前后 HEWJ 与 EWJ 的多因子比较研究", subtitle_zh),
             HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=16)]

    meta = [
        ["Course / 课程", "STA302 Final Project - Part 1 / STA302 期末项目 - 第一部分"],
        ["Prepared / 日期", "September 20, 2026 / 2026 年 9 月 20 日"],
        ["Group / 小组", "Haiwen Yi; [add all other members / 补充其他成员]"],
        ["Analysis / 分析", "R 4.4.3 | 2,753 daily observations | 2014-02-06 to 2026-07-31"],
    ]
    meta_table = Table(meta, colWidths=[1.25 * inch, 5.05 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#D9E0E6")),
    ]))
    story.extend([meta_table, Spacer(1, 15), Paragraph("R rerun - headline evidence / R 重跑核心结果", h1_zh)])

    key = [
        ["Full-model R² / 完整模型", "71.21%", "Pre slope / 疫情前斜率", f"{float(jpy['estimate']):.3f}"],
        ["Interaction / 交互项", f"{float(interaction_h['estimate']):.4f}", "OLS / HAC p", f"{float(interaction_c['p_value']):.4f} / {float(interaction_h['p_value']):.4f}"],
        ["Post slope / 疫情后斜率", "-0.917", "Maximum VIF / 最大 VIF", "3.55 (HML)"],
    ]
    key_table = Table(key, colWidths=[1.55 * inch, 1.0 * inch, 1.75 * inch, 1.65 * inch])
    key_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), .8, colors.HexColor("#C6D6E3")),
        ("INNERGRID", (0, 0), (-1, -1), .35, colors.HexColor("#C6D6E3")),
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([key_table, Spacer(1, 10), Paragraph(
        "The yen-spread association is strong, but evidence of a post-pandemic change is sensitive to the standard-error method. 日元与收益差的关系很强，但疫情后变化是否显著取决于标准误方法。",
        callout_zh), Spacer(1, 12)])
    warning = Table([[Paragraph(
        "Before submission / 提交前：replace all bracketed member fields, align the contribution agreement, and add required OneDrive links. / 补全成员与贡献、统一小组协议，并添加课程要求的 OneDrive 链接。",
        body_zh)]], colWidths=[6.25 * inch])
    warning.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3E8")),
        ("BOX", (0, 0), (-1, -1), .8, colors.HexColor("#E6B77A")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([warning, PageBreak(), Paragraph("Part I - English proposal (official course version)", h1)])

    contribution = [
        ["Member", "Proposed contribution"],
        ["Haiwen Yi", "Research design, data construction, R analysis, diagnostics, and first draft"],
        ["[Member 2]", "[Specify literature, validation, writing, or presentation tasks]"],
        ["[Member 3]", "[Specify literature, validation, writing, or presentation tasks]"],
        ["[Member 4, if applicable]", "[Specify contribution]"],
    ]
    story.extend([Paragraph("Contribution statement", h1), styled_table(contribution, [1.5 * inch, 4.75 * inch]),
                  Paragraph("The names and contributions must match the separately submitted group agreement.", small)])

    en_order = ["Introduction (341 words)", "Data description (272 words)", "Ethics statement (194 words)",
                "Preliminary results (368 words)", "Plan for the remaining analysis (275 words)",
                "References", "Data and product documentation", "Submission items still requiring group input"]
    results_table = [
        ["Term", "Estimate", "Classical SE", "Classical p", "HAC(5) SE", "HAC(5) p"],
        ["Yen appreciation (pre)", "-0.8520", "0.0178", "<0.001", "0.0307", "<0.001"],
        ["Post indicator", "0.0085", "0.0147", "0.562", "0.0063", "0.176"],
        ["Yen x Post", "-0.0648", "0.0227", "0.0043", "0.0355", "0.0683"],
        ["VIX log change", "-0.00687", "0.00082", "<0.001", "0.00164", "<0.001"],
    ]
    for section in en_order:
        story.append(Paragraph(section, h1))
        if section.startswith("Preliminary results"):
            story.extend([Image(str(SCATTER), width=6.25 * inch, height=4.17 * inch),
                          Paragraph("Figure 1. Daily HEWJ-minus-EWJ return spread versus yen appreciation. Lines are controlled period-specific slopes.", caption),
                          KeepTogether([styled_table(results_table, [1.55 * inch, .78 * inch, .9 * inch, .82 * inch, .86 * inch, .82 * inch]),
                                       Paragraph("Table 1. Selected full-model coefficients. HAC(5) changes inference for the pandemic interaction.", caption)])])
        story.extend(paragraph_blocks(en_sections[section], body, bullet, "Helvetica-Oblique"))
        if section.startswith("Preliminary results"):
            story.extend([PageBreak(), Paragraph("Residual diagnostics", h2),
                          Image(str(DIAGNOSTICS), width=6.25 * inch, height=5.56 * inch),
                          Paragraph("Figure 2. Residual diagnostics motivate robust inference and sensitivity checks.", caption)])

    story.extend([PageBreak(), Paragraph("第二部分 - 中文提案（组内讨论与理解版本）", h1_zh),
                  Paragraph("正式课程提交以第一部分英文版本为准；本部分与英文版本使用相同的研究设计、数值和限制。", callout_zh)])
    contribution_zh = [
        ["成员", "计划贡献"],
        ["Haiwen Yi", "研究设计、数据构建、R 分析、诊断检验和初稿撰写"],
        ["[成员 2]", "[补充文献、验证、写作或展示任务]"],
        ["[成员 3]", "[补充文献、验证、写作或展示任务]"],
        ["[成员 4，如适用]", "[补充具体贡献]"],
    ]
    story.extend([Paragraph("成员贡献说明", h1_zh),
                  styled_table(contribution_zh, [1.5 * inch, 4.75 * inch], header_font="STSong-Light", body_font="STSong-Light", font_size=8),
                  Paragraph("姓名与贡献说明必须和单独提交的小组协议一致。", small_zh)])
    zh_order = ["研究背景与问题", "数据说明", "伦理声明", "初步结果", "后续分析计划", "参考文献", "提交前仍需补充"]
    for section in zh_order:
        story.append(Paragraph(section, h1_zh))
        if section == "初步结果":
            zh_key = [
                ["指标", "结果", "指标", "结果"],
                ["完整模型 R²", "71.21%", "疫情前日元斜率", "-0.852"],
                ["日元 x 疫情后交互项", "-0.0648", "经典 / HAC p", "0.0043 / 0.0683"],
                ["疫情后隐含斜率", "-0.917", "最大 VIF", "3.55 (HML)"],
            ]
            story.extend([styled_table(zh_key, [1.7 * inch, 1.2 * inch, 1.7 * inch, 1.2 * inch],
                                       header_font="STSong-Light", body_font="STSong-Light", font_size=8), Spacer(1, 6)])
        story.extend(paragraph_blocks(zh_sections[section], body_zh, bullet_zh, "STSong-Light"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ProposalDoc(str(OUTPUT)).build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
