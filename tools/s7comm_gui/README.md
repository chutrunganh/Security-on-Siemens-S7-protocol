# S7comm Lab — GUI tools

Two standalone desktop applications (tkinter):

| App | Launch |
|-----|--------|
| **Attack Tool** | `python -m tools.s7comm_gui.attack_app` or `tools\run_attack_gui.bat` |
| **Suricata Rules Tool** | `python -m tools.s7comm_gui.rules_app` or `tools\run_rules_gui.bat` |
| **Both windows** | `tools\run_s7_gui.bat` |

## Attack Tool

Runs attack scenarios on the Attacker VM via SSH (recon, write, DoS, malformed, Start/Stop). Output goes to the execution log only — no Suricata alert capture in this window.

## Rules Tool

View rules in `detect/rules/` and monitor alerts (`fast.log`) on the IDS VM — switching to the Alerts tab starts tailing automatically. Deploy rules from the host: `python detect\deploy_ids.py`.

## Lab defaults

See `tools/s7comm_gui/config.py` for PLC, Attacker, and IDS addresses.

**Warning:** Use only on an isolated lab network.
