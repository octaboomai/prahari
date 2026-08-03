from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db, compliance, reports
from reference_data import CERT_IN_INCIDENT_TYPES

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Prahari -- Breach Compliance Automation")

# Mount static files only if the directory exists
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

db.init_db()


def _incident_with_clocks(incident):
    clocks = compliance.compute_clocks(incident)
    return {"incident": incident, "clocks": clocks}


@app.get("/")
def dashboard(request: Request):
    incidents = db.list_incidents()
    rows = [_incident_with_clocks(i) for i in incidents]
    open_count = sum(1 for i in incidents if i["status"] != "closed")
    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "rows": rows,
        "open_count": open_count,
        "now": datetime.now(),
        "type_labels": {code: label for code, label in CERT_IN_INCIDENT_TYPES},
    })


@app.get("/incidents/new")
def new_incident_form(request: Request):
    return templates.TemplateResponse(request, "incident_form.html", {
        "request": request,
        "incident_types": CERT_IN_INCIDENT_TYPES,
        "now": datetime.now().strftime("%Y-%m-%dT%H:%M"),
    })


@app.post("/incidents")
async def create_incident(request: Request):
    form = await request.form()
    incident_types = form.getlist("incident_types")

    data = {
        "reporter_role": form.get("reporter_role", "affected_entity"),
        "affected_entity_name": form.get("affected_entity_name", ""),
        "incident_types": incident_types,
        "incident_type_other": form.get("incident_type_other", ""),
        "is_critical_system": 1 if form.get("is_critical_system") == "yes" else 0,
        "critical_details": form.get("critical_details", ""),
        "domain_url": form.get("domain_url", ""),
        "ip_address": form.get("ip_address", ""),
        "operating_system": form.get("operating_system", ""),
        "make_model_cloud": form.get("make_model_cloud", ""),
        "affected_application": form.get("affected_application", ""),
        "location_city": form.get("location_city", ""),
        "location_region": form.get("location_region", ""),
        "location_country": form.get("location_country", "India"),
        "network_isp": form.get("network_isp", ""),
        "occurrence_datetime": form.get("occurrence_datetime", "") or None,
        "detection_datetime": form.get("detection_datetime"),
        "description": form.get("description", ""),
        "data_categories_affected": form.get("data_categories_affected", ""),
        "estimated_individuals_affected": int(form.get("estimated_individuals_affected") or 0) or None,
        "likely_consequences": form.get("likely_consequences", ""),
        "mitigation_measures": form.get("mitigation_measures", ""),
    }
    new_id = db.create_incident(data)
    return RedirectResponse(f"/incidents/{new_id}", status_code=303)


@app.get("/incidents/{incident_id}")
def incident_detail(request: Request, incident_id: int):
    incident = db.get_incident(incident_id)
    clocks = compliance.compute_clocks(incident)
    return templates.TemplateResponse(request, "incident_detail.html", {
        "request": request,
        "incident": incident,
        "clocks": clocks,
        "type_labels": {code: label for code, label in CERT_IN_INCIDENT_TYPES},
    })


@app.post("/incidents/{incident_id}/mark/{field}")
def mark_reported(incident_id: int, field: str):
    valid_fields = {"cert_in", "dpdp_initial", "dpdp_detailed"}
    if field in valid_fields:
        db.mark_reported(incident_id, f"{field}_reported_at")
    return RedirectResponse(f"/incidents/{incident_id}", status_code=303)


@app.post("/incidents/{incident_id}/close")
def close_incident(incident_id: int):
    db.close_incident(incident_id)
    return RedirectResponse(f"/incidents/{incident_id}", status_code=303)


@app.get("/incidents/{incident_id}/report/cert-in")
def cert_in_report(request: Request, incident_id: int):
    incident = db.get_incident(incident_id)
    org = db.get_org_profile()
    report = reports.build_cert_in_report(incident, org)
    return templates.TemplateResponse(request, "report_cert_in.html", {
        "request": request, "incident": incident, "report": report,
    })


@app.get("/incidents/{incident_id}/report/cert-in.txt")
def cert_in_report_txt(incident_id: int):
    incident = db.get_incident(incident_id)
    org = db.get_org_profile()
    report = reports.build_cert_in_report(incident, org)
    text = reports.cert_in_report_text(report)
    return PlainTextResponse(text)


@app.get("/incidents/{incident_id}/report/dpdp/{tier}")
def dpdp_report(request: Request, incident_id: int, tier: str):
    incident = db.get_incident(incident_id)
    org = db.get_org_profile()
    report = reports.build_dpdp_report(incident, org, tier)
    return templates.TemplateResponse(request, "report_dpdp.html", {
        "request": request, "incident": incident, "report": report, "tier": tier,
    })


@app.get("/incidents/{incident_id}/report/dpdp/{tier}.txt")
def dpdp_report_txt(incident_id: int, tier: str):
    incident = db.get_incident(incident_id)
    org = db.get_org_profile()
    report = reports.build_dpdp_report(incident, org, tier)
    text = reports.dpdp_report_text(report, tier)
    return PlainTextResponse(text)


@app.get("/settings")
def settings_form(request: Request):
    org = db.get_org_profile()
    return templates.TemplateResponse(request, "org_settings.html", {"org": org})


@app.post("/settings")
async def update_settings(request: Request):
    form = await request.form()
    fields = {
        "org_name": form.get("org_name", ""),
        "sector": form.get("sector", ""),
        "address": form.get("address", ""),
        "poc_name": form.get("poc_name", ""),
        "poc_role": form.get("poc_role", ""),
        "poc_contact": form.get("poc_contact", ""),
        "poc_email": form.get("poc_email", ""),
        "dpo_name": form.get("dpo_name", ""),
        "dpo_contact": form.get("dpo_contact", ""),
        "dpo_email": form.get("dpo_email", ""),
    }
    db.update_org_profile(fields)
    return RedirectResponse("/settings", status_code=303)


@app.get("/log-sources")
def log_sources_page(request: Request):
    sources = compliance.retention_status(db.list_log_sources())
    return templates.TemplateResponse(request, "log_sources.html", {
        "request": request,
        "sources": sources,
        "unified_days": compliance.UNIFIED_RETENTION_DAYS,
        "today": datetime.now().strftime("%Y-%m-%d"),
    })


@app.post("/log-sources")
async def add_log_source(request: Request):
    form = await request.form()
    db.create_log_source(
        form.get("name"), form.get("monitoring_start_date"), form.get("notes", "")
    )
    return RedirectResponse("/log-sources", status_code=303)


@app.post("/log-sources/{source_id}/delete")
def delete_log_source(source_id: int):
    db.delete_log_source(source_id)
    return RedirectResponse("/log-sources", status_code=303)

