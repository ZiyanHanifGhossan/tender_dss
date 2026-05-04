"""Utilities for exporting DataFrame to CSV and PDF bytes.

Functions:
- df_to_csv_bytes(df): returns CSV bytes (utf-8)
- df_to_pdf_bytes(df, title='Report'): returns PDF bytes (landscape letter)

This module is import-resilient: if `reportlab` is not installed, the module can still be imported
and `df_to_pdf_bytes` will raise a descriptive error when called.
"""
# Optional import of reportlab. Keep module import-safe so Streamlit pages don't crash when reportlab
# is missing; provide a clear error at call time.
try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    _HAS_REPORTLAB = True
except Exception:
    _HAS_REPORTLAB = False

import io
import pandas as pd
import os
import shutil
from datetime import datetime

# Optional import of plotly for interactive charts; keep module import-safe
try:
    import plotly.express as px
    _HAS_PLOTLY = True
except Exception:
    px = None
    _HAS_PLOTLY = False


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return CSV representation as UTF-8 bytes."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_pdf_bytes(
    df: pd.DataFrame,
    title: str = "Report",
    logo_path: str | None = None,
    logo_bytes: bytes | None = None,
    company_name: str | None = None,
    config_path: str | None = None,
    author: str | None = None,
) -> bytes:
    """Render DataFrame into a PDF (landscape) with header, optional logo, company name and pagination.

    Parameters
    - df: DataFrame to render
    - title: Report title shown in header
    - logo_path: path to an image file to show in the header
    - logo_bytes: in-memory image bytes (takes precedence over logo_path)
    - company_name: optional company name to display near the logo
    - author: optional author text to include in footer

    If `reportlab` is not available, this function will raise RuntimeError with an installation hint.
    """
    if not _HAS_REPORTLAB:
        raise RuntimeError("Optional dependency 'reportlab' is not installed. Install it with: pip install reportlab")

    # Lazy imports needed for extended layout functionality
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import PageBreak
    from datetime import datetime
    from reportlab.lib.styles import ParagraphStyle

    buffer = io.BytesIO()

    PAGE_SIZE = landscape(letter)
    left_margin = right_margin = bottom_margin = 20

    # Load config if available (config_path may be passed later)
    # cfg will be loaded below; top_margin depends on logo/title sizes

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    title_style = styles["Title"]
    small_style = styles["BodyText"]

    elements = []

    # compute a searchable columns summary (used both in page body and PDF metadata)
    col_list_str = ", ".join(str(c) for c in df.columns.astype(str)) if not df.empty else ""

    # Header/footer drawing callback
    def _on_page(canvas, doc):
        canvas.saveState()
        # Set PDF metadata subject to include column list so the bytes include column names
        try:
            if col_list_str:
                canvas.setSubject(col_list_str)
        except Exception:
            # metadata setting is best-effort; do not fail PDF generation if it raises
            pass

        # Header: logo, company name, title, date (positions configurable)
        page_width, page_height = PAGE_SIZE

        x_left = left_margin
        y_top = page_height - 12

        # Read config values (fallback to function args)
        # (cfg is captured from outer scope)

        # Draw logo if provided (respecting position)
        max_h = cfg.get("logo_max_height", 40)
        logo_w = 0
        if logo_bytes is not None:
            img = ImageReader(io.BytesIO(logo_bytes))
            iw, ih = img.getSize()
            scale = max_h / ih
            logo_w = iw * scale
            h = ih * scale
            pos = cfg.get("logo_position", "left")
            if pos == "left":
                canvas.drawImage(img, x_left, y_top - h, width=logo_w, height=h, preserveAspectRatio=True, mask='auto')
            elif pos == "center":
                canvas.drawImage(img, (page_width - logo_w) / 2.0, y_top - h, width=logo_w, height=h, preserveAspectRatio=True, mask='auto')
            else:  # right
                canvas.drawImage(img, page_width - right_margin - logo_w, y_top - h, width=logo_w, height=h, preserveAspectRatio=True, mask='auto')
        elif logo_path is not None and os.path.exists(logo_path):
            img = ImageReader(logo_path)
            iw, ih = img.getSize()
            scale = max_h / ih
            logo_w = iw * scale
            h = ih * scale
            pos = cfg.get("logo_position", "left")
            if pos == "left":
                canvas.drawImage(img, x_left, y_top - h, width=logo_w, height=h, preserveAspectRatio=True, mask='auto')
            elif pos == "center":
                canvas.drawImage(img, (page_width - logo_w) / 2.0, y_top - h, width=logo_w, height=h, preserveAspectRatio=True, mask='auto')
            else:  # right
                canvas.drawImage(img, page_width - right_margin - logo_w, y_top - h, width=logo_w, height=h, preserveAspectRatio=True, mask='auto')

        # Company name placement
        company_position = cfg.get("company_name_position", "left")
        if company_name:
            canvas.setFont("Helvetica-Bold", int(cfg.get("company_font_size", 12)))
            canvas.setFillColor(colors.darkblue)
            if company_position == "left":
                canvas.drawString(x_left + logo_w + 8, y_top - 6, company_name)
            elif company_position == "center":
                canvas.drawCentredString(page_width / 2.0, y_top - 24, company_name)
            else:  # right
                canvas.drawRightString(page_width - right_margin, y_top - 6, company_name)

        # Title centered
        canvas.setFont("Helvetica-Bold", int(cfg.get("title_font_size", 14)))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(page_width - right_margin, y_top, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Optional header separator line
        if cfg.get("header_separator"):
            sep_color = colors.HexColor(cfg.get("header_separator_color", "#444444"))
            sep_thickness = float(cfg.get("header_separator_thickness", 0.5))
            # place separator a bit below the top margin area
            y_sep = page_height - top_margin + 6
            canvas.setStrokeColor(sep_color)
            canvas.setLineWidth(sep_thickness)
            canvas.line(left_margin, y_sep, page_width - right_margin, y_sep)

        # Footer: page number and optional author
        canvas.setFont("Helvetica", 8)
        footer_text = f"Page {canvas.getPageNumber()}"
        if author:
            footer_text = author + " — " + footer_text
        canvas.drawString(left_margin, bottom_margin - 6, footer_text)

        canvas.restoreState()

    # If config path provided, load config
    cfg = load_reporting_config(config_path) if config_path else load_reporting_config()

    # allow function args to override config
    if company_name is None:
        company_name = cfg.get("company_name") or company_name
    if not logo_path and not logo_bytes:
        logo_path = cfg.get("logo_path")

    # compute top margin dynamically to make room for header (logo + company name + title)
    logo_h = int(cfg.get("logo_max_height", 40))
    title_fs = int(cfg.get("title_font_size", 14))
    company_fs = int(cfg.get("company_font_size", 12))
    top_margin = max(40, logo_h + title_fs + 20)
    # if a header separator line is enabled, add extra spacing so the table doesn't collide with it
    if cfg.get("header_separator"):
        top_margin = int(top_margin + cfg.get("header_separator_thickness", 0.5) + 6)

    # Create the document with dynamic top margin so body doesn't overlap header
    doc = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    # Title flowable as first element (keeps consistency when printing)
    elements.append(Paragraph(title, title_style))
    if cfg.get("company_name_position") == "center" and company_name:
        elements.append(Paragraph(company_name, small_style))
    elements.append(Spacer(1, 8))

    # Add a short, searchable columns summary so consumers (and tests) can detect presence of
    # important columns (e.g., 'Auto_Flag') in the generated PDF
    if not df.empty:
        col_list_str = ", ".join(str(c) for c in df.columns.astype(str))
        elements.append(Paragraph(f"Included columns: {col_list_str}", normal_style))
        elements.append(Spacer(1, 6))

    if df.empty:
        elements.append(Paragraph("No data available", normal_style))
        doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
        buffer.seek(0)
        return buffer.read()

    # Prepare table data and cell styles (wrap text using Paragraphs)
    page_width, _ = PAGE_SIZE
    usable_width = page_width - left_margin - right_margin
    n_cols = len(df.columns)

    # Basic heuristics: prefer at least 60pt per column
    min_col_width = 60
    default_col_width = max(min_col_width, usable_width / n_cols)
    col_widths = [default_col_width for _ in range(n_cols)]

    # Styles for table cells
    cell_style = ParagraphStyle(
        name="table_cell",
        parent=normal_style,
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        spaceBefore=0,
        spaceAfter=0,
    )
    header_cell_style = ParagraphStyle(
        name="table_header",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=0,
        spaceBefore=0,
        spaceAfter=0,
    )

    # Convert data to Paragraphs so long text wraps and respects padding
    data = []
    header_row = [Paragraph(str(col), header_cell_style) for col in df.columns.astype(str)]
    data.append(header_row)
    for row in df.astype(str).values.tolist():
        data.append([Paragraph(cell, cell_style) for cell in row])

    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Build TableStyle commands in a list first (avoids issues with incremental .add calls)
    table_style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]

    # If 'Total Score' and 'Win_Prob' columns exist, append a yellow background command for any row
    # meeting the auto-flag criteria: Win_Prob > 0.8 and Total Score < 0.6
    if "Total Score" in df.columns and "Win_Prob" in df.columns:
        for row_idx, (s, p) in enumerate(zip(df["Total Score"].tolist(), df["Win_Prob"].tolist()), start=1):
            try:
                s_val = float(s)
                p_val = float(p)
            except Exception:
                continue
            if (s_val < 0.6) and (p_val > 0.8):
                # Table data uses row 0 for header, so first data row is index 1
                table_style_commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#ffeb3b")))

    # Sanitize commands: ensure every command is a sequence of at least 3 elements
    valid_cmds = [tuple(c) for c in table_style_commands if isinstance(c, (list, tuple)) and len(c) >= 3]
    table.setStyle(TableStyle(valid_cmds))

    elements.append(table)

    # Build PDF with header/footer callback
    doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)

    buffer.seek(0)
    return buffer.read()


# --- Global logo management helpers ---
def get_global_logo_bytes(path: str = "assets/logo.png") -> bytes | None:

    """Return bytes of the global logo if it exists, otherwise None."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def save_global_logo_bytes(bytes_data: bytes, path: str = "assets/logo.png", backup_old: bool = True) -> None:
    """Save bytes as the global logo. If backup_old is True and a file exists, create a timestamped backup."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if backup_old and os.path.exists(path):
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{path}.{ts}.bak"
        shutil.copy(path, backup_path)
    with open(path, "wb") as f:
        f.write(bytes_data)


def delete_global_logo(path: str = "assets/logo.png") -> bool:
    """Delete the global logo file. Return True if deleted, False if file did not exist."""
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


# --- Reporting configuration (file-based) ---
import json

def load_reporting_config(path: str = "assets/reporting_config.json") -> dict:
    """Load report header config from JSON file. Returns a dict with defaults filled in."""
    defaults = {
        "company_name": "",
        "logo_path": "assets/logo.png",
        "logo_position": "left",  # left | center | right
        #"company_name_position": "left",  # left | center | right
        "title_font_size": 14,
        "company_font_size": 12,
        "logo_max_height": 40,
        "author": "",
        "header_separator": True,  # draw a horizontal line under header
        "header_separator_color": "#444444",
        "header_separator_thickness": 0.5,
    }
    if not os.path.exists(path):
        return defaults
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return defaults
    # fill defaults
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    return cfg


def save_reporting_config(cfg: dict, path: str = "assets/reporting_config.json") -> None:
    """Save report header config to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# -------------------------
# Visualization utilities
# -------------------------
from modules import ml_model
from modules.risk import risk_level


def flag_exception_candidates(df: pd.DataFrame) -> pd.Series:
    """Return a boolean Series flagging Exception Candidates.

    Condition: `Total Score` < 0.6 AND `Win_Prob` > 0.8

    The function is tolerant of missing columns and will return a Series of False
    if the necessary columns are not present.
    """
    if df is None or df.empty:
        return pd.Series([False] * (0 if df is None else len(df)), index=df.index if df is not None else None)
    if "Total Score" not in df.columns or "Win_Prob" not in df.columns:
        return pd.Series([False] * len(df), index=df.index)
    ts = pd.to_numeric(df["Total Score"], errors="coerce")
    wp = pd.to_numeric(df["Win_Prob"], errors="coerce")
    mask = (ts < 0.6) & (wp > 0.8)
    return mask.fillna(False)


def compute_pipeline_stats(df: pd.DataFrame) -> dict:
    """Compute counts for funnel stages and win probabilities.

    Returns dict with keys: identified, qualified, bid, win_prob_count, expected_wins
    """
    # Implement helper that flags Exception Candidates (kept as a separate utility)
    def _flag_exception_candidates_local(df_local_in: pd.DataFrame) -> pd.Series:
        if df_local_in is None or df_local_in.empty:
            return pd.Series([False] * (0 if df_local_in is None else len(df_local_in)), index=df_local_in.index if df_local_in is not None else None)
        if "Total Score" not in df_local_in.columns or "Win_Prob" not in df_local_in.columns:
            return pd.Series([False] * len(df_local_in), index=df_local_in.index)
        ts = pd.to_numeric(df_local_in["Total Score"], errors="coerce")
        wp = pd.to_numeric(df_local_in["Win_Prob"], errors="coerce")
        mask = (ts < 0.6) & (wp > 0.8)
        return mask.fillna(False)

    stats = {"identified": 0, "qualified": 0, "bid": 0, "win_prob_count": 0, "expected_wins": 0.0}
    if df is None or df.empty:
        return stats

    stats["identified"] = int(len(df))

    # Pre-qualification (same logic as Bid Decision page)
    df_local = df.copy()
    # Avoid division by zero
    df_local["nilai_hps"] = df_local.get("nilai_hps", pd.Series([1]*len(df_local)))
    def pre_qualification_row(row):
        if row.get("kesiapan_sertifikat") == "Tidak Siap":
            return "Not Qualified"
        try:
            if row.get("nilai_proyek", 0) > 1.2 * row.get("nilai_hps", 0):
                return "Not Qualified"
        except Exception:
            return "Not Qualified"
        if row.get("risiko") == 5:
            return "Not Qualified"
        return "Qualified"

    df_local["Pre-Qualification"] = df_local.apply(pre_qualification_row, axis=1)
    stats["qualified"] = int((df_local["Pre-Qualification"] == "Qualified").sum())

    # Compute normalized features for scoring - fallback safe ops
    # use small epsilon to avoid division by zero
    eps = 1e-9
    nilai_max = df_local["nilai_proyek"].max() if "nilai_proyek" in df_local else 1.0
    min_durasi = df_local["durasi"].min() if "durasi" in df_local else 1.0
    min_komp = df_local["kompleksitas"].min() if "kompleksitas" in df_local else 1.0
    min_risk = df_local["risiko"].min() if "risiko" in df_local else 1.0

    df_local["n_nilai"] = df_local["nilai_proyek"] / (nilai_max + eps)
    df_local["n_durasi"] = min_durasi / (df_local["durasi"] + eps)
    df_local["n_kompleksitas"] = min_komp / (df_local["kompleksitas"] + eps)
    df_local["n_risiko"] = min_risk / (df_local["risiko"] + eps)

    df_local["Total Score"] = (
        0.4 * df_local["n_nilai"] +
        0.2 * df_local["n_durasi"] +
        0.2 * df_local["n_kompleksitas"] +
        0.2 * df_local["n_risiko"]
    )

    # Risk Level
    df_local["Risk Level"] = df_local["risiko"].apply(lambda r: risk_level(r))

    # Bid decision
    def bid_decision_row(row):
        if row["Pre-Qualification"] != "Qualified":
            return "NO BID"
        if row["Total Score"] >= 0.6 and row["Risk Level"] != "High":
            return "BID"
        return "NO BID"

    df_local["Decision"] = df_local.apply(bid_decision_row, axis=1)
    stats["bid"] = int((df_local["Decision"] == "BID").sum())
    # Count NO BID per the same Bid Decision logic (pre-qualification, score, risk)
    stats["no_bid"] = int((df_local["Decision"] == "NO BID").sum())

    # Compute win probabilities for bids (use model if available)
    probs = []
    probs_all = []
    for _, r in df_local.iterrows():
        try:
            prob = float(ml_model.predict_win_probability([r["nilai_proyek"], r["durasi"], r["kompleksitas"], r["risiko"]]))
        except Exception:
            prob = 0.0
        probs_all.append(prob)
        if r["Decision"] == "BID":
            probs.append(prob)

    stats["expected_wins"] = float(sum(probs))
    stats["win_prob_count"] = int(sum(1 for p in probs if p >= 0.5))

    # Exception Candidate: tender with low score but high model-predicted win probability
    try:
        scores = df_local["Total Score"].tolist()
        stats["exception_candidates"] = int(sum(1 for s, p in zip(scores, probs_all) if (s is not None and s < 0.6 and p > 0.8)))
    except Exception:
        stats["exception_candidates"] = 0

    return stats


def apply_bid_decision(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with 'Pre-Qualification', 'Total Score', 'Risk Level' and 'Decision' columns applied

    The logic mirrors the Bid Decision page and compute_pipeline_stats to ensure consistency.
    """
    if df is None or df.empty:
        return df.copy()

    df_local = df.copy()
    # Avoid missing columns
    df_local["nilai_hps"] = df_local.get("nilai_hps", pd.Series([0]*len(df_local)))

    def pre_qualification_row(row):
        if row.get("kesiapan_sertifikat") == "Tidak Siap":
            return "Not Qualified"
        try:
            if row.get("nilai_proyek", 0) > 1.2 * row.get("nilai_hps", 0):
                return "Not Qualified"
        except Exception:
            return "Not Qualified"
        if row.get("risiko") == 5:
            return "Not Qualified"
        return "Qualified"

    df_local["Pre-Qualification"] = df_local.apply(pre_qualification_row, axis=1)

    # Normalized features for scoring
    eps = 1e-9
    nilai_max = df_local["nilai_proyek"].max() if "nilai_proyek" in df_local else 1.0
    min_durasi = df_local["durasi"].min() if "durasi" in df_local else 1.0
    min_komp = df_local["kompleksitas"].min() if "kompleksitas" in df_local else 1.0
    min_risk = df_local["risiko"].min() if "risiko" in df_local else 1.0

    df_local["n_nilai"] = df_local["nilai_proyek"] / (nilai_max + eps)
    df_local["n_durasi"] = min_durasi / (df_local["durasi"] + eps)
    df_local["n_kompleksitas"] = min_komp / (df_local["kompleksitas"] + eps)
    df_local["n_risiko"] = min_risk / (df_local["risiko"] + eps)

    df_local["Total Score"] = (
        0.4 * df_local["n_nilai"] +
        0.2 * df_local["n_durasi"] +
        0.2 * df_local["n_kompleksitas"] +
        0.2 * df_local["n_risiko"]
    )

    df_local["Risk Level"] = df_local["risiko"].apply(lambda r: risk_level(r))

    def bid_decision_row(row):
        if row["Pre-Qualification"] != "Qualified":
            return "NO BID"
        if row["Total Score"] >= 0.6 and row["Risk Level"] != "High":
            return "BID"
        return "NO BID"

    df_local["Decision"] = df_local.apply(bid_decision_row, axis=1)
    return df_local


def pipeline_funnel_figure(df: pd.DataFrame):
    """Return a Plotly funnel figure showing Identified -> Qualified -> Bid -> WinProb (count).
    Raises RuntimeError if plotly is not available."""
    if not _HAS_PLOTLY:
        raise RuntimeError("Optional dependency 'plotly' is not installed. Install it with: pip install plotly")
    stats = compute_pipeline_stats(df)
    stages = ["Identified", "Qualified", "Bid", "WinProb"]
    values = [stats["identified"], stats["qualified"], stats["bid"], stats["win_prob_count"]]
    fig = px.funnel(x=values, y=stages, orientation='h')
    fig.update_layout(margin=dict(l=30, r=10, t=20, b=20))
    return fig


def monthly_tenders_bar_figure(df: pd.DataFrame, periods: int = 12):
    """Return a Plotly bar figure with number of tenders per month (last `periods` months)."""
    if not _HAS_PLOTLY:
        raise RuntimeError("Optional dependency 'plotly' is not installed. Install it with: pip install plotly")
    if df is None or df.empty:
        return px.bar(x=[], y=[], labels={'x':'Month','y':'Count'})

    # Try parsing input_date or created date columns
    if "input_date" in df.columns:
        dates = pd.to_datetime(df["input_date"], errors='coerce')
    else:
        dates = pd.NaT

    df_dates = df.copy()
    df_dates["_month"] = dates.dt.to_period('M').dt.to_timestamp()
    counts = df_dates.groupby("_month").size().sort_index()

    # Keep last `periods` months
    if counts.empty:
        return px.bar(x=[], y=[], labels={'x':'Month','y':'Count'})
    counts = counts.tail(periods)
    x = [d.strftime("%Y-%m") for d in counts.index]
    y = counts.values.tolist()
    fig = px.bar(x=x, y=y, labels={'x': 'Month', 'y': 'Number of Tenders'})
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return fig


def risk_pie_figure(df: pd.DataFrame):
    """Return a Plotly pie chart showing distribution of risk levels."""
    if not _HAS_PLOTLY:
        raise RuntimeError("Optional dependency 'plotly' is not installed. Install it with: pip install plotly")
    if df is None or df.empty:
        return px.pie(names=[], values=[])
    levels = df["risiko"].apply(lambda r: risk_level(r))
    counts = levels.value_counts()
    fig = px.pie(names=counts.index.tolist(), values=counts.values.tolist(), hole=0.3)
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return fig
