"""Stream Suricata alerts and optional tcpdump from IDS VM."""
from __future__ import annotations

import threading
from typing import Callable

import paramiko

from .config import CAPTURE_IFACE, SURICATA_FAST_LOG, TCPDUMP_FILTER

TrafficFn = Callable[[str], None]


class SuricataMonitor:
    """Tail Suricata fast.log over SSH."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        on_line: TrafficFn,
        on_status: TrafficFn,
        *,
        tail_lines: int = 30,
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.on_line = on_line
        self.on_status = on_status
        self.tail_lines = tail_lines
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, filter_s7: bool = True) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(filter_s7,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self, filter_s7: bool) -> None:
        try:
            self.on_status(f"[IDS] Kết nối {self.user}@{self.host} ...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.user, password=self.password, timeout=15)

            grep = ' | grep --line-buffered "ICS S7COMM"' if filter_s7 else ""
            # Không dùng sudo — lubuntu thường đọc được fast.log; hiện N dòng gần nhất rồi follow
            cmd = f"tail -n {self.tail_lines} -f {SURICATA_FAST_LOG}{grep}"
            self.on_line(f"[IDS] {cmd}")

            transport = ssh.get_transport()
            if transport is None:
                raise RuntimeError("No SSH transport")
            channel = transport.open_session()
            channel.get_pty()
            channel.exec_command(cmd)

            buf = ""
            while not self._stop.is_set():
                if channel.recv_ready():
                    data = channel.recv(4096).decode(errors="replace")
                    buf += data
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        if line.strip():
                            self.on_line(line.rstrip())
                elif channel.exit_status_ready():
                    code = channel.recv_exit_status()
                    if code != 0 and buf.strip():
                        self.on_line(buf.rstrip())
                    break
                else:
                    threading.Event().wait(0.1)
            channel.close()
            ssh.close()
            self.on_status("[IDS] Dừng đọc alert.")
        except Exception as e:
            self.on_line(f"[IDS] Lỗi: {e!r}")
            self.on_status(f"[IDS] Lỗi: {e!r}")


class TcpdumpMonitor:
    """Capture S7 port 102 summary lines from IDS (short bursts)."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        plc_ip: str,
        on_line: TrafficFn,
        on_status: TrafficFn,
        iface: str = CAPTURE_IFACE,
    ) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.plc_ip = plc_ip
        self.iface = iface
        self.on_line = on_line
        self.on_status = on_status
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, count: int = 50) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(count,),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self, count: int) -> None:
        try:
            self.on_line(f"[Tcpdump] {self.iface} host {self.plc_ip} port 102 (max {count} gói)")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.user, password=self.password, timeout=15)
            cmd = (
                f"echo {self.password} | sudo -S timeout 15 tcpdump -i {self.iface} -nn -c {count} "
                f"host {self.plc_ip} and {TCPDUMP_FILTER} 2>&1"
            )
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30, get_pty=True)
            for line in stdout:
                if self._stop.is_set():
                    break
                text = line.rstrip()
                if text and "password for" not in text.lower():
                    self.on_line(text)
            ssh.close()
            self.on_line("[Tcpdump] Xong.")
        except Exception as e:
            self.on_line(f"[Tcpdump] Lỗi: {e!r}")
