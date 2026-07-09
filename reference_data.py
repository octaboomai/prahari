"""
Reference data pulled directly from CERT-In's published Incident Reporting Form
(Annexure I categories), so the intake form and generated report use language
CERT-In's own reviewers already recognize.
"""

CERT_IN_INCIDENT_TYPES = [
    ("scanning_probing", "Targeted scanning / probing of critical networks or systems"),
    ("compromise_critical", "Compromise of critical systems or information"),
    ("unauthorised_access", "Unauthorised access of IT systems or data"),
    ("defacement", "Defacement or intrusion into a website"),
    ("malicious_code", "Malicious code attack (virus / worm / trojan / ransomware / cryptominer)"),
    ("server_attack", "Attack on servers (database, mail, DNS) or network devices (routers)"),
    ("identity_phishing", "Identity theft, spoofing, or phishing attack"),
    ("dos_ddos", "DoS / DDoS attack"),
    ("critical_infra", "Attack on critical infrastructure, SCADA/OT systems, or wireless networks"),
    ("app_attack", "Attack on an application (e-governance, e-commerce, etc.)"),
    ("data_breach", "Data breach"),
    ("data_leak", "Data leak"),
    ("iot_attack", "Attack on IoT devices or associated systems"),
    ("payment_systems", "Attack or incident affecting digital payment systems"),
    ("malicious_app", "Attack through a malicious mobile app"),
    ("fake_app", "Fake mobile app"),
    ("social_media", "Unauthorised access to social media accounts"),
    ("cloud_systems", "Suspicious activity affecting cloud computing systems"),
    ("emerging_tech", "Suspicious activity affecting Big Data, blockchain, virtual assets, robotics, 3D/4D printing, or drones"),
    ("ai_ml", "Suspicious activity affecting AI/ML systems"),
    ("other", "Other (specify below)"),
]

CERT_IN_TYPE_LABELS = dict(CERT_IN_INCIDENT_TYPES)
