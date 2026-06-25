# Suricata rule-set evaluation report

- Generated: `2026-06-25T08:21:31.229323+00:00`
- IDS: `172.16.16.7` | Attacker: `172.16.16.5` | PLC: `192.168.50.10`

## Baseline

- Duration: 60s (2 benign Snap7 reads)
- Alerts: 3 (180.00/hour)

## Detection

- Rate: **7/7** (100.0%)

| Scenario | Detected | Alerts | Observed SIDs |
|----------|----------|--------|---------------|
| recon_nmap | yes | 6 | 1000001, 1000002, 1000003 |
| recon_blocks | yes | 1 | 1000001 |
| write_db | yes | 5 | 1000001, 1000010, 1000011 |
| dos_all | yes | 5850 | 1000001, 1000002, 1000040, 1000042 |
| malformed_all | yes | 14 | 1000001, 1000053, 1000054 |
| plc_stop | yes | 3 | 1000001, 1000032, 1000033 |
| plc_start | yes | 3 | 1000001, 1000030, 1000031 |

## Performance

- **baseline_start**: CPU=None% drops=None pkts=159318
- **baseline_end**: CPU=None% drops=None pkts=159318
- **before_attacks**: CPU=None% drops=None pkts=159318
- **under_dos**: CPU=None% drops=None pkts=159318
- **after_attacks**: CPU=None% drops=None pkts=159318
