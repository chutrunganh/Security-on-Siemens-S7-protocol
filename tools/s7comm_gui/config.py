"""Default lab settings for S7comm GUI tools."""
from __future__ import annotations

import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# PLC — IP local trên mạng lab (Attacker gửi gói tới địa chỉ này)
DEFAULT_PLC_IP = "192.168.50.10"
# Attacker lab-segment address (own LAN, tách khỏi vùng supervisory)
DEFAULT_ATTACKER_LAB_IP = "192.168.70.20"
DEFAULT_ATTACKER_HOST = "172.16.16.5"
DEFAULT_HMI_IP = "172.16.16.6"
DEFAULT_IDS_HOST = "172.16.16.7"

# Attacker VM — chạy script tấn công (uv project root trên Attacker)
DEFAULT_ATTACKER_USER = "ubuntu"
DEFAULT_ATTACKER_PASSWORD = "ubuntu"
DEFAULT_ATTACKER_REPO = "/home/ubuntu/Thesis"

# IDS VM — Suricata / deploy luật
DEFAULT_IDS_USER = "lubuntu"
DEFAULT_IDS_PASSWORD = "lubuntu"

DEFAULT_RACK = 0
DEFAULT_SLOT = 2

RULES_DIR = os.path.join(REPO_ROOT, "detect", "rules")
PATCH_SCRIPT = os.path.join(REPO_ROOT, "detect", "patch_suricata_yaml.py")
RULE_FILES = ("s7comm.rules", "ics_dos.rules", "s7comm_malformed.rules")
# Suricata — các phân vùng mạng lab (xem topology Chương 3)
CONTROL_NET = "192.168.50.0/24"      # PLC / controller segment (TCP/102)
SUPERVISOR_NET = "192.168.60.0/24"   # HMI / engineering hợp lệ
EXTERNAL_NET = "192.168.70.0/24"     # vùng attacker
# HOME_NET = vùng control + supervisory được bảo vệ (biến builtin của Suricata)
HOME_NET = f"[{CONTROL_NET},{SUPERVISOR_NET}]"
# ens33: mirror traffic tới PLC 192.168.50.x | ens37: NAT quản lý 172.16.16.x
CAPTURE_IFACE = "ens33"
CAPTURE_IFACE_MGMT = "ens37"

SURICATA_FAST_LOG = "/var/log/suricata/fast.log"
TCPDUMP_FILTER = "port 102"
