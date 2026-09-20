from __future__ import annotations

import csv
import html
import math
import re
from pathlib import Path
from statistics import NormalDist

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
SCATTER_ZH = ROOT / "figures" / "fx_slope_by_period_zh.png"
DIAGNOSTICS_ZH = ROOT / "figures" / "residual_diagnostics_zh.png"
ZH_FONT_PATH = Path("/System/Library/Fonts/STHeiti Medium.ttc")
ZH_FONT = "STHeiti-Embedded"

NAVY = colors.HexColor("#15324B")
BLUE = colors.HexColor("#1F6AA5")
LIGHT = colors.HexColor("#EAF1F7")
PALE = colors.HexColor("#F5F7F9")
MID = colors.HexColor("#5D6B78")


def register_fonts() -> None:
    if not ZH_FONT_PATH.exists():
        raise FileNotFoundError(f"Embedded Chinese font not found: {ZH_FONT_PATH}")
    pdfmetrics.registerFont(TTFont(ZH_FONT, str(ZH_FONT_PATH), subfontIndex=0))


def clean_inline(text: str) -> str:
    text = text.strip().removeprefix("> ")
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    text = text.replace("`", "")
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
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


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


def _pil_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ZH_FONT_PATH), size=size, index=0)


def _scale(value: float, low: float, high: float, start: float, end: float) -> float:
    if high == low:
        return (start + end) / 2
    return start + (value - low) * (end - start) / (high - low)


def _draw_axes(draw, box, x_range, y_range, x_label, y_label, title, font, small):
    left, top, right, bottom = box
    draw.rectangle(box, outline="#5D6B78", width=2)
    draw.text(((left + right) / 2, top - 52), title, font=font, fill="#15324B", anchor="mm")
    draw.text(((left + right) / 2, bottom + 48), x_label, font=small, fill="#1D252C", anchor="mm")
    vertical_label = y_label if "\n" in y_label else "\n".join(y_label)
    draw.multiline_text((left - 82, (top + bottom) / 2), vertical_label, font=small, fill="#1D252C",
                        anchor="mm", align="center", spacing=3)
    for i in range(5):
        xv = x_range[0] + i * (x_range[1] - x_range[0]) / 4
        px = _scale(xv, *x_range, left, right)
        draw.line((px, bottom, px, bottom + 8), fill="#5D6B78", width=2)
        draw.text((px, bottom + 22), f"{xv:.1f}", font=small, fill="#5D6B78", anchor="mm")
        yv = y_range[0] + i * (y_range[1] - y_range[0]) / 4
        py = _scale(yv, *y_range, bottom, top)
        draw.line((left - 8, py, left, py), fill="#5D6B78", width=2)
        draw.text((left - 14, py), f"{yv:.1f}", font=small, fill="#5D6B78", anchor="rm")


def build_chinese_figures() -> None:
    """Create Chinese-labelled figures without relying on an external R installation."""
    rows = read_csv(ROOT / "data" / "processed" / "sta302_daily_analysis.csv")
    coefficients = {
        row["term"]: float(row["estimate"])
        for row in read_csv(ROOT / "results" / "coefficients_classical.csv")
    }
    SCATTER_ZH.parent.mkdir(parents=True, exist_ok=True)

    # Figure 1: observed spread and controlled period-specific FX slopes.
    image = PILImage.new("RGB", (1800, 1120), "white")
    draw = ImageDraw.Draw(image)
    title = _pil_font(42)
    label = _pil_font(29)
    small = _pil_font(22)
    box = (170, 120, 1690, 960)
    xs = [float(row["JPY_app"]) for row in rows]
    ys = [float(row["Y"]) for row in rows]
    x_range = (math.floor(min(xs)), math.ceil(max(xs)))
    y_range = (math.floor(min(ys)), math.ceil(max(ys)))
    _draw_axes(draw, box, x_range, y_range, "日元升值（百分点）", "HEWJ-EWJ\n日收益差\n（百分点）",
               "日元升值与货币对冲收益差：疫情前后比较", title, small)
    left, top, right, bottom = box
    colors_by_period = {"Pre": "#3B82B8", "Post": "#D95F59"}
    for row in rows:
        px = _scale(float(row["JPY_app"]), *x_range, left, right)
        py = _scale(float(row["Y"]), *y_range, bottom, top)
        fill = colors_by_period[row["Post"]]
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=fill)
    for period, color in colors_by_period.items():
        post = 1.0 if period == "Post" else 0.0
        intercept = coefficients["(Intercept)"] + post * coefficients["PostPost"]
        slope = coefficients["JPY_app"] + post * coefficients["JPY_app:PostPost"]
        x1, x2 = x_range
        y1, y2 = intercept + slope * x1, intercept + slope * x2
        draw.line((_scale(x1, *x_range, left, right), _scale(y1, *y_range, bottom, top),
                   _scale(x2, *x_range, left, right), _scale(y2, *y_range, bottom, top)), fill=color, width=7)
    legend_y = 1040
    draw.ellipse((590, legend_y - 9, 608, legend_y + 9), fill=colors_by_period["Pre"])
    draw.text((620, legend_y), "疫情前", font=label, fill="#1D252C", anchor="lm")
    draw.ellipse((900, legend_y - 9, 918, legend_y + 9), fill=colors_by_period["Post"])
    draw.text((930, legend_y), "疫情后", font=label, fill="#1D252C", anchor="lm")
    image.save(SCATTER_ZH, optimize=True)

    # Figure 2: diagnostics reconstructed from the stored coefficients and processed data.
    term_order = ["(Intercept)", "JPY_app", "PostPost", "Nikkei_ret", "SMB", "HML", "RMW", "CMA",
                  "MOM", "dlog_VIX", "rate_diff", "JPY_app:PostPost"]
    fitted, residuals = [], []
    for row in rows:
        post = 1.0 if row["Post"] == "Post" else 0.0
        values = [1.0, float(row["JPY_app"]), post, float(row["Nikkei_ret"]), float(row["SMB"]),
                  float(row["HML"]), float(row["RMW"]), float(row["CMA"]), float(row["MOM"]),
                  float(row["dlog_VIX"]), float(row["rate_diff"]), float(row["JPY_app"]) * post]
        pred = sum(coefficients[term] * value for term, value in zip(term_order, values))
        fitted.append(pred)
        residuals.append(float(row["Y"]) - pred)

    influence_by_date = {
        row["date"]: row for row in read_csv(ROOT / "results" / "influence_audit.csv")
    }
    standardized = [float(influence_by_date[row["date"]]["standardized_residual"]) for row in rows]
    cooks = [float(influence_by_date[row["date"]]["cooks_distance"]) for row in rows]
    cooks_threshold = float(next(iter(influence_by_date.values()))["threshold_4_over_n"])

    image = PILImage.new("RGB", (1800, 1940), "white")
    draw = ImageDraw.Draw(image)
    panel_title = _pil_font(30)
    panel_label = _pil_font(21)
    panels = [
        (140, 115, 850, 570), (990, 115, 1700, 570),
        (140, 745, 850, 1200), (990, 745, 1700, 1200),
        (140, 1375, 850, 1830), (990, 1375, 1700, 1830),
    ]

    # Residuals versus fitted.
    xr = (min(fitted), max(fitted)); yr = (min(residuals), max(residuals))
    _draw_axes(draw, panels[0], xr, yr, "拟合值", "残差", "残差与拟合值", panel_title, panel_label)
    l, t, r, b = panels[0]
    for x, y in zip(fitted, residuals):
        px, py = _scale(x, *xr, l, r), _scale(y, *yr, b, t)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill="#397DAF")
    zero_y = _scale(0, *yr, b, t)
    draw.line((l, zero_y, r, zero_y), fill="#D95F59", width=3)

    # Scale-location plot.
    scale_location = [math.sqrt(abs(value)) for value in standardized]
    sl_range = (0.0, max(scale_location) * 1.05)
    _draw_axes(draw, panels[1], xr, sl_range, "拟合值", "标准化残差绝对值平方根",
               "尺度-位置图", panel_title, panel_label)
    l, t, r, b = panels[1]
    for x, y in zip(fitted, scale_location):
        px, py = _scale(x, *xr, l, r), _scale(y, *sl_range, b, t)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill="#397DAF")

    # Normal Q-Q plot.
    observed = sorted(standardized)
    n = len(observed)
    mean = sum(observed) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in observed) / (n - 1))
    theoretical = [NormalDist().inv_cdf((i + .5) / n) for i in range(n)]
    q_range = (theoretical[0], theoretical[-1]); o_range = (observed[0], observed[-1])
    _draw_axes(draw, panels[2], q_range, o_range, "正态理论分位数", "标准化残差", "正态 Q-Q 图", panel_title, panel_label)
    l, t, r, b = panels[2]
    for x, y in zip(theoretical, observed):
        px, py = _scale(x, *q_range, l, r), _scale(y, *o_range, b, t)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill="#397DAF")
    draw.line((_scale(q_range[0], *q_range, l, r), _scale(mean + sd * q_range[0], *o_range, b, t),
               _scale(q_range[1], *q_range, l, r), _scale(mean + sd * q_range[1], *o_range, b, t)), fill="#D95F59", width=3)

    # Residuals in time order.
    time_range = (1.0, float(n))
    _draw_axes(draw, panels[3], time_range, yr, "观测顺序", "残差", "残差的时间顺序", panel_title, panel_label)
    l, t, r, b = panels[3]
    points = [(_scale(i + 1, *time_range, l, r), _scale(y, *yr, b, t)) for i, y in enumerate(residuals)]
    draw.line(points, fill="#397DAF", width=2)
    zero_y = _scale(0, *yr, b, t)
    draw.line((l, zero_y, r, zero_y), fill="#D95F59", width=3)

    # Residual autocorrelation.
    max_lag = 30
    denom = sum((x - mean) ** 2 for x in residuals)
    acf = [sum((residuals[i] - mean) * (residuals[i - lag] - mean) for i in range(lag, n)) / denom
           for lag in range(1, max_lag + 1)]
    acf_limit = max(.20, max(abs(x) for x in acf) * 1.2)
    acf_range = (-acf_limit, acf_limit)
    _draw_axes(draw, panels[4], (1, max_lag), acf_range, "滞后阶数", "自相关系数", "残差自相关", panel_title, panel_label)
    l, t, r, b = panels[4]
    zero_y = _scale(0, *acf_range, b, t)
    conf = 1.96 / math.sqrt(n)
    for bound in (-conf, conf):
        py = _scale(bound, *acf_range, b, t)
        draw.line((l, py, r, py), fill="#D95F59", width=2)
    for lag, value in enumerate(acf, 1):
        px = _scale(lag, 1, max_lag, l, r)
        py = _scale(value, *acf_range, b, t)
        draw.line((px, zero_y, px, py), fill="#397DAF", width=6)

    # Cook's distance in time order.
    cook_range = (0.0, max(cooks) * 1.08)
    _draw_axes(draw, panels[5], time_range, cook_range, "观测顺序", "Cook 距离", "影响点筛查", panel_title, panel_label)
    l, t, r, b = panels[5]
    threshold_y = _scale(cooks_threshold, *cook_range, b, t)
    draw.line((l, threshold_y, r, threshold_y), fill="#D95F59", width=3)
    for i, value in enumerate(cooks, 1):
        px = _scale(i, *time_range, l, r)
        py = _scale(value, *cook_range, b, t)
        draw.line((px, b, px, py), fill="#397DAF", width=2)
    image.save(DIAGNOSTICS_ZH, optimize=True)


class ProposalDoc(BaseDocTemplate):
    def __init__(self, filename: str, title: str, header_text: str, page_label: str = "Page"):
        super().__init__(
            filename,
            pagesize=letter,
            rightMargin=.66 * inch,
            leftMargin=.66 * inch,
            topMargin=.70 * inch,
            bottomMargin=.96 * inch,
            title=title,
            author="Haiwen Yi and group members",
        )
        self.header_text = header_text
        self.page_label = page_label
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=self.draw_page))

    def draw_page(self, canvas, doc):
        canvas.saveState()
        page_number = canvas.getPageNumber()
        if page_number > 1:
            canvas.setStrokeColor(colors.HexColor("#D9E0E6"))
            canvas.line(doc.leftMargin, letter[1] - .45 * inch,
                        letter[0] - doc.rightMargin, letter[1] - .45 * inch)
            canvas.setFillColor(MID)
            canvas.setFont(ZH_FONT, 7.6)
            canvas.drawString(doc.leftMargin, letter[1] - .34 * inch,
                              self.header_text)
        canvas.setFillColor(MID)
        canvas.setFont(ZH_FONT if self.page_label != "Page" else "Helvetica", 8)
        footer = f"{self.page_label} {page_number}" if self.page_label == "Page" else f"第 {page_number} 页"
        canvas.drawRightString(letter[0] - doc.rightMargin, .36 * inch, footer)
        canvas.restoreState()


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=23, leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8),
        "title_zh": ParagraphStyle("TitleZH", parent=base["Title"], fontName=ZH_FONT,
                                   fontSize=19, leading=25, textColor=BLUE, alignment=TA_LEFT, spaceAfter=12),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Heading2"], fontName="Helvetica",
                                   fontSize=13, leading=18, textColor=BLUE, alignment=TA_LEFT, spaceAfter=16),
        "subtitle_zh": ParagraphStyle("SubtitleZH", parent=base["Heading2"], fontName=ZH_FONT,
                                      fontSize=12, leading=17, textColor=BLUE, alignment=TA_LEFT, spaceAfter=14),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14,
                             leading=18, textColor=NAVY, spaceBefore=10, spaceAfter=7, keepWithNext=True),
        "h1_zh": ParagraphStyle("H1ZH", parent=base["Heading1"], fontName=ZH_FONT, fontSize=13.2,
                                leading=17, textColor=NAVY, spaceBefore=8, spaceAfter=5, keepWithNext=True),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11,
                             leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=6, keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75,
                               leading=12.0, textColor=colors.HexColor("#1D252C"), alignment=TA_LEFT),
        "body_zh": ParagraphStyle("BodyZH", parent=base["BodyText"], fontName=ZH_FONT, fontSize=8.35,
                                  leading=11.9, textColor=colors.HexColor("#1D252C"), alignment=TA_LEFT),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75,
                                 leading=12.0, leftIndent=16, firstLineIndent=-12, bulletIndent=0),
        "bullet_zh": ParagraphStyle("BulletZH", parent=base["BodyText"], fontName=ZH_FONT, fontSize=8.35,
                                    leading=11.9, leftIndent=18, firstLineIndent=-14, bulletIndent=0),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica-Oblique",
                                  fontSize=7.6, leading=9.4, textColor=MID, spaceBefore=3, spaceAfter=8),
        "caption_zh": ParagraphStyle("CaptionZH", parent=base["BodyText"], fontName=ZH_FONT,
                                     fontSize=7.7, leading=10.2, textColor=MID, spaceBefore=3, spaceAfter=8),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.6,
                                leading=9.5, textColor=MID),
        "small_zh": ParagraphStyle("SmallZH", parent=base["BodyText"], fontName=ZH_FONT, fontSize=7.7,
                                   leading=10.5, textColor=MID),
        "equation": ParagraphStyle("Equation", parent=base["BodyText"], fontName="Helvetica-Oblique",
                                   fontSize=9.0, leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4),
        "equation_zh": ParagraphStyle("EquationZH", parent=base["BodyText"], fontName=ZH_FONT,
                                      fontSize=9.0, leading=13, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4),
    }


def wrap_table(data, widths, styles, font_size=7.1, repeat_rows=1, chinese=False):
    cell_style = ParagraphStyle(
        "CellZH" if chinese else "Cell",
        parent=styles["small_zh" if chinese else "small"],
        fontName=ZH_FONT if chinese else "Helvetica",
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.HexColor("#1D252C"),
    )
    header_style = ParagraphStyle(
        "CellHeaderZH" if chinese else "CellHeader",
        parent=cell_style,
        fontName=ZH_FONT if chinese else "Helvetica-Bold",
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
    header = ["Variable", "Type", "Mean", "SD", "Range", "Missing", "Important feature"]
    if chinese:
        header = ["变量", "类型", "均值", "标准差", "范围", "缺失", "主要特征"]
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
            str(int(float(row.get("missing", 0)))),
            feature,
        ])
    rows.append([
        "Post period" if not chinese else "疫情后时期",
        "Categorical" if not chinese else "分类",
        f"Pre: {int(diagnostics['pre_observations']):,}" if not chinese else f"疫情前：{int(diagnostics['pre_observations']):,}",
        f"Post: {int(diagnostics['post_observations']):,}" if not chinese else f"疫情后：{int(diagnostics['post_observations']):,}",
        "2 levels" if not chinese else "2 个水平",
        "0",
        "WHO-defined break" if not chinese else "WHO 事件定义断点",
    ])
    return wrap_table(rows, [.80 * inch, .54 * inch, .60 * inch, .58 * inch, .96 * inch, .52 * inch, 2.40 * inch],
                      styles, font_size=6.1, chinese=chinese)


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
        wrap_table(meta, [1.25 * inch, 5.15 * inch], styles, font_size=8.2, repeat_rows=0,
                   chinese=(bilingual or chinese_only)),
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
        Paragraph("Abstract", styles["h1"]),
        *paragraph_blocks(sections["Abstract"], styles["body"], styles["bullet"], styles["equation"]),
        Paragraph("Contribution statement", styles["h1"]),
        contribution_table(styles),
        Spacer(1, 4),
        Paragraph("Names and responsibilities must match the separately submitted Group Teamwork Agreement.", styles["small"]),
    ])
    order = [
        "Introduction (400 words)",
        "Data description (289 words)",
        "Ethics discussion (198 words)",
        "Preliminary results (391 words including captions)",
        "Plan for the remaining analysis (285 words)",
        "References",
        "Data and product documentation",
        "Submission items requiring group confirmation",
    ]
    for section in order:
        story.append(Paragraph(section, styles["h1"]))
        if section.startswith("Data description"):
            story.extend([
                variable_summary_table(styles),
                Paragraph("Table 1. Summary and missingness for all preliminary-model variables.", styles["caption"]),
            ])
        if section.startswith("Preliminary results"):
            story.extend([
                Image(str(SCATTER), width=6.38 * inch, height=4.25 * inch),
                Paragraph("Figure 1. Daily return spread versus yen appreciation with period-specific controlled OLS slopes.", styles["caption"]),
                coefficient_table(styles),
                Paragraph("Table 2. Preliminary OLS estimates with classical standard errors and 95% confidence intervals.", styles["caption"]),
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
        Image(str(DIAGNOSTICS), width=6.38 * inch, height=7.44 * inch),
        Paragraph("Figure 2. Six-panel diagnostics for the uncorrected preliminary OLS model.", styles["caption"]),
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
        Paragraph("摘要", styles["h1_zh"]),
        *paragraph_blocks(sections["摘要"], styles["body_zh"], styles["bullet_zh"], styles["equation_zh"], paragraph_space=3),
        Paragraph("成员贡献说明", styles["h1_zh"]),
        contribution_table(styles, chinese=True),
        Spacer(1, 4),
        Paragraph("姓名与职责必须和单独提交的小组协议一致。", styles["small_zh"]),
    ])
    order = ["研究背景与问题", "数据说明", "伦理声明", "初步结果", "后续分析计划", "参考文献", "数据与产品文档", "提交前仍需确认"]
    for section in order:
        story.append(Paragraph(section, styles["h1_zh"]))
        if section == "数据说明":
            story.extend([
                variable_summary_table(styles, chinese=True),
                Paragraph("表 1：全部初步模型变量的数值汇总与缺失数量。", styles["caption_zh"]),
            ])
        if section == "初步结果":
            if include_figures:
                story.extend([
                    Image(str(SCATTER_ZH), width=6.25 * inch, height=3.89 * inch),
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
            Image(str(DIAGNOSTICS_ZH), width=6.25 * inch, height=6.60 * inch),
            Paragraph("图 2：未修正初步 OLS 模型的六面板函数形式、方差、正态性、依赖与影响诊断。", styles["caption_zh"]),
        ])
    return story


def build() -> None:
    register_fonts()
    build_chinese_figures()
    styles = make_styles()
    en_sections = parse_sections(EN_SOURCE.read_text(encoding="utf-8"))
    zh_sections = parse_sections(ZH_SOURCE.read_text(encoding="utf-8"))
    OUTPUT_EN.parent.mkdir(parents=True, exist_ok=True)

    official_story = cover(styles, bilingual=False) + english_content(en_sections, styles)
    ProposalDoc(
        str(OUTPUT_EN), "STA302 Research Proposal - Official English Version",
        "STA302 | Currency-Hedged Japan ETF Study"
    ).build(official_story)

    bilingual_story = cover(styles, bilingual=True) + english_content(en_sections, styles) + chinese_content(zh_sections, styles)
    ProposalDoc(
        str(OUTPUT_BILINGUAL), "STA302 Bilingual Research Proposal",
        "STA302 | Currency-Hedged Japan ETF Study | 日元对冲研究"
    ).build(bilingual_story)

    chinese_story = cover(styles, chinese_only=True) + chinese_content(
        zh_sections, styles, start_new_page=False, standalone=True, include_figures=True
    )
    ProposalDoc(
        str(OUTPUT_ZH), "STA302 Research Proposal - Chinese Version",
        "STA302 | 日元对冲研究", page_label="页"
    ).build(chinese_story)

    print(OUTPUT_EN)
    print(OUTPUT_BILINGUAL)
    print(OUTPUT_ZH)


if __name__ == "__main__":
    build()
