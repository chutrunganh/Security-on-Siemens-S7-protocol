#!/usr/bin/env python3
"""Deploy Suricata S7comm rules to the IDS VM."""
from __future__ import annotations

import os
import sys
import textwrap

import paramiko

HOST = "172.16.16.7"
USER = "lubuntu"
PASSWORD = "lubuntu"
RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")
RULE_FILES = ("s7comm.rules", "ics_dos.rules", "s7comm_malformed.rules")
CAPTURE_IFACE = "ens33"
HOME_NET = "[192.168.50.0/24,192.168.60.0/24]"


def connect() -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    return ssh


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    print(f"\n>>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.rstrip().encode("ascii", errors="replace").decode("ascii"))
    if err.strip():
        print(err.rstrip().encode("ascii", errors="replace").decode("ascii"), file=sys.stderr)
    return code, out, err


def upload_rules(ssh: paramiko.SSHClient) -> None:
    sftp = ssh.open_sftp()
    run(ssh, "sudo mkdir -p /etc/suricata/rules")
    for name in RULE_FILES:
        local = os.path.join(RULES_DIR, name)
        remote = f"/etc/suricata/rules/{name}"
        tmp = f"/tmp/{name}"
        sftp.put(local, tmp)
        run(
            ssh,
            f"sudo mv {tmp} {remote} && sudo chown root:root {remote} && sudo chmod 644 {remote}",
        )
    sftp.close()


def install_suricata(ssh: paramiko.SSHClient) -> None:
    code, out, _ = run(ssh, "command -v suricata || true")
    if "suricata" in out:
        print("Suricata already installed.")
        return

    script = textwrap.dedent(
        """\
        set -e
        export DEBIAN_FRONTEND=noninteractive
        sudo apt-get update -qq
        if ! apt-cache show suricata >/dev/null 2>&1; then
          sudo add-apt-repository -y ppa:oisf/suricata-stable
          sudo apt-get update -qq
        fi
        sudo apt-get install -y suricata jq
        """
    )
    run(ssh, script, timeout=900)


def configure_suricata(ssh: paramiko.SSHClient) -> None:
    sftp = ssh.open_sftp()
    sftp.put(os.path.join(os.path.dirname(__file__), "patch_suricata_yaml.py"), "/tmp/patch_suricata_yaml.py")
    sftp.close()

    run(
        ssh,
        f"sudo cp /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.bak.$(date +%Y%m%d%H%M%S) && "
        f"sudo python3 /tmp/patch_suricata_yaml.py '{HOME_NET}' '{CAPTURE_IFACE}' && "
        "grep -n 'HOME_NET\\|rule-files\\|s7comm\\|interface:' /etc/suricata/suricata.yaml | head -25",
    )


def validate_and_start(ssh: paramiko.SSHClient) -> None:
    run(ssh, "sudo suricata -T -c /etc/suricata/suricata.yaml -v")
    run(ssh, "sudo systemctl enable suricata")
    run(ssh, "sudo systemctl restart suricata")
    run(ssh, "sleep 2 && systemctl is-active suricata && sudo suricata --list-app-layer-protos 2>/dev/null | head -5 || true")
    run(ssh, "sudo tail -n 20 /var/log/suricata/suricata.log 2>/dev/null || sudo journalctl -u suricata -n 20 --no-pager")


def main() -> int:
    for name in RULE_FILES:
        path = os.path.join(RULES_DIR, name)
        if not os.path.isfile(path):
            print(f"Missing rules file: {path}", file=sys.stderr)
            return 1

    ssh = connect()
    try:
        print(f"Connected to {HOST}")
        install_suricata(ssh)
        upload_rules(ssh)
        configure_suricata(ssh)
        validate_and_start(ssh)
        print("\nDeployment complete.")
        print(f"Rules: /etc/suricata/rules/{{{', '.join(RULE_FILES)}}}")
        print(f"Capture interface: {CAPTURE_IFACE}")
        print(f"HOME_NET: {HOME_NET}")
        print("Alerts: /var/log/suricata/eve.json")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
