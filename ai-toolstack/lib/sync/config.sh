# ai-toolstack-sync — paths, logs, lock (source after paths.sh + log.sh).
# shellcheck disable=SC2034

SCRIPTS="${AI_TOOLSTACK_SCRIPTS}"
LOCK_FILE="${AI_TOOLSTACK_LOCAL}/sync.lock"
CRON_LOG="${HOME}/.cache/ai-toolstack-sync-cron.log"
LOG_DIR="${HOME}/.cache"

GIT_CHANGE_JSON='{"is_git_repo": false, "total": 0}'

SYNC_CURRENT_STAGE="init"
SYNC_ERR_TRAP_INSTALLED=false
