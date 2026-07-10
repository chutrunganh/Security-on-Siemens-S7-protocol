#!/usr/bin/env python3
"""Insert \\ref{} mentions and missing \\label{} for figure environments."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FIGURE_BLOCK = re.compile(r"\\begin\{figure\}.*?\\end\{figure\}", re.DOTALL)
INCLUDEGRAPHICS = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
CAPTION = re.compile(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}")
LABEL = re.compile(r"\\label\{([^}]+)\}")


def slug_from_image(path: str) -> str:
    path = path.replace("\\", "/")
    name = Path(path).stem.replace(" ", "_")
    parent = Path(path).parent.name.replace(" ", "_")
    if parent and parent not in (".", "Figure", "figures"):
        return f"fig:{parent}-{name}"
    return f"fig:{name}"


def make_ref_sentence(label: str, caption: str, lang: str) -> str:
    cap = caption.strip()
    if not cap:
        cap = "the captured traffic"
    cap = cap.rstrip(".")
    if lang == "vi":
        return f"Hình~\\ref{{{label}}} minh họa {cap[0].lower()}{cap[1:]}."
    return f"Figure~\\ref{{{label}}} shows {cap[0].lower()}{cap[1:]}."


def process_text(text: str, lang: str) -> tuple[str, int]:
    refs_added = 0

    def repl(block_match: re.Match[str]) -> str:
        nonlocal refs_added
        block = block_match.group(0)
        imgs = INCLUDEGRAPHICS.findall(block)
        cap_m = CAPTION.search(block)
        caption = cap_m.group(1) if cap_m else ""
        labels = LABEL.findall(block)

        if labels:
            label = labels[0]
        else:
            img = imgs[0] if imgs else "unknown"
            label = slug_from_image(img)
            if "\\label{" not in block:
                block = block.replace("\\end{figure}", f"    \\label{{{label}}}\n\\end{{figure}}")

        if re.search(rf"\\ref\{{{re.escape(label)}\}}", text):
            return block

        ref_line = make_ref_sentence(label, caption, lang)
        refs_added += 1
        return f"{ref_line}\n\n{block}"

    # Process from end to start so offsets stay valid — rebuild manually
    parts: list[str] = []
    last = 0
    for m in FIGURE_BLOCK.finditer(text):
        parts.append(text[last : m.start()])
        new_block, _ = repl(m), None
        # repl uses outer `text` for ref check; re-call properly
        block = m.group(0)
        imgs = INCLUDEGRAPHICS.findall(block)
        cap_m = CAPTION.search(block)
        caption = cap_m.group(1) if cap_m else ""
        labels = LABEL.findall(block)
        if labels:
            label = labels[0]
        else:
            img = imgs[0] if imgs else "unknown"
            label = slug_from_image(img)
            if "\\label{" not in block:
                block = block.replace("\\end{figure}", f"    \\label{{{label}}}\n\\end{{figure}}")

        if not re.search(rf"\\ref\{{{re.escape(label)}\}}", text):
            ref_line = make_ref_sentence(label, caption, lang)
            parts.append(ref_line + "\n\n")
            refs_added += 1
        parts.append(block)
        last = m.end()
    parts.append(text[last:])
    return "".join(parts), refs_added


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    jobs = [
        (root / "DATN/en/Chapter/2_Literature_review.tex", "en"),
        (root / "DATN/en/Chapter/3_Methodology.tex", "en"),
        (root / "DATN/en/Chapter/stuxnet_mitm_body.tex", "en"),
    ]
    total = 0
    for path, lang in jobs:
        if not path.exists():
            print(f"skip missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text, n = process_text(text, lang)
        if n:
            path.write_text(new_text, encoding="utf-8")
            print(f"{path.name}: added {n} figure references")
            total += n
        else:
            print(f"{path.name}: already referenced")
    print(f"total references added: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
