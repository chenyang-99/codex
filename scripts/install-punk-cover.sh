#!/usr/bin/env bash
set -euo pipefail

PUNK_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PUNK_REPO_DIR="$(git -C "$PUNK_SCRIPT_DIR" rev-parse --show-toplevel)"
PUNK_SOURCE_DIR="$PUNK_REPO_DIR/vendor/punk-skill"
PUNK_EXPECTED_COMMIT="c9ad7a3745e07060c50270141efed418a0cd04d6"

# Preserve any existing local edits instead of overwriting them.
if [[ -f "$PUNK_SOURCE_DIR/.git" || -d "$PUNK_SOURCE_DIR/.git" ]]; then
  if [[ -n "$(git -C "$PUNK_SOURCE_DIR" status --porcelain)" ]]; then
    printf '%s\n' 'Punk source has local changes; preserve them before reinstalling.' >&2
    exit 1
  fi
fi

git -C "$PUNK_REPO_DIR" submodule update --init --depth 1 -- vendor/punk-skill
git -C "$PUNK_SOURCE_DIR" sparse-checkout init --cone
git -C "$PUNK_SOURCE_DIR" sparse-checkout set skills/punk-cover styles

python3 - "$PUNK_REPO_DIR" "$PUNK_EXPECTED_COMMIT" <<'PY'
import json
from pathlib import Path
import re
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
expected = sys.argv[2]
source = repo / "vendor" / "punk-skill"
official = source / "skills" / "punk-cover"
entry = repo / ".agents" / "skills" / "punk-cover"

def git(*args):
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()

if git("rev-parse", "HEAD") != expected:
    raise SystemExit("Installed commit does not match the pinned upstream revision.")
if git("remote", "get-url", "origin") != "https://github.com/adrianpunk/Punk-Skill.git":
    raise SystemExit("Punk source origin is not the official repository.")
if not entry.is_symlink() or entry.resolve() != official.resolve():
    raise SystemExit("Codex skill entry is missing or does not resolve to the original skill.")
if git("status", "--porcelain"):
    raise SystemExit("The installed upstream files are modified.")

manifest = (official / "SKILL.md").read_text(encoding="utf-8")
if not re.search(r"(?m)^name:\s*punk-cover\s*$", manifest):
    raise SystemExit("The original SKILL.md does not declare punk-cover.")

required = [
    "agents/openai.yaml",
    "references/style-catalog.md",
    "references/platform-catalog.md",
    "references/cover-prompt-blueprint.md",
]
for relative in required:
    if not (official / relative).is_file():
        raise SystemExit("Missing skill resource: " + relative)
for filename in ("LICENSE", "LICENSE-PERSONAL.md", "COMMERCIAL-LICENSE.md", "THIRD_PARTY_NOTICES.md"):
    if not (source / filename).is_file():
        raise SystemExit("Missing upstream notice: " + filename)

catalog = (official / "references/style-catalog.md").read_text(encoding="utf-8")
styles = sorted(set(re.findall(r"styles/([a-z0-9-]+)/(?:META|STYLE)\.md", catalog)))
if not styles:
    raise SystemExit("No cover styles were found in the original catalog.")
for style_id in styles:
    # Resolve from the ORIGINAL skill directory, preserving ../../styles.
    style_root = official / ".." / ".." / "styles" / style_id
    for filename in ("META.md", "STYLE.md"):
        if not (style_root / filename).is_file():
            raise SystemExit("Missing shared style resource: " + style_id + "/" + filename)
    metadata = (style_root / "META.md").read_text(encoding="utf-8")
    outputs_match = re.search(r"(?m)^outputs:\s*\[([^\]]+)\]", metadata)
    outputs = set() if outputs_match is None else {
        value.strip().strip(chr(34) + chr(39)) for value in outputs_match.group(1).split(",")
    }
    if not outputs.intersection({"cover", "poster"}):
        raise SystemExit("The cover catalog contains an ineligible style: " + style_id)

discovered = list((repo / ".agents" / "skills").glob("*/SKILL.md"))
if entry / "SKILL.md" not in discovered:
    raise SystemExit("The repo-scoped skill entry is not readable.")
for unrelated in ("punk-avatar", "punk-ip-video-cover"):
    if (source / "skills" / unrelated / "SKILL.md").exists():
        raise SystemExit("An unrelated Punk skill was included in the sparse installation.")

print(json.dumps({
    "skill": "punk-cover",
    "upstream_commit": expected,
    "cover_styles_verified": len(styles),
    "entry_point": str(entry / "SKILL.md"),
    "original_workflow": str(official / "SKILL.md"),
    "original_files_unmodified": True,
    "license_notices_preserved": True,
}, ensure_ascii=False, indent=2))
PY
