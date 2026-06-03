# Tấn công từ chối dịch vụ (DoS) — một script lab

**File duy nhất:** `s7comm_dos.py` — mặc định chạy **tất cả** phase DoS, có nghỉ giữa các phase để Suricata alert.

## Chạy nhanh

```bash
# Kiểm tra PLC
python3 attacks/dos/s7comm_dos.py 172.16.16.145 --check

# Toàn bộ kịch bản DoS (~10s/phase + 8s pause) — khuyến nghị
python3 attacks/dos/s7comm_dos.py 172.16.16.145

# Tùy chỉnh
python3 attacks/dos/s7comm_dos.py 172.16.16.145 --duration 12 --pause 10
```

## Chuỗi `--mode all` (mặc định)

| Thứ tự | Phase | Suricata SID |
|--------|--------|----------------|
| 1 | `setup_flood` | 1000041, 1000043 |
| 2 | *(pause)* | — |
| 3 | `tcp_connect` | 1000040 |
| 4 | *(pause)* | — |
| 5 | `szl_flood` | 1000042 |

Chạy riêng một phase: `--mode setup_flood` (cần `python-snap7` cho `szl_flood`).

## Lý thuyết OT/ICS

- MITRE ICS: **T0814** Denial of Service, **T0803/T0804** block command/reporting.
- DoS S7 thường dùng **lệnh hợp lệ** lặp nhanh, không cần malformed PDU.
- Báo cáo: `DATN/Chapter/2` (rủi ro), `Chapter/3` (`sec:dos_s7comm`), `Chapter/4` (`sec:rules-dos`).
- Luật: `detect/rules/ics_dos.rules`.

## Tích hợp IDS test

```powershell
python detect\run_attack_tests.py
```

Gọi một lần: `python3 /tmp/s7comm_dos.py <PLC> --mode all --duration 10 --pause 8`.
