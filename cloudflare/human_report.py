"""Daily browser analytics PDF. No edge-traffic or user-agent fallback."""

from datetime import date, datetime, time, timedelta, timezone
import fcntl
from html import escape
from io import BytesIO
import json
import math
import os
from pathlib import Path
import tempfile
from urllib.request import Request

from export import API, DOMAIN, LOCAL, ExportError


def reporting_day(value=None, now=None):
    today = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).date()
    try:
        day = date.fromisoformat(value) if value else today - timedelta(days=1)
        if value and day.isoformat() != value:
            raise ValueError
    except ValueError:
        raise ExportError("Report date must be YYYY-MM-DD") from None
    if day >= today:
        raise ExportError("Choose a completed UTC day; today is still in progress")
    start = datetime.combine(day, time(), tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def belongs_to_domain(host):
    host = str(host).lower().rstrip(".")
    return host == DOMAIN or host.endswith("." + DOMAIN)


def site_tags(sites, zone_id):
    tags = []
    for site in sites:
        ruleset = site.get("ruleset") or {}
        matches = (ruleset.get("zone_tag") == zone_id or
                   ruleset.get("zone_name") == DOMAIN or
                   any(belongs_to_domain(rule.get("host", "")) for rule in site.get("rules", [])))
        if matches and ruleset.get("enabled") is not False and site.get("site_tag"):
            tags.append(site["site_tag"])
    if not tags:
        raise ExportError("No enabled Web Analytics site was found for 500nits.com. Enable collection before reporting.")
    return sorted(set(tags))


def build_query(account_id, tags, start, end):
    base = ('datetime_geq: ' + json.dumps(start.isoformat()) +
            ', datetime_lt: ' + json.dumps(end.isoformat()) +
            ', siteTag_in: ' + json.dumps(tags) +
            ', OR: [{requestHost: "500nits.com"}, {requestHost_like: "%.500nits.com"}]')
    selections = {
        "totals": (1, None), "hourly": (25, "datetimeHour"),
        "sites": (8, "requestHost"), "pages": (8, "requestHost requestPath"),
        "countries": (6, "countryName"),
    }
    groups = []
    for alias, (limit, fields) in selections.items():
        selection = 'count sum { visits }'
        if fields:
            selection += ' dimensions { ' + fields + ' }'
        groups.append(alias + ': rumPageloadEventsAdaptiveGroups(limit: ' + str(limit) +
                      ', orderBy: [sum_visits_DESC], filter: {' + base + ', bot: 0}) { ' + selection + ' }')
    # Used solely to distinguish no collection from zero qualifying visits. Never displayed as human traffic.
    groups.append('collection: rumPageloadEventsAdaptiveGroups(limit: 1, filter: {' + base + '}) { count }')
    return ('query DailyHumanVisits { viewer { accounts(filter: {accountTag: ' +
            json.dumps(account_id) + '}) { ' + ' '.join(groups) + ' } } }')


def query_account(api, account_id, query):
    request = Request(API + "/graphql", method="POST", data=json.dumps({"query": query}).encode(),
                      headers={"Authorization": "Bearer " + api.token, "Content-Type": "application/json"})
    try:
        response = json.loads(api.read_response(request))
    except ValueError:
        raise ExportError("Invalid analytics response") from None
    if not isinstance(response, dict):
        raise ExportError("Invalid analytics response")
    if response.get("errors"):
        message = "; ".join(str(e.get("message", "Analytics error")) for e in response["errors"])
        raise ExportError(message.replace(api.token, "[redacted]").replace(account_id, "[account]")[:500])
    accounts = ((response.get("data") or {}).get("viewer") or {}).get("accounts")
    if not isinstance(accounts, list) or len(accounts) != 1 or not isinstance(accounts[0], dict):
        raise ExportError("Web Analytics did not return the requested account")
    return accounts[0]


def validate_data(data):
    for name in ["totals", "hourly", "sites", "pages", "countries", "collection"]:
        if not isinstance(data.get(name), list):
            raise ExportError("Incomplete Web Analytics response: " + name)
        for row in data[name]:
            values = [row.get("count")]
            if name != "collection":
                values.append((row.get("sum") or {}).get("visits"))
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
                raise ExportError("Invalid Web Analytics metrics: " + name)
    if len(data["totals"]) > 1 or len(data["collection"]) > 1:
        raise ExportError("Unexpected totals grouping")


def collect(api, start, end):
    zones = [zone for zone in api.listing("/zones", {"name": DOMAIN}) if zone.get("name") == DOMAIN]
    if len(zones) != 1:
        raise ExportError("Expected exactly one accessible 500nits.com zone")
    zone = zones[0]
    account_id = zone["account"]["id"]
    try:
        sites = api.listing("/accounts/" + account_id + "/rum/site_info/list")
    except ExportError as error:
        raise ExportError("Web Analytics site configuration could not be read (" + str(error) +
                          "). Account Settings Read is required.") from None
    tags = site_tags(sites, zone["id"])
    data = query_account(api, account_id, build_query(account_id, tags, start, end))
    validate_data(data)
    collection = sum(row["count"] for row in data.pop("collection"))
    if not collection:
        return {"status": "no_data", "reason": "No browser measurements were recorded for this day. This does not establish zero human visits."}
    if not data["totals"]:
        data["totals"] = [{"count": 0, "sum": {"visits": 0}}]
    return {"status": "ok", "data": data, "configured_site_count": len(tags)}


def render_pdf(report):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
    except ImportError:
        raise ExportError("Install cloudflare/requirements-report.txt in the Python environment used by your daily script") from None

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("500nits daily visits - " + report["date"])
    pdf.setAuthor("500nits")
    width, height = A4
    ink, muted, accent = colors.HexColor("#172c32"), colors.HexColor("#58676c"), colors.HexColor("#176a68")
    margin = 42

    def text(x, y, value, size=10, bold=False, color=ink):
        pdf.setFillColor(color)
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        pdf.drawString(x, y, str(value).encode("latin-1", "replace").decode("latin-1"))

    def paragraph(value, y, size=9, color=muted):
        style = ParagraphStyle("note", fontName="Helvetica", fontSize=size, leading=size*1.45, textColor=color)
        p = Paragraph(escape(value), style)
        _, h = p.wrap(width - 2*margin, 150)
        p.drawOn(pdf, margin, y-h)
        return y-h

    def fit(value, available, size=9):
        value = str(value).encode("latin-1", "replace").decode("latin-1")
        while value and stringWidth(value, "Helvetica", size) > available:
            value = value[:-4] + "..." if len(value) > 4 else ""
        return value

    def table(title, rows, x, y, w):
        text(x, y, title, 11, True)
        pdf.setStrokeColor(colors.HexColor("#d9e2e3")); pdf.line(x, y-10, x+w, y-10)
        y -= 29
        if not rows:
            text(x, y, "No qualifying visits", 9, color=muted)
        for label, value in rows:
            text(x, y, fit(label, w-68), 9)
            pdf.setFont("Helvetica", 9); pdf.setFillColor(ink)
            pdf.drawRightString(x+w, y, f"{value:,.0f}")
            y -= 20

    text(margin, height-46, "500nits", 15, True, accent)
    text(margin, height-82, "Daily visits", 26, True)
    text(margin, height-103, report["date"] + "  |  00:00-24:00 UTC", 10, color=muted)
    text(margin, height-121, "500nits.com and its measured subdomains", 9, color=muted)

    if report["status"] != "ok":
        text(margin, height-180, "Visit data unavailable", 22, True)
        y = paragraph(report["reason"], height-205, 11)
        paragraph("No human visit count has been inferred from raw traffic. Check Web Analytics collection and token access, then rerun this date.", y-25, 10)
    else:
        data = report["data"]
        total = data["totals"][0]
        text(margin, height-174, "ESTIMATED HUMAN VISITS", 9, True, muted)
        text(margin, height-219, f"{total['sum']['visits']:,.0f}", 38, True)
        text(width/2+10, height-174, "FILTERED PAGE VIEWS", 9, True, muted)
        text(width/2+10, height-219, f"{total['count']:,.0f}", 38, True)
        text(margin, height-250, "Visits by hour (UTC)", 11, True)
        hourly = [0]*24
        for row in data["hourly"]:
            dt = datetime.fromisoformat(row["dimensions"]["datetimeHour"].replace("Z", "+00:00"))
            hourly[dt.astimezone(timezone.utc).hour] += row["sum"]["visits"]
        chart_y, chart_h = height-352, 76
        bar_w = (width-2*margin)/24
        maximum = max(hourly) or 1
        pdf.setFillColor(accent)
        for i, value in enumerate(hourly):
            if value:
                pdf.rect(margin+i*bar_w+2, chart_y, bar_w-4, chart_h*value/maximum, stroke=0, fill=1)
        pdf.setStrokeColor(colors.HexColor("#d9e2e3")); pdf.line(margin, chart_y, width-margin, chart_y)
        for i in [0,6,12,18,23]: text(margin+i*bar_w, chart_y-15, f"{i:02d}", 8, color=muted)
        text(margin, chart_y+chart_h+6, f"Peak hour: {max(hourly):,.0f} visits", 8, color=muted)
        col_w = (width-2*margin-28)/2
        sites = [(r["dimensions"]["requestHost"], r["sum"]["visits"]) for r in data["sites"] if r["sum"]["visits"] > 0][:5]
        countries = [(r["dimensions"]["countryName"] or "Unknown", r["sum"]["visits"]) for r in data["countries"] if r["sum"]["visits"] > 0][:5]
        table("Top sites / visits", sites, margin, height-400, col_w)
        table("Top countries / visits", countries, margin+col_w+28, height-400, col_w)
        pages = [(r["dimensions"]["requestHost"]+r["dimensions"]["requestPath"], r["sum"]["visits"]) for r in data["pages"] if r["sum"]["visits"] > 0][:5]
        table("Top entry pages / visits", pages, margin, height-558, width-2*margin)
    paragraph("Source: Cloudflare Web Analytics with Exclude Bots enabled (bot = 0). Known bots are excluded; detection is imperfect and data may be sampled. Browser blocking can undercount. Visits count arrivals, not unique people. Tables show the top five.", 102, 8)
    text(margin, 27, "Generated " + report["generated_at"][:19].replace("T", " ") + " UTC", 7, color=muted)
    pdf.showPage(); pdf.save()
    return buffer.getvalue()


def atomic_write(path, content):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".report-", delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(content); output.flush(); os.fsync(output.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run(api, report_date=None, output=None):
    start, end = reporting_day(report_date)
    path = (output or LOCAL / "reports" / f"500nits-human-visits-{start.date()}.pdf").resolve()
    if path.suffix.lower() != ".pdf":
        raise ExportError("PDF output must end in .pdf")
    # Check the optional dependency before making network calls or replacing an existing report.
    try:
        import reportlab  # noqa: F401
    except ImportError:
        raise ExportError("Install cloudflare/requirements-report.txt in the Python environment used by your daily script") from None
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.with_suffix(".lock").open("a") as lock:
        os.chmod(lock.name, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExportError("Another process is generating this report") from None
        report = {
            "date": str(start.date()), "domain": DOMAIN,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_start": start.isoformat(), "window_end_exclusive": end.isoformat(),
            "source": "Cloudflare Web Analytics / rumPageloadEventsAdaptiveGroups",
            "filter": {"bot": 0}, "interpretation": "Estimated human visits; not verified individuals.",
        }
        try:
            report.update(collect(api, start, end))
        except ExportError as error:
            report.update(status="unavailable", reason=str(error))
        content = render_pdf(report)
        atomic_write(path, content)
        atomic_write(path.with_suffix(".json"), (json.dumps(report, indent=2, sort_keys=True)+"\n").encode())
    print(path)
    if report["status"] != "ok":
        import sys
        print("Human visits unavailable: " + report["reason"], file=sys.stderr)
        return 2
    return 0
