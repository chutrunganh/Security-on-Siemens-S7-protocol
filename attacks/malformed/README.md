# Malformed S7comm (lab)

Script gửi các PDU **cố ý sai** tới PLC cổng TCP/102. Mỗi phase tương ứng một luật trong `detect/rules/s7comm_malformed.rules` (`sid:1000050`–`1000058`).

**Chỉ dùng trên lab cô lập.**

## Chạy nhanh

```bash
python3 attacks/malformed/s7comm_malformed.py <IP_PLC>
# hoặc: --mode all --repeats 3 --pause 6

python3 attacks/malformed/s7comm_malformed.py <IP_PLC> --list
python3 attacks/malformed/s7comm_malformed.py <IP_PLC> --mode s7_bad_rosctr
```

## Nhóm malformed và phase script

| Nhóm | Ý nghĩa | `--mode` | SID |
|------|---------|----------|-----|
| **1 — Vỏ TPKT/COTP** | Lỗi đóng gói ISO-on-TCP | `tpkt_bad_version` | 1000050 |
| | Length TPKT > payload TCP | `tpkt_len_gt_payload` | 1000051 |
| | Length TPKT < payload thực | `tpkt_len_lt_payload` | 1000058 |
| | COTP không phải `02 F0 80` | `cotp_invalid` | 1000056 |
| **2 — S7 header** | Protocol ID ≠ `0x32` | `s7_bad_protocol_id` | 1000052 |
| | ROSCTR = `0xFF` | `s7_bad_rosctr` | 1000053 |
| **3 — Lớp chức năng** | Function Job = `0xFF` | `job_bad_opcode` | 1000054 |
| | Write Var `0x05` PDU quá ngắn | `write_var_malformed` | 1000057 |
| **4 — Cắt cụt** | Setup bị cắt 14 byte | `setup_truncated` | 1000055 |

PDU gốc hợp lệ: **Setup Communication** (giống `attacks/dos/s7comm_dos.py`). Các phase khác **sửa một trường** (hoặc cắt) để dễ đối chiếu trong Wireshark và báo cáo.

## Kỳ vọng trên PLC lab

- OpenPLC / S7 server mô phỏng: thường **từ chối**, **đóng TCP** hoặc timeout — hiếm khi “chiếm” CPU như Stop/Write.
- Khác **DoS** (`ics_dos.rules`): malformed không cần `threshold`, mỗi gói bất thường đủ để alert.

## Triển khai IDS

Đưa `s7comm_malformed.rules` vào `suricata.yaml` (xem `detect/patch_suricata_yaml.py`, `detect/deploy_ids.py`) và restart Suricata.

Tự động: `python detect/run_attack_tests.py` (có bước Malformed).
