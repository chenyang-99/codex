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
