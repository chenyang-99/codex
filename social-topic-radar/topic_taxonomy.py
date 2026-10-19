#!/usr/bin/env python3
"""V2 AI topic taxonomy. Classification is a discovery hint, not editorial approval.

Orthogonal dimensions:
- content_type: what the reader gets (five types)
- domains: what AI subject the content covers (15 areas, possibly multiple)
- source_roles: why a source is useful (six roles)
"""
import re

CONTENT_TYPES = {
    "tool_resource": "工具与资源",
    "news_update": "资讯与动态",
    "tutorial": "教程与技巧",
    "case_review": "案例与测评",
    "opinion_trend": "观点与趋势",
}
AI_DOMAINS = {
    "foundation_models": "大模型与前沿能力",
    "model_evaluation": "模型评测与排行榜",
    "ai_research": "AI学术研究",
    "tools_products": "AI工具与新品",
    "agents_automation": "Agent与自动化",
    "ai_coding": "AI编程",
    "aicg_image": "AI绘画与设计",
    "aicg_video": "AI视频与影视",
    "ai_audio_avatars": "AI音频与数字人",
    "ai_education": "AI教程与学习",
    "ai_infrastructure": "AI基础设施",
    "robotics": "机器人与具身智能",
    "industry_applications": "AI行业应用",
    "safety_policy": "AI安全与政策",
    "business_trends": "AI商业与产业趋势",
}
SOURCE_ROLES = {
    "official": "官方一手发布",
    "discovery": "新内容发现与聚合",
    "evaluation": "独立评测",
    "community": "真实社区反馈",
    "tutorial": "教程与实操",
    "trend": "热度与需求验证",
}

TYPE_KEYWORDS = {
    "tutorial": ["tutorial", "how to", "step by step", "walkthrough", "hands-on", "guide to", "best practices", "教程", "实操", "操作指南", "步骤", "技巧", "怎么做", "提示词模板"],
    "case_review": ["benchmark", "leaderboard", "comparison", "review", "case study", "behind the scenes", "experiment", "versus", "vs.", "评测", "测评", "横评", "实测", "幕后", "案例拆解", "对比测试"],
    "tool_resource": ["open source", "open-source", "skill library", "plugin", "software", "resource list", "toolkit", "mcp server", "开源", "工具合集", "宝藏工具", "插件", "资源库", "工作流模板"],
    "news_update": ["announces", "announced", "launches", "launch", "released", "release", "update", "new feature", "发布", "上线", "推出", "重大更新", "新功能", "升级"],
    "opinion_trend": ["opinion", "future of", "what it means", "why ai", "trend", "impact", "预测", "趋势", "争议", "影响", "观点", "反常识"],
}
DOMAIN_KEYWORDS = {
    "foundation_models": ["llm", "language model", "reasoning model", "multimodal", "openai", "claude", "gemini", "deepseek", "qwen", "大模型", "多模态", "推理模型"],
    "model_evaluation": ["benchmark", "leaderboard", "model evaluation", "artificial analysis", "arena.ai", "模型评测", "排行榜", "模型横评"],
    "ai_research": ["arxiv", "openreview", "research paper", "neurips", "iclr", "学术论文", "前沿研究", "科研突破"],
    "tools_products": ["product hunt", "ai tool", "ai app", "plugin", "software", "skill library", "开源工具", "ai工具", "插件", "宝藏网站"],
    "agents_automation": ["agent", "agents", "mcp", "skills.sh", "workflow", "n8n", "automation", "智能体", "自动化", "工作流", "技能包"],
    "ai_coding": ["coding agent", "vibe coding", "cursor", "replit", "lovable", "code generation", "codex", "编程", "写代码", "网站开发"],
    "aicg_image": ["midjourney", "comfyui", "flux", "image generation", "image editing", "photoshop ai", "生图", "绘画", "海报", "视觉设计", "修图"],
    "aicg_video": ["runway", "kling", "sora", "veo", "pika", "video generation", "filmmaking", "ai video", "运镜", "生视频", "电影镜头", "ai视频"],
    "ai_audio_avatars": ["elevenlabs", "suno", "heygen", "voice cloning", "text-to-speech", "music generation", "数字人", "配音", "语音合成", "ai音乐"],
    "ai_education": ["prompt engineering", "prompt", "rag", "fine tuning", "fine-tuning", "tutorial", "course", "教程", "提示词", "微调", "学习路线"],
    "ai_infrastructure": ["gpu", "nvidia", "inference", "vllm", "ollama", "local deployment", "推理加速", "算力", "本地部署", "显卡"],
    "robotics": ["robot", "robotics", "humanoid", "embodied ai", "lerobot", "机器人", "具身智能", "自动驾驶"],
    "industry_applications": ["microsoft 365", "excel", "powerpoint", "education", "healthcare", "ecommerce", "customer service", "office automation", "办公", "医疗", "电商", "行业应用"],
    "safety_policy": ["safety", "security", "alignment", "privacy", "regulation", "copyright", "owasp", "合规", "安全", "版权", "监管", "隐私"],
    "business_trends": ["startup", "adoption", "revenue", "market", "funding", "ai index", "enterprise ai", "商业模式", "融资", "营收", "商业化", "产业趋势"],
}
TYPE_ORDER = ("tutorial", "case_review", "tool_resource", "news_update", "opinion_trend")
ROLE_BY_LEGACY_KIND = {
    "official": ["official"],
    "creator": ["community", "tutorial"],
    "community": ["community", "trend"],
    "video": ["community", "tutorial"],
    "research": ["discovery"],
    "media": ["discovery"],
}

def _has_term(haystack, term):
    """Word boundaries for Latin tokens; substring matching for Chinese."""
    term = term.casefold()
    if re.search(r"[a-z]", term):
        return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", haystack) is not None
    return term in haystack

def classify_text(title, description=""):
    value = " ".join(v for v in (title, description) if isinstance(v, str)).casefold()
    types = [k for k in TYPE_ORDER if any(_has_term(value, w) for w in TYPE_KEYWORDS[k])]
    domains = [k for k, terms in DOMAIN_KEYWORDS.items() if any(_has_term(value, w) for w in terms)]
    return {
        "content_type": types[0] if types else "unclassified",
        "content_type_matches": types,
        "domains": domains,
        "taxonomy_version": "2.0",
        "classification_status": "keyword_hints_require_editor_review",
    }
