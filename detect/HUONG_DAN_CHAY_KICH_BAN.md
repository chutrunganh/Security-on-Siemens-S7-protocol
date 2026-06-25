# Hướng dẫn chạy kịch bản tấn công và xem cảnh báo Suricata

Tài liệu này tóm tắt **cách chạy lab**, **từng kịch bản tấn công** và **lệnh xem alert** trên IDS. Chi tiết kỹ thuật từng byte luật xem thêm `detect/README.md`.

**Copy-paste demo buổi trình bày:** xem [`DEMO_LENH_DAY_DU.md`](DEMO_LENH_DAY_DU.md) — đủ lệnh Windows + IDS + từng kịch bản.

---

## 1. Tổng quan

| Thành phần | Mô tả |
|---|---|
| **Luật** | `s7comm.rules` (19) + `ics_dos.rules` (4) + `s7comm_malformed.rules` (9) |
| **IDS** | Suricata trên VM `lubuntu@172.16.16.143` |
| **Bắt gói** | `ens37` (mạng `172.16.16.x`) và `ens33` (mạng `192.168.60.x` / traffic tới `192.168.50.x`) |
| **PLC trong lab** | Ví dụ `172.16.16.145` hoặc `192.168.50.10` (OpenPLC + S7 server, cổng **102**) |

**Quan trọng:** Suricata chỉ báo khi **nhìn thấy gói tin** trên interface đang bắt. Nếu quét từ máy khác mà traffic không đi qua IDS (hoặc chưa SPAN mirror), sẽ **không có alert** dù nmap vẫn thành công.

---

## 2. Kịch bản đã chạy thử vs chưa chạy live

| Kịch bản | Đã mô phỏng & test alert? | Luật Suricata (SID) |
|---|---|---|
| Reconnaissance (nmap s7-info, đọc SZL) | Có | 1000001–1000004 |
| Reconnaissance (liệt kê block) | Có (một phần) | 1000005 |
| Ghi biến quá trình — Write Var vào DB | Có | 1000010–1000011 |
| **DoS S7comm** (flood TCP/Setup/SZL) | Có (script mới) | **1000040–1000043** |
| **Malformed S7comm** | Có (`s7comm_malformed.py`) | **1000050–1000058** |
| Start / Stop PLC (replay) | Có | 1000030–1000033 |
| MITM (sửa phản hồi HMI) | Chưa test đầy đủ trong lab | 1000013 (+ ARP ngoài S7) |
| **Upload / Download block** | **Chưa** — chưa mô phỏng được trên PLC | **1000020–1000026** (đã viết luật, chờ file PCAP) |

**Upload/Download:** Luật đã có trong `s7comm.rules` (function `0x1a`–`0x1f`). Khi có file PCAP mô phỏng (từ TIA Portal hoặc capture thật), chạy:

```bash
sudo suricata -r ten_file.pcap -c /etc/suricata/suricata.yaml -k none
```

hoặc replay qua `tcpreplay` vào mạng lab để kiểm tra alert.

---

## 3. Chuẩn bị trước khi chạy

### 3.1. Trên máy IDS (`172.16.16.143`)

```bash
ssh lubuntu@172.16.16.143
systemctl is-active suricata    # phải: active
```

Triển khai lại luật từ máy Windows (nếu sửa `s7comm.rules`):

```powershell
python detect\deploy_ids.py
```

### 3.2. Mở terminal theo dõi alert (chạy song song)

```bash
sudo tail -f /var/log/suricata/fast.log | grep --line-buffered "ICS S7COMM"
```

Hoặc dạng JSON:

```bash
sudo tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
```

### 3.3. Kiểm tra IDS có thấy traffic tới PLC không

Thay `PLC_IP` bằng IP PLC (ví dụ `192.168.50.10`):

```bash
sudo tcpdump -i ens33 -n host PLC_IP and port 102
# hoặc trên mạng 172.16.16.x:
sudo tcpdump -i ens37 -n host PLC_IP and port 102
```

Có gói trên tcpdump → Suricata mới có thể báo.

---

## 4. Xem alert (tóm tắt lệnh)

| Mục đích | Lệnh |
|---|---|
| Realtime, dễ đọc | `sudo tail -f /var/log/suricata/fast.log` |
| Chỉ S7comm | `sudo grep "ICS S7COMM" /var/log/suricata/fast.log \| tail -30` |
| Theo IP PLC | `sudo grep "192.168.50.10" /var/log/suricata/fast.log` |
| JSON chi tiết | `sudo tail -f /var/log/suricata/eve.json \| jq 'select(.event_type=="alert")'` |
| Trạng thái service | `systemctl status suricata` |

---

## 5. Từng kịch bản tấn công

### 5.1. Reconnaissance — quét thông tin PLC (Nmap)

**Mục đích:** Attacker tìm PLC mở cổng 102, thiết lập S7comm, đọc **SZL** (System Status List) để lấy model CPU, serial, tên hệ thống — giống bước fingerprint trong `attacks/reconnaissance/`.

**Chạy** (trên máy có nmap, ví dụ `ubuntuserver2204`):

```bash
nmap -p 102 --script s7-info 192.168.50.10
```

**Suricata thường báo:**

- `ICS S7COMM Setup Communication to PLC` (SID 1000001)
- `ICS S7COMM Read SZL request` (1000002)
- `ICS S7COMM Read SZL module identification 0x0011` (1000003)

**Lưu ý:** Máy quét phải nằm trên đường mà IDS bắt được (`ens33` nếu đi qua router tới `192.168.50.x`).

---

### 5.2. Reconnaissance — liệt kê block trên PLC

**Mục đích:** Đọc danh sách OB/FB/FC/DB trên PLC (chuẩn bị upload/download hoặc phân tích logic).

**Chạy** (cần Python + snap7, sửa `IP_ADDRESS` trong file):

```bash
cd attacks/reconnaissance
python3 scanBlock.py --ip PLC_IP --list-only
```

**Lưu ý OpenPLC:** `get_block_info()` thường **timeout** (S7 server mô phỏng không đầy đủ). Dùng `--list-only` để chỉ gọi `list_blocks()` — đủ cho recon và alert 1000005.

**Suricata có thể báo:**

- `ICS S7COMM Setup Communication` (1000001)
- `ICS S7COMM List Blocks request` (1000005) — khi lệnh List Blocks được gửi thành công

---

### 5.3. Ghi biến quá trình — Write Var vào DB

**Mục đích:** Phát hiện lệnh S7comm `Write Var` ghi vào vùng nhớ **Data Block** (`area = 0x84`). Kịch bản lab Stuxnet (`attacks/stuxnet_mitm_sim`) là ví dụ: ghi `DB1.DBW2` (`iSetpoint`) từ `1200` lên `2000`.

**Chạy:**

```bash
# Sửa IP_ADDRESS trong file cho đúng PLC
python3 attacks/stuxnet_mitm_sim/attacker/test_readwrite_db_via_snap7.py
```

**Suricata thường báo:**

- `ICS S7COMM Write Var request to PLC` (1000010) — mọi lệnh ghi biến
- `ICS S7COMM Write Var to DB memory area` (1000011) — ghi qua Any-type vào DB (mọi số DB, mọi offset)

---

### 5.4. DoS trên kênh S7comm (một script)

**Mục đích:** Flood TCP/102, Setup Communication, Read SZL — một lệnh, có **pause** giữa các phase để Suricata kịp alert.

**Script:** `attacks/dos/s7comm_dos.py`

```bash
python3 attacks/dos/s7comm_dos.py <IP_PLC> --check

# Mặc định: --mode all — setup_flood → pause 8s → tcp_connect → pause → szl_flood
python3 attacks/dos/s7comm_dos.py <IP_PLC>

# Tùy chỉnh thời gian (mặc định duration=10s, pause=8s)
python3 attacks/dos/s7comm_dos.py <IP_PLC> --duration 12 --pause 10
```

**Suricata (`ics_dos.rules`):** 1000040 (tcp), 1000041 (setup), 1000042 (szl), 1000043 (job).

**Lưu ý:** Traffic qua IDS mirror; sau test có thể cần restart OpenPLC.

---

### 5.4b. Malformed S7comm (gói tin sai cú pháp)

**Mục đích:** Gửi PDU **cố ý sai** tới cổng 102 (khác DoS — không flood lệnh hợp lệ). Bốn nhóm: TPKT/COTP, header S7, function/tham số, cắt cụt.

**Script:** `attacks/malformed/s7comm_malformed.py`

```bash
python3 attacks/malformed/s7comm_malformed.py <IP_PLC> --list

# Mặc định: 9 phase, repeats=3, pause=6s
python3 attacks/malformed/s7comm_malformed.py <IP_PLC>

# Một mẫu
python3 attacks/malformed/s7comm_malformed.py <IP_PLC> --mode s7_bad_rosctr
```

**Suricata (`s7comm_malformed.rules`):** 1000050 (TPKT version), 1000051/1000058 (TPKT length), 1000056 (COTP), 1000052–1000054 (S7 header/function), 1000057 (Write Var ngắn), 1000055 (truncated).

**Lưu ý:** PLC lab thường chỉ từ chối/đóng TCP; không kỳ vọng Stop CPU như replay Start/Stop.

---

### 5.5. Start / Stop PLC (replay attack)

**Mục đích:** Phát lại gói S7comm đã capture từ TIA Portal để **Stop** hoặc **Start** CPU mà không cần đăng nhập (`attacks/start_stop_plc`).

**Chạy:**

```bash
cd attacks/start_stop_plc

# Kiểm tra kết nối S7
python3 start_stop_plc.py <IP_PLC> --check -v

# Dừng CPU
python3 start_stop_plc.py <IP_PLC> stop -v

# Khởi động lại CPU
python3 start_stop_plc.py <IP_PLC> start -v
```

Ví dụ: `python3 start_stop_plc.py 172.16.16.145 stop -v`

**Suricata thường báo:**

| Hành động | Alert (SID) |
|---|---|
| Stop | PLC Stop (1000032), replayed Stop P_PROGRAM (1000033) |
| Start | PLC Control (1000030), replayed Start P_PROGRAM (1000031) |
| Mỗi phiên | Setup Communication (1000001) |

**Lưu ý:** Sau khi test Stop, nhớ chạy lại `start` để PLC về RUN.

---

### 5.6. Upload / Download block — chưa chạy live

**Mục đích (lý thuyết):**

- **Download:** Client gửi chương trình **xuống** PLC (nạp block OB/DB/FC/FB).
- **Upload:** Client **lấy** chương trình từ PLC về.

**Trạng thái lab:** Chưa mô phỏng được trên OpenPLC trong đồ án. Luật **đã viết sẵn** (SID 1000020–1000026) cho các function `0x1a`–`0x1f`.

**Khi có file PCAP mô phỏng:**

```bash
# Trên IDS
sudo suricata -r /path/to/upload_download.pcap -c /etc/suricata/suricata.yaml -k none -l /var/log/suricata/
sudo grep "ICS S7COMM" /var/log/suricata/fast.log
```

Tham khảo mô tả giao thức: `attacks/down_up_program/README.md`.

---

### 5.7. MITM Stuxnet (ARP + sửa S7) — chưa test alert đầy đủ

**Mục đích:** Attacker chặn/sửa traffic giữa HMI và PLC; HMI vẫn thấy setpoint cũ trong khi PLC đã bị ghi giá trị mới.

**Script lab:** `attacks/stuxnet_mitm_sim/attacker/mitm/s7_intercept.py` (cần quyền root, bettercap ARP spoof).

**Suricata liên quan:**

- Ghi PLC: giống mục 5.3 (1000010–1000011)
- Quan sát phụ: `suspicious Ack_Data` (1000013) — cần tương quan thêm, không khẳng định MITM một mình
- ARP spoof: **không** nằm trong `s7comm.rules`; cần luật/tool khác (Zeek, switch log, v.v.)

---

## 6. Chạy nhanh kịch bản từ Windows (`run_attack_tests.py`)

**Hai bước tách riêng:**

1. **Deploy luật** (một lần đầu buổi lab, hoặc sau khi sửa file `.rules`):

```powershell
python detect\deploy_ids.py
```

2. **Chạy kịch bản** — chỉ upload script tấn công, SSH chạy lệnh, đọc alert (không deploy lại Suricata):

```powershell
python detect\run_attack_tests.py --list
python detect\run_attack_tests.py -s dos
python detect\run_attack_tests.py -s write
python detect\run_attack_tests.py --plc 172.16.16.152 -s malformed
```

**Chạy tất cả kịch bản** (không có tham số `-s`):

```powershell
python detect\run_attack_tests.py
```

Thứ tự: `recon-nmap` → `recon-blocks` → `write` → `dos` → `malformed` → `stop`.

| ID | Kịch bản |
|----|----------|
| `recon-nmap` | `nmap --script s7-info` |
| `recon-blocks` | `scanBlock.py` |
| `write` | Ghi DB (`write_db_lab.py`) |
| `dos` | `s7comm_dos.py --mode all` |
| `malformed` | `s7comm_malformed.py --mode all` |
| `stop` | `start_stop_plc.py` check + stop |

**Tuỳ chọn:**

- `--plc IP` — chỉ định PLC (vẫn kiểm tra cổng 102 từ IDS).
- `--setup-tools` — cài nmap/snap7 trên IDS (chỉ lần đầu lab).

PLC mặc định: tự quét `PLC_CANDIDATES` trong script (hiện `.152`, `.145`, `.44`, `.136`).

---

## 7. Bảng tra SID ↔ kịch bản

| SID | Tên alert (rút gọn) | Kịch bản |
|-----|---------------------|----------|
| 1000001 | Setup Communication | Mọi phiên S7 mới |
| 1000002 | Read SZL | Nmap s7-info |
| 1000003 | Read SZL 0x0011 | Nmap s7-info |
| 1000004 | Read SZL 0x001c | Nmap s7-info |
| 1000005 | List Blocks | scanBlock.py |
| 1000010 | Write Var | Ghi biến bất kỳ (M/I/Q/DB, …) |
| 1000011 | Write Var vào DB | Ghi Data Block (Any-type, area 0x84) |
| 1000013 | Ack_Data (nhiều) | Gợi ý MITM (hỗ trợ) |
| 1000040 | TCP SYN flood :102 | DoS `tcp_connect` |
| 1000041 | Setup Communication flood | DoS `setup_flood` |
| 1000042 | Read SZL flood | DoS `szl_flood` |
| 1000043 | S7 Job flood | DoS `setup` / `job_flood` |
| 1000050 | Invalid TPKT version | Malformed `tpkt_bad_version` |
| 1000051 | TPKT length > payload | Malformed `tpkt_len_gt_payload` |
| 1000058 | TPKT length < payload | Malformed `tpkt_len_lt_payload` |
| 1000056 | Invalid COTP | Malformed `cotp_invalid` |
| 1000052–1000055, 1000057 | S7 header / trunc / Write | Malformed các `--mode` tương ứng |
| 1000020–1000026 | Up/Download block | **Chờ PCAP** |
| 1000030–1000031 | PLC Control / Start | start_stop_plc start |
| 1000032–1000033 | PLC Stop | start_stop_plc stop |

---

## 8. Sự cố thường gặp

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Nmap thành công, không alert | Traffic không đi qua `ens33`/`ens37` của IDS; cần SPAN hoặc chạy tấn công qua đường IDS nhìn thấy |
| Không alert trên `192.168.50.10` | Trước đây Suricata chỉ bắt `ens37`; đã thêm `ens33` — restart: `sudo systemctl restart suricata` |
| Quá nhiều Setup Communication | HMI poll liên tục; có thể bỏ qua hoặc thu hẹp `HOME_NET` |
| Upload/Download không báo | Chưa có traffic thật/PCAP; luật chỉ kích hoạt khi có gói `0x1a`–`0x1f` |

---

## 9. File liên quan trong repo

```text
detect/
  rules/s7comm.rules
  rules/ics_dos.rules
  rules/s7comm_malformed.rules
  deploy_ids.py
  run_attack_tests.py
  README.md
  HUONG_DAN_CHAY_KICH_BAN.md
  DEMO_LENH_DAY_DU.md          # Lệnh demo copy-paste đầy đủ

attacks/
  malformed/s7comm_malformed.py
  dos/s7comm_dos.py
  reconnaissance/
  start_stop_plc/
  stuxnet_mitm_sim/
  down_up_program/
```
