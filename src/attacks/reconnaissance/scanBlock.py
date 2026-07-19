"""Đọc cấu trúc block trên PLC qua Snap7.

OpenPLC / S7 server mô phỏng thường hỗ trợ list_blocks nhưng get_block_info có thể timeout.
Dùng --list-only trong lab để tránh lỗi và vẫn sinh traffic List Blocks (Suricata sid:1000005).
"""
from __future__ import annotations

import argparse
import sys

import snap7
from snap7.type import Block

DEFAULT_IP = "172.16.16.145"
DEFAULT_RACK = 0
DEFAULT_SLOT = 2


def dump_block_info(
    plc: snap7.client.Client,
    block_type: int,
    label: str,
    count: int,
    list_only: bool,
) -> None:
    if count <= 0:
        return
    nums = plc.list_blocks_of_type(block_type, count)
    for i in range(count):
        num = int(nums[i])
        if list_only:
            print(f"{label} {num}: (list-only, no get_block_info)")
            continue
        try:
            info = plc.get_block_info(block_type, num)
            print(f"{label} {num}:\n{info}")
        except Exception as e:
            print(f"{label} {num}: get_block_info failed — {e!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="List PLC blocks via Snap7 (lab recon)")
    parser.add_argument("--ip", default=DEFAULT_IP, help="PLC IP")
    parser.add_argument("--rack", type=int, default=DEFAULT_RACK)
    parser.add_argument("--slot", type=int, default=DEFAULT_SLOT)
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Chỉ list_blocks / list_blocks_of_type; không gọi get_block_info (khuyên dùng OpenPLC)",
    )
    args = parser.parse_args()

    plc = snap7.client.Client()
    try:
        plc.connect(args.ip, args.rack, args.slot)
        summary = plc.list_blocks()
        print("All blocks:", summary)

        dump_block_info(plc, Block.OB, "OB", summary.OBCount, args.list_only)
        dump_block_info(plc, Block.FB, "FB", summary.FBCount, args.list_only)
        dump_block_info(plc, Block.FC, "FC", summary.FCCount, args.list_only)
        dump_block_info(plc, Block.SFB, "SFB", summary.SFBCount, args.list_only)
        dump_block_info(plc, Block.SFC, "SFC", summary.SFCCount, args.list_only)
        dump_block_info(plc, Block.DB, "DB", summary.DBCount, args.list_only)
        dump_block_info(plc, Block.SDB, "SDB", summary.SDBCount, args.list_only)
        return 0
    except Exception as e:
        print(f"ERROR: {e!r}", file=sys.stderr)
        return 1
    finally:
        try:
            plc.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
