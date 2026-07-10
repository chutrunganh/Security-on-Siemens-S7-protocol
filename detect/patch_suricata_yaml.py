#!/usr/bin/env python3
"""Patch /etc/suricata/suricata.yaml for the thesis lab.

Usage:
    patch_suricata_yaml.py CONTROL_NET SUPERVISOR_NET EXTERNAL_NET IFACE [HOME_NET]

Sets:
  - HOME_NET        = protected segments (default [CONTROL_NET,SUPERVISOR_NET members])
  - CONTROL_NET     = PLC / controller segment
  - SUPERVISOR_NET  = authorized HMI / engineering (+ optional infra hosts)
  - EXTERNAL_NET    = attacker segment
  - capture interface
and ensures the thesis rule-files are referenced.
"""
from pathlib import Path
import re
import sys

cfg_path = Path("/etc/suricata/suricata.yaml")
control = sys.argv[1]
supervisor = sys.argv[2]
external = sys.argv[3]
iface = sys.argv[4]
text = cfg_path.read_text()

home = sys.argv[5] if len(sys.argv) > 5 else f"[{control},{supervisor}]"


def set_group(text: str, name: str, value: str) -> str:
    """Set an address-group; create it just after HOME_NET if missing."""
    if re.search(rf"(?m)^(\s*){name}:\s*", text):
        return re.sub(rf"(?m)^(\s*{name}:\s*).*$", rf'\1"{value}"', text, count=1)
    return re.sub(
        r"(?m)^(\s*)(HOME_NET:.*)$",
        rf'\1\2\n\1{name}: "{value}"',
        text,
        count=1,
    )


# HOME_NET covers the protected control + supervisory segments.
text = set_group(text, "HOME_NET", home)
# Custom address-groups referenced by the thesis rules.
text = set_group(text, "CONTROL_NET", control)
text = set_group(text, "SUPERVISOR_NET", supervisor)
text = set_group(text, "EXTERNAL_NET", external)

for rules_name in ("s7comm.rules", "ics_dos.rules", "s7comm_malformed.rules"):
    if rules_name not in text:
        text = re.sub(
            r"(?m)^(rule-files:\s*)$",
            rf"\1\n  - {rules_name}",
            text,
            count=1,
        )

text = re.sub(
    r"(?m)^(\s*- interface:\s*)eth0\s*$",
    rf"\1{iface}",
    text,
    count=1,
)

cfg_path.write_text(text)
print(f"Patched {cfg_path}")
print("Address-groups, rule-files and interface:")
for line in text.splitlines():
    if (
        "HOME_NET" in line
        or "CONTROL_NET" in line
        or "SUPERVISOR_NET" in line
        or "EXTERNAL_NET" in line
        or "rule-files" in line
        or "s7comm" in line
        or "- interface:" in line
    ):
        print(line)
