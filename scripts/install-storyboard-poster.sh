#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SRC="$ROOT/vendor/storyboard-skill"
ENTRY="$ROOT/.agents/skills/storyboard-poster/SKILL.md"
EXPECTED="6c1b8976764824907c73d85d125a59f76c536218"
if [[ -e "$SRC/.git" ]] && [[ -n "$(git -C "$SRC" status --porcelain)" ]]; then
  echo "Modified upstream source; aborting" >&2; exit 1
fi
git -C "$ROOT" submodule update --init --depth 1 -- vendor/storyboard-skill
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$EXPECTED" ]] || { echo "Unexpected commit" >&2; exit 1; }
[[ "$(git -C "$SRC" remote get-url origin)" == "https://github.com/H4pplness/storyboard-skill.git" ]] || { echo "Wrong upstream origin" >&2; exit 1; }
[[ -L "$ENTRY" ]] && [[ "$(readlink -f "$ENTRY")" == "$(readlink -f "$SRC/storyboard-skill-en.md")" ]] || { echo "Skill symlink invalid" >&2; exit 1; }
grep -q '^name: storyboard-poster$' "$ENTRY" || { echo "Skill name wrong" >&2; exit 1; }
test -s "$SRC/storyboard-chacracter-ref-chatgpt-en.md"
echo "Original storyboard-poster source installed and verified: $EXPECTED"
