# Repository guidance

## Punk Cover in Codex Cloud

When the user requests Punk cover images or invokes $punk-cover, use the author's
original skill from https://github.com/adrianpunk/Punk-Skill.

Before using it, run the following from this repository's root:

~~~sh
bash scripts/install-punk-cover.sh
~~~

The installer initializes the pinned upstream Git submodule, includes only the
punk-cover workflow plus its shared style library, and verifies every style
resource referenced by the cover catalog. It does not execute upstream scripts.
If initialization fails, report the concrete error and do not claim installation
or image generation succeeded.

Read .agents/skills/punk-cover/SKILL.md after initialization. This is a symlink to
vendor/punk-skill/skills/punk-cover/SKILL.md, so read its relative resources from
that original directory; shared styles are in vendor/punk-skill/styles.
Follow the original workflow and the user's requested platform, ratio, language,
and style. When a managed cloud skill catalog has not refreshed, explicitly open
that file instead of relying on automatic skill discovery.

Preserve the original copyright and license notices. The current upstream
release permits free personal non-commercial use; commercial use requires the
author's separate authorization. Installation does not grant commercial rights.


## X account operations in the AI content project

For tasks involving operating, planning, auditing, growing, or monetizing the user's X account @CY160909, read \`.agents/skills/x-account-operations/SKILL.md\` and its task-relevant references before proposing decisions. It is the strategy and accountability layer; do not replace the existing topic research, copy-production, or X publishing-format adapter skills.

For confirmed topics and X copy tasks, continue following \`.agents/skills/ai-copy-production/SKILL.md\` and \`.agents/skills/x-content-adapter/SKILL.md\`. For current project history and real content data, use the existing Google Docs and Google Sheets project records as the single source of truth. Do not infer the private Original Content Rewards metrics from public views, pretend to have a live X connection, or automatically create/post content for rewards. The operations Skill is a human-in-the-loop research-backed prototype; no real account outcome is yet validated.


## H4pplness Storyboard Poster Skill

For storyboard, short video, shot breakdown and storyboard-poster tasks, run `bash scripts/install-storyboard-poster.sh` from repo root. The installed repo-scoped entry `.agents/skills/storyboard-poster/SKILL.md` symlinks to the author's unmodified `vendor/storyboard-skill/storyboard-skill-en.md`, pinned to commit `6c1b8976764824907c73d85d125a59f76c536218`. Follow the original skill: 16:9 storyboard POSTER PROMPT + VIDEO PROMPT; character reference prompt only when requested. It does not itself generate a finished video. The distinct upstream ChatGPT executor (`storyboard-chacracter-ref-chatgpt-en.md`) invokes an image-generation tool to produce still images. Never conflate prompt-only, generated still and rendered video. Keep source attribution, avoid redistributing original examples without explicit permission. No LICENSE file was present in the inspected upstream commit.
