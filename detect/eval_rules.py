#!/usr/bin/env python3
"""Automated Suricata rule-set evaluation for the thesis lab.

Runs baseline + attack scenarios from Attacker VM, collects alerts and IDS
metrics from IDS VM, exports JSON/CSV/LaTeX tables for Chapter 5.

Usage:
  python detect/eval_rules.py
  python detect/eval_rules.py --baseline-sec 90 --output-dir detect/eval_results
  python detect/eval_rules.py --scenarios dos_all write_db --skip-baseline
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import paramiko

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab_config import (
    ATTACKER_HOST,
    ATTACKER_PASSWORD,
    ATTACKER_REPO,
    ATTACKER_USER,
    CAPTURE_IFACE,
    DOS_THRESHOLDS,
    HOME_NET,
    IDS_HOST,
    IDS_PASSWORD,
    IDS_USER,
    PLC_IP,
    PLC_RACK,
    PLC_SLOT,
    SURICATA_FAST_LOG,
    SURICATA_STATS_LOG,
)
from lab_scenarios import BENIGN_BASELINE_CMD, DEFAULT_ORDER, SCENARIOS, EvalScenario

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SID_RE = re.compile(r"\[\*\*\]\s+\[1:(\d+):")
STATS_KV_RE = re.compile(r"^([a-zA-Z0-9_.]+)\s+\|\s+Total\s+\|\s+(\d+)\s*$")


@dataclass
class AlertSlice:
    line_count_before: int
    line_count_after: int
    lines: list[str]
    sids: Counter[str]
    messages: list[str]

    @property
    def total(self) -> int:
        return len(self.lines)


@dataclass
class ScenarioResult:
    scenario_id: str
    title: str
    category: str
    exit_code: int
    expected_sids: list[str]
    observed_sids: list[str]
    missing_sids: list[str]
    detected: bool
    new_alerts: int
    duration_sec: float


@dataclass
class PerformanceSnapshot:
    label: str
    suricata_active: bool
    cpu_percent: float | None
    mem_percent: float | None
    kernel_packets: int | None
    kernel_drops: int | None
    decoder_pkts: int | None
    detect_alerts: int | None
    capture_errors: int | None


@dataclass
class EvalReport:
    generated_at: str
    ids_host: str
    attacker_host: str
    plc_ip: str
    home_net: str
    capture_iface: str
    baseline_duration_sec: int
    baseline_alerts: int
    baseline_alerts_per_hour: float
    baseline_by_sid: dict[str, int]
    benign_runs: int
    scenario_results: list[ScenarioResult] = field(default_factory=list)
    performance: list[PerformanceSnapshot] = field(default_factory=list)
    detection_rate: float = 0.0
    scenarios_tested: int = 0
    scenarios_detected: int = 0
    notes: list[str] = field(default_factory=list)


def connect(host: str, user: str, password: str) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=20)
    return ssh


def run_ssh(ssh: paramiko.SSHClient, cmd: str, timeout: int = 180) -> tuple[int, str, str]:
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def safe(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


def fast_log_line_count(ssh: paramiko.SSHClient) -> int:
    _, out, _ = run_ssh(ssh, f"sudo wc -l < {SURICATA_FAST_LOG} 2>/dev/null || echo 0", timeout=30)
    try:
        return int(out.strip())
    except ValueError:
        return 0


def read_new_alerts(ssh: paramiko.SSHClient, since_lines: int) -> list[str]:
    if since_lines <= 0:
        cmd = f"sudo tail -n 500 {SURICATA_FAST_LOG} 2>/dev/null"
    else:
        cmd = f"sudo tail -n +{since_lines + 1} {SURICATA_FAST_LOG} 2>/dev/null"
    _, out, _ = run_ssh(ssh, cmd, timeout=90)
    return [ln for ln in out.splitlines() if ln.strip()]


def parse_alerts(lines: list[str]) -> AlertSlice:
    sids: Counter[str] = Counter()
    messages: list[str] = []
    for line in lines:
        m = SID_RE.search(line)
        if m:
            sids[m.group(1)] += 1
        if "[**]" in line:
            messages.append(line.strip())
    return AlertSlice(0, 0, lines, sids, messages)


def parse_stats_log(text: str) -> dict[str, int]:
    stats: dict[str, int] = {}
    for line in text.splitlines():
        m = STATS_KV_RE.match(line.strip())
        if m:
            stats[m.group(1)] = int(m.group(2))
    return stats


def suricata_performance(ssh: paramiko.SSHClient, label: str) -> PerformanceSnapshot:
    active = False
    cpu: float | None = None
    mem: float | None = None
    _, active_out, _ = run_ssh(
        ssh,
        "systemctl is-active suricata 2>/dev/null || echo inactive",
        timeout=15,
    )
    active = active_out.strip() == "active"

    _, top_out, _ = run_ssh(
        ssh,
        "top -b -n 1 | grep -Ei 'suricata' | head -1; "
        "ps -o pcpu=,pmem= -C suricata 2>/dev/null | head -1",
        timeout=20,
    )
    if top_out.strip():
        for line in top_out.splitlines():
            parts = line.split()
            percents: list[float] = []
            for p in parts:
                if p.endswith("%"):
                    try:
                        percents.append(float(p.rstrip("%")))
                    except ValueError:
                        pass
                else:
                    try:
                        v = float(p)
                        if 0 <= v <= 100:
                            percents.append(v)
                    except ValueError:
                        pass
            if percents:
                cpu = percents[0]
                if len(percents) > 1:
                    mem = percents[1]
                break

    _, stats_out, _ = run_ssh(ssh, f"sudo tail -n 80 {SURICATA_STATS_LOG} 2>/dev/null", timeout=30)
    stats = parse_stats_log(stats_out)

    return PerformanceSnapshot(
        label=label,
        suricata_active=active,
        cpu_percent=cpu,
        mem_percent=mem,
        kernel_packets=stats.get("capture.kernel_packets"),
        kernel_drops=stats.get("capture.kernel_drops"),
        decoder_pkts=stats.get("decoder.pkts"),
        detect_alerts=stats.get("detect.alert"),
        capture_errors=stats.get("capture.errors"),
    )


def check_plc_from_attacker(attacker: paramiko.SSHClient, plc_ip: str) -> bool:
    _, out, _ = run_ssh(
        attacker,
        f"nc -z -w3 {plc_ip} 102 && echo OPEN || echo CLOSED",
        timeout=15,
    )
    return "OPEN" in out


def run_benign_read(attacker: paramiko.SSHClient, plc_ip: str, rack: int, slot: int, repo: str) -> int:
    cmd = BENIGN_BASELINE_CMD.format(plc=plc_ip, rack=rack, slot=slot).replace(
        "/home/ubuntu/Thesis", repo
    )
    code, _, _ = run_ssh(attacker, cmd, timeout=60)
    return code


def run_baseline(
    ids: paramiko.SSHClient,
    attacker: paramiko.SSHClient,
    duration_sec: int,
    plc_ip: str,
    rack: int,
    slot: int,
    repo: str,
    benign_interval: int = 45,
) -> tuple[AlertSlice, int]:
    print(f"\n=== BASELINE ({duration_sec}s, no attack scripts) ===")
    before = fast_log_line_count(ids)
    perf_before = suricata_performance(ids, "baseline_start")
    benign_runs = 0
    t0 = time.time()
    next_benign = 5.0

    while time.time() - t0 < duration_sec:
        elapsed = time.time() - t0
        if elapsed >= next_benign:
            print(f"  Benign read-only Snap7 list_blocks @ t={elapsed:.0f}s")
            run_benign_read(attacker, plc_ip, rack, slot, repo)
            benign_runs += 1
            next_benign += benign_interval
            time.sleep(3)
        else:
            time.sleep(2)

    after = fast_log_line_count(ids)
    lines = read_new_alerts(ids, before)
    slice_ = parse_alerts(lines)
    slice_.line_count_before = before
    slice_.line_count_after = after
    perf_end = suricata_performance(ids, "baseline_end")
    return slice_, benign_runs, perf_before, perf_end


def run_scenario(
    ids: paramiko.SSHClient,
    attacker: paramiko.SSHClient,
    scenario: EvalScenario,
    plc_ip: str,
    rack: int,
    slot: int,
    repo: str,
) -> ScenarioResult:
    print(f"\n=== ATTACK: {scenario.title} [{scenario.id}] ===")
    before = fast_log_line_count(ids)
    cmd = scenario.build_cmd(plc_ip, rack, slot, repo)
    t0 = time.time()
    code, out, err = run_ssh(attacker, cmd, timeout=scenario.timeout)
    time.sleep(4)
    duration = time.time() - t0
    lines = read_new_alerts(ids, before)
    alerts = parse_alerts(lines)
    expected = set(scenario.expected_sids)
    observed = set(alerts.sids.keys())
    missing = sorted(expected - observed)
    detected = bool(expected & observed)
    print(safe((out + err)[-600:]))
    print(
        f"  exit={code} alerts={alerts.total} detected={detected} "
        f"SIDs={sorted(observed)} missing={missing}"
    )
    return ScenarioResult(
        scenario_id=scenario.id,
        title=scenario.title,
        category=scenario.category,
        exit_code=code,
        expected_sids=list(scenario.expected_sids),
        observed_sids=sorted(observed),
        missing_sids=missing,
        detected=detected,
        new_alerts=alerts.total,
        duration_sec=round(duration, 1),
    )


def build_report(
    baseline_slice: AlertSlice | None,
    baseline_sec: int,
    benign_runs: int,
    scenarios: list[ScenarioResult],
    perf: list[PerformanceSnapshot],
    notes: list[str],
) -> EvalReport:
    baseline_n = baseline_slice.total if baseline_slice else 0
    per_hour = (baseline_n / baseline_sec * 3600) if baseline_sec > 0 else 0.0
    detected = sum(1 for s in scenarios if s.detected)
    total = len(scenarios)
    return EvalReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        ids_host=IDS_HOST,
        attacker_host=ATTACKER_HOST,
        plc_ip=PLC_IP,
        home_net=HOME_NET,
        capture_iface=CAPTURE_IFACE,
        baseline_duration_sec=baseline_sec,
        baseline_alerts=baseline_n,
        baseline_alerts_per_hour=round(per_hour, 2),
        baseline_by_sid=dict(baseline_slice.sids) if baseline_slice else {},
        benign_runs=benign_runs,
        scenario_results=scenarios,
        performance=perf,
        detection_rate=round(detected / total, 3) if total else 0.0,
        scenarios_tested=total,
        scenarios_detected=detected,
        notes=notes,
    )


def export_json(report: EvalReport, path: str) -> None:
    data = asdict(report)

    def _ser(obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return obj

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=_ser)


def export_csv(report: EvalReport, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "scenario_id",
                "title",
                "category",
                "detected",
                "new_alerts",
                "expected_sids",
                "observed_sids",
                "missing_sids",
                "exit_code",
                "duration_sec",
            ]
        )
        for s in report.scenario_results:
            w.writerow(
                [
                    s.scenario_id,
                    s.title,
                    s.category,
                    s.detected,
                    s.new_alerts,
                    ";".join(s.expected_sids),
                    ";".join(s.observed_sids),
                    ";".join(s.missing_sids),
                    s.exit_code,
                    s.duration_sec,
                ]
            )


def _latex_escape(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("&", "\\&")
        .replace("%", "\\%")
    )


def export_latex(report: EvalReport, path: str) -> None:
    lines: list[str] = [
        "% Auto-generated by detect/eval_rules.py — do not edit by hand",
        f"% Generated: {report.generated_at}",
        "",
    ]

    # Table: lab setup
    lines.extend(
        [
            "\\begin{table}[H]",
            "    \\centering",
            "    \\footnotesize",
            "    \\begin{tabular}{|l|l|}",
            "        \\hline",
            "        \\textbf{Thành phần} & \\textbf{Giá trị lab} \\\\",
            "        \\hline",
            f"        IDS (Suricata) & {IDS_HOST} ({IDS_USER}), mirror {CAPTURE_IFACE} \\\\",
            f"        Attacker (chạy kịch bản) & {ATTACKER_HOST} ({ATTACKER_USER}) \\\\",
            f"        PLC (OpenPLC :102) & {PLC_IP} (rack {PLC_RACK}, slot {PLC_SLOT}) \\\\",
            f"        HOME\\_NET & \\texttt{{{HOME_NET.replace('[', '').replace(']', '')}}} \\\\",
            "        \\hline",
            "    \\end{tabular}",
            "    \\caption{Thiết lập môi trường đánh giá tập luật}",
            "    \\label{tab:eval-lab-setup}",
            "\\end{table}",
            "",
        ]
    )

    # Table: methodology metrics
    lines.extend(
        [
            "\\begin{table}[H]",
            "    \\centering",
            "    \\footnotesize",
            "    \\begin{tabular}{|l|p{8.5cm}|}",
            "        \\hline",
            "        \\textbf{Chỉ số} & \\textbf{Định nghĩa trong đồ án} \\\\",
            "        \\hline",
            "        Tỷ lệ phát hiện kịch bản & Số kịch bản có $\\geq 1$ SID kỳ vọng / tổng kịch bản \\\\",
            "        \\hline",
            "        Mật độ alert baseline & Số alert Suricata khi chỉ chạy thao tác đọc Snap7 định kỳ, không script tấn công \\\\",
            "        \\hline",
            "        FP vận hành (baseline) & Alert phát sinh trong baseline, phân loại theo SID (Setup, List Blocks, \\ldots) \\\\",
            "        \\hline",
            "        kernel\\_drops & Gói bị kernel drop trên IDS; $=0$ nghĩa là chưa ``ngạt'' tại tải lab \\\\",
            "        \\hline",
            "    \\end{tabular}",
            "    \\caption{Các chỉ số đánh giá hiệu quả và false positive}",
            "    \\label{tab:eval-metrics-def}",
            "\\end{table}",
            "",
        ]
    )

    # Baseline results
    sid_rows = sorted(report.baseline_by_sid.items(), key=lambda x: -x[1])
    lines.extend(
        [
            "\\begin{table}[H]",
            "    \\centering",
            "    \\footnotesize",
            f"    \\begin{{tabular}}{{|l|r|}}",
            "        \\hline",
            "        \\textbf{Baseline} & \\textbf{Giá trị} \\\\",
            "        \\hline",
            f"        Thời gian quan sát & {report.baseline_duration_sec}\\,s ({report.benign_runs} lần đọc Snap7) \\\\",
            f"        Tổng alert mới & {report.baseline_alerts} \\\\",
            f"        Mật độ alert & {report.baseline_alerts_per_hour:.2f} alert/giờ \\\\",
            "        \\hline",
            "    \\end{tabular}",
            "    \\caption{Kết quả baseline — lưu lượng vận hành hợp lệ}",
            "    \\label{tab:eval-baseline}",
            "\\end{table}",
            "",
        ]
    )

    if sid_rows:
        lines.extend(
            [
                "\\begin{table}[H]",
                "    \\centering",
                "    \\footnotesize",
                "    \\begin{tabular}{|r|r|l|}",
                "        \\hline",
                "        \\textbf{SID} & \\textbf{Số alert} & \\textbf{Ghi chú} \\\\",
                "        \\hline",
            ]
        )
        sid_notes = {
            "1000001": "Setup Communication — thao tác Snap7 hợp lệ",
            "1000005": "List Blocks — đọc danh sách block",
        }
        for sid, cnt in sid_rows[:12]:
            note = sid_notes.get(sid, "Alert vận hành / cần triage")
            lines.append(f"        {sid} & {cnt} & {_latex_escape(note)} \\\\")
            lines.append("        \\hline")
        lines.extend(
            [
                "    \\end{tabular}",
                "    \\caption{Phân bố SID trong baseline (false positive vận hành)}",
                "    \\label{tab:eval-baseline-sid}",
                "\\end{table}",
                "",
            ]
        )

    # Attack detection matrix
    lines.extend(
        [
            "\\begin{table}[H]",
            "    \\centering",
            "    \\scriptsize",
            "    \\begin{tabular}{|l|l|c|c|l|}",
            "        \\hline",
            "        \\textbf{ID} & \\textbf{Kịch bản} & \\textbf{Alert} & \\textbf{OK?} & \\textbf{SID quan sát} \\\\",
            "        \\hline",
        ]
    )
    for s in report.scenario_results:
        ok = "\\checkmark" if s.detected else "---"
        obs = ", ".join(s.observed_sids[:6])
        if len(s.observed_sids) > 6:
            obs += ", \\ldots"
        lines.append(
            f"        \\texttt{{{s.scenario_id}}} & {_latex_escape(s.title[:32])} & "
            f"{s.new_alerts} & {ok} & \\texttt{{{obs}}} \\\\"
        )
        lines.append("        \\hline")
    det_pct = report.detection_rate * 100
    cap_det = (
        f"Ma trận phát hiện tấn công ({report.scenarios_detected}/{report.scenarios_tested} kịch bản, "
        f"{det_pct:.0f}\\%)"
    )
    lines.extend(
        [
            "    \\end{tabular}",
            f"    \\caption{{{cap_det}}}",
            "    \\label{tab:eval-detection-matrix}",
            "\\end{table}",
            "",
        ]
    )

    # Performance
    lines.extend(
        [
            "\\begin{table}[H]",
            "    \\centering",
            "    \\footnotesize",
            "    \\begin{tabular}{|l|c|c|r|r|r|}",
            "        \\hline",
            "        \\textbf{Trạng thái} & \\textbf{CPU (\\%)} & \\textbf{RAM (\\%)} & "
            "\\textbf{kernel\\_pkts} & \\textbf{drops} & \\textbf{detect.alert} \\\\",
            "        \\hline",
        ]
    )
    for p in report.performance:
        cpu = f"{p.cpu_percent:.1f}" if p.cpu_percent is not None else "---"
        mem = f"{p.mem_percent:.1f}" if p.mem_percent is not None else "---"
        kp = str(p.kernel_packets) if p.kernel_packets is not None else "---"
        kd = str(p.kernel_drops) if p.kernel_drops is not None else "0"
        da = str(p.detect_alerts) if p.detect_alerts is not None else "---"
        lines.append(
            f"        {_latex_escape(p.label)} & {cpu} & {mem} & {kp} & {kd} & {da} \\\\"
        )
        lines.append("        \\hline")
    lines.extend(
        [
            "    \\end{tabular}",
            "    \\caption{Hiệu năng Suricata trên IDS (stats.log / top)}",
            "    \\label{tab:eval-performance}",
            "\\end{table}",
            "",
        ]
    )

    # DoS thresholds safety margin (static reference)
    lines.extend(
        [
            "\\begin{table}[H]",
            "    \\centering",
            "    \\footnotesize",
            "    \\begin{tabular}{|r|r|r|l|}",
            "        \\hline",
            "        \\textbf{SID} & \\textbf{Ngưỡng} & \\textbf{Cửa sổ (s)} & \\textbf{Mô tả} \\\\",
            "        \\hline",
        ]
    )
    for sid, meta in sorted(DOS_THRESHOLDS.items()):
        lines.append(
            f"        {sid} & {meta['count']} & {meta['seconds']} & {_latex_escape(meta['desc'])} \\\\"
        )
        lines.append("        \\hline")
    lines.extend(
        [
            "    \\end{tabular}",
            "    \\caption{Ngưỡng luật DoS (ics\\_dos.rules) — cần lớn hơn baseline HMI}",
            "    \\label{tab:eval-dos-thresholds}",
            "\\end{table}",
            "",
        ]
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_markdown(report: EvalReport, path: str) -> None:
    lines = [
        "# Suricata rule-set evaluation report",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- IDS: `{report.ids_host}` | Attacker: `{report.attacker_host}` | PLC: `{report.plc_ip}`",
        "",
        "## Baseline",
        "",
        f"- Duration: {report.baseline_duration_sec}s ({report.benign_runs} benign Snap7 reads)",
        f"- Alerts: {report.baseline_alerts} ({report.baseline_alerts_per_hour:.2f}/hour)",
        "",
        "## Detection",
        "",
        f"- Rate: **{report.scenarios_detected}/{report.scenarios_tested}** "
        f"({report.detection_rate * 100:.1f}%)",
        "",
        "| Scenario | Detected | Alerts | Observed SIDs |",
        "|----------|----------|--------|---------------|",
    ]
    for s in report.scenario_results:
        ok = "yes" if s.detected else "no"
        lines.append(
            f"| {s.scenario_id} | {ok} | {s.new_alerts} | {', '.join(s.observed_sids[:8])} |"
        )
    lines.extend(["", "## Performance", ""])
    for p in report.performance:
        lines.append(
            f"- **{p.label}**: CPU={p.cpu_percent}% drops={p.kernel_drops} pkts={p.kernel_packets}"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Automated Suricata rule-set evaluation")
    p.add_argument("--baseline-sec", type=int, default=90, help="Baseline duration (default 90)")
    p.add_argument("--skip-baseline", action="store_true")
    p.add_argument(
        "--scenarios",
        nargs="*",
        metavar="ID",
        help=f"Scenario IDs (default: all). Choices: {', '.join(DEFAULT_ORDER)}",
    )
    p.add_argument("--plc", default=PLC_IP)
    p.add_argument("--rack", type=int, default=PLC_RACK)
    p.add_argument("--slot", type=int, default=PLC_SLOT)
    p.add_argument("--repo", default=ATTACKER_REPO)
    p.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "eval_results"),
    )
    p.add_argument("--list", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        for sid in DEFAULT_ORDER:
            sc = SCENARIOS[sid]
            print(f"{sid:16}  {sc.title}")
        return 0

    os.makedirs(args.output_dir, exist_ok=True)
    scenario_ids = tuple(args.scenarios) if args.scenarios else DEFAULT_ORDER
    notes: list[str] = []
    perf_snaps: list[PerformanceSnapshot] = []

    ids = connect(IDS_HOST, IDS_USER, IDS_PASSWORD)
    attacker = connect(ATTACKER_HOST, ATTACKER_USER, ATTACKER_PASSWORD)
    try:
        print(f"IDS {IDS_HOST} OK | Attacker {ATTACKER_HOST} OK")
        if not check_plc_from_attacker(attacker, args.plc):
            print(f"ERROR: PLC {args.plc}:102 not reachable from Attacker")
            return 1
        print(f"PLC {args.plc}:102 reachable from Attacker")

        baseline_slice: AlertSlice | None = None
        benign_runs = 0
        baseline_sec = 0

        if not args.skip_baseline:
            baseline_sec = args.baseline_sec
            baseline_slice, benign_runs, p0, p1 = run_baseline(
                ids,
                attacker,
                baseline_sec,
                args.plc,
                args.rack,
                args.slot,
                args.repo,
            )
            perf_snaps.extend([p0, p1])
        else:
            notes.append("Baseline skipped by --skip-baseline")

        perf_snaps.append(suricata_performance(ids, "before_attacks"))

        results: list[ScenarioResult] = []
        for sid in scenario_ids:
            if sid not in SCENARIOS:
                print(f"Unknown scenario: {sid}", file=sys.stderr)
                return 1
            sc = SCENARIOS[sid]
            results.append(
                run_scenario(ids, attacker, sc, args.plc, args.rack, args.slot, args.repo)
            )
            if sc.id == "dos_all":
                perf_snaps.append(suricata_performance(ids, "under_dos"))
            time.sleep(5)

        perf_snaps.append(suricata_performance(ids, "after_attacks"))

        report = build_report(baseline_slice, baseline_sec, benign_runs, results, perf_snaps, notes)

        json_path = os.path.join(args.output_dir, "eval_report.json")
        csv_path = os.path.join(args.output_dir, "eval_detection.csv")
        tex_path = os.path.join(args.output_dir, "eval_tables.tex")
        md_path = os.path.join(args.output_dir, "eval_report.md")

        export_json(report, json_path)
        export_csv(report, csv_path)
        export_latex(report, tex_path)
        export_markdown(report, md_path)

        print("\n========== EVAL SUMMARY ==========")
        print(f"Baseline: {report.baseline_alerts} alerts / {report.baseline_duration_sec}s")
        print(
            f"Detection: {report.scenarios_detected}/{report.scenarios_tested} "
            f"({report.detection_rate * 100:.1f}%)"
        )
        print(f"Exported: {json_path}")
        print(f"          {tex_path}")
        return 0
    finally:
        ids.close()
        attacker.close()


if __name__ == "__main__":
    raise SystemExit(main())
