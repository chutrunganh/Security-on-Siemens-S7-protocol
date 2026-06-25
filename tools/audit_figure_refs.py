#!/usr/bin/env python3
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "DATN"

def load_ch3_en():
    t = (root / "en/Chapter/3_Methodology.tex").read_text(encoding="utf-8")
    body = (root / "en/Chapter/stuxnet_mitm_body.tex").read_text(encoding="utf-8")
    return t.replace("\\input{stuxnet_mitm_body.tex}", body)

def audit(name, text):
    figs = re.findall(r"\\begin\{figure\}.*?\\label\{([^}]+)\}", text, re.S)
    refs = set(re.findall(r"\\ref\{([^}]+)\}", text))
    unref = [l for l in figs if l not in refs]
    print(f"{name}: {len(figs)} figures, {len(unref)} unreferenced")
    for l in unref:
        print(f"  - {l}")

for rel, lang in [
    ("en/Chapter/2_Literature_review.tex", "en"),
    ("Chapter/2_Literature_review.tex", "vi"),
    ("Chapter/3_Methodology.tex", "vi"),
]:
    audit(rel, (root / rel).read_text(encoding="utf-8"))

audit("en/Chapter/3_Methodology.tex (merged)", load_ch3_en())
audit("en/Chapter/stuxnet_mitm_body.tex", (root / "en/Chapter/stuxnet_mitm_body.tex").read_text(encoding="utf-8"))
