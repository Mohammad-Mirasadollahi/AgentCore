#!/usr/bin/env bash
# Regenerate ai-toolstack/cursor-agent-config/MANIFEST.md from canonical store.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${SCRIPT_DIR}/../lib/paths.sh"

OUT="${AI_TOOLSTACK_ROOT}/cursor-agent-config/MANIFEST.md"
RULES="${AI_TOOLSTACK_RULES}"
SKILLS="${AI_TOOLSTACK_ROOT}/skills"
TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

skill_desc() {
  local f="${1}/SKILL.md"
  [[ -f "${f}" ]] || { echo "—"; return; }
  awk '
    /^---$/ { if (++n == 2) exit; next }
    n == 1 && /^description:/ {
      sub(/^description:[[:space:]]*/, "")
      gsub(/^>-$/, "")
      gsub(/^>-$/, "")
      print
      exit
    }
  ' "${f}" | tr '\n' ' ' | sed 's/[[:space:]]*$//'
}

{
  echo "# Cursor Agent Config Manifest"
  echo
  echo "Auto-generated. Do not edit by hand — run \`./ai-toolstack/scripts/generate-cursor-agent-manifest.sh\`."
  echo
  echo "| Field | Value |"
  echo "|-------|-------|"
  echo "| Generated | ${TS} |"
  echo "| Restore | \`./ai-toolstack/install.sh\` |"
  echo "| Rules source | \`ai-toolstack/rules/\` |"
  echo "| Skills source | \`ai-toolstack/skills/\` |"
  echo
  echo "## Rules ($(find "${RULES}" -maxdepth 1 -name '*.mdc' | wc -l | tr -d ' '))"
  echo
  echo "| Rule | Role |"
  echo "|------|------|"
  for f in "${RULES}"/*.mdc; do
    [[ -f "${f}" ]] || continue
    base="$(basename "${f}")"
    desc="$(grep -m1 '^description:' "${f}" 2>/dev/null | sed 's/^description:[[:space:]]*//' || echo "—")"
    echo "| [\`${base}\`](../rules/${base}) | ${desc} |"
  done
  echo
  echo "## Skills — ThinkingSOC ($(find "${SKILLS}/thinkingsoc" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' '))"
  echo
  echo "| Skill | Description |"
  echo "|-------|-------------|"
  for d in "${SKILLS}"/thinkingsoc/*/; do
    [[ -d "${d}" ]] || continue
    name="$(basename "${d}")"
    desc="$(skill_desc "${d}")"
    echo "| [\`${name}\`](../skills/thinkingsoc/${name}/SKILL.md) | ${desc} |"
  done
  echo
  echo "## Skills — vendor/mattpocock ($(ls -1 "${SKILLS}/vendor/mattpocock" 2>/dev/null | grep -v README.md | wc -l | tr -d ' '))"
  echo
  echo "| Skill | Description |"
  echo "|-------|-------------|"
  for d in "${SKILLS}"/vendor/mattpocock/*/; do
    [[ -d "${d}" ]] || continue
    name="$(basename "${d}")"
    desc="$(skill_desc "${d}")"
    echo "| [\`${name}\`](../skills/vendor/mattpocock/${name}/SKILL.md) | ${desc} |"
  done
  echo
  echo "## Skills — vendor/ponytail ($(ls -1 "${SKILLS}/vendor/ponytail" 2>/dev/null | grep -v VENDOR_REV.txt | wc -l | tr -d ' '))"
  echo
  echo "| Skill | Description |"
  echo "|-------|-------------|"
  for d in "${SKILLS}"/vendor/ponytail/*/; do
    [[ -d "${d}" ]] || continue
    name="$(basename "${d}")"
    desc="$(skill_desc "${d}")"
    echo "| [\`${name}\`](../skills/vendor/ponytail/${name}/SKILL.md) | ${desc} |"
  done
  echo
  echo "## Agent setup docs"
  echo
  echo "| File | Purpose |"
  echo "|------|---------|"
  echo "| [\`docs/agents/issue-tracker.md\`](../../docs/agents/issue-tracker.md) | GitHub issue tracker for mattpocock skills |"
  echo "| [\`docs/agents/triage-labels.md\`](../../docs/agents/triage-labels.md) | Triage label vocabulary |"
  echo "| [\`docs/agents/domain.md\`](../../docs/agents/domain.md) | Domain doc layout for this monorepo |"
} > "${OUT}"

echo "Wrote ${OUT}"
