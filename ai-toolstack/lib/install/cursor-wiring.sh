# ai-toolstack install — Cursor rules, skills, manifest, entrypoints.

install_cursor_skills() {
  local skills_root="${AI_TOOLSTACK_ROOT}/skills"
  local dest_root="${REPO_ROOT}/.cursor/skills"
  local bucket name src dest
  local -a keep_names=()

  install_ensure_dir "${dest_root}"
  # Order matters: thinkingsoc last so it overrides same-named vendor skills (e.g. ponytail-debt).
  # Persian chat lives only under cursor-agent-config/global-skills/ → ~/.cursor/skills (not here).
  for bucket in vendor/mattpocock vendor/ponytail thinkingsoc; do
    shopt -s nullglob
    for src in "${skills_root}/${bucket}"/*/; do
      [[ -d "${src}" ]] || continue
      [[ -f "${src}/SKILL.md" ]] || continue
      name="$(basename "${src}")"
      keep_names+=("${name}")
      dest="${dest_root}/${name}"
      if [[ -e "${dest}" || -L "${dest}" ]]; then
        rm -rf "${dest}"
      fi
      install_link_path "${src}" "${dest}"
    done
    shopt -u nullglob
  done

  shopt -s nullglob
  for existing in "${dest_root}"/*; do
    [[ -e "${existing}" || -L "${existing}" ]] || continue
    base="$(basename "${existing}")"
    keep=false
    for k in "${keep_names[@]}"; do
      [[ "${k}" == "${base}" ]] && keep=true && break
    done
    if [[ "${keep}" != true ]]; then
      rm -rf "${existing}"
    fi
  done
  shopt -u nullglob
}

install_cursor_entrypoints() {
  local ep="${AI_TOOLSTACK_ROOT}/cursor-agent-config/entrypoints"
  if [[ "${AI_TOOLSTACK_PROFILE:-}" == "agentcore" ]]; then
    if [[ -f "${ep}/AGENTS.agentcore.md" ]]; then
      cp -f "${ep}/AGENTS.agentcore.md" "${REPO_ROOT}/AGENTS.md"
    fi
    if [[ -f "${ep}/.cursorrules.agentcore" ]]; then
      cp -f "${ep}/.cursorrules.agentcore" "${REPO_ROOT}/.cursorrules"
    fi
    echo "agentcore" > "${AI_TOOLSTACK_LOCAL}/install-profile"
  else
    rm -f "${AI_TOOLSTACK_LOCAL}/install-profile"
  fi
  install_sync_agents_docs
}

# Sync IDE-agnostic agent docs (all profiles). Source: ai-toolstack/docs/agents/ → docs/agents/
install_sync_agents_docs() {
  local src="${AI_TOOLSTACK_DOCS}/agents"
  local dest="${REPO_ROOT}/docs/agents"
  [[ -d "${src}" ]] || return 0
  install_ensure_dir "${dest}"
  if compgen -G "${src}/*.md" >/dev/null; then
    cp -f "${src}/"*.md "${dest}/" 2>/dev/null || true
  fi
}

# Mirror portable laws into .agents/rules/ for non-Cursor agents (Claude Code, etc.)
install_agents_rules_mirror() {
  local dest="${REPO_ROOT}/.agents/rules"
  local law="${REPO_ROOT}/docs/agents/documentation-authoring.md"
  install_ensure_dir "${dest}"
  if [[ -f "${law}" ]]; then
    install_link_path "${law}" "${dest}/documentation-authoring.md"
  fi
  if [[ ! -f "${dest}/README.md" ]]; then
    cat > "${dest}/README.md" <<'EOF'
# Agent rules (IDE-agnostic)

Git-tracked laws for **any** coding agent. Not Cursor-only.

| Rule | Path |
|------|------|
| Documentation authoring | [documentation-authoring.md](./documentation-authoring.md) → `docs/agents/documentation-authoring.md` |

Skills live under [../skills/](../skills/) (mirrored from `ai-toolstack/skills/` by `./ai-toolstack/install.sh`).

Canonical standards: `backend/docs/standards/documentation/`.
EOF
  fi
}

install_agents_skills_mirror() {
  local cur="${REPO_ROOT}/.cursor/skills"
  local agents="${REPO_ROOT}/.agents/skills"
  [[ -d "${cur}" ]] || return 0
  install_ensure_dir "${agents}"
  local name existing base keep
  shopt -s nullglob
  for existing in "${agents}"/*; do
    [[ -e "${existing}" || -L "${existing}" ]] || continue
    base="$(basename "${existing}")"
    keep=false
    for name in "${cur}"/*; do
      [[ -e "${name}" || -L "${name}" ]] || continue
      [[ "$(basename "${name}")" == "${base}" ]] && keep=true && break
    done
    if [[ "${keep}" != true ]]; then
      rm -rf "${existing}"
    fi
  done
  for name in "${cur}"/*; do
    [[ -e "${name}" || -L "${name}" ]] || continue
    # Skip dangling project skill links
    [[ -e "${name}" ]] || continue
    base="$(basename "${name}")"
    install_link_path "$(readlink -f "${name}")" "${agents}/${base}"
  done
  shopt -u nullglob
}

install_cursor_agent_manifest() {
  local gen="${AI_TOOLSTACK_SCRIPTS}/generate-cursor-agent-manifest.sh"
  if [[ ! -x "${gen}" ]]; then
    ai_toolstack_warn "generate-cursor-agent-manifest.sh missing — skip manifest"
    return 0
  fi
  if ! "${gen}"; then
    ai_toolstack_warn "cursor-agent manifest generation failed"
    return 1
  fi
}

install_cursor_rules() {
  local rules=(
    no-cloud-exfiltration.mdc
    root-cause-fix.mdc
    ai-toolstack.mdc
    mcp-memory.mdc
    code-and-docs-english-only.mdc
    ponytail.mdc
  )
  if [[ "${AI_TOOLSTACK_PROFILE:-}" != "agentcore" ]]; then
    rules=(
      no-cloud-exfiltration.mdc
      root-cause-fix.mdc
      ai-toolstack.mdc
      code-and-docs-english-only.mdc
      long-job-progress-chat.mdc
      ponytail.mdc
      mcp-memory.mdc
      microservice-architecture.mdc
      documentation-authoring.mdc
      structured-logging.mdc
      deploy-long-job-heartbeat.mdc
    )
  fi
  install_ensure_dir "${REPO_ROOT}/.cursor/rules"
  local name existing base keep
  shopt -s nullglob
  for existing in "${REPO_ROOT}/.cursor/rules"/*.mdc; do
    base="$(basename "${existing}")"
    keep=false
    for name in "${rules[@]}"; do
      if [[ "${name}" == "${base}" ]]; then keep=true; break; fi
    done
    if [[ "${keep}" != true ]]; then
      rm -f "${existing}"
    fi
  done
  for name in "${rules[@]}"; do
    install_link_path "${AI_TOOLSTACK_RULES}/${name}" "${REPO_ROOT}/.cursor/rules/${name}"
  done
}

install_global_cursor_rules() {
  local src_dir="${AI_TOOLSTACK_ROOT}/cursor-agent-config/global-rules"
  local dest="${HOME}/.cursor/rules"
  [[ -d "${src_dir}" ]] || return 0
  install_ensure_dir "${dest}"
  local f base
  shopt -s nullglob
  for f in "${src_dir}"/*.mdc; do
    base="$(basename "${f}")"
    if [[ -e "${dest}/${base}" || -L "${dest}/${base}" ]]; then
      rm -f "${dest}/${base}"
    fi
    install_link_path "${f}" "${dest}/${base}"
  done
  shopt -u nullglob
  ai_toolstack_info "Global user rules: ${dest} (← cursor-agent-config/global-rules/)"
}

install_global_cursor_skills() {
  local src_root="${AI_TOOLSTACK_ROOT}/cursor-agent-config/global-skills"
  local dest_root="${HOME}/.cursor/skills"
  [[ -d "${src_root}" ]] || return 0
  install_ensure_dir "${dest_root}"
  local src name dest
  shopt -s nullglob
  for src in "${src_root}"/*/; do
    [[ -d "${src}" ]] || continue
    name="$(basename "${src}")"
    dest="${dest_root}/${name}"
    if [[ -e "${dest}" || -L "${dest}" ]]; then
      rm -rf "${dest}"
    fi
    install_link_path "${src}" "${dest}"
  done
  shopt -u nullglob
  ai_toolstack_info "Global user skills: ${dest_root}/persian-chat-reply (← global-skills/)"
}
