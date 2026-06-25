"""Attack scenarios for automated rule-set evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


def _py(repo: str, script: str, args: str) -> str:
    return f'cd "{repo}" && "{repo}/.venv/bin/python" "{script}" {args} 2>&1'


@dataclass(frozen=True)
class EvalScenario:
    id: str
    title: str
    category: str
    expected_sids: tuple[str, ...]
    build_cmd: Callable[[str, int, int, str], str]
    timeout: int = 180


def all_scenarios() -> tuple[EvalScenario, ...]:
    repo = "/home/ubuntu/Thesis"  # placeholder; replaced at runtime
    plc = "192.168.50.10"
    r, s = 0, 2

    def cmd(fn: Callable[[str, int, int, str], str]) -> Callable[[str, int, int, str], str]:
        return fn

    return (
        EvalScenario(
            "recon_nmap",
            "Reconnaissance — nmap s7-info",
            "reconnaissance",
            ("1000001", "1000002", "1000003", "1000004", "1000005"),
            cmd(lambda p, _r, _s, _repo: f"nmap -p 102 --script s7-info {p} 2>&1"),
            timeout=120,
        ),
        EvalScenario(
            "recon_blocks",
            "Reconnaissance — list blocks (Snap7)",
            "reconnaissance",
            ("1000001", "1000005"),
            cmd(
                lambda p, rack, slot, rep: _py(
                    rep,
                    "attacks/reconnaissance/scanBlock.py",
                    f"--ip {p} --rack {rack} --slot {slot} --list-only",
                )
            ),
        ),
        EvalScenario(
            "write_db",
            "Modify process — Write Var DB",
            "modify",
            ("1000010", "1000011"),
            cmd(
                lambda p, rack, slot, rep: _py(
                    rep,
                    "attacks/stuxnet_mitm_sim/attacker/test_readwrite_db_via_snap7.py",
                    f"--ip {p} --rack {rack} --slot {slot}",
                )
            ),
        ),
        EvalScenario(
            "dos_all",
            "DoS — setup / tcp / szl (all phases)",
            "dos",
            ("1000040", "1000041", "1000042", "1000043"),
            cmd(
                lambda p, _r, _s, rep: _py(
                    rep,
                    "attacks/dos/s7comm_dos.py",
                    f"{p} --mode all --duration 10 --pause 8",
                )
            ),
            timeout=300,
        ),
        EvalScenario(
            "malformed_all",
            "Malformed S7comm — all phases",
            "malformed",
            (
                "1000050",
                "1000051",
                "1000052",
                "1000053",
                "1000054",
                "1000055",
                "1000056",
                "1000057",
                "1000058",
            ),
            cmd(
                lambda p, _r, _s, rep: _py(
                    rep,
                    "attacks/malformed/s7comm_malformed.py",
                    f"{p} --mode all --repeats 2 --pause 6",
                )
            ),
            timeout=360,
        ),
        EvalScenario(
            "plc_stop",
            "Start/Stop replay — PLC Stop",
            "plc_control",
            ("1000032", "1000033"),
            cmd(
                lambda p, rack, slot, rep: _py(
                    rep,
                    "attacks/start_stop_plc/start_stop_plc.py",
                    f"{p} stop --rack {rack} --slot {slot}",
                )
            ),
        ),
        EvalScenario(
            "plc_start",
            "Start/Stop replay — PLC Start",
            "plc_control",
            ("1000030", "1000031"),
            cmd(
                lambda p, rack, slot, rep: _py(
                    rep,
                    "attacks/start_stop_plc/start_stop_plc.py",
                    f"{p} start --rack {rack} --slot {slot}",
                )
            ),
        ),
    )


SCENARIOS: dict[str, EvalScenario] = {s.id: s for s in all_scenarios()}
DEFAULT_ORDER: tuple[str, ...] = tuple(SCENARIOS.keys())

# Benign baseline: periodic read-only Snap7 (no nmap / no write)
BENIGN_BASELINE_CMD = _py(
    "/home/ubuntu/Thesis",
    "attacks/reconnaissance/scanBlock.py",
    "--ip {plc} --rack {rack} --slot {slot} --list-only",
)
