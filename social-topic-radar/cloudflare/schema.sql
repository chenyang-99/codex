-- AI30 V3.2 Cloudflare migration STAGING schema only; collected from live new D1.
-- Old D1 business data and private secrets are NOT part of this public backup.
-- Original source commit: 24a8413586fdc58276df2fb5e2b8a6b769161c3c

CREATE TABLE editorial_review(entity_key TEXT PRIMARY KEY,value_scan_json TEXT,main_reader_value TEXT,value_proof_json TEXT,original_review_status TEXT NOT NULL DEFAULT 'pending',attraction_score INTEGER,spread_score INTEGER,payoff_score INTEGER,credibility_score INTEGER,user_decision TEXT NOT NULL DEFAULT 'unreviewed',publication_status TEXT NOT NULL DEFAULT 'not_published',updated_utc TEXT NOT NULL);

CREATE TABLE entities(entity_key TEXT PRIMARY KEY, canonical_url TEXT NOT NULL, title TEXT NOT NULL, first_seen_utc TEXT NOT NULL, last_seen_utc TEXT NOT NULL, cross_source_count INTEGER NOT NULL DEFAULT 1, source_ids_json TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'research_only');

CREATE TABLE evidence(source_id TEXT NOT NULL, canonical_url TEXT NOT NULL, original_url TEXT NOT NULL, title TEXT NOT NULL, excerpt TEXT, author TEXT, published_utc TEXT, first_seen_utc TEXT NOT NULL, last_seen_utc TEXT NOT NULL, source_scope TEXT NOT NULL DEFAULT 'discovery_only', observed_metrics_json TEXT, raw_json TEXT, PRIMARY KEY(source_id,canonical_url));

CREATE TABLE migrations(version TEXT PRIMARY KEY, applied_utc TEXT NOT NULL);

CREATE TABLE run_source_health(run_id TEXT NOT NULL,source_id TEXT NOT NULL, status TEXT NOT NULL, http_status INTEGER, item_count INTEGER NOT NULL DEFAULT 0, error_text TEXT, checked_utc TEXT NOT NULL, PRIMARY KEY(run_id, source_id));

CREATE TABLE runs(run_id TEXT PRIMARY KEY, trigger_kind TEXT NOT NULL, started_utc TEXT NOT NULL, finished_utc TEXT, status TEXT NOT NULL, feeds_checked INTEGER NOT NULL DEFAULT 0, retrieved INTEGER NOT NULL DEFAULT 0, new_entities INTEGER NOT NULL DEFAULT 0, errors_json TEXT, provenance_commit TEXT NOT NULL);

CREATE TABLE sources(source_id TEXT PRIMARY KEY, name TEXT NOT NULL, feed_url TEXT NOT NULL, kind TEXT NOT NULL, priority INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, created_utc TEXT NOT NULL, last_checked_utc TEXT, last_result TEXT);

CREATE INDEX idx_entities_lastseen ON entities(last_seen_utc DESC);

CREATE INDEX idx_evidence_lastseen ON evidence(last_seen_utc DESC);
