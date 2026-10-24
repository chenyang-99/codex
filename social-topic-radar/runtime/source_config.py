SOURCES = [
 {
  "source_id": "hn_top",
  "platform": "hackernews",
  "kind": "hn_topstories",
  "url": "https://hacker-news.firebaseio.com/v0/topstories.json",
  "allowed_hosts": [
   "hacker-news.firebaseio.com"
  ],
  "modes": [
   "H",
   "D"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "historical_single_item_verified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "github_ai",
  "platform": "github",
  "kind": "github_search",
  "url": "https://api.github.com/search/repositories?q=topic%3Aartificial-intelligence&sort=updated&order=desc&per_page=10",
  "allowed_hosts": [
   "api.github.com"
  ],
  "modes": [
   "K"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "arxiv_csai",
  "platform": "arxiv",
  "kind": "rss",
  "url": "https://export.arxiv.org/rss/cs.AI",
  "allowed_hosts": [
   "export.arxiv.org"
  ],
  "modes": [
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "hn_show",
  "platform": "hackernews",
  "kind": "hn_topstories",
  "url": "https://hacker-news.firebaseio.com/v0/showstories.json",
  "allowed_hosts": [
   "hacker-news.firebaseio.com"
  ],
  "modes": [
   "H",
   "D"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "producthunt_feed",
  "platform": "producthunt",
  "kind": "rss",
  "url": "https://www.producthunt.com/feed",
  "allowed_hosts": [
   "www.producthunt.com"
  ],
  "modes": [
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "youtube_fireship",
  "platform": "youtube",
  "kind": "rss",
  "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA",
  "allowed_hosts": [
   "www.youtube.com"
  ],
  "modes": [
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "linuxdo_top",
  "platform": "linuxdo",
  "kind": "rss",
  "url": "https://linux.do/top.rss?period=daily",
  "allowed_hosts": [
   "linux.do"
  ],
  "modes": [
   "F",
   "H"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "github_agent",
  "platform": "github",
  "kind": "github_search",
  "url": "https://api.github.com/search/repositories?q=topic%3Aai-agent&sort=updated&order=desc&per_page=8",
  "allowed_hosts": [
   "api.github.com"
  ],
  "modes": [
   "K"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "arxiv_csml",
  "platform": "arxiv",
  "kind": "rss",
  "url": "https://export.arxiv.org/rss/cs.LG",
  "allowed_hosts": [
   "export.arxiv.org"
  ],
  "modes": [
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "yt_two_minute_papers",
  "platform": "youtube",
  "kind": "rss",
  "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg",
  "allowed_hosts": [
   "www.youtube.com"
  ],
  "modes": [
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "hf_models_trending",
  "platform": "huggingface",
  "kind": "hf_repo_list",
  "repo_type": "model",
  "result_mode": "H",
  "url": "https://huggingface.co/api/models?sort=trendingScore&limit=8",
  "allowed_hosts": [
   "huggingface.co"
  ],
  "modes": [
   "H",
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "hf_models_recent",
  "platform": "huggingface",
  "kind": "hf_repo_list",
  "repo_type": "model",
  "result_mode": "K",
  "url": "https://huggingface.co/api/models?sort=createdAt&direction=-1&limit=8",
  "allowed_hosts": [
   "huggingface.co"
  ],
  "modes": [
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "hf_spaces_trending",
  "platform": "huggingface",
  "kind": "hf_repo_list",
  "repo_type": "space",
  "result_mode": "H",
  "url": "https://huggingface.co/api/spaces?sort=trendingScore&limit=8",
  "allowed_hosts": [
   "huggingface.co"
  ],
  "modes": [
   "H",
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "early_original"
 },
 {
  "source_id": "reddit_localllama_hot",
  "platform": "reddit",
  "kind": "reddit_listing",
  "url": "https://www.reddit.com/r/LocalLLaMA/hot.json?limit=8",
  "allowed_hosts": [
   "www.reddit.com"
  ],
  "modes": [
   "H",
   "F"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "bsky_trends",
  "platform": "bluesky",
  "kind": "bsky_trends",
  "url": "https://api.bsky.app/xrpc/app.bsky.unspecced.getTrends?limit=25",
  "allowed_hosts": [
   "api.bsky.app"
  ],
  "modes": [
   "H"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "hot_snapshot_only_no_native_subscription",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "hn_best",
  "platform": "hackernews",
  "kind": "hn_topstories",
  "url": "https://hacker-news.firebaseio.com/v0/beststories.json",
  "allowed_hosts": [
   "hacker-news.firebaseio.com"
  ],
  "modes": [
   "H",
   "D"
  ],
  "deployment_stage": "adapter_configured",
  "access_status": "worker_runtime_unverified",
  "planned_signal": "hot_signal"
 },
 {
  "source_id": "x_explore",
  "platform": "x",
  "kind": "x_hybrid_fx",
  "url": "https://x.com/explore",
  "allowed_hosts": [
   "x.com"
  ],
  "modes": [
   "D",
   "K",
   "F",
   "H"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S127",
  "access_status": "r21_tavily_keyless_worker_K_auto_index_verified_D_F_H_prior_live_global_complete_unavailable",
  "deployment_stage": "adapter_configured",
  "verification_scope": "K first tries Fx third-party search (currently 404), then anonymous Tavily public index search and individually refetches X post via Fx D; fallback keyword matching watched RSS; no full X coverage or guaranteed recency; no Tavily search result cached, no paid key or cron",
  "provider_detail": "FxEmbed v2 opt-in third-party; original X session provenance not verified",
  "official_fallback": "X Publish oEmbed D"
 },
 {
  "source_id": "threads_search",
  "platform": "threads",
  "kind": "oembed_direct",
  "url": "https://www.threads.net/search?q=AI",
  "allowed_hosts": [
   "www.threads.net"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S130",
  "access_status": "official_direct_post_oembed_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "verification_scope": "known_public_post_url_only"
 },
 {
  "source_id": "tiktok_explore",
  "platform": "tiktok",
  "kind": "oembed_direct",
  "url": "https://www.tiktok.com/explore",
  "allowed_hosts": [
   "www.tiktok.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S134",
  "access_status": "official_direct_post_oembed_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "verification_scope": "known_public_post_url_only"
 },
 {
  "source_id": "instagram_explore",
  "platform": "instagram",
  "kind": "oembed_direct",
  "url": "https://www.instagram.com/explore/",
  "allowed_hosts": [
   "www.instagram.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S135",
  "access_status": "official_direct_post_oembed_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "verification_scope": "known_public_post_url_only"
 },
 {
  "source_id": "discord_servers",
  "platform": "discord",
  "kind": "html_index",
  "url": "https://discord.com/servers",
  "allowed_hosts": [
   "discord.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S138",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/servers/"
  ]
 },
 {
  "source_id": "civitai_models",
  "platform": "civitai",
  "kind": "civitai_models",
  "url": "https://civitai.com/api/v1/models?limit=8&sort=Newest",
  "allowed_hosts": [
   "civitai.com"
  ],
  "modes": [
   "H",
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S193",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "telegram_public_ai",
  "platform": "telegram",
  "kind": "telegram_public_posts",
  "url": "https://t.me/s/Artificial_intelligence_in",
  "allowed_hosts": [
   "t.me"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S137",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/s/"
  ]
 },
 {
  "source_id": "openrouter_rankings",
  "platform": "openrouter",
  "kind": "public_token_rankings",
  "url": "https://openrouter.ai/rankings",
  "allowed_hosts": [
   "openrouter.ai"
  ],
  "modes": [
   "H"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S306",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/models/"
  ]
 },
 {
  "source_id": "replicate_explore",
  "platform": "replicate",
  "kind": "html_index",
  "url": "https://replicate.com/explore",
  "allowed_hosts": [
   "replicate.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S307",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/"
  ]
 },
 {
  "source_id": "fal_explore",
  "platform": "fal",
  "kind": "html_index",
  "url": "https://fal.ai/explore",
  "allowed_hosts": [
   "fal.ai"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S308",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/models/"
  ]
 },
 {
  "source_id": "skills_sh",
  "platform": "skills",
  "kind": "html_index",
  "url": "https://www.skills.sh/trending",
  "allowed_hosts": [
   "www.skills.sh"
  ],
  "modes": [
   "H",
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/"
  ]
 },
 {
  "source_id": "behance_ai",
  "platform": "behance",
  "kind": "html_index",
  "url": "https://www.behance.net/search/projects/generative%20ai",
  "allowed_hosts": [
   "www.behance.net"
  ],
  "modes": [
   "K",
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S141",
  "access_status": "public_search_index_worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/gallery/"
  ],
  "verification_scope": "project_links_only_no_hotness"
 },
 {
  "source_id": "artstation_ai",
  "platform": "artstation",
  "kind": "html_index",
  "url": "https://www.artstation.com/search?query=AI&sort_by=relevance",
  "allowed_hosts": [
   "www.artstation.com"
  ],
  "modes": [
   "K",
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S209",
  "access_status": "public_search_index_worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/artwork/"
  ],
  "verification_scope": "artwork_links_only_no_hotness"
 },
 {
  "source_id": "github_student_pack",
  "platform": "github_education",
  "kind": "html_index",
  "url": "https://education.github.com/pack",
  "allowed_hosts": [
   "education.github.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "benefit_signal",
  "r8_id": "",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/pack"
  ]
 },
 {
  "source_id": "google_startups",
  "platform": "google_startups",
  "kind": "official_startup_benefits",
  "url": "https://cloud.google.com/startup/benefits",
  "allowed_hosts": [
   "cloud.google.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "benefit_signal",
  "r8_id": "",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/startup/"
  ]
 },
 {
  "source_id": "microsoft_startups",
  "platform": "microsoft_startups",
  "kind": "html_index",
  "url": "https://learn.microsoft.com/en-us/startups/benefits",
  "allowed_hosts": [
   "learn.microsoft.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "benefit_signal",
  "r8_id": "",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/en-us/startups/"
  ]
 },
 {
  "source_id": "appsumo_ai",
  "platform": "appsumo",
  "kind": "html_index",
  "url": "https://appsumo.com/",
  "allowed_hosts": [
   "appsumo.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "benefit_signal",
  "r8_id": "",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/products/"
  ]
 },
 {
  "source_id": "linkedin_public",
  "platform": "linkedin",
  "kind": "registry_only",
  "url": "https://www.linkedin.com/feed/",
  "allowed_hosts": [
   "www.linkedin.com"
  ],
  "modes": [],
  "planned_signal": "hot_signal",
  "r8_id": "S132",
  "access_status": "login_required",
  "deployment_stage": "registered_only"
 },
 {
  "source_id": "pinterest_ai",
  "platform": "pinterest",
  "kind": "rss",
  "url": "https://newsroom.pinterest.com/feed/news.xml",
  "allowed_hosts": [
   "newsroom.pinterest.com"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "official_news_signal",
  "r8_id": "S136",
  "access_status": "official_newsroom_rss_configured_worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "verification_scope": "official_pinterest_newsroom_articles_only_not_pin_search_or_trends",
  "source_url_citation": "https://newsroom.pinterest.com/contact/"
 },
 {
  "source_id": "substack_ai",
  "platform": "substack",
  "kind": "rss",
  "url": "https://importai.substack.com/feed",
  "allowed_hosts": [
   "importai.substack.com"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S139",
  "access_status": "official_publication_feed_unverified",
  "deployment_stage": "adapter_configured"
 },
 {
  "source_id": "medium_ai",
  "platform": "medium",
  "kind": "rss",
  "url": "https://medium.com/feed/tag/artificial-intelligence",
  "allowed_hosts": [
   "medium.com"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S116",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "devto_ai",
  "platform": "devto",
  "kind": "devto_articles",
  "url": "https://dev.to/api/articles?tag=ai&per_page=8",
  "allowed_hosts": [
   "dev.to"
  ],
  "modes": [
   "K",
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S114",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "indiehackers",
  "platform": "indiehackers",
  "kind": "html_index",
  "url": "https://www.indiehackers.com/",
  "allowed_hosts": [
   "www.indiehackers.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S102",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/post/"
  ]
 },
 {
  "source_id": "betalist",
  "platform": "betalist",
  "kind": "rss",
  "url": "https://betalist.com/startups/feed_original",
  "allowed_hosts": [
   "betalist.com"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S104",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/startups/"
  ]
 },
 {
  "source_id": "theresanaiforthat",
  "platform": "theresanaiforthat",
  "kind": "html_index",
  "url": "https://theresanaiforthat.com/just-launched/",
  "allowed_hosts": [
   "theresanaiforthat.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S094",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/ai/"
  ]
 },
 {
  "source_id": "futurepedia",
  "platform": "futurepedia",
  "kind": "html_index",
  "url": "https://www.futurepedia.io/whats-new",
  "allowed_hosts": [
   "www.futurepedia.io"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S095",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/tool/",
   "/ai-tools/"
  ]
 },
 {
  "source_id": "arena_leaderboard",
  "platform": "arena",
  "kind": "arena_hf_rows",
  "url": "https://datasets-server.huggingface.co/rows?dataset=lmarena-ai%2Fleaderboard-dataset&config=agent&split=latest&offset=0&length=3",
  "allowed_hosts": [
   "datasets-server.huggingface.co"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S067",
  "access_status": "official_dataset_snapshot_unverified",
  "deployment_stage": "adapter_configured"
 },
 {
  "source_id": "artificial_analysis",
  "platform": "artificial_analysis",
  "kind": "aa_v2_free_api",
  "url": "https://artificialanalysis.ai/api/v2/language/models/free?page=1",
  "allowed_hosts": [
   "artificialanalysis.ai"
  ],
  "modes": [
   "K"
  ],
  "planned_signal": "benchmark_snapshot",
  "r8_id": "S068",
  "access_status": "official_free_api_code_ready_credential_required_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "verification_scope": "free_language_image_video_snapshot_only_no_anonymous_scraping",
  "credential_binding": "AA_API_KEY; Cloudflare encrypted server-side secret only; not installed"
 },
 {
  "source_id": "openreview",
  "platform": "openreview",
  "kind": "html_index",
  "url": "https://openreview.net/",
  "allowed_hosts": [
   "openreview.net"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S047",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/forum"
  ]
 },
 {
  "source_id": "ollama_library",
  "platform": "ollama",
  "kind": "html_index",
  "url": "https://ollama.com/library",
  "allowed_hosts": [
   "ollama.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S082",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/library/"
  ]
 },
 {
  "source_id": "kaggle_models",
  "platform": "kaggle",
  "kind": "html_index",
  "url": "https://www.kaggle.com/models",
  "allowed_hosts": [
   "www.kaggle.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S075",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/models/"
  ]
 },
 {
  "source_id": "gitlab_explore",
  "platform": "gitlab",
  "kind": "gitlab_projects",
  "url": "https://gitlab.com/api/v4/projects?search=ai&per_page=8&order_by=last_activity_at",
  "allowed_hosts": [
   "gitlab.com"
  ],
  "modes": [
   "K",
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S079",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "openai_news",
  "platform": "openai",
  "kind": "rss",
  "url": "https://openai.com/news/rss.xml",
  "allowed_hosts": [
   "openai.com"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S001",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "anthropic_news",
  "platform": "anthropic",
  "kind": "html_index",
  "url": "https://www.anthropic.com/news",
  "allowed_hosts": [
   "www.anthropic.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S002",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/news/"
  ]
 },
 {
  "source_id": "deepmind_blog",
  "platform": "google_deepmind",
  "kind": "html_index",
  "url": "https://deepmind.google/blog/",
  "allowed_hosts": [
   "deepmind.google"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S003",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/blog/"
  ]
 },
 {
  "source_id": "meta_ai_blog",
  "platform": "meta",
  "kind": "html_index",
  "url": "https://ai.meta.com/blog/",
  "allowed_hosts": [
   "ai.meta.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S005",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/blog/"
  ]
 },
 {
  "source_id": "nvidia_ai_blog",
  "platform": "nvidia",
  "kind": "rss",
  "url": "https://blogs.nvidia.com/feed/",
  "allowed_hosts": [
   "blogs.nvidia.com"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S008",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "mistral_ai",
  "platform": "mistral",
  "kind": "html_index",
  "url": "https://mistral.ai/news/",
  "allowed_hosts": [
   "mistral.ai"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S015",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/news/"
  ]
 },
 {
  "source_id": "huggingface_blog",
  "platform": "huggingface",
  "kind": "rss",
  "url": "https://huggingface.co/blog/feed.xml",
  "allowed_hosts": [
   "huggingface.co"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "early_original",
  "r8_id": "S017",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "huggingface_papers",
  "platform": "huggingface",
  "kind": "hf_daily_papers",
  "url": "https://huggingface.co/api/daily_papers?limit=8",
  "allowed_hosts": [
   "huggingface.co"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S048",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/papers/"
  ]
 },
 {
  "source_id": "github_trending",
  "platform": "github",
  "kind": "github_trending_public",
  "url": "https://github.com/trending",
  "allowed_hosts": [
   "github.com"
  ],
  "modes": [
   "H",
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S077",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/"
  ]
 },
 {
  "source_id": "producthunt_search",
  "platform": "producthunt",
  "kind": "html_index",
  "url": "https://www.producthunt.com/search?q=ai",
  "allowed_hosts": [
   "www.producthunt.com"
  ],
  "modes": [
   "K",
   "D"
  ],
  "planned_signal": "early_original",
  "r8_id": "S093",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/products/"
  ]
 },
 {
  "source_id": "youtube_search",
  "platform": "youtube",
  "kind": "youtube_public_search_html",
  "url": "https://www.youtube.com/results?search_query=AI+agent",
  "allowed_hosts": [
   "www.youtube.com"
  ],
  "modes": [
   "K",
   "D"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S133",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/watch"
  ]
 },
 {
  "source_id": "reddit_search",
  "platform": "reddit",
  "kind": "reddit_listing",
  "url": "https://www.reddit.com/r/LocalLLaMA/search.json?q=AI&restrict_sr=1&sort=new&limit=8",
  "allowed_hosts": [
   "www.reddit.com"
  ],
  "modes": [
   "K",
   "F"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S128",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "bluesky_search",
  "platform": "bluesky",
  "kind": "bsky_search",
  "url": "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=AI%20agent&limit=8",
  "allowed_hosts": [
   "api.bsky.app"
  ],
  "modes": [
   "K",
   "F"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S129",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "linuxdo_latest",
  "platform": "linuxdo",
  "kind": "rss",
  "url": "https://linux.do/latest.rss",
  "allowed_hosts": [
   "linux.do"
  ],
  "modes": [
   "F"
  ],
  "planned_signal": "hot_signal",
  "r8_id": "S153",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": []
 },
 {
  "source_id": "openai_api_changelog",
  "platform": "openai",
  "kind": "markdown_changelog",
  "url": "https://developers.openai.com/api/docs/changelog.md",
  "allowed_hosts": [
   "developers.openai.com"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "benefit_signal",
  "r8_id": "S302",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/api/docs/changelog"
  ]
 },
 {
  "source_id": "gemini_api_changelog",
  "platform": "google",
  "kind": "html_index",
  "url": "https://ai.google.dev/gemini-api/docs/changelog",
  "allowed_hosts": [
   "ai.google.dev"
  ],
  "modes": [
   "D"
  ],
  "planned_signal": "benefit_signal",
  "r8_id": "S304",
  "access_status": "worker_runtime_unverified",
  "deployment_stage": "adapter_configured",
  "path_prefixes": [
   "/gemini-api/docs/"
  ]
 }
]
