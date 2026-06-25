#!/usr/bin/env python3
"""Deploy attack scripts + offline Python venv to Attacker VM (run once from Windows)."""
from __future__ import annotations

import os
import sys

import paramiko

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)

from tools.s7comm_gui.attacks import ATTACK_FILES, REPO_MANIFEST_FILES  # noqa: E402
from tools.s7comm_gui.config import (  # noqa: E402
    DEFAULT_ATTACKER_HOST,
    DEFAULT_ATTACKER_PASSWORD,
    DEFAULT_ATTACKER_REPO,
    DEFAULT_ATTACKER_USER,
    DEFAULT_PLC_IP,
)

HOST = DEFAULT_ATTACKER_HOST
USER = DEFAULT_ATTACKER_USER
PASSWORD = DEFAULT_ATTACKER_PASSWORD
REMOTE_REPO = DEFAULT_ATTACKER_REPO
LOCAL_WHEELS = os.path.join(REPO, "tools", "offline_wheels")
LOCAL_SNAP7 = os.path.join(REPO, "tools", "snap7-full-1.4.2")
REMOTE_SNAP7 = "/tmp/snap7-full-1.4.2"


def mkdir_p(sftp: paramiko.SFTPClient, path: str) -> None:
    parts = path.replace("\\", "/").split("/")
    cur = ""
    for p in parts:
        if not p:
            cur = "/"
            continue
        cur = f"{cur}/{p}" if cur != "/" else f"/{p}"
        try:
            sftp.stat(cur)
        except OSError:
            sftp.mkdir(cur)


def upload_dir(sftp: paramiko.SFTPClient, local_root: str, remote_root: str) -> int:
    count = 0
    for root, _dirs, files in os.walk(local_root):
        rel = os.path.relpath(root, local_root).replace("\\", "/")
        remote_dir = remote_root if rel == "." else f"{remote_root}/{rel}"
        mkdir_p(sftp, remote_dir)
        for name in files:
            sftp.put(os.path.join(root, name), f"{remote_dir}/{name}")
            count += 1
    return count


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str]:
    print(f"\n$ {cmd}")
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    text = out + err
    print(text)
    code = stdout.channel.recv_exit_status()
    return code, text


def main() -> int:
    if not os.path.isdir(LOCAL_SNAP7):
        print(f"Missing {LOCAL_SNAP7} — extract snap7-full-1.4.2 first.")
        return 1

    print(f"Connecting {USER}@{HOST} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    sftp = ssh.open_sftp()
    mkdir_p(sftp, REMOTE_REPO)

    for name in REPO_MANIFEST_FILES:
        local = os.path.join(REPO, name)
        if os.path.isfile(local):
            sftp.put(local, f"{REMOTE_REPO}/{name}")
            print(f"upload {name}")

    for rel in ATTACK_FILES:
        local = os.path.join(REPO, rel.replace("/", os.sep))
        remote = f"{REMOTE_REPO}/{rel}"
        mkdir_p(sftp, os.path.dirname(remote))
        sftp.put(local, remote)
        print(f"upload {rel}")

    n = upload_dir(sftp, LOCAL_WHEELS, f"{REMOTE_REPO}/offline_wheels")
    print(f"upload offline_wheels ({n} files)")

    n = upload_dir(sftp, LOCAL_SNAP7, REMOTE_SNAP7)
    print(f"upload snap7 source ({n} files)")
    sftp.close()

    run(ssh, f"cd {REMOTE_SNAP7}/build/unix && make -f x86_64_linux.mk", timeout=300)
    run(
        ssh,
        f"echo {PASSWORD} | sudo -S cp {REMOTE_SNAP7}/build/bin/x86_64-linux/libsnap7.so /usr/local/lib/ "
        f"&& echo {PASSWORD} | sudo -S ldconfig",
        timeout=60,
    )

    run(ssh, f"cd {REMOTE_REPO} && python3 -m venv .venv", timeout=120)
    run(
        ssh,
        f"cd {REMOTE_REPO} && .venv/bin/pip install --no-index "
        f"--find-links=offline_wheels setuptools-82.0.1-py3-none-any.whl wheel scapy "
        f"&& .venv/bin/pip install --no-index --no-build-isolation "
        f"offline_wheels/python_snap7-2.1.0.tar.gz",
        timeout=300,
    )

    code, _ = run(ssh, f'cd {REMOTE_REPO} && .venv/bin/python -c "import snap7; print(snap7.__version__)"', timeout=60)
    if code != 0:
        return 1
    code, _ = run(
        ssh,
        f'cd {REMOTE_REPO} && .venv/bin/python attacks/reconnaissance/scanBlock.py '
        f'--ip {DEFAULT_PLC_IP} --list-only',
        timeout=120,
    )
    if code != 0:
        return 1

    ssh.close()
    print("\nDeploy OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
