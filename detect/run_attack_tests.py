#!/usr/bin/env python3
"""Run attack scenarios on lab PLC via IDS VM and verify Suricata alerts."""

from __future__ import annotations

import os
import sys
import time

import paramiko

HOST = "172.16.16.143"
USER = "lubuntu"
PASSWORD = "lubuntu"
PLC_CANDIDATES = ["172.16.16.145", "172.16.16.44", "172.16.16.136"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")
RULE_FILES = ("s7comm.rules", "ics_dos.rules")

SCENARIO_EXPECTED_SIDS: dict[str, tuple[str, ...]] = {
    "Write Var": ("1000010", "1000011"),
    "DoS": ("1000040", "1000041", "1000042", "1000043"),
}


def connect() -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    return ssh


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 180) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def safe(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


def upload(ssh: paramiko.SSHClient, local: str, remote: str) -> None:
    sftp = ssh.open_sftp()
    sftp.put(local, remote)
    sftp.close()


def alert_count(ssh: paramiko.SSHClient) -> int:
    _, out, _ = run(ssh, "sudo wc -l < /var/log/suricata/fast.log 2>/dev/null || echo 0", timeout=30)
    try:
        return int(out.strip())
    except ValueError:
        return 0


def recent_alerts(ssh: paramiko.SSHClient, since_lines: int = 0) -> list[str]:
    cmd = "sudo tail -n +1 /var/log/suricata/fast.log 2>/dev/null"
    if since_lines:
        cmd = f"sudo tail -n +{since_lines + 1} /var/log/suricata/fast.log 2>/dev/null"
    _, out, _ = run(ssh, cmd, timeout=60)
    return [line for line in out.splitlines() if line.strip()]


def find_plc(ssh: paramiko.SSHClient) -> str | None:
    for ip in PLC_CANDIDATES:
        _, out, _ = run(ssh, f"nc -z -w2 {ip} 102 && echo OPEN || echo CLOSED", timeout=15)
        if "OPEN" in out:
            return ip
    return None


def deploy_rules(ssh: paramiko.SSHClient) -> None:
    run(ssh, "sudo mkdir -p /etc/suricata/rules", timeout=30)
    for name in RULE_FILES:
        local = os.path.join(RULES_DIR, name)
        if not os.path.isfile(local):
            raise FileNotFoundError(local)
        upload(ssh, local, f"/tmp/{name}")
        run(
            ssh,
            f"sudo mv /tmp/{name} /etc/suricata/rules/{name} "
            f"&& sudo chown root:root /etc/suricata/rules/{name} "
            f"&& sudo chmod 644 /etc/suricata/rules/{name}",
            timeout=30,
        )
    run(
        ssh,
        "sudo suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -8 "
        "&& sudo systemctl restart suricata",
        timeout=120,
    )


def sids_in_alerts(lines: list[str]) -> set[str]:
    found: set[str] = set()
    for line in lines:
        if "[**] [" in line:
            try:
                found.add(line.split("[**] [")[1].split(":")[0])
            except IndexError:
                pass
    return found


def expected_sids_for_scenario(name: str) -> set[str] | None:
    for key, sids in SCENARIO_EXPECTED_SIDS.items():
        if key in name:
            return set(sids)
    return None


def ensure_tools(ssh: paramiko.SSHClient) -> None:
    run(
        ssh,
        "sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive "
        "apt-get install -y -qq nmap netcat-openbsd python3-pip 2>/dev/null || true",
        timeout=300,
    )
    run(ssh, "python3 -m pip install --user python-snap7 -q 2>/dev/null || true", timeout=180)


def run_scenarios(ssh: paramiko.SSHClient, plc_ip: str) -> list[dict]:
    results: list[dict] = []
    upload(ssh, os.path.join(REPO, "attacks", "reconnaissance", "scanBlock.py"), "/tmp/scanBlock.py")
    upload(ssh, os.path.join(REPO, "attacks", "start_stop_plc", "start_stop_plc.py"), "/tmp/start_stop_plc.py")
    upload(ssh, os.path.join(REPO, "attacks", "start_stop_plc", "payloads.py"), "/tmp/payloads.py")
    upload(
        ssh,
        os.path.join(REPO, "attacks", "stuxnet_mitm_sim", "attacker", "test_readwrite_db_via_snap7.py"),
        "/tmp/write_db_lab.py",
    )
    upload(ssh, os.path.join(REPO, "attacks", "dos", "s7comm_dos.py"), "/tmp/s7comm_dos.py")

    scenarios = [
        ("Reconnaissance - nmap s7-info", f"nmap -p 102 --script s7-info {plc_ip} 2>&1 | tail -20"),
        (
            "Reconnaissance - list blocks",
            f"sed -i 's/172.16.16.145/{plc_ip}/' /tmp/scanBlock.py && python3 /tmp/scanBlock.py 2>&1 | head -20",
        ),
        (
            "Write Var - DB area",
            f'sed -i "s/172.16.16.44/{plc_ip}/" /tmp/write_db_lab.py && python3 /tmp/write_db_lab.py 2>&1',
        ),
        (
            "DoS - all phases (setup, tcp, szl)",
            f"python3 /tmp/s7comm_dos.py {plc_ip} --mode all --duration 10 --pause 8 2>&1",
        ),
        (
            "Start/Stop replay - check + stop",
            f"cd /tmp && python3 start_stop_plc.py {plc_ip} --check -v 2>&1; "
            f"python3 start_stop_plc.py {plc_ip} stop -v 2>&1",
        ),
    ]

    for name, cmd in scenarios:
        before = alert_count(ssh)
        print(f"\n--- Running: {name} ---")
        code, out, err = run(ssh, cmd)
        time.sleep(3)
        after = alert_count(ssh)
        new_lines = recent_alerts(ssh, before)
        results.append(
            {
                "scenario": name,
                "exit_code": code,
                "alerts_before": before,
                "alerts_after": after,
                "new_alerts": new_lines,
                "output_tail": safe((out + err)[-1500:]),
            }
        )
        print(safe(out[-800:]))
        if new_lines:
            print("NEW ALERTS:")
            for line in new_lines[-12:]:
                print(" ", safe(line))
            expected = expected_sids_for_scenario(name)
            if expected:
                missing = expected - sids_in_alerts(new_lines)
                if missing:
                    print(f"  Note: expected SIDs {sorted(expected)}, missing {sorted(missing)}")
                else:
                    print(f"  OK: saw SIDs {sorted(expected)}")
        else:
            print("No new alerts captured yet.")
    return results


def main() -> int:
    ssh = connect()
    try:
        print(f"Connected to IDS VM {HOST}")
        print("Deploying s7comm.rules + ics_dos.rules ...")
        deploy_rules(ssh)
        ensure_tools(ssh)
        plc = find_plc(ssh)
        if not plc:
            print("ERROR: No PLC reachable on TCP/102 in", PLC_CANDIDATES)
            return 1
        print(f"Target PLC: {plc}")
        print(f"Baseline alerts: {alert_count(ssh)}")
        results = run_scenarios(ssh, plc)
        print("\n========== SUMMARY ==========")
        for r in results:
            n = len(r["new_alerts"])
            print(f"- {r['scenario']}: {n} alert(s)")
        print("\nDoS manual: python3 attacks/dos/s7comm_dos.py <PLC>   # default --mode all")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
