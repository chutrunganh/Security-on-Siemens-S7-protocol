"""Shared lab topology for detect/ scripts and thesis evaluation."""
from __future__ import annotations

# Management / NAT (SSH from Windows host — not used in Suricata !$SUPERVISOR_NET)
IDS_HOST = "172.16.16.7"
IDS_USER = "lubuntu"
IDS_PASSWORD = "lubuntu"

ATTACKER_HOST = "172.16.16.5"
ATTACKER_USER = "ubuntu"
ATTACKER_PASSWORD = "ubuntu"
ATTACKER_REPO = "/home/ubuntu/Thesis"

HMI_HOST = "172.16.16.6"
ROUTER_HOST = "172.16.16.1"

# Lab Local-NIC addresses (ens33 segments — used by Suricata address-groups)
HMI_LAB_IP = "192.168.60.10"
IDS_LAB_IP = "192.168.60.30"
# Design: 192.168.70.20 on EXTERNAL_NET; current lab uses 60.20 on supervisory segment.
ATTACKER_LAB_IP = "192.168.60.20"
ATTACKER_LAB_IP_DESIGN = "192.168.70.20"
ROUTER_LAB_IPS = ("192.168.50.1", "192.168.60.1", "192.168.70.1")

# PLC on mirrored OT segment (Attacker reaches PLC via lab routing)
PLC_IP = "192.168.50.10"
PLC_RACK = 0
PLC_SLOT = 2

# Lab network segments (see Chapter 3 topology).
CONTROL_NET = "192.168.50.0/24"      # PLC / controller segment (TCP/102)
SUPERVISOR_NET = "192.168.60.0/24"   # GUI / docs label — authorized HMI / engineering
EXTERNAL_NET = "192.168.70.0/24"     # attacker segment (design target; not reconfigured now)

# Suricata SUPERVISOR: explicit authorized hosts only (not whole 192.168.60.0/24).
# Attacker at 192.168.60.20 shares the segment but must NOT be whitelisted.
_SUPERVISOR_ALLOWED_HOSTS = (
    HMI_LAB_IP,
    IDS_LAB_IP,
    *ROUTER_LAB_IPS,
)


def _slash32(ip: str) -> str:
    return ip if "/" in ip else f"{ip}/32"


def _suricata_host_group(hosts: tuple[str, ...]) -> str:
    return "[" + ",".join(_slash32(h) for h in hosts) + "]"


SUPERVISOR_NET_SURICATA = _suricata_host_group(_SUPERVISOR_ALLOWED_HOSTS)
HOME_NET_SURICATA = f"[{CONTROL_NET},{SUPERVISOR_NET_SURICATA[1:-1]}]"

# Legacy alias used in docs / eval reporting (segment labels only).
HOME_NET = f"[{CONTROL_NET},{SUPERVISOR_NET}]"

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
