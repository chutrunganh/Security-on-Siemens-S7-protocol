"""Đọc cấu trúc block trên PLC: chỉ list_blocks + list_blocks_of_type + get_block_info."""
import snap7
from snap7.type import Block

IP_ADDRESS = "172.16.16.145"
TRACK = 0
SLOT = 2


def main() -> None:
    plc = snap7.client.Client()
    try:
        plc.connect(IP_ADDRESS, TRACK, SLOT)

        summary = plc.list_blocks()
        print("All blocks:", summary)

        n = summary.OBCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.OB, n)
            for i in range(n):
                print(f"OB {int(nums[i])}:\n{plc.get_block_info(Block.OB, int(nums[i]))}")

        n = summary.FBCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.FB, n)
            for i in range(n):
                print(f"FB {int(nums[i])}:\n{plc.get_block_info(Block.FB, int(nums[i]))}")

        n = summary.FCCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.FC, n)
            for i in range(n):
                print(f"FC {int(nums[i])}:\n{plc.get_block_info(Block.FC, int(nums[i]))}")

        n = summary.SFBCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.SFB, n)
            for i in range(n):
                print(f"SFB {int(nums[i])}:\n{plc.get_block_info(Block.SFB, int(nums[i]))}")

        n = summary.SFCCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.SFC, n)
            for i in range(n):
                print(f"SFC {int(nums[i])}:\n{plc.get_block_info(Block.SFC, int(nums[i]))}")

        n = summary.DBCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.DB, n)
            for i in range(n):
                dbn = int(nums[i])
                print(f"DB {dbn}:\n{plc.get_block_info(Block.DB, dbn)}")

        n = summary.SDBCount
        if n > 0:
            nums = plc.list_blocks_of_type(Block.SDB, n)
            for i in range(n):
                print(f"SDB {int(nums[i])}:\n{plc.get_block_info(Block.SDB, int(nums[i]))}")
    finally:
        plc.disconnect()


if __name__ == "__main__":
    main()
