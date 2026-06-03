#!/usr/bin/env python3
from pathlib import Path
import re
import sys

cfg_path = Path("/etc/suricata/suricata.yaml")
home = sys.argv[1]
iface = sys.argv[2]
text = cfg_path.read_text()

text = re.sub(
    r"(?m)^(\s*HOME_NET:\s*).*$",
    rf'\1"{home}"',
    text,
    count=1,
)

for rules_name in ("s7comm.rules", "ics_dos.rules"):
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
print("HOME_NET and rule-files:")
for line in text.splitlines():
    if "HOME_NET" in line or "rule-files" in line or "s7comm" in line or "- interface:" in line:
        print(line)
