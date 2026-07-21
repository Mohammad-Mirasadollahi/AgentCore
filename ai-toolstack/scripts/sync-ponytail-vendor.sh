#!/usr/bin/env bash
# Refresh vendored ponytail *skills* from DietrichGebert/ponytail (network required).
# Does NOT overwrite ThinkingSOC `ai-toolstack/rules/ponytail.mdc` (project-owned: ladder + chat policy).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/paths.sh
source "${SCRIPT_DIR}/../lib/paths.sh"

VENDOR="${AI_TOOLSTACK_ROOT}/skills/vendor/ponytail"
TMP="${AI_TOOLSTACK_DATA}/ponytail/sync-tmp"
REPO_URL="${PONYTAIL_REPO:-https://github.com/DietrichGebert/ponytail.git}"

if ! command -v git >/dev/null 2>&1; then
  echo "git required" >&2
  exit 1
fi

rm -rf "${TMP}"
mkdir -p "${TMP}"
git clone --depth 1 "${REPO_URL}" "${TMP}/ponytail"

rm -rf "${VENDOR}"
mkdir -p "${VENDOR}"
cp -r "${TMP}/ponytail/skills/"* "${VENDOR}/"
# Keep upstream rule text for reference only — never replace project `rules/ponytail.mdc`.
if [[ -f "${TMP}/ponytail/.cursor/rules/ponytail.mdc" ]]; then
  cp "${TMP}/ponytail/.cursor/rules/ponytail.mdc" "${VENDOR}/upstream-ponytail.mdc"
fi
git -C "${TMP}/ponytail" rev-parse HEAD > "${VENDOR}/VENDOR_REV.txt"
rm -rf "${TMP}"

echo "Ponytail skills vendored to ${VENDOR} (rev $(cat "${VENDOR}/VENDOR_REV.txt"))"
echo "Project rule unchanged: ${AI_TOOLSTACK_RULES}/ponytail.mdc"
echo "Upstream rule snapshot: ${VENDOR}/upstream-ponytail.mdc"
echo "Re-run: ./ai-toolstack/install.sh && ./ai-toolstack/scripts/generate-cursor-agent-manifest.sh"
