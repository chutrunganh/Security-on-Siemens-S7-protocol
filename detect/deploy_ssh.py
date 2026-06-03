#!/usr/bin/env python3
"""Helper to run commands on the IDS VM via SSH."""
import sys
import paramiko

HOST = "172.16.16.143"
USER = "lubuntu"
PASSWORD = "lubuntu"


def run(cmd: str, timeout: int = 60) -> tuple[int, str, str]:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    code = stdout.channel.recv_exit_status()
    ssh.close()
    return code, out, err


def safe_print(text: str, file=None) -> None:
    safe = text.encode("ascii", errors="replace").decode("ascii")
    end = "" if safe.endswith("\n") else "\n"
    print(safe, end=end, file=file)


def main() -> None:
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "hostname"
    code, out, err = run(cmd)
    if out:
        safe_print(out)
    if err:
        safe_print(err, file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
