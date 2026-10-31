"""Render a saved full-history Web Analytics JSON export without fetching new data."""

import argparse
from datetime import date, datetime, timedelta
from html import escape
from io import BytesIO
import json
import math
import os
from pathlib import Path

from export import ExportError
from human_report import atomic_write


def render_pdf(report):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph

    if report.get("status") != "ok" or report.get("filter") != {"bot": 0}:
        raise ExportError("Expected a successful bot-filtered full-history export")
    start = datetime.fromisoformat(report["window_start"])
    end = datetime.fromisoformat(report["window_end_exclusive"])
    data = report["data"]
    by_day = {date.fromisoformat(r["dimensions"]["date"]): r for r in data["daily"]}
    days = []
    day = start.date()
    while day <= (end - timedelta(microseconds=1)).date():
        row = by_day.get(day, {"count": 0, "sum": {"visits": 0}})
        partial = start > start.replace(hour=0, minute=0, second=0, microsecond=0) and day == start.date()
        partial = partial or (day == end.date() and end.time().isoformat() != "00:00:00")
        days.append((day, row["sum"]["visits"], row["count"], partial))
        day += timedelta(days=1)
    if not days:
        raise ExportError("Empty reporting window")
    total = data["totals"][0]
    rows_per_column, columns = 34, 3
    per_page = rows_per_column * columns
    pages = 1 + math.ceil(len(days) / per_page)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("500nits - full-history visits and daily counts")
    pdf.setAuthor("500nits")
    width, height = A4
    margin = 42
    ink, muted, accent, rule = map(colors.HexColor, ["#172c32", "#58676c", "#176a68", "#d9e2e3"])

    def text(x, y, value, size=10, bold=False, color=ink, right=False):
        pdf.setFillColor(color)
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        draw = pdf.drawRightString if right else pdf.drawString
        draw(x, y, str(value).encode("latin-1", "replace").decode("latin-1"))

    def paragraph(value, y, size=9):
        p = Paragraph(escape(value), ParagraphStyle("note", fontName="Helvetica", fontSize=size,
                                                  leading=size*1.4, textColor=muted))
        _, h = p.wrap(width-2*margin, 200)
        p.drawOn(pdf, margin, y-h)
        return y-h

    def footer(number):
        text(margin, 27, "Data fetched " + report["generated_at"][:19].replace("T", " ") + " UTC", 7, color=muted)
        text(width-margin, 27, f"{number} / {pages}", 8, color=muted, right=True)

    def table(title, rows, x, y, w):
        text(x, y, title, 11, True)
        pdf.setStrokeColor(rule); pdf.line(x, y-10, x+w, y-10)
        if not rows:
            text(x, y-29, "No qualifying visits", 9, color=muted)
        for i, (label, value) in enumerate(rows[:5]):
            label = label.encode("latin-1", "replace").decode("latin-1")
            while stringWidth(label, "Helvetica", 9) > w-65:
                label = label[:-4] + "..."
            text(x, y-29-i*20, label, 9)
            text(x+w, y-29-i*20, f"{value:,.0f}", 9, right=True)

    text(margin, height-46, "500nits", 15, True, accent)
    text(margin, height-82, "Full-history visits", 26, True)
    text(margin, height-104, start.strftime("%d %b %Y %H:%M") + " - " + end.strftime("%d %b %Y %H:%M UTC"), 10, color=muted)
    text(margin, height-122, "500nits.com and its measured subdomains", 9, color=muted)
    text(margin, height-158, "ESTIMATED HUMAN VISITS", 9, True, muted)
    text(margin, height-201, f"{total['sum']['visits']:,.0f}", 36, True)
    text(width/2+10, height-158, "FILTERED PAGE VIEWS", 9, True, muted)
    text(width/2+10, height-201, f"{total['count']:,.0f}", 36, True)
    text(margin, height-232, "Estimated visits per UTC day", 11, True)
    text(margin, height-248, "One bar = one date. Read its height against the numbered scale.", 9, color=muted)
    chart_x, chart_y = margin+32, height-363
    chart_w, chart_h = width-margin-chart_x, 96
    values = [r[1] for r in days]
    tick = max(1, math.ceil(max(values)/4))
    maximum = tick*4
    for value in range(0, maximum+1, tick):
        y = chart_y+chart_h*value/maximum
        pdf.setStrokeColor(rule); pdf.setLineWidth(.5)
        pdf.line(chart_x, y, width-margin, y)
        text(chart_x-7, y-3, f"{value:,}", 8, color=muted, right=True)
    bar_w = chart_w/len(days)
    pdf.setFillColor(accent)
    for i, value in enumerate(values):
        if value:
            pdf.rect(chart_x+i*bar_w+.15, chart_y, max(.5, bar_w-.3), chart_h*value/maximum, stroke=0, fill=1)
    last_label_x = -100
    for i, (day, *_rest) in enumerate(days):
        if day.day == 1 or (i == 0 and day.day < 25):
            x = chart_x+i*bar_w
            if x-last_label_x >= 40 and x < width-margin-25:
                text(x, chart_y-14, day.strftime("%b"), 8, color=muted)
                last_label_x = x
    peak = days[values.index(max(values))]
    paragraph(f"Peak: {peak[1]:,.0f} estimated visits on {peak[0]:%d %b %Y}. A height of 20 means about 20 arrivals that day, not 20 unique people. Exact returned daily estimates are on the following pages.", height-389, 8)
    col_w = (width-2*margin-28)/2
    positive = lambda key: [r for r in data[key] if r["sum"]["visits"] > 0]
    table("Top sites / visits", [(r["dimensions"]["requestHost"], r["sum"]["visits"]) for r in positive("sites")], margin, height-439, col_w)
    table("Top countries / visits", [(r["dimensions"]["countryName"] or "Unknown", r["sum"]["visits"]) for r in positive("countries")], margin+col_w+28, height-439, col_w)
    table("Top entry pages / visits", [(r["dimensions"]["requestHost"]+r["dimensions"]["requestPath"], r["sum"]["visits"]) for r in positive("pages")], margin, height-587, width-2*margin)
    paragraph("Cloudflare Web Analytics, Exclude Bots (bot = 0). Bot detection is imperfect; browser blocking can undercount. Counts may be sampled estimates. A separately queried daily report can differ because sampling depends on the query window. First and last days are partial in this export.", 88, 8)
    footer(1); pdf.showPage()

    for offset in range(0, len(days), per_page):
        batch = days[offset:offset+per_page]
        text(margin, height-46, "500nits", 15, True, accent)
        text(margin, height-80, "Day-by-day counts", 25, True)
        text(margin, height-101, f"{batch[0][0]:%d %b %Y} - {batch[-1][0]:%d %b %Y} | UTC", 10, color=muted)
        paragraph("Read each column from top to bottom, then move right. Visits are estimated arrivals; views are filtered page loads. Both use the same saved, bot-filtered dataset as the chart.", height-115, 9)
        gap = 20
        column_w = (width-2*margin-gap*(columns-1))/columns
        for col in range(columns):
            subset = batch[col*rows_per_column:(col+1)*rows_per_column]
            if not subset:
                continue
            x, y = margin+col*(column_w+gap), height-173
            text(x, y, "Date", 9, True)
            text(x+column_w-39, y, "Visits", 9, True, right=True)
            text(x+column_w, y, "Views", 9, True, right=True)
            pdf.setStrokeColor(rule); pdf.line(x, y-8, x+column_w, y-8)
            for i, (day, visits, views, partial) in enumerate(subset):
                row_y = y-24-i*17
                color = ink if visits or views else muted
                text(x, row_y, day.strftime("%d %b") + (" *" if partial else ""), 9, color=color)
                text(x+column_w-39, row_y, f"{visits:,.0f}", 9, bold=bool(visits), color=color, right=True)
                text(x+column_w, row_y, f"{views:,.0f}", 9, color=color, right=True)
        paragraph("0 = no qualifying measurements returned for that date; it does not prove nobody visited. * = partial UTC day at the export boundary. Sampling can produce rounded estimates and can miss low-volume dates. Visits count arrivals, so the same person can contribute more than one visit.", 78, 8)
        footer(2+offset//per_page); pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Private full-history JSON export")
    parser.add_argument("--output", type=Path, help="Defaults to the matching PDF")
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(".pdf")
    if output.suffix.lower() != ".pdf":
        parser.error("Output must end in .pdf")
    os.umask(0o077)
    report = json.loads(args.input.read_text())
    content = render_pdf(report)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_write(output, content)
    print(output.resolve())


if __name__ == "__main__":
    main()
