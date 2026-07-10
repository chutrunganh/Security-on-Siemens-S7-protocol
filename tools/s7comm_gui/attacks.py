"""Attack scenario definitions for the GUI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


def _run_py(repo: str, script: str, args: str) -> str:
    py = f"{repo}/.venv/bin/python"
    return f'cd "{repo}" && "{py}" "{script}" {args} 2>&1'


@dataclass(frozen=True)
class AttackScenario:
    id: str
    name: str
    description: str
    uploads: tuple[str, ...]
    expected_sids: tuple[str, ...]
    build_remote_cmd: Callable[[str, int, int, str], str]
    build_local_cmd: Callable[[str, str, int, int], str]


def _remote_write(plc: str, rack: int, slot: int, repo: str) -> str:
    return _run_py(
        repo,
        "attacks/stuxnet_mitm_sim/attacker/test_readwrite_db_via_snap7.py",
        f"--ip {plc} --rack {rack} --slot {slot}",
    )


def _local_write(plc: str, repo: str, rack: int, slot: int) -> str:
    return (
        f'uv run python "{repo}/attacks/stuxnet_mitm_sim/attacker/test_readwrite_db_via_snap7.py" '
        f"--ip {plc} --rack {rack} --slot {slot}"
    )


SCENARIOS: tuple[AttackScenario, ...] = (
    AttackScenario(
        "recon_nmap",
        "Recon — Nmap s7-info",
        "",
        (),
        ("1000001", "1000002", "1000003"),
        lambda plc, _r, _s, _repo: f"nmap -p 102 --script s7-info {plc} 2>&1",
        lambda plc, repo, _r, _s: f"nmap -p 102 --script s7-info {plc}",
    ),
    AttackScenario(
        "recon_blocks",
        "Recon — List blocks",
        "",
        ("attacks/reconnaissance/scanBlock.py",),
        ("1000001", "1000005"),
        lambda plc, rack, slot, repo: _run_py(
            repo,
            "attacks/reconnaissance/scanBlock.py",
            f"--ip {plc} --rack {rack} --slot {slot} --list-only",
        ),
        lambda plc, repo, rack, slot: (
            f'uv run python "{repo}/attacks/reconnaissance/scanBlock.py" '
            f"--ip {plc} --rack {rack} --slot {slot} --list-only"
        ),
    ),
    AttackScenario(
        "write_db",
        "Write Var — DB",
        "",
        ("attacks/stuxnet_mitm_sim/attacker/test_readwrite_db_via_snap7.py",),
        ("1000010", "1000011"),
        _remote_write,
        _local_write,
    ),
    AttackScenario(
        "dos_all",
        "DoS — full (3 phases)",
        "",
        ("attacks/dos/s7comm_dos.py",),
        ("1000040", "1000041", "1000042", "1000043"),
        lambda plc, _r, _s, repo: _run_py(
            repo, "attacks/dos/s7comm_dos.py", f"{plc} --mode all --duration 10 --pause 8"
        ),
        lambda plc, repo, _r, _s: (
            f'uv run python "{repo}/attacks/dos/s7comm_dos.py" {plc} '
            f"--mode all --duration 10 --pause 8"
        ),
    ),
    AttackScenario(
        "malformed_all",
        "Malformed — full (9 variants)",
        "",
        ("attacks/malformed/s7comm_malformed.py",),
        ("1000050", "1000051", "1000052", "1000053", "1000054", "1000055", "1000056", "1000057", "1000058"),
        lambda plc, _r, _s, repo: _run_py(
            repo,
            "attacks/malformed/s7comm_malformed.py",
            f"{plc} --mode all --repeats 2 --pause 6",
        ),
        lambda plc, repo, _r, _s: (
            f'uv run python "{repo}/attacks/malformed/s7comm_malformed.py" {plc} '
            f"--mode all --repeats 2 --pause 6"
        ),
    ),
    AttackScenario(
        "plc_stop",
        "PLC Stop (command injection)",
        "",
        (
            "attacks/start_stop_plc/start_stop_plc.py",
            "attacks/start_stop_plc/payloads.py",
        ),
        ("1000001", "1000032", "1000033"),
        lambda plc, rack, slot, repo: _run_py(
            repo,
            "attacks/start_stop_plc/start_stop_plc.py",
            f"{plc} stop --rack {rack} --slot {slot}",
        ),
        lambda plc, repo, rack, slot: (
            f'uv run python "{repo}/attacks/start_stop_plc/start_stop_plc.py" {plc} stop '
            f"--rack {rack} --slot {slot}"
        ),
    ),
    AttackScenario(
        "plc_start",
        "PLC Start (command injection)",
        "",
        (
            "attacks/start_stop_plc/start_stop_plc.py",
            "attacks/start_stop_plc/payloads.py",
        ),
        ("1000001", "1000030", "1000031"),
        lambda plc, rack, slot, repo: _run_py(
            repo,
            "attacks/start_stop_plc/start_stop_plc.py",
            f"{plc} start --rack {rack} --slot {slot}",
        ),
        lambda plc, repo, rack, slot: (
            f'uv run python "{repo}/attacks/start_stop_plc/start_stop_plc.py" {plc} start '
            f"--rack {rack} --slot {slot}"
        ),
    ),
)

SCENARIO_BY_ID: dict[str, AttackScenario] = {s.id: s for s in SCENARIOS}

SNAP7_SCENARIOS: frozenset[str] = frozenset(
    {"recon_blocks", "write_db", "dos_all", "plc_stop", "plc_start"}
)

REPO_MANIFEST_FILES: tuple[str, ...] = ("pyproject.toml", "uv.lock")


def _collect_attack_files() -> tuple[str, ...]:
    seen: set[str] = set()
    files: list[str] = []
    for sc in SCENARIOS:
        for rel in sc.uploads:
            if rel not in seen:
                seen.add(rel)
                files.append(rel)
    return tuple(sorted(files))


ATTACK_FILES: tuple[str, ...] = _collect_attack_files()
