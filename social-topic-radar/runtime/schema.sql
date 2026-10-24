-- D1 schema snapshot from production. Schema only; no operational records or secrets.
-- Source: Cloudflare D1 open-topic-radar-v01, 2026-10-24.
-- EXCLUDES Cloudflare-internal _cf_KV table.

CREATE TABLE attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, source_id TEXT NOT NULL, source_url TEXT NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL, collected_at TEXT NOT NULL, item_count INTEGER NOT NULL);

CREATE TABLE evidence(source_id TEXT NOT NULL, canonical_url TEXT NOT NULL, entity_id TEXT NOT NULL, collected_at TEXT NOT NULL, evidence_json TEXT NOT NULL, PRIMARY KEY(source_id,canonical_url));

CREATE TABLE r64_cases(case_id TEXT PRIMARY KEY,event_id TEXT NOT NULL,lane TEXT NOT NULL,search_term TEXT NOT NULL,baseline_match INTEGER NOT NULL CHECK(baseline_match IN (0,1)),baseline_source TEXT NOT NULL,assessment TEXT NOT NULL,checked_at TEXT NOT NULL);

CREATE TABLE r64_events(event_id TEXT PRIMARY KEY,title TEXT NOT NULL,primary_url TEXT NOT NULL,event_date TEXT,source_class TEXT NOT NULL,source_verified TEXT NOT NULL,history_state TEXT NOT NULL,editorial_state TEXT NOT NULL DEFAULT 'research_only',discovery_path TEXT NOT NULL,reviewed_at TEXT NOT NULL,limitations TEXT NOT NULL);

CREATE TABLE r64_lanes(event_id TEXT NOT NULL,lane TEXT NOT NULL CHECK(lane IN ('major_updates','social_signals','quality_archive','cross_source_discovery')),PRIMARY KEY(event_id,lane));

CREATE TABLE r64_links(event_id TEXT NOT NULL,url TEXT NOT NULL,source_role TEXT NOT NULL,access_level TEXT NOT NULL,PRIMARY KEY(event_id,url));

CREATE TABLE r64_metric_history(source_id TEXT NOT NULL,canonical_url TEXT NOT NULL,observed_at TEXT NOT NULL,metric_key TEXT NOT NULL,metric_value REAL NOT NULL,provenance TEXT NOT NULL,PRIMARY KEY(source_id,canonical_url,observed_at,metric_key));

CREATE TABLE r64_run_receipts(run_id TEXT PRIMARY KEY,created_at TEXT NOT NULL,status TEXT NOT NULL,pass INTEGER NOT NULL,results_json TEXT NOT NULL);

CREATE TABLE r65_regression_cases(case_id TEXT PRIMARY KEY,event_id TEXT NOT NULL,original_url TEXT NOT NULL,channel TEXT NOT NULL,source_registered INTEGER NOT NULL,suspected_cause TEXT NOT NULL,observed_from TEXT NOT NULL,expected_auto_discovery INTEGER NOT NULL DEFAULT 1,status TEXT NOT NULL DEFAULT 'failed_current_coverage',checked_date TEXT NOT NULL,notes TEXT NOT NULL);

CREATE TABLE r66_source_additions(source_id TEXT PRIMARY KEY, platform TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL, deployment_version TEXT NOT NULL, deployment_state TEXT NOT NULL, worker_collector_state TEXT NOT NULL, limitations TEXT NOT NULL, updated_at TEXT NOT NULL);

CREATE TABLE r67_active_mode_audit(source_id TEXT NOT NULL,mode TEXT NOT NULL,source_status TEXT NOT NULL,independent_live_test TEXT NOT NULL DEFAULT 'not_run_r67',audit_source TEXT NOT NULL,updated_utc TEXT NOT NULL,PRIMARY KEY(source_id,mode));

CREATE TABLE r74_mode_remediation(source_id TEXT NOT NULL,mode TEXT NOT NULL,baseline_state TEXT NOT NULL,remediation_state TEXT NOT NULL,production_version TEXT NOT NULL,independent_worker_test TEXT NOT NULL DEFAULT 'not_run',updated_utc TEXT NOT NULL,PRIMARY KEY(source_id,mode));

CREATE TABLE r76_live_mode_audit(source_id TEXT NOT NULL, mode TEXT NOT NULL, test_utc TEXT NOT NULL, worker_status TEXT NOT NULL, count_items INTEGER NOT NULL, reported_detail TEXT, updated_by TEXT NOT NULL DEFAULT 'r76_authenticated_worker_browser', PRIMARY KEY(source_id,mode));

CREATE TABLE r76_test_sessions(token_sha256 TEXT PRIMARY KEY, allowed_sources TEXT NOT NULL, valid_until TEXT NOT NULL, uses_remaining INTEGER NOT NULL CHECK(uses_remaining>=0), issued_utc TEXT NOT NULL);

CREATE TABLE r79_date_parse(source_id TEXT NOT NULL,canonical_url TEXT NOT NULL,published_utc TEXT NOT NULL,raw_date TEXT NOT NULL,parse_method TEXT NOT NULL,PRIMARY KEY(source_id,canonical_url));

CREATE TABLE r79_discovery_runs(run_id TEXT PRIMARY KEY,started_utc TEXT NOT NULL,query_group TEXT NOT NULL,sources_tested INTEGER NOT NULL,success_count INTEGER NOT NULL,new_evidence_urls INTEGER NOT NULL,quality_candidate_count INTEGER NOT NULL,limitations TEXT NOT NULL);

CREATE TABLE raw_payloads(sha256 TEXT PRIMARY KEY, bytes BLOB NOT NULL, stored_at TEXT NOT NULL);

CREATE INDEX idx_entity ON evidence(entity_id);

CREATE TRIGGER r64_after_evidence_insert AFTER INSERT ON evidence BEGIN INSERT OR IGNORE INTO r64_metric_history(source_id,canonical_url,observed_at,metric_key,metric_value,provenance) SELECT NEW.source_id,NEW.canonical_url,NEW.collected_at,j.key,CAST(j.value AS REAL),CASE WHEN j.key LIKE 'fx_%' THEN 'third_party_fx' ELSE NEW.source_id END FROM json_each(NEW.evidence_json,'$.metrics') j WHERE j.key IN ('hn_points','hn_comments','github_stars','hf_likes','hf_downloads','hf_trending_score','fx_likes','fx_quotes','fx_replies','fx_reposts','likes','reposts','reactions','comments') AND j.type IN ('integer','real'); END;

CREATE TRIGGER r64_after_evidence_update AFTER UPDATE ON evidence BEGIN INSERT OR IGNORE INTO r64_metric_history(source_id,canonical_url,observed_at,metric_key,metric_value,provenance) SELECT NEW.source_id,NEW.canonical_url,NEW.collected_at,j.key,CAST(j.value AS REAL),CASE WHEN j.key LIKE 'fx_%' THEN 'third_party_fx' ELSE NEW.source_id END FROM json_each(NEW.evidence_json,'$.metrics') j WHERE j.key IN ('hn_points','hn_comments','github_stars','hf_likes','hf_downloads','hf_trending_score','fx_likes','fx_quotes','fx_replies','fx_reposts','likes','reposts','reactions','comments') AND j.type IN ('integer','real'); END;

CREATE VIEW r64_discovery_feed AS SELECT * FROM r64_verified_feed UNION ALL SELECT * FROM r64_unlinked_worker_feed;

CREATE VIEW r64_metric_deltas AS WITH v AS (SELECT source_id,canonical_url,metric_key,provenance,observed_at,metric_value,LAG(metric_value) OVER(PARTITION BY source_id,canonical_url,metric_key ORDER BY observed_at) AS previous_value,LAG(observed_at) OVER(PARTITION BY source_id,canonical_url,metric_key ORDER BY observed_at) AS previous_at FROM r64_metric_history) SELECT *, CASE WHEN previous_value IS NULL THEN 'single_snapshot_not_trend' WHEN metric_value<previous_value THEN 'value_decreased_check_source' ELSE 'two_observations_not_independent_virality_proof' END AS review_state FROM v;

CREATE VIEW r64_unlinked_worker_feed AS SELECT ('worker:'||e.source_id||':'||e.entity_id) AS event_id, CASE WHEN e.source_id IN ('x_explore','hn_top','hn_best','hn_show','bluesky_search','bsky_trends','youtube_fireship','yt_two_minute_papers') THEN 'social_signals' WHEN e.source_id IN ('github_ai','github_agent','github_trending','hf_models_recent','hf_models_trending','hf_spaces_trending','civitai_models','producthunt_feed','betalist','skills_sh') THEN 'quality_archive' WHEN e.source_id IN ('openai_news','anthropic_news','nvidia_ai_blog','huggingface_blog','deepmind_blog','meta_ai_blog','openai_api_changelog','gemini_api_changelog') THEN 'major_updates' ELSE 'cross_source_discovery' END AS lane, json_extract(e.evidence_json,'$.title') AS title,e.canonical_url AS primary_url,json_extract(e.evidence_json,'$.published_at') AS event_date,COALESCE(json_extract(e.evidence_json,'$.evidence_status'),'unverified') AS provenance_level,'worker_evidence_unlinked' AS discovery_path,'research_only' AS editorial_state,'Automatic lane is a source-type routing hint only; not verified topic relevance, virality, publication date or rights' AS limitations,1 AS direct_worker_links,e.source_id AS worker_sources FROM evidence e WHERE NOT EXISTS(SELECT 1 FROM r64_links k WHERE rtrim(lower(k.url),'/')=rtrim(lower(e.canonical_url),'/'));

CREATE VIEW r64_verified_feed AS SELECT e.event_id AS event_id,l.lane AS lane,e.title AS title,e.primary_url AS primary_url,e.event_date AS event_date,e.source_verified AS provenance_level,e.discovery_path AS discovery_path,e.editorial_state AS editorial_state,e.limitations AS limitations,(SELECT COUNT(DISTINCT v.source_id||v.canonical_url) FROM evidence v JOIN r64_links k ON k.event_id=e.event_id AND rtrim(lower(k.url),'/')=rtrim(lower(v.canonical_url),'/')) AS direct_worker_links,(SELECT group_concat(DISTINCT v.source_id) FROM evidence v JOIN r64_links k ON k.event_id=e.event_id AND rtrim(lower(k.url),'/')=rtrim(lower(v.canonical_url),'/')) AS worker_sources FROM r64_events e JOIN r64_lanes l ON l.event_id=e.event_id WHERE e.editorial_state <> 'benchmark_only';

CREATE VIEW r65_coverage_audit AS SELECT b.case_id,b.event_id,b.channel,b.original_url,b.source_registered,b.suspected_cause,b.status,b.checked_date,b.notes,(SELECT COUNT(*) FROM evidence e WHERE lower(rtrim(e.canonical_url,'/'))=lower(rtrim(b.original_url,'/'))) AS matching_worker_evidence,(SELECT COUNT(*) FROM r64_events v WHERE v.event_id=b.event_id AND v.discovery_path LIKE 'r65_chat_%') AS manually_indexed FROM r65_regression_cases b;

CREATE VIEW r66_live_recall AS SELECT c.case_id,c.event_id,c.original_url,c.channel,c.suspected_cause,c.status AS baseline_status,(SELECT COUNT(*) FROM evidence e WHERE lower(rtrim(e.canonical_url,'/'))=lower(rtrim(c.original_url,'/'))) AS original_url_worker_hits,CASE WHEN EXISTS(SELECT 1 FROM evidence e WHERE lower(rtrim(e.canonical_url,'/'))=lower(rtrim(c.original_url,'/'))) THEN 'exact_worker_evidence_found' ELSE 'no_exact_worker_evidence' END AS current_evidence_state FROM r65_regression_cases c;

CREATE VIEW r79_quality_inventory AS
WITH raw AS (
 SELECT e.source_id,e.canonical_url,e.entity_id,e.collected_at,
 json_extract(e.evidence_json,'$.title') AS title,
 json_extract(e.evidence_json,'$.body_excerpt') AS excerpt,
 json_extract(e.evidence_json,'$.content_type') AS content_type,
 json_extract(e.evidence_json,'$.evidence_status') AS evidence_status,
 json_extract(e.evidence_json,'$.mode') AS mode,
 json_extract(e.evidence_json,'$.published_at') AS raw_published_at,
 d.published_utc AS published_utc
 FROM evidence e LEFT JOIN r79_date_parse d ON d.source_id=e.source_id AND d.canonical_url=e.canonical_url
 WHERE EXISTS(SELECT 1 FROM r74_mode_remediation m WHERE m.source_id=e.source_id)
)
SELECT *,length(COALESCE(excerpt,'')) excerpt_chars,
CASE WHEN published_utc IS NULL THEN 'unknown_publication_date'
 WHEN datetime(published_utc)>datetime('now','+1 hour') THEN 'suspicious_future_date'
 WHEN datetime(published_utc)>=datetime('now','-72 hours') THEN 'source_dated_last_72h'
 ELSE 'source_dated_older_than_72h' END freshness_class,
CASE WHEN evidence_status='research_only' THEN 'research_only_not_editorial_verified'
 WHEN content_type IN ('site_discovery','video_public_search_metadata','video_metadata_visuals_not_verified','official_trending_topic_unfiltered','official_token_usage_rank','leaderboard_snapshot','model','space','repository') THEN 'metadata_not_full_body'
 WHEN length(COALESCE(excerpt,''))>=220 THEN 'substantive_excerpt_not_full_article'
 WHEN length(COALESCE(excerpt,''))>=100 THEN 'short_excerpt_not_full_article'
 ELSE 'insufficient_article_text' END content_quality_class,
CASE WHEN content_type IN ('site_discovery','official_program_benefits_snapshot','changelog_snapshot','official_token_usage_rank','leaderboard_snapshot','official_trending_topic_unfiltered') THEN 0
 WHEN length(COALESCE(title,''))<15 THEN 0
 WHEN lower(trim(COALESCE(title,''))) IN ('featured','official','try it now!','see docs','trending (24h)','read more','get started','sign in','view all','español – américa latina') THEN 0
 ELSE 1 END candidate_shape_ok
FROM raw;

CREATE VIEW r79_recent_discovery AS
WITH scored AS (
SELECT source_id,canonical_url,entity_id,collected_at,title,excerpt,mode,content_type,evidence_status,published_utc,freshness_class,content_quality_class,excerpt_chars,
(CASE
 WHEN source_id IN ('openai_news','anthropic_news','deepmind_blog','mistral_ai','nvidia_ai_blog','huggingface_blog','meta_ai_blog','openai_api_changelog','gemini_api_changelog') THEN 45
 WHEN source_id IN ('github_ai','github_agent','github_trending','hf_models_recent','hf_models_trending','hf_spaces_trending','bluesky_search','devto_ai','gitlab_explore','civitai_models','producthunt_feed') THEN 22
 ELSE 10 END
+CASE WHEN content_quality_class='substantive_excerpt_not_full_article' THEN 28 WHEN content_quality_class='short_excerpt_not_full_article' THEN 11 WHEN content_quality_class='insufficient_article_text' THEN -10 ELSE 0 END
+CASE WHEN excerpt_chars>=600 THEN 12 ELSE 0 END
+CASE WHEN lower(title) LIKE '%agent%' OR lower(title) LIKE '%ai %' OR lower(title) LIKE '%model%' OR lower(title) LIKE '%video%' OR lower(title) LIKE '%4k%' OR lower(title) LIKE '%llm%' THEN 8 ELSE 0 END
) as discovery_rank,
ROW_NUMBER() OVER (PARTITION BY canonical_url ORDER BY (CASE WHEN content_quality_class='substantive_excerpt_not_full_article' THEN 4 WHEN content_quality_class='short_excerpt_not_full_article' THEN 3 WHEN content_quality_class='metadata_not_full_body' THEN 2 ELSE 1 END) DESC, excerpt_chars DESC, published_utc DESC) AS duplicate_position
FROM r79_quality_inventory
WHERE candidate_shape_ok=1 AND freshness_class='source_dated_last_72h')
SELECT source_id,canonical_url,entity_id,collected_at,title,excerpt,mode,content_type,evidence_status,published_utc,freshness_class,content_quality_class,excerpt_chars,discovery_rank FROM scored WHERE duplicate_position=1;

CREATE VIEW r81_x_ai_signal_feed AS
SELECT source_id,canonical_url,published_utc,collected_at,
       title,excerpt,mode,content_quality_class,excerpt_chars,
       CASE WHEN mode='F' THEN 'watched_account_update' WHEN mode='D' THEN 'known_post_lookup' ELSE 'limited_public_index_search' END AS signal_origin,
       'third_party_x_content_upstream_unverified' AS evidence_boundary,
       'NOT_X_TRENDS_NOT_FULL_PLATFORM_COVERAGE' AS hotness_boundary,
       CASE WHEN lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%model%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%agent%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%ai %'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%claude%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%gemini%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%gpt%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%codex%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%nemotron%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%mistral%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%video%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%llm%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%blender%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%frontier%'
          OR lower(coalesce(title,'')||' '||coalesce(excerpt,'')) LIKE '%nvidia%'
       THEN 'ai_keyword_in_visible_text' ELSE 'no_ai_keyword_visible_requires_review' END AS ai_relevance_signal
FROM r79_recent_discovery
WHERE source_id='x_explore' AND mode IN ('F','D','K');

CREATE VIEW r82_x_scoped_hot_feed AS SELECT e.canonical_url, json_extract(e.evidence_json,'$.title') AS title,substr(json_extract(e.evidence_json,'$.body_excerpt'),1,700) AS excerpt, json_extract(e.evidence_json,'$.author') AS author,json_extract(e.evidence_json,'$.published_at') AS published_utc,e.collected_at AS measured_utc,cast(json_extract(e.evidence_json,'$.metrics.fx_likes') AS INTEGER) AS likes,cast(json_extract(e.evidence_json,'$.metrics.fx_reposts') AS INTEGER) AS reposts,cast(json_extract(e.evidence_json,'$.metrics.fx_quotes') AS INTEGER) AS quotes,cast(json_extract(e.evidence_json,'$.metrics.fx_replies') AS INTEGER) AS replies,cast(json_extract(e.evidence_json,'$.metrics.r82_engagement_count') AS INTEGER) AS weighted_engagement,cast(json_extract(e.evidence_json,'$.metrics.r82_72h_velocity_score') AS REAL) AS age_adjusted_score,'five_named_ai_accounts' AS monitoring_scope,'third_party_fx_metrics_unverified_against_x' AS metric_provenance,'NOT_OFFICIAL_X_TRENDS' AS scope_warning FROM evidence e WHERE e.source_id='x_explore' AND json_extract(e.evidence_json,'$.mode')='H' AND json_extract(e.evidence_json,'$.content_type')='monitored_account_high_engagement_post_not_x_trends' AND julianday(json_extract(e.evidence_json,'$.published_at'))>=julianday('now','-72 hours');
