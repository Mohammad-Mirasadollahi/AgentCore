"""SSH identity bootstrap for AgentCore connect (password once → pubkey forever).

Role: own dedicated AgentCore SSH key material and one-shot password pubkey install.
SoT: local identity file under ~/.ssh; remote authorized_keys after successful install.
Fail closed on empty password, non-OpenSSH install failure, or BatchMode probe failure;
never log or persist OS passwords; wipe askpass temps in finally.
"""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_IDENTITY_NAME = "id_ed25519_agentcore"


@dataclass(frozen=True)
class IdentityResult:
    """Local key paths plus previous public key line (for remote cleanup on rotate)."""

    private_path: Path
    public_path: Path
    old_public_line: str = ""


def default_identity_path() -> Path:
    return Path.home() / ".ssh" / DEFAULT_IDENTITY_NAME


def public_key_path(identity: Path) -> Path:
    return Path(f"{identity}.pub")


def read_public_line(identity: Path) -> str:
    pub = public_key_path(identity)
    if not pub.is_file():
        return ""
    return pub.read_text(encoding="utf-8").strip().splitlines()[0].strip()


def probe_batch_mode(
    ssh_target: str,
    identity: Path | str | None = None,
    *,
    connect_timeout: int = 15,
) -> bool:
    """Return True when non-interactive SSH with the AgentCore identity succeeds."""
    from agentcore_cli.remote_client import ssh_argv

    identity_file = str(identity) if identity else str(default_identity_path())
    expanded = Path(identity_file).expanduser()
    if identity is not None and not expanded.is_file():
        return False
    use_identity = str(expanded) if expanded.is_file() else None
    argv = ssh_argv(
        ssh_target,
        ["true"],
        batch_mode=True,
        connect_timeout=connect_timeout,
        identity_file=use_identity,
    )
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=max(connect_timeout + 5, 20),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def ensure_identity(*, rotate: bool = False, identity: Path | None = None) -> IdentityResult:
    """Create ed25519 AgentCore identity if missing; regenerate when *rotate* is True."""
    path = (identity or default_identity_path()).expanduser()
    pub = public_key_path(path)
    old_line = ""
    if path.is_file():
        old_line = read_public_line(path)
        if not rotate:
            return IdentityResult(private_path=path, public_path=pub, old_public_line=old_line)

    path.parent.mkdir(parents=True, exist_ok=True)
    if rotate and path.is_file():
        path.unlink(missing_ok=True)
        pub.unlink(missing_ok=True)

    cmd = [
        "ssh-keygen",
        "-t",
        "ed25519",
        "-N",
        "",
        "-f",
        str(path),
        "-C",
        "agentcore-connect",
        "-q",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise SystemExit(f"error: ssh-keygen failed: {detail or completed.returncode}")

    if sys.platform != "win32":
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        if pub.is_file():
            os.chmod(pub, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    return IdentityResult(private_path=path, public_path=pub, old_public_line=old_line)


def _write_askpass_script(password: str) -> Path:
    """Write a short-lived executable that prints *password* once for SSH_ASKPASS."""
    fd, name = tempfile.mkstemp(prefix="agentcore-askpass-", suffix=".sh")
    path = Path(name)
    try:
        os.close(fd)
        # Keep password out of argv of the parent; file mode 700 only.
        script = (
            "#!/bin/sh\n"
            "exec cat <<'AGENTCORE_ASKPASS_EOF'\n"
            f"{password}\n"
            "AGENTCORE_ASKPASS_EOF\n"
        )
        path.write_text(script, encoding="utf-8")
        if sys.platform != "win32":
            os.chmod(path, stat.S_IRWXU)
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _ssh_password_env(askpass: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["SSH_ASKPASS"] = str(askpass)
    env["SSH_ASKPASS_REQUIRE"] = "force"
    # Some OpenSSH builds still require DISPLAY/SSH_ASKPASS to activate.
    env.setdefault("DISPLAY", "agentcore-askpass")
    return env


def install_pubkey(
    ssh_target: str,
    identity: Path,
    password: str,
    *,
    connect_timeout: int = 30,
) -> None:
    """Install the local public key on *ssh_target* using a one-shot password auth."""
    if not password:
        raise SystemExit("error: empty SSH password; cannot install pubkey")
    pub_line = read_public_line(identity)
    if not pub_line:
        raise SystemExit(f"error: missing public key at {public_key_path(identity)}")

    remote = (
        "umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; "
        "chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys; "
        f"grep -qxF {shlex.quote(pub_line)} ~/.ssh/authorized_keys || "
        f"printf '%s\\n' {shlex.quote(pub_line)} >> ~/.ssh/authorized_keys"
    )
    askpass: Path | None = None
    try:
        askpass = _write_askpass_script(password)
        argv = [
            "ssh",
            "-o",
            "BatchMode=no",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            "-o",
            "NumberOfPasswordPrompts=1",
            "-o",
            f"ConnectTimeout={connect_timeout}",
            ssh_target,
            remote,
        ]
        completed = subprocess.run(
            argv,
            env=_ssh_password_env(askpass),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=max(connect_timeout + 15, 45),
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise SystemExit(
                f"error: failed to install SSH pubkey on {ssh_target}"
                + (f": {detail}" if detail else "")
            )
    finally:
        if askpass is not None:
            try:
                askpass.write_text("", encoding="utf-8")
            except OSError:
                pass
            askpass.unlink(missing_ok=True)


def remove_old_pubkey(
    ssh_target: str,
    identity: Path,
    old_public_line: str,
    *,
    connect_timeout: int = 15,
) -> bool:
    """Best-effort remove a prior AgentCore pubkey line from remote authorized_keys."""
    old = (old_public_line or "").strip()
    if not old:
        return True
    new_line = read_public_line(identity)
    if old == new_line:
        return True

    remote = (
        "test -f ~/.ssh/authorized_keys || exit 0; "
        f"grep -vxF {shlex.quote(old)} ~/.ssh/authorized_keys > ~/.ssh/authorized_keys.agentcore.tmp "
        "&& mv ~/.ssh/authorized_keys.agentcore.tmp ~/.ssh/authorized_keys "
        "|| rm -f ~/.ssh/authorized_keys.agentcore.tmp"
    )
    from agentcore_cli.remote_client import ssh_argv

    argv = ssh_argv(
        ssh_target,
        ["bash", "-lc", remote],
        batch_mode=True,
        connect_timeout=connect_timeout,
        identity_file=str(identity),
    )
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=max(connect_timeout + 5, 20)
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def bootstrap_ssh_auth(
    ssh_target: str,
    password: str,
    *,
    rotate: bool = False,
    identity: Path | None = None,
) -> IdentityResult:
    """Ensure local identity, install pubkey with password, optionally drop old remote line."""
    result = ensure_identity(rotate=rotate, identity=identity)
    install_pubkey(ssh_target, result.private_path, password)
    if rotate and result.old_public_line:
        remove_old_pubkey(ssh_target, result.private_path, result.old_public_line)
    if not probe_batch_mode(ssh_target, result.private_path):
        raise SystemExit(
            f"error: pubkey installed but BatchMode SSH still fails for {ssh_target}; "
            "check server authorized_keys and PermitRootLogin / AllowUsers"
        )
    return result
