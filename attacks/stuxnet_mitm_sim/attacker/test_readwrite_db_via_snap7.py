"""Ghi setpoint DB1.DBW2 trên PLC lab (Snap7)."""
from __future__ import annotations

import argparse
import sys
from time import sleep

import snap7

DEFAULT_IP = "172.16.16.44"
DEFAULT_RACK = 0
DEFAULT_SLOT = 2


def write_and_read_db(plc: snap7.client.Client, value_to_write: int) -> None:
    plc.db_write(1, 2, value_to_write.to_bytes(2, byteorder="big"))
    sleep(1)
    i_sim = plc.db_read(1, 0, 2)
    i_set = plc.db_read(1, 2, 2)
    status = plc.db_read(2, 0, 1)
    print(
        int.from_bytes(i_sim, "big", signed=False),
        "   |   ",
        int.from_bytes(i_set, "big", signed=False),
        "   |   ",
        int.from_bytes(status, "big", signed=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write/read DB lab values via Snap7")
    parser.add_argument("--ip", default=DEFAULT_IP, help="PLC IP")
    parser.add_argument("--rack", type=int, default=DEFAULT_RACK)
    parser.add_argument("--slot", type=int, default=DEFAULT_SLOT)
    args = parser.parse_args()

    plc = snap7.client.Client()
    try:
        plc.connect(args.ip, args.rack, args.slot)
        print("Current Speed | Setpoint Speed | Centrifuge Status")
        print("--------------------------------------------------")
        write_and_read_db(plc, 1200)
        sleep(5)
        write_and_read_db(plc, 2000)
        return 0
    finally:
        try:
            plc.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
