"""
generate_pdf_docs.py
====================
Trevolk Forecasting Engine — PDF Architecture Documentation Generator

Run this standalone script from the project root to produce:
    ./Trevolk_API_Architecture.pdf

Usage:
    python generate_pdf_docs.py

Dependencies:
    pip install reportlab
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    sys.exit(
        "reportlab is not installed. Run:  pip install reportlab\n"
        "Then re-execute this script."
    )

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_PATH = Path(__file__).parent / "Trevolk_API_Architecture.pdf"
GENERATED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Brand colours
BRAND_DARK = colors.HexColor("#0F172A")   # slate-900
BRAND_BLUE = colors.HexColor("#2563EB")   # blue-600
BRAND_LIGHT = colors.HexColor("#F8FAFC")  # slate-50
BRAND_GREY = colors.HexColor("#64748B")   # slate-500
ACCENT = colors.HexColor("#10B981")       # emerald-500

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
def _styles():
    base = getSampleStyleSheet()

    custom = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontSize=30,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=8,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontSize=13,
            textColor=colors.HexColor("#CBD5E1"),
            alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontSize=9,
            textColor=colors.HexColor("#94A3B8"),
            alignment=TA_CENTER,
            fontName="Helvetica",
        ),
        "h1": ParagraphStyle(
            "h1",
            fontSize=18,
            textColor=BRAND_DARK,
            fontName="Helvetica-Bold",
            spaceBefore=18,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontSize=13,
            textColor=BRAND_BLUE,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=10,
            textColor=BRAND_DARK,
            fontName="Helvetica",
            leading=15,
            spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "code",
            fontSize=8.5,
            textColor=colors.HexColor("#1E293B"),
            fontName="Courier",
            backColor=colors.HexColor("#F1F5F9"),
            borderPadding=(6, 8, 6, 8),
            leading=13,
            spaceAfter=8,
        ),
        "label": ParagraphStyle(
            "label",
            fontSize=9,
            textColor=BRAND_GREY,
            fontName="Helvetica-Oblique",
            alignment=TA_RIGHT,
        ),
    }
    return base, custom


def _hr(story, color=BRAND_BLUE, thickness=0.8):
    story.append(HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6))


def _table(data, col_widths, header_bg=BRAND_BLUE):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    n_rows = len(data)
    t.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                # Data rows
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


# ---------------------------------------------------------------------------
# Page canvas — header / footer on every page except cover
# ---------------------------------------------------------------------------
def _page_decorator(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, PAGE_H - 1.1 * cm, PAGE_W, 1.1 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN, PAGE_H - 0.7 * cm, "Trevolk Forecasting Engine")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.7 * cm, "API Architecture Documentation")
    # Footer
    canvas.setFillColor(BRAND_GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN, 0.65 * cm, f"Generated: {GENERATED_AT}  |  Confidential")
    canvas.drawRightString(PAGE_W - MARGIN, 0.65 * cm, f"Page {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Document sections
# ---------------------------------------------------------------------------
def _cover(story, styles):
    _, s = styles
    # Dark cover background
    story.append(Spacer(1, 5 * cm))
    story.append(Paragraph("TREVOLK", s["cover_title"]))
    story.append(Paragraph("Forecasting Engine", s["cover_title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("API Architecture &amp; Integration Documentation", s["cover_sub"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        Paragraph(
            f"Version 2.0.0 &nbsp;&nbsp;|&nbsp;&nbsp; Generated {GENERATED_AT}",
            s["cover_meta"],
        )
    )
    story.append(PageBreak())


def _section_overview(story, styles):
    _, s = styles
    story.append(Paragraph("1. System Overview", s["h1"]))
    _hr(story)
    story.append(
        Paragraph(
            "Trevolk Forecasting Engine is a production-grade FastAPI microservice that serves a "
            "trained <b>XGBoost regression model</b> for 7-day Rossmann store-sales prediction. "
            "It is consumed by a Next.js frontend dashboard that renders KPI cards and a daily "
            "forecast table in real-time.",
            s["body"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Key characteristics:", s["h2"]))
    bullets = [
        "Modular package layout (app/main, app/api, app/schemas, app/services)",
        "Thread-safe singleton MLService — model loaded once at startup",
        "Batch inference across a 7-day rolling window",
        "Strict Pydantic v2 request/response validation",
        "CORS pre-configured for Next.js (localhost:3000)",
        "OpenAPI / Swagger UI available at /docs",
    ]
    for b in bullets:
        story.append(Paragraph(f"• {b}", s["body"]))
    story.append(Spacer(1, 0.4 * cm))


def _section_architecture(story, styles):
    _, s = styles
    story.append(Paragraph("2. Directory Structure", s["h1"]))
    _hr(story)
    tree = (
        "Trevolk_Forecasting_Engine/\n"
        "├── app/\n"
        "│   ├── __init__.py\n"
        "│   ├── main.py               ← FastAPI app, CORS, lifespan, routers\n"
        "│   ├── api/\n"
        "│   │   ├── __init__.py\n"
        "│   │   └── endpoints.py      ← POST /api/predict route\n"
        "│   ├── schemas/\n"
        "│   │   ├── __init__.py\n"
        "│   │   └── predict.py        ← ForecastRequest, ForecastResponse\n"
        "│   └── services/\n"
        "│       ├── __init__.py\n"
        "│       └── ml_service.py     ← Singleton, feature engineering, inference\n"
        "├── trevolk_sales_model.pkl   ← Trained XGBoost model (required)\n"
        "├── generate_pdf_docs.py      ← This documentation generator\n"
        "├── requirements.txt\n"
        "└── Trevolk_API_Architecture.pdf  ← Generated output"
    )
    story.append(Paragraph(tree.replace("\n", "<br/>").replace(" ", "&nbsp;"), s["code"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Layer Responsibilities", s["h2"]))
    data = [
        ["Layer", "File", "Responsibility"],
        ["Entry Point", "app/main.py", "App init, CORS, lifespan model warm-up, router registration"],
        ["Router", "app/api/endpoints.py", "HTTP routing, error mapping to status codes"],
        ["Schema", "app/schemas/predict.py", "Pydantic validation for request and response"],
        ["Service", "app/services/ml_service.py", "Model loading, feature engineering, batch inference"],
        ["Script", "generate_pdf_docs.py", "Standalone PDF documentation generator"],
    ]
    story.append(_table(data, [2.8 * cm, 5.2 * cm, 8.8 * cm]))
    story.append(Spacer(1, 0.4 * cm))


def _section_endpoints(story, styles):
    _, s = styles
    story.append(Paragraph("3. API Endpoints", s["h1"]))
    _hr(story)

    # Endpoint table
    data = [
        ["Method", "Path", "Description", "Auth"],
        ["GET", "/", "Service root — returns version and status", "None"],
        ["GET", "/health", "Readiness probe — confirms model is loaded", "None"],
        ["POST", "/api/predict", "7-day sales forecast", "None"],
        ["GET", "/docs", "Interactive Swagger UI (OpenAPI)", "None"],
        ["GET", "/redoc", "ReDoc API documentation", "None"],
    ]
    story.append(_table(data, [1.8 * cm, 4 * cm, 9.4 * cm, 1.6 * cm]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("3.1  POST /api/predict", s["h2"]))
    story.append(
        Paragraph(
            "Accepts a JSON payload from the Next.js frontend, builds a 7×12 feature matrix, "
            "runs a single batch XGBoost inference call, and returns structured KPI data.",
            s["body"],
        )
    )


def _section_payload(story, styles):
    _, s = styles
    story.append(Paragraph("4. Payload Structures", s["h1"]))
    _hr(story)

    story.append(Paragraph("4.1  Request Payload (ForecastRequest)", s["h2"]))
    req_json = (
        '{\n'
        '  "store_id":             1,\n'
        '  "forecast_start_date":  "2026-10-02",\n'
        '  "promotion_active":     true,\n'
        '  "school_holiday":       false,\n'
        '  "competition_distance": 1270.0\n'
        '}'
    )
    story.append(Paragraph(req_json.replace("\n", "<br/>").replace(" ", "&nbsp;"), s["code"]))

    data = [
        ["Field", "Type", "Constraints", "Description"],
        ["store_id", "integer", ">= 1", "Rossmann store identifier"],
        ["forecast_start_date", "string", "YYYY-MM-DD, real date", "First day of 7-day window"],
        ["promotion_active", "boolean", "—", "Whether a promo is running"],
        ["school_holiday", "boolean", "—", "Whether schools are closed"],
        ["competition_distance", "float", ">= 0.0", "Metres to nearest competitor"],
    ]
    story.append(_table(data, [4.2 * cm, 2.2 * cm, 3.2 * cm, 7.2 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("4.2  Response Payload (ForecastResponse)", s["h2"]))
    res_json = (
        '{\n'
        '  "expected_revenue":         57893.5,\n'
        '  "optimal_price_adjustment": 4.8,\n'
        '  "confidence_score":         95.0,\n'
        '  "daily_forecast": [\n'
        '    { "date": "2026-10-02", "day": "Fri", "predicted_sales": 8257.0 },\n'
        '    { "date": "2026-10-03", "day": "Sat", "predicted_sales": 9412.0 },\n'
        '    ...\n'
        '  ]\n'
        '}'
    )
    story.append(Paragraph(res_json.replace("\n", "<br/>").replace(" ", "&nbsp;"), s["code"]))

    data = [
        ["Field", "Type", "Description"],
        ["expected_revenue", "float", "Sum of all 7 daily predictions — drives the Revenue KPI card"],
        ["optimal_price_adjustment", "float", "CV-based price signal in percentage points (±10 % band)"],
        ["confidence_score", "float (0–100)", "Model accuracy indicator — currently static at 95.0"],
        ["daily_forecast", "array", "7 objects: {date, day, predicted_sales} — drives the table"],
    ]
    story.append(_table(data, [5 * cm, 3.2 * cm, 8.6 * cm]))
    story.append(Spacer(1, 0.4 * cm))


def _section_ml(story, styles):
    _, s = styles
    story.append(Paragraph("5. ML Model Integration", s["h1"]))
    _hr(story)

    story.append(Paragraph("5.1  Model File", s["h2"]))
    story.append(
        Paragraph(
            "The trained XGBoost regressor is serialised with <b>joblib</b> and stored as "
            "<b>trevolk_sales_model.pkl</b> in the project root. "
            "It must be present before the server starts.",
            s["body"],
        )
    )

    story.append(Paragraph("5.2  Feature Engineering", s["h2"]))
    story.append(
        Paragraph(
            "For each incoming request, MLService generates 7 rows — one per forecast day — "
            "by decomposing <i>forecast_start_date</i> and the following 6 dates:",
            s["body"],
        )
    )
    data = [
        ["Feature", "Source", "Notes"],
        ["Store", "store_id (request)", "Direct mapping"],
        ["DayOfWeek", "forecast_start_date + offset", "Rossmann convention: 1=Mon … 7=Sun"],
        ["Promo", "promotion_active (request)", "bool → int (0/1)"],
        ["SchoolHoliday", "school_holiday (request)", "bool → int (0/1)"],
        ["StoreType", "DEFAULT_STORE_TYPE = 0", "Mocked — replace with label-encoded value"],
        ["Assortment", "DEFAULT_ASSORTMENT = 0", "Mocked — replace with label-encoded value"],
        ["CompetitionDistance", "competition_distance (request)", "Float, metres"],
        ["Year", "forecast_start_date + offset", "4-digit year"],
        ["Month", "forecast_start_date + offset", "1–12"],
        ["Day", "forecast_start_date + offset", "1–31"],
        ["WeekOfYear", "forecast_start_date + offset", "ISO week number"],
        ["StateHoliday", "DEFAULT_STATE_HOLIDAY = 0", "Mocked — replace with real encoding"],
    ]
    story.append(_table(data, [4.2 * cm, 5.8 * cm, 6.8 * cm]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("5.3  Inference Pipeline", s["h2"]))
    steps = [
        "1. Singleton MLService.load_model() deserialises the .pkl file at startup.",
        "2. ForecastRequest is validated by Pydantic before reaching the service.",
        "3. _build_feature_matrix() produces a (7 × 12) pd.DataFrame in FEATURE_ORDER.",
        "4. model.predict(df) runs a single vectorised XGBoost batch inference.",
        "5. Predictions are clipped to >= 0 (sales cannot be negative).",
        "6. KPIs (expected_revenue, optimal_price_adjustment) are computed from the array.",
        "7. ForecastResponse is serialised and returned as JSON.",
    ]
    for step in steps:
        story.append(Paragraph(step, s["body"]))
    story.append(Spacer(1, 0.4 * cm))


def _section_ops(story, styles):
    _, s = styles
    story.append(Paragraph("6. Operations Guide", s["h1"]))
    _hr(story)

    story.append(Paragraph("6.1  Local Development", s["h2"]))
    cmds = (
        "# Install dependencies\n"
        "pip install -r requirements.txt\n\n"
        "# Start the API server (auto-reload)\n"
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n\n"
        "# Open interactive API docs\n"
        "http://localhost:8000/docs"
    )
    story.append(Paragraph(cmds.replace("\n", "<br/>").replace(" ", "&nbsp;"), s["code"]))

    story.append(Paragraph("6.2  Environment Variables", s["h2"]))
    data = [
        ["Variable", "Default", "Description"],
        ["MODEL_PATH", "trevolk_sales_model.pkl", "Relative/absolute path to the .pkl file"],
        ["PORT", "8000", "Server listen port"],
        ["LOG_LEVEL", "info", "Uvicorn / Python logging level"],
    ]
    story.append(_table(data, [5 * cm, 5.5 * cm, 6.3 * cm]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("6.3  Health Check", s["h2"]))
    story.append(
        Paragraph(
            "The <b>GET /health</b> endpoint returns HTTP 200 with "
            "<code>model_loaded: true</code> when the service is ready. "
            "Use this for Kubernetes liveness/readiness probes or load-balancer health checks.",
            s["body"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))


def _section_errors(story, styles):
    _, s = styles
    story.append(Paragraph("7. Error Reference", s["h1"]))
    _hr(story)
    data = [
        ["HTTP Code", "Scenario", "Response body"],
        ["200 OK", "Successful forecast", '{"expected_revenue": …, "daily_forecast": […]}'],
        ["422 Unprocessable Entity", "Invalid payload (Pydantic validation)", '{"detail": [{"loc": …, "msg": …}]}'],
        ["503 Service Unavailable", "Model not yet loaded", '{"detail": "Model is not available …"}'],
        ["500 Internal Server Error", "Unexpected inference crash", '{"detail": "Inference error: …"}'],
    ]
    story.append(_table(data, [3.2 * cm, 5.2 * cm, 8.4 * cm]))
    story.append(Spacer(1, 0.4 * cm))


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------
def build_pdf(output_path: Path) -> None:
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=1.6 * cm,
        bottomMargin=1.4 * cm,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        title="Trevolk API Architecture",
        author="Trevolk Engineering",
        subject="API Architecture & ML Integration Documentation",
    )

    styles = _styles()
    story = []

    _cover(story, styles)
    _section_overview(story, styles)
    _section_architecture(story, styles)
    _section_endpoints(story, styles)
    _section_payload(story, styles)
    _section_ml(story, styles)
    _section_ops(story, styles)
    _section_errors(story, styles)

    doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=_page_decorator)
    print(f"PDF generated successfully: {output_path.resolve()}")


if __name__ == "__main__":
    build_pdf(OUTPUT_PATH)
