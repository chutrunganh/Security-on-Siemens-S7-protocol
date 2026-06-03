#!/usr/bin/env python3
"""Add ens33 to Suricata af-packet capture if missing."""
from pathlib import Path
import re
import sys

cfg_path = Path("/etc/suricata/suricata.yaml")
extra_iface = sys.argv[1] if len(sys.argv) > 1 else "ens33"
text = cfg_path.read_text()

if re.search(rf"(?m)^\s*- interface:\s*{re.escape(extra_iface)}\s*$", text):
    print(f"{extra_iface} already configured")
    sys.exit(0)

block = f"""  - interface: {extra_iface}
    cluster-id: 100
    cluster-type: cluster_flow
    defrag: yes
"""

text = re.sub(
    r"(?m)(^af-packet:\n\s*- interface: \w+\n(?:.*\n)*?)(?=^\S|\Z)",
    lambda m: m.group(1) + block,
    text,
    count=1,
)

cfg_path.write_text(text)
print(f"Added {extra_iface} to af-packet")
