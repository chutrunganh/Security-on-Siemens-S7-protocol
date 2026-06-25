"""Deploy and validate Suricata rules on IDS VM."""
from __future__ import annotations

import os
from typing import Callable

import paramiko

from .config import (
    CAPTURE_IFACE,
    HOME_NET,
    PATCH_SCRIPT,
    REPO_ROOT,
    RULE_FILES,
    RULES_DIR,
)

LogFn = Callable[[str], None]


class SuricataDeployer:
    def __init__(self, host: str, user: str, password: str, log: LogFn) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.log = log

    def _connect(self) -> paramiko.SSHClient:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.user, password=self.password, timeout=15)
        return ssh

    def _run(self, ssh: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str]:
        self.log(f">>> {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        code = stdout.channel.recv_exit_status()
        for line in (out + err).splitlines():
            if line.strip():
                self.log(line.rstrip())
        return code, out + err

    def upload_rules(self, ssh: paramiko.SSHClient | None = None) -> int:
        own = ssh is None
        if own:
            ssh = self._connect()
        try:
            sftp = ssh.open_sftp()
            self._run(ssh, "sudo mkdir -p /etc/suricata/rules", timeout=30)
            for name in RULE_FILES:
                local = os.path.join(RULES_DIR, name)
                tmp = f"/tmp/{name}"
                sftp.put(local, tmp)
                self._run(
                    ssh,
                    f"sudo mv {tmp} /etc/suricata/rules/{name} "
                    f"&& sudo chown root:root /etc/suricata/rules/{name} "
                    f"&& sudo chmod 644 /etc/suricata/rules/{name}",
                    timeout=30,
                )
                self.log(f"Uploaded {name}")
            sftp.close()
            return 0
        finally:
            if own:
                ssh.close()

    def validate_and_restart(self, ssh: paramiko.SSHClient | None = None) -> int:
        own = ssh is None
        if own:
            ssh = self._connect()
        try:
            code, _ = self._run(
                ssh,
                "sudo suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -12",
                timeout=120,
            )
            if code != 0:
                self.log("suricata -T FAILED")
                return code
            code, _ = self._run(ssh, "sudo systemctl restart suricata && sleep 1 && systemctl is-active suricata", timeout=60)
            return code
        finally:
            if own:
                ssh.close()

    def patch_yaml(self, home_net: str, iface: str, ssh: paramiko.SSHClient | None = None) -> int:
        own = ssh is None
        if own:
            ssh = self._connect()
        try:
            sftp = ssh.open_sftp()
            sftp.put(PATCH_SCRIPT, "/tmp/patch_suricata_yaml.py")
            sftp.close()
            code, _ = self._run(
                ssh,
                f"sudo cp /etc/suricata/suricata.yaml "
                f"/etc/suricata/suricata.yaml.bak.gui && "
                f"sudo python3 /tmp/patch_suricata_yaml.py '{home_net}' '{iface}'",
                timeout=60,
            )
            return code
        finally:
            if own:
                ssh.close()

    def deploy_rules_only(self) -> int:
        self.log(f"[Deploy] Rules only → {self.host}")
        ssh = self._connect()
        try:
            if self.upload_rules(ssh) != 0:
                return 1
            return self.validate_and_restart(ssh)
        finally:
            ssh.close()

    def deploy_full(self, home_net: str = HOME_NET, iface: str = CAPTURE_IFACE) -> int:
        self.log(f"[Deploy] Full (rules + suricata.yaml) → {self.host}")
        ssh = self._connect()
        try:
            if self.upload_rules(ssh) != 0:
                return 1
            if self.patch_yaml(home_net, iface, ssh) != 0:
                return 1
            return self.validate_and_restart(ssh)
        finally:
            ssh.close()

    def validate_remote(self) -> int:
        ssh = self._connect()
        try:
            code, _ = self._run(ssh, "sudo suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -15", timeout=120)
            return code
        finally:
            ssh.close()

    def fetch_remote_status(self) -> int:
        ssh = self._connect()
        try:
            self._run(ssh, "systemctl is-active suricata", timeout=20)
            self._run(
                ssh,
                "grep -n 'HOME_NET\\|rule-files\\|s7comm\\|- interface:' "
                "/etc/suricata/suricata.yaml | head -20",
                timeout=20,
            )
            self._run(ssh, "ls -la /etc/suricata/rules/*.rules 2>/dev/null | tail -10", timeout=20)
            return 0
        finally:
            ssh.close()
