-- Prahari compliance-automation schema
-- SQLite for MVP; every column here maps cleanly onto a Postgres table if this
-- needs to grow into a multi-tenant product later (add an org_id FK everywhere).

CREATE TABLE IF NOT EXISTS org_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),   -- single-row table for MVP (one org)
    org_name TEXT NOT NULL,
    sector TEXT,
    address TEXT,
    poc_name TEXT,
    poc_role TEXT,
    poc_contact TEXT,
    poc_email TEXT,
    dpo_name TEXT,
    dpo_contact TEXT,
    dpo_email TEXT
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Reporter Information (mirrors CERT-In Incident Reporting Form)
    reporter_role TEXT,              -- 'affected_entity' | 'reporting_for_other'
    affected_entity_name TEXT,       -- only if different from org_profile

    -- Basic Incident Details
    incident_types TEXT,             -- JSON array of selected category codes
    incident_type_other TEXT,
    is_critical_system INTEGER DEFAULT 0,
    critical_details TEXT,

    -- Basic Information of Affected System
    domain_url TEXT,
    ip_address TEXT,
    operating_system TEXT,
    make_model_cloud TEXT,
    affected_application TEXT,
    location_city TEXT,
    location_region TEXT,
    location_country TEXT,
    network_isp TEXT,

    -- Timing -- this is what drives every compliance clock
    occurrence_datetime TEXT,        -- ISO 8601, when the incident happened (if known)
    detection_datetime TEXT NOT NULL,-- ISO 8601, when it was noticed -- clocks start here

    description TEXT,

    -- DPDP-specific fields (personal-data-breach notification content)
    data_categories_affected TEXT,
    estimated_individuals_affected INTEGER,
    likely_consequences TEXT,
    mitigation_measures TEXT,

    -- Compliance tracking -- the actual audit trail
    cert_in_reported_at TEXT,
    dpdp_initial_reported_at TEXT,
    dpdp_detailed_reported_at TEXT,

    status TEXT DEFAULT 'open',      -- open | partially_reported | fully_reported | closed
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS log_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- e.g. "ERP server", "Firewall", "Email gateway"
    monitoring_start_date TEXT NOT NULL,  -- ISO date -- when continuous logging began
    notes TEXT
);
