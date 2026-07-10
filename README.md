# Thesis — Passive S7comm attack detection (Suricata IDS)

Repository layout for thesis defense and lab reproduction.

| Folder | Contents |
|--------|----------|
| [`DATN/`](DATN/) | Thesis LaTeX (English: `DATN/en/`) |
| [`docs/`](docs/) | Reference notes, installation guides, papers |
| [`attacks/`](attacks/) | Attack tools and Stuxnet-inspired MITM simulation |
| [`detect/`](detect/) | Suricata rules, lab config, automated evaluation |
| [`tools/s7comm_gui/`](tools/s7comm_gui/) | Desktop GUI for attacks and rule inspection |

## Quick start

1. Deploy rules: `python detect/deploy_ids.py`
2. Run evaluation: `python detect/eval_rules.py`
3. Lab scenarios: see [`detect/HUONG_DAN_CHAY_KICH_BAN.md`](detect/HUONG_DAN_CHAY_KICH_BAN.md)

## Main components

- **Rules:** `detect/rules/` (`s7comm.rules`, `ics_dos.rules`, `s7comm_malformed.rules`)
- **Evaluation output:** `detect/eval_results/eval_tables_en.tex` (included in thesis Chapter 5)
