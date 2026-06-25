# Lệnh demo đầy đủ — Lab S7comm + Suricata IDS

Tài liệu copy-paste cho buổi demo. Thay `PLC_IP` bằng IP PLC thật trong lab (ví dụ `172.16.16.152`).

| Thành phần | Giá trị mặc định lab |
|------------|----------------------|
| IDS VM | `lubuntu@172.16.16.143` (mật khẩu `lubuntu`) |
| PLC | `PLC_IP` — cổng **102** (OpenPLC + S7 server) |
| Repo (Windows) | `C:\Users\chutrunganh\Documents\HUST\Thesis` |

**Điều kiện:** Traffic tấn công phải đi qua interface IDS đang bắt (`ens37` / `ens33`). Nếu không có alert dù script chạy OK → kiểm tra mirror/SPAN.

---

## A. Chuẩn bị demo (3 bước)

### A1. Terminal 1 — SSH vào IDS, theo dõi alert realtime

```bash
ssh lubuntu@172.16.16.143
sudo tail -f /var/log/suricata/fast.log | grep --line-buffered "ICS S7COMM"
```

Hoặc JSON:

```bash
ssh lubuntu@172.16.16.143
sudo tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
```

### A2. Terminal 2 — Kiểm tra Suricata + (tuỳ chọn) tcpdump

```bash
ssh lubuntu@172.16.16.143
systemctl is-active suricata
sudo tcpdump -i ens37 -n host PLC_IP and port 102
# mạng 192.168.x: sudo tcpdump -i ens33 -n host PLC_IP and port 102
```

### A3. Terminal 3 — Máy Windows (thư mục repo)

```powershell
cd C:\Users\chutrunganh\Documents\HUST\Thesis
pip install paramiko
```

---

## B. Triển khai luật Suricata (một lần — script riêng)

**Luôn chạy trước buổi demo** (hoặc sau khi sửa file `.rules`). `run_attack_tests.py` **không** deploy lại.

```powershell
cd C:\Users\chutrunganh\Documents\HUST\Thesis
python detect\deploy_ids.py
```

### Hoặc thủ công trên IDS

```bash
ssh lubuntu@172.16.16.143
sudo suricata -T -c /etc/suricata/suricata.yaml
sudo systemctl restart suricata
sudo systemctl status suricata
```

Ba file luật:

- `detect/rules/s7comm.rules` (19 luật, SID 1000001–1000033)
- `detect/rules/ics_dos.rules` (4 luật, SID 1000040–1000043)
- `detect/rules/s7comm_malformed.rules` (9 luật, SID 1000050–1000058)

---

## C. Demo nhanh — chạy kịch bản (từ Windows)

Đã deploy luật ở mục B. Script chỉ SSH, chạy tấn công, đọc alert.

```powershell
cd C:\Users\chutrunganh\Documents\HUST\Thesis

# Liệt kê ID kịch bản
python detect\run_attack_tests.py --list

# Chạy TẤT CẢ: recon-nmap → recon-blocks → write → dos → malformed → stop
python detect\run_attack_tests.py

# Chỉ định PLC (nếu biết IP)
python detect\run_attack_tests.py --plc 172.16.16.152

# Một kịch bản
python detect\run_attack_tests.py -s dos
```

**Thứ tự mặc định và SID kỳ vọng:**

| Thứ tự | `--scenario` | Mô tả | SID chính |
|--------|--------------|-------|-----------|
| 1 | `recon-nmap` | nmap s7-info | 1000001–1000004 |
| 2 | `recon-blocks` | scanBlock.py | 1000001, 1000005 |
| 3 | `write` | Ghi DB | 1000010, 1000011 |
| 4 | `dos` | DoS 3 phase | 1000040–1000043 |
| 5 | `malformed` | 9 phase malformed | 1000050–1000058 |
| 6 | `stop` | Stop CPU replay | 1000001, 1000032, 1000033 |

---

## D. Demo từng kịch bản — `run_attack_tests.py` (Windows)

```powershell
cd C:\Users\chutrunganh\Documents\HUST\Thesis

python detect\run_attack_tests.py -s recon-nmap
python detect\run_attack_tests.py -s recon-blocks
python detect\run_attack_tests.py -s write
python detect\run_attack_tests.py -s dos
python detect\run_attack_tests.py -s malformed
python detect\run_attack_tests.py -s stop

# Gộp vài kịch bản
python detect\run_attack_tests.py -s recon-nmap -s write -s stop
python detect\run_attack_tests.py -s dos -s malformed

# PLC cố định + một kịch bản
python detect\run_attack_tests.py --plc 172.16.16.152 -s write
python detect\run_attack_tests.py --plc 172.16.16.152 -s stop
```

---

## E. Demo thủ công từng kịch bản (chạy trên IDS hoặc máy có route tới PLC)

Thay `PLC_IP` ở mọi lệnh dưới đây.

### E1. Reconnaissance — Nmap s7-info

**Chạy trên IDS** (traffic chắc chắn qua mirror):

```bash
ssh lubuntu@172.16.16.143
nmap -p 102 --script s7-info PLC_IP
```

**Chạy từ máy Linux khác** (phải nằm trên đường IDS nhìn thấy):

```bash
nmap -p 102 --script s7-info PLC_IP
```

**Alert kỳ vọng:** 1000001 (Setup), 1000002 (Read SZL), 1000003 (SZL 0x0011), có thể 1000004.

---

### E2. Reconnaissance — Liệt kê block

```bash
cd attacks/reconnaissance
# Sửa IP_ADDRESS trong scanBlock.py = PLC_IP
python3 scanBlock.py
```

Hoặc từ IDS (sau khi upload file):

```bash
ssh lubuntu@172.16.16.143
python3 /tmp/scanBlock.py
```

**Alert kỳ vọng:** 1000001, 1000005 (List Blocks).

---

### E3. Ghi biến quá trình — Write Var vào DB

```bash
# Sửa IP trong file cho đúng PLC_IP
python3 attacks/stuxnet_mitm_sim/attacker/test_readwrite_db_via_snap7.py
```

Cần `python-snap7`:

```bash
pip install python-snap7
```

**Alert kỳ vọng:** 1000010 (Write Var), 1000011 (Write Var vào DB, area 0x84).

---

### E4. DoS S7comm

```bash
# Kiểm tra PLC mở cổng 102
python3 attacks/dos/s7comm_dos.py PLC_IP --check

# Demo đầy đủ 3 phase (setup_flood → tcp_connect → szl_flood), pause 8s
python3 attacks/dos/s7comm_dos.py PLC_IP
python3 attacks/dos/s7comm_dos.py PLC_IP --mode all --duration 10 --pause 8

# Từng phase riêng (demo chi tiết)
python3 attacks/dos/s7comm_dos.py PLC_IP --mode setup_flood --duration 12
python3 attacks/dos/s7comm_dos.py PLC_IP --mode tcp_connect --duration 12 --workers 6
python3 attacks/dos/s7comm_dos.py PLC_IP --mode szl_flood --duration 12
python3 attacks/dos/s7comm_dos.py PLC_IP --mode job_flood --duration 12
```

**Alert kỳ vọng:**

| Phase | SID |
|-------|-----|
| setup_flood | 1000041, 1000043 |
| tcp_connect | 1000040 |
| szl_flood | 1000042 |

---

### E5. Malformed S7comm

```bash
# Xem 9 mẫu
python3 attacks/malformed/s7comm_malformed.py --list

# Demo đầy đủ 9 phase
python3 attacks/malformed/s7comm_malformed.py PLC_IP
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode all --repeats 3 --pause 6

# Demo từng mẫu (giải thích từng nhóm cho thầy)
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode tpkt_bad_version
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode tpkt_len_gt_payload
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode tpkt_len_lt_payload
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode cotp_invalid
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode s7_bad_protocol_id
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode s7_bad_rosctr
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode job_bad_opcode
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode write_var_malformed
python3 attacks/malformed/s7comm_malformed.py PLC_IP --mode setup_truncated
```

**Alert kỳ vọng (mỗi mode → SID tương ứng):**

| `--mode` | SID |
|----------|-----|
| tpkt_bad_version | 1000050 |
| tpkt_len_gt_payload | 1000051 |
| tpkt_len_lt_payload | 1000058 |
| cotp_invalid | 1000056 |
| s7_bad_protocol_id | 1000052 |
| s7_bad_rosctr | 1000053 |
| job_bad_opcode | 1000054 |
| write_var_malformed | 1000057 |
| setup_truncated | 1000055 |

---

### E6. Start / Stop PLC (replay)

```bash
cd attacks/start_stop_plc

python3 start_stop_plc.py PLC_IP --check -v
python3 start_stop_plc.py PLC_IP stop -v
python3 start_stop_plc.py PLC_IP start -v
```

**Sau demo Stop — bắt buộc Start lại PLC:**

```bash
python3 start_stop_plc.py PLC_IP start -v
```

**Alert kỳ vọng:**

| Hành động | SID |
|-----------|-----|
| Stop | 1000032, 1000033 |
| Start | 1000030, 1000031 |
| Mỗi phiên | 1000001 |

---

## F. Kịch bản chưa chạy live (chỉ đề cập khi hỏi)

### Upload / Download — luật sẵn, chờ PCAP

```bash
# Trên IDS, khi có file PCAP
sudo suricata -r /path/to/upload_download.pcap -c /etc/suricata/suricata.yaml -k none -l /tmp/pcap-test/
sudo grep "ICS S7COMM" /tmp/pcap-test/fast.log
```

SID: 1000020–1000026.

### MITM Stuxnet — cần root + ARP spoof

```bash
# Tham khảo (không nằm trong run_attack_tests.py)
sudo python3 attacks/stuxnet_mitm_sim/attacker/mitm/s7_intercept.py
```

SID hỗ trợ: 1000010–1000011 (ghi), 1000013 (Ack_Data nhiều — gợi ý, không chứng minh MITM).

---

## G. Xem lại alert sau demo

```bash
ssh lubuntu@172.16.16.143

# 30 alert S7 gần nhất
sudo grep "ICS S7COMM" /var/log/suricata/fast.log | tail -30

# Đếm theo SID (thô)
sudo grep -oP '\[\*\*\] \[\K[0-9]+' /var/log/suricata/fast.log | sort | uniq -c | sort -rn | head -20

# Xóa log cũ trước buổi demo mới (tuỳ chọn)
sudo truncate -s 0 /var/log/suricata/fast.log
sudo systemctl restart suricata
```

---

## H. Kịch bản trình bày gợi ý (15–25 phút)

Thứ tự dễ kể cho hội đồng: **recon → ghi DB → DoS → malformed → stop → khôi phục**.

```powershell
# Terminal Windows — từng bước, quan sát Terminal IDS
cd C:\Users\chutrunganh\Documents\HUST\Thesis

python detect\run_attack_tests.py --plc PLC_IP -s recon-nmap
# Giải thích SZL / Setup → chờ 5s, xem fast.log

python detect\run_attack_tests.py --plc PLC_IP -s write
# Giải thích Write Var DB → 1000010/1000011

python detect\run_attack_tests.py --plc PLC_IP -s dos
# Giải thích threshold DoS → 1000040–1000043

python detect\run_attack_tests.py --plc PLC_IP -s malformed
# Giải thích malformed vs DoS → 100005x

python detect\run_attack_tests.py --plc PLC_IP -s stop
# Cảnh báo Stop CPU → 1000032/1000033
```

**Khôi phục PLC sau Stop:**

```bash
python3 attacks/start_stop_plc/start_stop_plc.py PLC_IP start -v
```

Hoặc một lệnh gộp cuối buổi (không khôi phục Start):

```powershell
python detect\run_attack_tests.py --plc PLC_IP
```

---

## I. Bảng tra nhanh SID ↔ lệnh demo

| SID | Alert (rút gọn) | Lệnh / kịch bản |
|-----|-----------------|-----------------|
| 1000001 | Setup Communication | Mọi phiên S7 |
| 1000002–1000004 | Read SZL | `nmap s7-info`, DoS szl |
| 1000005 | List Blocks | `scanBlock.py` |
| 1000010 | Write Var | `test_readwrite_db_via_snap7.py` |
| 1000011 | Write Var DB | Ghi DB (area 0x84) |
| 1000013 | Ack_Data nhiều | MITM (hỗ trợ) |
| 1000030–1000031 | Start | `start_stop_plc.py start` |
| 1000032–1000033 | Stop | `start_stop_plc.py stop` |
| 1000040 | TCP flood :102 | DoS `tcp_connect` |
| 1000041 | Setup flood | DoS `setup_flood` |
| 1000042 | SZL flood | DoS `szl_flood` |
| 1000043 | Job flood | DoS setup/job |
| 1000050–1000058 | Malformed | `s7comm_malformed.py` |
| 1000020–1000026 | Up/Download | PCAP (chưa live) |

---

## J. Sự cố nhanh khi demo

| Triệu chứng | Lệnh kiểm tra / xử lý |
|-------------|------------------------|
| Script OK, không alert | `sudo tcpdump -i ens37 host PLC_IP and port 102` trên IDS |
| SSH timeout từ Windows | Ping `172.16.16.143`, VPN/lab bật chưa |
| PLC không :102 | `nc -z -w2 PLC_IP 102` trên IDS |
| Quá nhiều alert cũ | `sudo truncate -s 0 /var/log/suricata/fast.log` |
| Sau DoS PLC chậm | Restart OpenPLC / đợi vài phút |
| Sau Stop — PLC STOP | `start_stop_plc.py PLC_IP start -v` |

---

*Tài liệu liên quan: `detect/HUONG_DAN_CHAY_KICH_BAN.md`, `detect/README.md`, `attacks/malformed/README.md`, `attacks/dos/README.md`*
