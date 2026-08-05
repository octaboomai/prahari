"""
The dual-clock engine. This is the actual product.

Every real breach that involves both a cybersecurity incident AND personal
data can trigger two separate, parallel legal obligations in India:

  1. CERT-In (IT Act, Section 70B): report within 6 hours of noticing the
     incident. Fixed, hard deadline.
  2. DPDP Act, 2023 (Data Protection Board): notify the Board "without delay"
     (no fixed hour count -- treated here as an immediate/soft obligation),
     then file a detailed report within 72 hours.

These are separate regulators, separate forms, separate clocks -- and they
start from the same trigger: the moment the incident is *detected*, not the
moment it happened, and not the moment you've finished investigating it.

Retention: CERT-In requires logs kept 180 days; DPDP requires records kept
at least 365 days. Architecting for 365 days satisfies both at once.
"""

from datetime import datetime, timedelta

CERT_IN_WINDOW_HOURS = 6
DPDP_DETAILED_WINDOW_HOURS = 72

RETENTION_DAYS_CERT_IN = 180
RETENTION_DAYS_DPDP = 365
UNIFIED_RETENTION_DAYS = max(RETENTION_DAYS_CERT_IN, RETENTION_DAYS_DPDP)  # 365


def _parse(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


def _band(remaining_seconds, total_seconds):
    """Classify urgency as a fraction of the total window remaining, not an
    absolute cutoff -- so the 6h clock and the 72h clock feel equally urgent
    at equivalent points in their own window."""
    if remaining_seconds is None:
        return "reported"
    if remaining_seconds <= 0:
        return "breached"
    pct = remaining_seconds / total_seconds
    if pct > 0.5:
        return "ok"
    elif pct > 0.15:
        return "warning"
    else:
        return "critical"


def _clock(deadline: datetime, total_hours: float, reported_at_str, now: datetime):
    total_seconds = total_hours * 3600
    if reported_at_str:
        reported_at = _parse(reported_at_str)
        return {
            "status": "reported",
            "deadline": deadline,
            "reported_at": reported_at,
            "on_time": reported_at <= deadline,
            "remaining_seconds": None,
            "total_seconds": total_seconds,
            "pct_remaining": None,
        }
    remaining = (deadline - now).total_seconds()
    return {
        "status": _band(remaining, total_seconds),
        "deadline": deadline,
        "reported_at": None,
        "on_time": None,
        "remaining_seconds": max(remaining, -remaining if remaining < 0 else remaining),
        "remaining_seconds_signed": remaining,
        "total_seconds": total_seconds,
        "pct_remaining": max(remaining / total_seconds, 0),
    }


def compute_clocks(incident: dict, now: datetime = None) -> dict:
    now = now or datetime.now()
    detected = _parse(incident["detection_datetime"])

    cert_in_deadline = detected + timedelta(hours=CERT_IN_WINDOW_HOURS)
    dpdp_detailed_deadline = detected + timedelta(hours=DPDP_DETAILED_WINDOW_HOURS)

    cert_in = _clock(cert_in_deadline, CERT_IN_WINDOW_HOURS, incident.get("cert_in_reported_at"), now)
    dpdp_detailed = _clock(dpdp_detailed_deadline, DPDP_DETAILED_WINDOW_HOURS, incident.get("dpdp_detailed_reported_at"), now)

    # DPDP's initial Board notice has no fixed hour count ("without delay"),
    # so it doesn't get a countdown ring -- just an open/reported flag.
    dpdp_initial_reported = incident.get("dpdp_initial_reported_at")
    dpdp_initial = {
        "status": "reported" if dpdp_initial_reported else "due_now",
        "reported_at": _parse(dpdp_initial_reported) if dpdp_initial_reported else None,
    }

    # If the incident has been explicitly closed, treat all clocks as reported.
    # This stops client-side setInterval timers from continuing to display an
    # active countdown after the user has closed the incident in the UI.
    if incident.get("status") == "closed":
        reported_at = now
        cert_in = {
            "status": "reported",
            "deadline": cert_in_deadline,
            "reported_at": reported_at,
            "on_time": reported_at <= cert_in_deadline,
            "remaining_seconds": None,
            "total_seconds": CERT_IN_WINDOW_HOURS * 3600,
            "pct_remaining": None,
        }
        dpdp_detailed = {
            "status": "reported",
            "deadline": dpdp_detailed_deadline,
            "reported_at": reported_at,
            "on_time": reported_at <= dpdp_detailed_deadline,
            "remaining_seconds": None,
            "total_seconds": DPDP_DETAILED_WINDOW_HOURS * 3600,
            "pct_remaining": None,
        }
        dpdp_initial = {"status": "reported", "reported_at": reported_at}

    return {
        "detected": detected,
        "cert_in": cert_in,
        "dpdp_initial": dpdp_initial,
        "dpdp_detailed": dpdp_detailed,
    }


def retention_status(log_sources: list, now: datetime = None) -> list:
    now = now or datetime.now()
    results = []
    for src in log_sources:
        start = datetime.fromisoformat(src["monitoring_start_date"])
        days_running = (now - start).days
        compliant_from = start + timedelta(days=UNIFIED_RETENTION_DAYS)
        results.append({
            **src,
            "days_running": days_running,
            "compliant": days_running >= UNIFIED_RETENTION_DAYS,
            "compliant_from": compliant_from,
            "days_until_compliant": max((compliant_from - now).days, 0),
        })
    return results
