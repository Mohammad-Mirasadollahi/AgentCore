# ai-toolstack-sync — plan.

sync_git_change_stats() {
  REPO_ROOT="${REPO_ROOT}" PYTHONPATH="${AI_TOOLSTACK_ROOT}/lib${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -c "from git_changes import git_change_stats; import json, os; print(json.dumps(git_change_stats(__import__('pathlib').Path(os.environ['REPO_ROOT']))))"
}

sync_decide_plan() {
  :
}

sync_any_work_planned() {
  false
}

sync_print_plan_header() {
  sync_info "Agent stack sync — no graph build stages."
  python3 - <<PY 2>/dev/null || true
import json, os
g = json.loads(os.environ.get("GIT_CHANGE_JSON") or '{"is_git_repo": false}')
if g.get("is_git_repo"):
    print(f"  Git changes: total={g.get('total', 0)}")
PY
}

sync_print_plan_stages() {
  sync_plan "Run ./ai-toolstack/install.sh after rules/skills/MCP template changes"
}

sync_print_summary_stats() {
  sync_info "Sync complete (no graph artifacts)."
}
