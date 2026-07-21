#!/usr/bin/env python3
"""Post-install verification for ThinkingSOC ai-toolstack."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from cli.log_util import ts_section
from cli.paths import ToolstackPaths, extend_tool_path
from cli.verify_runner import VerifyRunner

_LIB = Path(__file__).resolve().parents[1]
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))


def _bash_node_toolchain(paths: ToolstackPaths) -> bool:
    resolve_sh = paths.ai_toolstack / "lib" / "resolve-node.sh"
    script = (
        f'source "{paths.ai_toolstack / "lib/paths.sh"}" && '
        f'source "{resolve_sh}" && ensure_node_toolchain'
    )
    return subprocess.run(["bash", "-lc", script], cwd=paths.repo).returncode == 0


def _bash_npx_doctor(paths: ToolstackPaths) -> tuple[bool, str]:
    resolve_sh = paths.ai_toolstack / "lib" / "resolve-node.sh"
    script = (
        f'source "{paths.ai_toolstack / "lib/paths.sh"}" && '
        f'source "{resolve_sh}" && '
        f'timeout 120 "${{NODE_TOOLCHAIN_BIN}}/npx" -y mcp-lazy doctor'
    )
    proc = subprocess.run(["bash", "-lc", script], cwd=paths.repo, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def verify_layout(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Layout")
    v.file_ok(paths.ai_toolstack / "install.sh", "install.sh")
    v.file_ok(paths.config / "mcp.json.template", "config/mcp.json.template")
    v.file_ok(paths.config / "mcp-lazy-servers.json.template", "mcp-lazy template")
    v.file_ok(paths.config / "cursor-hooks.json.template", "cursor-hooks template")


def verify_repo_symlinks(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Repo symlinks")
    v.symlink_ok(paths.legacy_mcp_memory, paths.mcp_memory_dir, ".mcp-memory")


def verify_runtime_not_tracked(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Git (runtime must not be tracked)")
    blocked = [".mcp-memory"]
    for rel in blocked:
        proc = subprocess.run(
            ["git", "-C", str(paths.repo), "ls-files", "--error-unmatch", rel],
            capture_output=True,
        )
        if proc.returncode == 0:
            v.fail(f"{rel} is tracked in git (machine-local symlink; git rm --cached {rel})")
        else:
            v.pass_(f"{rel} not tracked")

    proc = subprocess.run(
        ["git", "-C", str(paths.repo), "ls-files", "ai-toolstack/data/"],
        capture_output=True,
        text=True,
    )
    if proc.stdout.strip():
        v.fail("ai-toolstack/data/ has tracked files (must stay gitignored)")
    else:
        v.pass_("ai-toolstack/data/ not tracked")


def verify_user_symlinks(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("User symlinks")
    home = Path.home()
    v.symlink_ok(home / ".cursor/mcp.json", paths.local / "mcp.json", "~/.cursor/mcp.json")
    v.symlink_ok(home / ".mcp-lazy/servers.json", paths.local / "mcp-lazy-servers.json", "~/.mcp-lazy/servers.json")
    v.symlink_ok(home / ".cursor/hooks.json", paths.local / "cursor-hooks.json", "~/.cursor/hooks.json")


def verify_generated_configs(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Generated configs (data/local)")
    v.file_ok(paths.local / "mcp.json", "mcp.json (generated)")
    v.file_ok(paths.local / "mcp-lazy-servers.json", "mcp-lazy-servers.json")
    v.file_ok(paths.local / "cursor-hooks.json", "cursor-hooks.json")
    v.json_ok(paths.local / "mcp-lazy-servers.json", "mcp-lazy-servers.json parse")
    v.json_ok(paths.local / "cursor-hooks.json", "cursor-hooks.json parse")
    mcp_json = Path.home() / ".cursor/mcp.json"
    v.json_ok(mcp_json, "~/.cursor/mcp.json parse")

    text = mcp_json.read_text(encoding="utf-8") if mcp_json.is_file() else ""
    direct_backends = ("code-review-graph", "graphify", "graphify-read")
    if '"mcp-lazy"' in text and not any(b in text for b in direct_backends):
        v.pass_("mcp.json exposes mcp-lazy (no direct graph backends)")
    else:
        v.fail("mcp.json must expose only mcp-lazy — not direct memory, headroom, or removed graph backends")

    if "mcp-lazy-serve.sh" in text:
        v.pass_("mcp.json uses mcp-lazy-serve wrapper (PATH-independent)")
    else:
        v.fail("mcp.json should use mcp-lazy-serve.sh — re-run ./ai-toolstack/install.sh")

    if '"rtk"' in text:
        v.fail("mcp.json should not expose RTK — re-run ./ai-toolstack/install.sh")
    elif '"headroom"' in text:
        v.fail(
            "mcp.json should not expose headroom directly — Headroom is only via mcp-lazy "
            "(servers.json); re-run ./ai-toolstack/install.sh"
        )
    else:
        v.pass_("mcp.json is mcp-lazy only (memory + headroom via proxy)")

    servers = paths.local / "mcp-lazy-servers.json"
    if servers.is_file() and "ai-toolstack" in servers.read_text(encoding="utf-8"):
        v.pass_("servers.json uses ai-toolstack paths")


def verify_mcp_backends(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("MCP backends (servers.json)")
    data = json.loads((paths.local / "mcp-lazy-servers.json").read_text(encoding="utf-8"))
    servers = data.get("servers") or {}
    expected = {"memory", "headroom"}
    missing = expected - set(servers)
    if missing:
        v.fail(f"servers.json backends: missing {missing}")
        return

    issues: list[str] = []
    for name, cfg in servers.items():
        cmd = cfg.get("command", "")
        if name == "headroom" and "headroom-mcp-serve.sh" not in cmd:
            issues.append(f"headroom should use headroom-mcp-serve.sh wrapper: {cmd}")
        if name == "memory":
            mem = (cfg.get("env") or {}).get("MEMORY_FILE_PATH", "")
            if mem and not str(mem).startswith(str(paths.repo)):
                issues.append(f"memory path outside repo: {mem}")
            elif not mem:
                issues.append("MEMORY_FILE_PATH unset")

    if issues:
        for issue in issues:
            v.fail(f"servers.json backends: {issue}")
    else:
        v.pass_("servers.json backends")


def verify_cursor_hooks(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Cursor hooks")
    v.executable_ok(paths.hooks / "rtk-cursor-hook.sh", "hook rtk-cursor-hook.sh")
    v.executable_ok(paths.hooks / "ponytail-output-stats.sh", "hook ponytail-output-stats.sh")

    hooks_json = json.loads((paths.local / "cursor-hooks.json").read_text(encoding="utf-8"))
    h = hooks_json.get("hooks") or {}
    if "sessionStart" not in h or not h["sessionStart"]:
        v.fail("cursor-hooks.json structure: missing sessionStart")
        return

    if "preToolUse" not in h:
        v.fail("cursor-hooks.json structure: missing preToolUse key")
        return

    pre_tool = h.get("preToolUse") or []
    rtk_hooks = [
        e
        for e in pre_tool
        if "hook cursor" in e.get("command", "") or "rtk" in e.get("command", "").lower()
    ]
    rtk_bin = shutil.which("rtk")
    rtk_disabled = os.environ.get("AI_TOOLSTACK_RTK_HOOK", "1") == "0"

    if rtk_disabled:
        if rtk_hooks:
            v.fail("AI_TOOLSTACK_RTK_HOOK=0 but RTK preToolUse hook is still configured")
            return
    elif rtk_bin:
        if not rtk_hooks:
            v.fail(
                "rtk is installed but Shell preToolUse hook is missing — re-run ./ai-toolstack/install.sh"
            )
            return
        if len(rtk_hooks) != 1 or rtk_hooks[0].get("matcher") != "Shell":
            v.fail("RTK preToolUse must be a single Shell matcher entry")
            return
        hook_cmd = rtk_hooks[0].get("command", "")
        expected = paths.hooks / "rtk-cursor-hook.sh"
        if not hook_cmd.endswith("rtk-cursor-hook.sh") and "rtk-cursor-hook.sh" not in hook_cmd:
            v.fail(f"RTK hook should use rtk-cursor-hook.sh (watermark guard), got: {hook_cmd}")
            return
        if not expected.is_file():
            v.fail(f"missing {expected}")
            return
        v.pass_("RTK Shell hook (watermark + Headroom bypass guard)")
    elif rtk_hooks:
        v.fail("RTK preToolUse hook configured but rtk binary not on PATH")
        return
    else:
        v.warn("rtk not installed — Shell output is raw unless agent uses headroom_compress")

    for entry in h.get("sessionStart") or []:
        cmd = entry.get("command", "")
        if "ai-toolstack/hooks/" not in cmd and "ai-toolstack" not in cmd:
            v.fail(f"cursor-hooks.json structure: hook not under ai-toolstack/hooks: {cmd}")
            return
        if not Path(cmd).is_file():
            v.fail(f"cursor-hooks.json structure: hook script missing: {cmd}")
            return

    v.pass_("cursor-hooks.json structure")


def _agentcore_profile(paths: ToolstackPaths) -> bool:
    prof = paths.local / "install-profile"
    return prof.is_file() and prof.read_text(encoding="utf-8").strip() == "agentcore"


def verify_cursor_rules(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Cursor rules")
    rule_names = [
        "no-cloud-exfiltration.mdc",
        "ai-toolstack.mdc",
        "ponytail.mdc",
        "mcp-memory.mdc",
        "code-and-docs-english-only.mdc",
    ]
    if not _agentcore_profile(paths):
        rule_names.extend(
            [
                "root-cause-fix.mdc",
                "long-job-progress-chat.mdc",
                "microservice-architecture.mdc",
                "documentation-authoring.mdc",
                "structured-logging.mdc",
                "deploy-long-job-heartbeat.mdc",
            ]
        )
    for name in rule_names:
        v.symlink_ok(paths.repo / ".cursor/rules" / name, paths.rules / name, f"rule {name}")
    global_rule = Path.home() / ".cursor/rules/persian-chat-typography-global.mdc"
    expected_global = (
        paths.ai_toolstack / "cursor-agent-config/global-rules/persian-chat-typography-global.mdc"
    )
    v.symlink_ok(global_rule, expected_global, "global rule persian-chat-typography-global.mdc")


def verify_cursor_skills(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Cursor skills")
    skills_root = paths.ai_toolstack / "skills"
    # Prefer ThinkingSOC override when the same skill name exists under vendor/.
    expected: dict[str, Path] = {}
    for bucket in (
        skills_root / "vendor" / "mattpocock",
        skills_root / "vendor" / "ponytail",
        skills_root / "thinkingsoc",
    ):
        if not bucket.is_dir():
            v.fail(f"skills bucket missing: {bucket.relative_to(paths.repo)}")
            continue
        for skill_dir in sorted(bucket.iterdir()):
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
                continue
            expected[skill_dir.name] = skill_dir

    for name, skill_dir in sorted(expected.items()):
        v.symlink_ok(
            paths.repo / ".cursor/skills" / name,
            skill_dir,
            f"skill {name}",
        )
        agents_link = paths.repo / ".agents/skills" / name
        v.symlink_ok(agents_link, skill_dir, f".agents skill {name}")

    # Stale / dangling project skill links (e.g. removed skills)
    skills_dest = paths.repo / ".cursor/skills"
    if skills_dest.is_dir():
        for link in sorted(skills_dest.iterdir()):
            if link.is_symlink() and not link.exists():
                v.fail(f"dangling skill symlink: .cursor/skills/{link.name}")
            elif link.is_symlink() or link.is_dir():
                if link.name not in expected:
                    v.fail(f"unexpected project skill (not in ai-toolstack/skills): {link.name}")

    # Persian chat is user-global only — must not appear under project .cursor/skills
    project_persian = paths.repo / ".cursor/skills" / "persian-chat-reply"
    if project_persian.exists() or project_persian.is_symlink():
        v.fail("persian-chat-reply must not be under .cursor/skills (user-global only)")
    else:
        v.pass_("persian-chat-reply absent from project .cursor/skills")
    global_persian = Path.home() / ".cursor/skills" / "persian-chat-reply"
    expected_global = (
        paths.ai_toolstack / "cursor-agent-config/global-skills/persian-chat-reply"
    )
    v.symlink_ok(global_persian, expected_global, "global skill persian-chat-reply")


def verify_scripts(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Scripts")
    for script in (
        "ai-toolstack.sh",
        "verify-install.sh",
        "sync-ponytail-vendor.sh",
        "run-tests.sh",
    ):
        v.executable_ok(paths.scripts / script, f"script {script}")
    for module in (
        "cli/verify_agent_stack.py",
        "cli/verify_install.py",
    ):
        v.file_ok(paths.ai_toolstack / "lib" / module, f"module {module}")


def verify_binaries(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Host binaries")
    extend_tool_path()

    headroom_bin = (
        shutil.which("headroom")
        or Path.home() / ".local/share/pipx/venvs/headroom-ai/bin/headroom"
    )
    if isinstance(headroom_bin, str):
        headroom_path = Path(headroom_bin) if headroom_bin else None
    else:
        headroom_path = headroom_bin
    if headroom_path and headroom_path.is_file():
        ver = subprocess.run([str(headroom_path), "--version"], capture_output=True)
        if ver.returncode == 0:
            line = (ver.stdout or b"").decode().splitlines()[0] if ver.stdout else "unknown"
            v.pass_(f"headroom CLI ({line})")
        else:
            v.fail("headroom CLI not on PATH or broken")
    else:
        v.fail("headroom CLI not found — run: pipx install 'headroom-ai[mcp]' && ./ai-toolstack/install.sh")

    v.executable_ok(paths.ai_toolstack / "bin/mcp-lazy-serve.sh", "mcp-lazy-serve wrapper")
    v.executable_ok(paths.ai_toolstack / "bin/headroom-mcp-serve.sh", "headroom-mcp-serve wrapper")
    v.file_ok(paths.config / "headroom-env.sh", "headroom-env.sh")

    if _bash_node_toolchain(paths):
        node_bin = paths.local / "bin"
        v.pass_(f"node/npx toolchain ({node_bin})")
    else:
        v.fail("node/npx not resolvable (required for mcp-lazy)")


def verify_pipx_venvs(v: VerifyRunner) -> None:
    v.section("Pipx venv imports")
    v.pass_("Graphify/CRG pipx not required (removed from stack)")


def verify_mcp_lazy(v: VerifyRunner, paths: ToolstackPaths, quick: bool) -> None:
    v.section("mcp-lazy")
    if quick:
        v.warn("skipped mcp-lazy doctor (--quick)")
        return
    if not _bash_node_toolchain(paths):
        v.fail("node/npx missing — cannot run mcp-lazy doctor")
        return
    ok, out = _bash_npx_doctor(paths)
    if ok and any(x in out for x in ("4 server", "52 tool", "3 server", "49 tool", "Ready")):
        v.pass_("mcp-lazy doctor")
    elif ok:
        v.warn("mcp-lazy doctor ran but output unclear — run manually")
    else:
        v.fail("mcp-lazy doctor failed or timed out (120s)")


def verify_runtime_optional(v: VerifyRunner, paths: ToolstackPaths) -> None:
    v.section("Runtime (optional)")
    if paths.mcp_memory_file.is_file():
        v.pass_("MCP memory file present")
    else:
        v.pass_("MCP memory file will be created on first use")


def print_summary(v: VerifyRunner) -> int:
    ts_section("Summary")
    print(f"  Passed: {v.pass_count}  Warnings: {v.warn_count}  Failed: {v.fail_count}")
    if v.fail_count > 0:
        print()
        print("Install verification FAILED. Fix failures above and re-run:")
        print("  ./ai-toolstack/install.sh")
        print("  ./ai-toolstack/scripts/verify-install.sh")
        return 1
    if v.warn_count > 0:
        print()
        print("Install verification PASSED with warnings.")
    else:
        print()
        print("Install verification PASSED.")
    print()
    print("Next steps:")
    print("  npx mcp-lazy init")
    print("  Cursor → Reload Window")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify ai-toolstack install")
    parser.add_argument("--quick", action="store_true", help="Symlinks + configs only (no mcp-lazy doctor)")
    args = parser.parse_args(argv)

    paths = ToolstackPaths.discover()
    os.environ.setdefault("REPO_ROOT", str(paths.repo))
    print("[ai-toolstack] Verifying install...")

    v = VerifyRunner()
    verify_layout(v, paths)
    verify_repo_symlinks(v, paths)
    verify_runtime_not_tracked(v, paths)
    verify_user_symlinks(v, paths)
    verify_generated_configs(v, paths)
    verify_mcp_backends(v, paths)
    verify_cursor_hooks(v, paths)
    verify_cursor_rules(v, paths)
    verify_cursor_skills(v, paths)
    verify_scripts(v, paths)
    verify_binaries(v, paths)
    verify_pipx_venvs(v)
    verify_mcp_lazy(v, paths, args.quick)
    verify_runtime_optional(v, paths)
    return print_summary(v)


if __name__ == "__main__":
    raise SystemExit(main())
