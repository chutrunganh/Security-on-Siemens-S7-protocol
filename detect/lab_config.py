"""Shared lab topology for detect/ scripts and thesis evaluation."""
from __future__ import annotations

# Management / NAT (SSH from Windows host)
IDS_HOST = "172.16.16.7"
IDS_USER = "lubuntu"
IDS_PASSWORD = "lubuntu"

ATTACKER_HOST = "172.16.16.5"
ATTACKER_USER = "ubuntu"
ATTACKER_PASSWORD = "ubuntu"
ATTACKER_REPO = "/home/ubuntu/Thesis"

HMI_HOST = "172.16.16.6"

# PLC on mirrored OT segment (Attacker reaches PLC via lab routing)
PLC_IP = "192.168.50.10"
PLC_RACK = 0
PLC_SLOT = 2

HOME_NET = "[192.168.50.0/24,192.168.60.0/24]"
CAPTURE_IFACE = "ens33"

SURICATA_FAST_LOG = "/var/log/suricata/fast.log"
SURICATA_STATS_LOG = "/var/log/suricata/stats.log"
SURICATA_EVE_LOG = "/var/log/suricata/eve.json"

RULE_FILES = ("s7comm.rules", "ics_dos.rules", "s7comm_malformed.rules")

# DoS thresholds from ics_dos.rules (for safety-margin reporting)
DOS_THRESHOLDS = {
    "1000040": {"count": 40, "seconds": 10, "desc": "TCP SYN flood :102"},
    "1000041": {"count": 25, "seconds": 10, "desc": "Setup Communication flood"},
    "1000042": {"count": 25, "seconds": 10, "desc": "Read SZL flood"},
    "1000043": {"count": 80, "seconds": 10, "desc": "S7 Job request flood"},
}
