-- Cloudflare production D1 schema snapshot, 2026-10-25, after quality-gate blocker column and private review views.
-- From live sqlite_master; no business data, passwords or user records.
-- Original pre-ban source baseline: 24a8413586fdc58276df2fb5e2b8a6b769161c3c.
-- Public/safe source tree backup; CF remains the only execution environment.

CREATE TABLE editorial_review(entity_key TEXT PRIMARY KEY,value_scan_json TEXT,main_reader_value TEXT,value_proof_json TEXT,original_review_status TEXT NOT NULL DEFAULT 'pending',attraction_score INTEGER,spread_score INTEGER,payoff_score INTEGER,credibility_score INTEGER,user_decision TEXT NOT NULL DEFAULT 'unreviewed',publication_status TEXT NOT NULL DEFAULT 'not_published',updated_utc TEXT NOT NULL, machine_blockers_json TEXT NOT NULL DEFAULT '["missing_nine_value_scan","missing_value_proof","missing_social_pitch","missing_content_values","missing_or_invalid_content_scores","no_recheckable_primary_evidence"]');

CREATE TABLE entities(entity_key TEXT PRIMARY KEY, canonical_url TEXT NOT NULL, title TEXT NOT NULL, first_seen_utc TEXT NOT NULL, last_seen_utc TEXT NOT NULL, cross_source_count INTEGER NOT NULL DEFAULT 1, source_ids_json TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'research_only');

CREATE TABLE evidence(source_id TEXT NOT NULL, canonical_url TEXT NOT NULL, original_url TEXT NOT NULL, title TEXT NOT NULL, excerpt TEXT, author TEXT, published_utc TEXT, first_seen_utc TEXT NOT NULL, last_seen_utc TEXT NOT NULL, source_scope TEXT NOT NULL DEFAULT 'discovery_only', observed_metrics_json TEXT, raw_json TEXT, PRIMARY KEY(source_id,canonical_url));

CREATE TABLE migrations(version TEXT PRIMARY KEY, applied_utc TEXT NOT NULL);

CREATE TABLE run_source_health(run_id TEXT NOT NULL,source_id TEXT NOT NULL, status TEXT NOT NULL, http_status INTEGER, item_count INTEGER NOT NULL DEFAULT 0, error_text TEXT, checked_utc TEXT NOT NULL, PRIMARY KEY(run_id, source_id));

CREATE TABLE runs(run_id TEXT PRIMARY KEY, trigger_kind TEXT NOT NULL, started_utc TEXT NOT NULL, finished_utc TEXT, status TEXT NOT NULL, feeds_checked INTEGER NOT NULL DEFAULT 0, retrieved INTEGER NOT NULL DEFAULT 0, new_entities INTEGER NOT NULL DEFAULT 0, errors_json TEXT, provenance_commit TEXT NOT NULL);

CREATE TABLE sources(source_id TEXT PRIMARY KEY, name TEXT NOT NULL, feed_url TEXT NOT NULL, kind TEXT NOT NULL, priority INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, created_utc TEXT NOT NULL, last_checked_utc TEXT, last_result TEXT);

CREATE INDEX idx_entities_lastseen ON entities(last_seen_utc DESC);

CREATE INDEX idx_evidence_lastseen ON evidence(last_seen_utc DESC);

CREATE VIEW cf_research_review_queue AS SELECT e.entity_key AS entity_key,e.title AS title,e.canonical_url AS source_url,e.first_seen_utc AS first_seen_utc,e.last_seen_utc AS last_seen_utc,e.cross_source_count AS cross_source_count,e.source_ids_json AS source_ids_json,r.original_review_status AS editorial_state,r.main_reader_value AS verified_primary_value,r.value_proof_json AS primary_value_proof,r.attraction_score AS attraction_score,r.spread_score AS spread_score,r.payoff_score AS payoff_score,r.credibility_score AS credibility_score,r.user_decision AS user_decision,r.publication_status AS publication_status, CASE WHEN r.original_review_status='pending' OR r.main_reader_value IS NULL OR r.value_proof_json IS NULL OR r.attraction_score IS NULL OR r.spread_score IS NULL OR r.payoff_score IS NULL OR r.credibility_score IS NULL THEN 'evidence_and_human_review_required' ELSE 'requires_original_source_and_visual_review' END AS mechanical_qa_state, 'No automatic approval or publication permitted' AS human_gate FROM entities e JOIN editorial_review r ON e.entity_key=r.entity_key;

CREATE VIEW cf_source_health_overview AS SELECT s.source_id,s.name,s.kind,s.enabled,s.priority,s.last_checked_utc,s.last_result,(SELECT h.status FROM run_source_health h WHERE h.source_id=s.source_id ORDER BY h.checked_utc DESC LIMIT 1) AS last_probe_status,(SELECT h.item_count FROM run_source_health h WHERE h.source_id=s.source_id ORDER BY h.checked_utc DESC LIMIT 1) AS last_probe_items,(SELECT h.error_text FROM run_source_health h WHERE h.source_id=s.source_id ORDER BY h.checked_utc DESC LIMIT 1) AS last_probe_error FROM sources s;
