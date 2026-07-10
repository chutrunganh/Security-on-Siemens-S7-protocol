"""Parse and manage local Suricata rule files."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .config import REPO_ROOT, RULE_FILES, RULES_DIR

SID_RE = re.compile(r"sid:(\d+)", re.I)
REV_RE = re.compile(r"rev:(\d+)", re.I)
MSG_RE = re.compile(r'msg:"([^"]*)"', re.I)
PRIORITY_RE = re.compile(r"priority:(\d+)", re.I)
ATTACK_RE = re.compile(r"attack\s+([^;]+)", re.I)
PROTOCOL_RE = re.compile(r"protocol\s+([^;]+)", re.I)


@dataclass
class SuricataRule:
    file_name: str
    line_no: int
    sid: str
    rev: str
    msg: str
    attack: str
    protocol: str
    priority: str
    raw: str
    enabled: bool = True

    @property
    def summary(self) -> str:
        return self.msg or self.raw[:60]


def rules_path(name: str) -> str:
    return os.path.join(RULES_DIR, name)


def load_rule_file(name: str) -> list[SuricataRule]:
    path = rules_path(name)
    rules: list[SuricataRule] = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                if stripped.lower().startswith("# alert"):
                    rules.append(_parse_rule(name, i, stripped.lstrip("# ").strip(), enabled=False))
                continue
            if stripped.startswith("alert "):
                rules.append(_parse_rule(name, i, stripped, enabled=True))
    return rules


def _parse_rule(file_name: str, line_no: int, raw: str, enabled: bool) -> SuricataRule:
    sid_m = SID_RE.search(raw)
    rev_m = REV_RE.search(raw)
    msg_m = MSG_RE.search(raw)
    pri_m = PRIORITY_RE.search(raw)
    atk_m = ATTACK_RE.search(raw)
    proto_m = PROTOCOL_RE.search(raw)
    return SuricataRule(
        file_name=file_name,
        line_no=line_no,
        sid=sid_m.group(1) if sid_m else "?",
        rev=rev_m.group(1) if rev_m else "?",
        msg=msg_m.group(1) if msg_m else "",
        attack=(atk_m.group(1).strip() if atk_m else ""),
        protocol=(proto_m.group(1).strip() if proto_m else ""),
        priority=pri_m.group(1) if pri_m else "?",
        raw=raw,
        enabled=enabled,
    )


def load_all_rules() -> dict[str, list[SuricataRule]]:
    return {name: load_rule_file(name) for name in RULE_FILES}


def save_rule(rule: SuricataRule) -> None:
    path = rules_path(rule.file_name)
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    idx = rule.line_no - 1
    if idx < 0 or idx >= len(lines):
        raise IndexError(f"Line {rule.line_no} out of range in {rule.file_name}")
    prefix = "" if rule.enabled else "# "
    lines[idx] = prefix + rule.raw.rstrip() + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def save_file_content(name: str, content: str) -> None:
    path = rules_path(name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.rstrip() + "\n")


def read_file_content(name: str) -> str:
    with open(rules_path(name), encoding="utf-8") as f:
        return f.read()


def rule_stats(rules_by_file: dict[str, list[SuricataRule]]) -> str:
    total = sum(len(v) for v in rules_by_file.values())
    parts = [f"{name}: {len(rules_by_file[name])}" for name in RULE_FILES]
    return f"{total} rules ({', '.join(parts)})"
