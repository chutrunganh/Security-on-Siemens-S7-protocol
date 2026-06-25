#!/usr/bin/env python3
"""Run attack scenarios from Attacker VM; verify Suricata alerts on IDS.

Deploy Suricata rules separately (once, or after editing rules):
  python detect/deploy_ids.py

Full evaluation (baseline + metrics + LaTeX tables):
  python detect/eval_rules.py
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from typing import Callable

import paramiko

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab_config import (
    ATTACKER_HOST,
    ATTACKER_PASSWORD,
    ATTACKER_REPO,
    ATTACKER_USER,
    IDS_HOST,
    IDS_PASSWORD,
    IDS_USER,
    PLC_IP,
    PLC_RACK,
    PLC_SLOT,
    SURICATA_FAST_LOG,
)
from lab_scenarios import DEFAULT_ORDER, SCENARIOS, EvalScenario

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    build_cmd: Callable[[str, int, int, str], str]
    expected_sids: tuple[str, ...]
    timeout: int = 180


def _wrap(sc: EvalScenario) -> Scenario:
    return Scenario(
        sc.id,
        sc.title,
        sc.build_cmd,
        sc.expected_sids,
        sc.timeout,
    )


SCENARIO_MAP: dict[str, Scenario] = {sid: _wrap(SCENARIOS[sid]) for sid in DEFAULT_ORDER}


def connect(host: str, user: str, password: str) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=20)
    return ssh


def run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 180) -> tuple[int, str, str]:
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def safe(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


def alert_count(ids: paramiko.SSHClient) -> int:
    _, out, _ = run(ids, f"sudo wc -l < {SURICATA_FAST_LOG} 2>/dev/null || echo 0", timeout=30)
    try:
        return int(out.strip())
    except ValueError:
        return 0


def recent_alerts(ids: paramiko.SSHClient, since_lines: int = 0) -> list[str]:
    cmd = f"sudo tail -n +{since_lines + 1} {SURICATA_FAST_LOG} 2>/dev/null"
    _, out, _ = run(ids, cmd, timeout=60)
    return [line for line in out.splitlines() if line.strip()]


def find_plc(attacker: paramiko.SSHClient, override: str | None = None) -> str | None:
    ip = override or PLC_IP
    _, out, _ = run(attacker, f"nc -z -w3 {ip} 102 && echo OPEN || echo CLOSED", timeout=15)
    return ip if "OPEN" in out else None


def sids_in_alerts(lines: list[str]) -> set[str]:
    found: set[str] = set()
    for line in lines:
        if "[**] [" in line:
            try:
                found.add(line.split("[**] [")[1].split(":")[0])
            except IndexError:
                pass
    return found


def run_one_scenario(
    ids: paramiko.SSHClient,
    attacker: paramiko.SSHClient,
    scenario: Scenario,
    plc_ip: str,
    rack: int,
    slot: int,
    repo: str,
) -> dict:
    before = alert_count(ids)
    cmd = scenario.build_cmd(plc_ip, rack, slot, repo)
    print(f"\n--- Running: {scenario.title} [{scenario.id}] ---")
    code, out, err = run(attacker, cmd, timeout=scenario.timeout)
    time.sleep(4)
    after = alert_count(ids)
    new_lines = recent_alerts(ids, before)
    print(safe(out[-800:]))
    expected = set(scenario.expected_sids)
    observed = sids_in_alerts(new_lines)
    if new_lines:
        print("NEW ALERTS (sample):")
        for line in new_lines[-8:]:
            print(" ", safe(line))
        missing = expected - observed
        if missing:
            print(f"  Note: expected {sorted(expected)}, missing {sorted(missing)}")
        elif expected:
            print(f"  OK: saw expected SIDs {sorted(expected & observed)}")
    else:
        print("No new alerts captured.")
    return {
        "scenario": scenario.title,
        "scenario_id": scenario.id,
        "exit_code": code,
        "alerts_before": before,
        "alerts_after": after,
        "new_alerts": new_lines,
        "detected": bool(expected & observed) if expected else None,
    }


def run_scenarios(
    ids: paramiko.SSHClient,
    attacker: paramiko.SSHClient,
    plc_ip: str,
    scenario_ids: tuple[str, ...],
    rack: int,
    slot: int,
    repo: str,
) -> list[dict]:
    return [
        run_one_scenario(ids, attacker, SCENARIO_MAP[sid], plc_ip, rack, slot, repo)
        for sid in scenario_ids
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run S7comm attacks from Attacker VM; read alerts on IDS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Deploy rules first: python detect/deploy_ids.py\n"
            "Full eval + tables: python detect/eval_rules.py\n"
            f"\nScenario IDs: {', '.join(DEFAULT_ORDER)}\n"
        ),
    )
    parser.add_argument(
        "-s",
        "--scenario",
        action="append",
        dest="scenarios",
        metavar="ID",
        choices=DEFAULT_ORDER,
        help="Run only this scenario (repeatable). Default: all.",
    )
    parser.add_argument("--plc", default=PLC_IP, help="PLC IP on OT segment")
    parser.add_argument("--list", action="store_true", help="List scenarios")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        for sid in DEFAULT_ORDER:
            print(f"{sid:16}  {SCENARIO_MAP[sid].title}")
        return 0

    scenario_ids = tuple(args.scenarios) if args.scenarios else DEFAULT_ORDER
    ids = connect(IDS_HOST, IDS_USER, IDS_PASSWORD)
    attacker = connect(ATTACKER_HOST, ATTACKER_USER, ATTACKER_PASSWORD)
    try:
        print(f"IDS={IDS_HOST} | Attacker={ATTACKER_HOST}")
        plc = find_plc(attacker, args.plc)
        if not plc:
            print(f"ERROR: PLC {args.plc} not reachable on :102 from Attacker")
            return 1
        print(f"Target PLC: {plc}")
        print(f"Scenarios: {', '.join(scenario_ids)}")
        print(f"Baseline alert lines: {alert_count(ids)}")
        results = run_scenarios(
            ids, attacker, plc, scenario_ids, PLC_RACK, PLC_SLOT, ATTACKER_REPO
        )
        print("\n========== SUMMARY ==========")
        for r in results:
            det = r.get("detected")
            flag = " OK" if det else (" FAIL" if det is False else "")
            print(f"- [{r['scenario_id']}] {r['scenario']}: {len(r['new_alerts'])} alert(s){flag}")
        return 0
    finally:
        ids.close()
        attacker.close()


if __name__ == "__main__":
    raise SystemExit(main())
