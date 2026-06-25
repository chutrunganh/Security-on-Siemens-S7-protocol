"""Execute attacks on Attacker VM via SSH (.venv Python, no auto-upload)."""
from __future__ import annotations

import os
import subprocess
import threading
from typing import Callable

import paramiko

from .attacks import SNAP7_SCENARIOS, AttackScenario
from .config import DEFAULT_ATTACKER_REPO, REPO_ROOT
from .suricata_deploy import SuricataDeployer

LogFn = Callable[[str], None]


class RemoteRunner:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        log: LogFn,
        repo: str = DEFAULT_ATTACKER_REPO,
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.log = log
        self.repo = repo.rstrip("/")
        self._ssh: paramiko.SSHClient | None = None
        self._lock = threading.Lock()
        self._env_ready = False
        self._nmap_ready = False

    def connect(self) -> None:
        with self._lock:
            if self._ssh is not None:
                return
            self.log(f"[Attacker] Connecting to {self.user}@{self.host} ...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.user, password=self.password, timeout=15)
            self._ssh = ssh
            self.log("[Attacker] Connected.")

    def close(self) -> None:
        with self._lock:
            if self._ssh:
                self._ssh.close()
                self._ssh = None

    def _ssh_client(self) -> paramiko.SSHClient:
        if self._ssh is None:
            raise RuntimeError("Not connected")
        return self._ssh

    def run_shell(
        self,
        cmd: str,
        timeout: int = 600,
        cancel: threading.Event | None = None,
        *,
        log_cmd: bool = True,
        log_output: bool = True,
    ) -> tuple[int, str]:
        self.connect()
        ssh = self._ssh_client()
        if log_cmd:
            self.log(f"[CMD] {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
        channel = stdout.channel
        chunks: list[str] = []
        while True:
            if cancel and cancel.is_set():
                channel.close()
                self.log("[CMD] Cancelled.")
                return 130, "".join(chunks)
            if channel.recv_ready():
                data = channel.recv(4096).decode(errors="replace")
                if data:
                    chunks.append(data)
                    for line in data.splitlines():
                        if log_output and line.strip():
                            self.log(line.rstrip())
            if channel.exit_status_ready():
                while channel.recv_ready():
                    data = channel.recv(4096).decode(errors="replace")
                    if data:
                        chunks.append(data)
                        for line in data.splitlines():
                            if log_output and line.strip():
                                self.log(line.rstrip())
                break
            if not channel.recv_ready():
                threading.Event().wait(0.05)
        code = channel.recv_exit_status()
        err = stderr.read().decode(errors="replace")
        if log_output and err.strip():
            for line in err.splitlines():
                self.log(f"[stderr] {line}")
        return code, "".join(chunks)

    def probe_plc(self, plc_ip: str) -> bool:
        _, out = self.run_shell(
            f"nc -z -w2 {plc_ip} 102 && echo OPEN || echo CLOSED",
            timeout=20,
        )
        return "OPEN" in out

    def _check_remote(self, cmd: str, timeout: int = 30) -> bool:
        code, out = self.run_shell(cmd, timeout=timeout, log_cmd=False, log_output=False)
        return code == 0 and "OK" in out

    def ensure_nmap(self) -> None:
        if self._nmap_ready:
            return
        if self._check_remote("command -v nmap >/dev/null && echo OK"):
            self._nmap_ready = True
            return
        self.log("[Attacker] Installing nmap ...")
        self.run_shell(
            "sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq && "
            "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nmap netcat-openbsd 2>&1",
            timeout=300,
        )
        self._nmap_ready = True

    def ensure_python_env(self, need_snap7: bool = False) -> None:
        if self._env_ready:
            return
        venv_py = f"{self.repo}/.venv/bin/python"
        if not self._check_remote(f'test -x "{venv_py}" && echo OK'):
            raise RuntimeError(
                f"Chưa có {venv_py} trên Attacker. "
                "Chạy một lần từ máy Windows: python tools/s7comm_gui/deploy_attacker.py"
            )
        if need_snap7:
            ok = self._check_remote(
                f'cd "{self.repo}" && .venv/bin/python -c "import snap7" && echo OK'
            )
            if not ok:
                raise RuntimeError("snap7 chưa có trong .venv trên Attacker.")
        self._env_ready = True

    def deploy_rules(self) -> int:
        deployer = SuricataDeployer(self.host, self.user, self.password, self.log)
        return deployer.deploy_rules_only()

    def run_scenario(
        self,
        scenario: AttackScenario,
        plc_ip: str,
        rack: int,
        slot: int,
        cancel: threading.Event | None = None,
    ) -> int:
        if scenario.id == "recon_nmap":
            self.ensure_nmap()
        else:
            self.ensure_python_env(need_snap7=scenario.id in SNAP7_SCENARIOS)
        cmd = scenario.build_remote_cmd(plc_ip, rack, slot, self.repo)
        code, _ = self.run_shell(cmd, cancel=cancel, log_cmd=False)
        return code


class LocalRunner:
    def __init__(self, log: LogFn) -> None:
        self.log = log
        self.repo = REPO_ROOT

    def run_shell(
        self,
        cmd: str,
        cancel: threading.Event | None = None,
        timeout: int = 600,
    ) -> tuple[int, str]:
        self.log(f"[CMD] {cmd}")
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.repo,
        )
        out_chunks: list[str] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            if cancel and cancel.is_set():
                proc.kill()
                self.log("[CMD] Cancelled.")
                return 130, "".join(out_chunks)
            out_chunks.append(line)
            self.log(line.rstrip())
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            self.log("[CMD] Timeout.")
            return 124, "".join(out_chunks)
        return proc.returncode or 0, "".join(out_chunks)

    def probe_plc(self, plc_ip: str) -> bool:
        code, out = self.run_shell(
            f'python -c "import socket; s=socket.socket(); s.settimeout(2); '
            f"s.connect(('{plc_ip}', 102)); s.close(); print('OPEN')\"",
            timeout=10,
        )
        return code == 0 and "OPEN" in out

    def run_scenario(
        self,
        scenario: AttackScenario,
        plc_ip: str,
        rack: int,
        slot: int,
        cancel: threading.Event | None = None,
    ) -> int:
        cmd = scenario.build_local_cmd(plc_ip, self.repo, rack, slot)
        self.log(f"=== {scenario.name} ===")
        if scenario.expected_sids:
            self.log(f"Expected SID: {', '.join(scenario.expected_sids)}")
        code, _ = self.run_shell(cmd, cancel=cancel)
        self.log(f"=== Finished ({scenario.id}) exit={code} ===")
        return code
