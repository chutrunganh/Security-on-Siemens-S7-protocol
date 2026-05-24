# Phát hiện tấn công S7comm bằng Suricata

Thư mục này chứa các luật Suricata để phát hiện các hành vi S7comm đã mô phỏng trong phần `attacks`:

- Reconnaissance: quét TCP/102, thiết lập S7, đọc SZL, liệt kê block.
- Ghi biến quá trình: ghi `DB1.DBW2` để đổi `iSetpoint` từ `1200` lên `2000`.
- Up/Download chương trình: các lệnh truyền block `0x1a` đến `0x1f`.
- Start/Stop PLC replay: phát lại payload `PLC Control 0x28` và `PLC Stop 0x29`.
- MITM Stuxnet mô phỏng: sửa dữ liệu trả về cho HMI. Phần S7comm có thể quan sát bằng luật phản hồi `Ack_Data`; phần ARP spoofing nên kết hợp thêm phát hiện ARP bất thường hoặc log switch vì bản chất cần tương quan trạng thái L2.

File luật chính:

```text
detect/rules/s7comm.rules
```

## Cách nạp luật

Copy hoặc include file luật vào cấu hình Suricata:

```yaml
rule-files:
  - detect/rules/s7comm.rules
```

Sau đó chạy kiểm tra cú pháp:

```bash
suricata -T -c /etc/suricata/suricata.yaml -S detect/rules/s7comm.rules
```

Khi chạy trong lab, nên cấu hình `HOME_NET` trỏ đúng tới IP PLC hoặc dải PLC, ví dụ:

```yaml
vars:
  address-groups:
    HOME_NET: "[192.168.50.10,172.16.16.44,172.16.16.136]"
```

Nếu để `HOME_NET` quá rộng, các lệnh đọc hợp lệ từ HMI cũng có thể sinh nhiều cảnh báo.

## Nền tảng giao thức dùng để viết luật

S7comm cổ điển chạy trên TCP/102 theo stack:

```text
TCP -> TPKT -> COTP -> S7comm
```

Trong các gói S7comm dạng Data TPDU thường gặp trong lab, phần payload TCP có bố cục ổn định:

| Offset | Giá trị | Ý nghĩa |
|---:|---|---|
| `0` | `03` | TPKT version |
| `1` | `00` | TPKT reserved |
| `4..6` | `02 f0 80` | COTP Data TPDU |
| `7` | `32` | S7 protocol id |
| `8` | `01` / `03` / `07` | `ROSCTR`: Job / Ack_Data / Userdata |
| `17` | Function code | Byte đầu của phần S7 Parameter đối với Job/Userdata thông thường |

Vì vậy hầu hết luật đều bắt đầu bằng các điều kiện:

```suricata
content:"|03 00|"; offset:0; depth:2;
content:"|02 F0 80 32 01|"; offset:4; depth:5;
```

Điều này giúp luật chỉ khớp các gói có TPKT, COTP và S7comm, tránh báo nhầm trên TCP/102 nhưng không phải S7comm.

Các mã chức năng được lấy từ bài viết `gmiru.com/article/s7comm-part2/` và đối chiếu với traffic trong thư mục `attacks`:

| Function | Ý nghĩa | Liên quan trong đồ án |
|---:|---|---|
| `0xf0` | Setup Communication | Bước đầu của mọi phiên S7comm |
| `0x04` | Read Var | HMI đọc `DB1`, `DB2`; attacker đọc lại trạng thái |
| `0x05` | Write Var | Attacker ghi `DB1.DBW2` |
| `0x1a` | Request Download | Chuẩn bị tải block xuống PLC |
| `0x1b` | Download Block | Truyền block xuống PLC |
| `0x1c` | Download Ended | Kết thúc download |
| `0x1d` | Start Upload | Bắt đầu lấy block từ PLC |
| `0x1e` | Upload Block | Lấy dữ liệu block |
| `0x1f` | End Upload | Kết thúc upload |
| `0x28` | PLC Control | Start CPU, activate/delete block, copy RAM to ROM |
| `0x29` | PLC Stop | Stop CPU |

## Giải thích từng nhóm luật

### 1. Setup Communication

Luật:

```suricata
sid:1000001
msg:"ICS S7COMM Setup Communication to PLC"
```

Lý do xây dựng:

- Trong S7comm, client phải gửi `Setup Communication` (`0xf0`) trước khi đọc, ghi, upload, download hoặc điều khiển PLC.
- Bản thân gói này chưa phải tấn công, nhưng là dấu hiệu có một client đang mở phiên S7comm tới PLC.
- Trong tấn công reconnaissance, start/stop replay và ghi biến, script đều thực hiện TCP -> COTP -> S7 Setup trước khi gửi lệnh chính.

Tham số chính:

- `flow:to_server,established`: chỉ xét chiều client tới PLC sau khi TCP đã bắt tay.
- `content:"|02 F0 80 32 01|"; offset:4; depth:5`: xác nhận COTP Data TPDU, S7 protocol id `0x32`, ROSCTR `0x01` là Job.
- `content:"|F0|"; offset:17; depth:1`: function code `Setup Communication`.

Ý nghĩa cảnh báo:

- Có một phiên S7comm mới được mở tới PLC.
- Nên dùng để dựng baseline hoặc phát hiện engineering station lạ. Nếu HMI/SCADA poll liên tục, luật này có thể báo nhiều khi kết nối được tạo lại.

### 2. Read SZL và quét thông tin PLC

Luật:

```suricata
sid:1000002  Read SZL request
sid:1000003  Read SZL module identification 0x0011
sid:1000004  Read SZL communication status 0x001c
```

Lý do xây dựng:

- Trong `attacks/reconnaissance`, Nmap NSE `s7-info` sau khi Setup Communication sẽ gửi `Read SZL` để lấy thông tin CPU.
- SZL `0x0011` trả về module identification, ví dụ order number `6ES7 315-2EH14-0AB0`.
- SZL `0x001c` trả về communication status, system name, module type, serial number, copyright.
- Đây là thông tin phục vụ fingerprint PLC, thường xuất hiện trong giai đoạn reconnaissance.

Tham số chính:

- `content:"|02 F0 80 32 07|"; offset:4; depth:5`: ROSCTR `0x07`, tức S7 Userdata. Read SZL thuộc nhóm Userdata/CPU functions, không phải Job `Read Var`.
- `content:"|00 01 12 04 11 44 01 00|"; offset:17; depth:8`: mẫu parameter của `CPU functions -> Read SZL`.
  - `00 01`: function CPU services / item count.
  - `12`: variable specification.
  - `04`: độ dài phần địa chỉ phía sau.
  - `11`: method request.
  - `44`: type request + function group CPU functions.
  - `01`: subfunction Read SZL.
- `content:"|00 11 00 01|"`: SZL-ID `0x0011`, index `0x0001`.
- `content:"|00 1C 00 00|"`: SZL-ID `0x001c`, index `0x0000`.

Ý nghĩa cảnh báo:

- `sid:1000002` báo mọi yêu cầu đọc SZL.
- `sid:1000003` và `sid:1000004` cụ thể hơn, bám sát traffic trong phần reconnaissance nên phù hợp để chứng minh Nmap/S7 fingerprinting.

### 3. List Blocks

Luật:

```suricata
sid:1000005
msg:"ICS S7COMM List Blocks request - PLC block inventory enumeration"
```

Lý do xây dựng:

- Script `scanBlock.py` dùng Snap7 để gọi `list_blocks()` và `list_blocks_of_type()`.
- Traffic tương ứng là `Userdata -> Block functions -> List blocks`.
- Việc liệt kê OB/FB/FC/DB/SDB/SFC/SFB giúp attacker biết PLC đang có block nào trước khi upload, download hoặc đọc metadata block.

Tham số chính:

- `ROSCTR 0x07`: Userdata.
- `content:"|00 01 12 04 11 13 01 00|"; offset:17; depth:8`:
  - `13`: type request + function group Block functions.
  - `01`: subfunction List blocks.

Ý nghĩa cảnh báo:

- Có client đang kiểm kê block chương trình trên PLC.
- Đây thường là bước reconnaissance sâu hơn so với chỉ quét cổng TCP/102.

### 4. Write Var và ghi setpoint trong mô phỏng Stuxnet

Luật:

```suricata
sid:1000010  Write Var request to PLC
sid:1000011  Write Var to DB1.DBW2 setpoint
sid:1000012  Write Var DB1.DBW2 setpoint to 2000
```

Lý do xây dựng:

- Trong mô phỏng Stuxnet MITM, attacker ghi `iSetpoint` tại `DB1.DBW2` từ `1200` (`0x04b0`) thành `2000` (`0x07d0`).
- S7comm cổ điển không có xác thực hoặc toàn vẹn đủ mạnh, nên nếu attacker tới được TCP/102 thì có thể gửi `Write Var`.
- Ghi biến quá trình là hành vi nguy hiểm hơn đọc biến vì nó làm thay đổi logic vận hành.

Tham số chính:

- `content:"|05|"; offset:17; depth:1`: function code `Write Var`.
- `content:"|12 0A 10|"; offset:19; depth:3`:
  - `12`: variable specification.
  - `0A`: độ dài request item kiểu any-type.
  - `10`: syntax id any-type.
- `content:"|00 01 84 00 00 10|"; offset:25; depth:6`:
  - `00 01`: DB number 1.
  - `84`: memory area DB.
  - `00 00 10`: địa chỉ bit offset `0x10` = `16` bit = byte offset `2`, tức `DBW2`.
- `content:"|00 04 00 10 07 D0|"; offset:31; depth:6`:
  - `00`: return code trong Write Request.
  - `04`: transport size BYTE/WORD/DWORD.
  - `00 10`: độ dài 16 bit = 2 byte.
  - `07 D0`: giá trị `2000`.

Ý nghĩa cảnh báo:

- `sid:1000010`: có bất kỳ lệnh ghi biến nào vào PLC. Trong môi trường vận hành ổn định, lệnh này nên rất hiếm và cần điều tra.
- `sid:1000011`: có ghi đúng địa chỉ `DB1.DBW2`, là biến `iSetpoint` của mô phỏng.
- `sid:1000012`: có ghi đúng giá trị `2000`, khớp payload làm máy ly tâm vượt ngưỡng trong kịch bản Stuxnet mô phỏng.

### 5. Ack_Data bất thường chiều PLC về HMI

Luật:

```suricata
sid:1000013
msg:"ICS S7COMM suspicious Ack_Data response to HMI/engineering station"
```

Lý do xây dựng:

- Trong MITM, attacker không chỉ ghi PLC mà còn sửa gói trả về từ PLC tới HMI để HMI vẫn thấy setpoint `1200`.
- Suricata rule thuần chữ ký không thể chứng minh payload đã bị sửa nếu không có trạng thái ứng dụng hoặc so sánh với giá trị thật trong PLC.
- Tuy nhiên có thể ghi nhận luồng `Ack_Data` từ TCP/102 về HMI với threshold để hỗ trợ điều tra và tương quan cùng cảnh báo `Write Var`.

Tham số chính:

- `flow:from_server,established`: xét chiều PLC trả lời.
- `content:"|02 F0 80 32 03|"; offset:4; depth:5`: ROSCTR `0x03` là `Ack_Data`.
- `threshold:type both, track by_src, count 60, seconds 10`: giảm nhiễu bằng cách chỉ báo khi một PLC gửi nhiều phản hồi trong thời gian ngắn.

Ý nghĩa cảnh báo:

- Không khẳng định MITM một mình.
- Có giá trị khi đi kèm cảnh báo ARP spoofing, thay đổi MAC bất thường trên switch, hoặc cảnh báo `Write Var DB1.DBW2`.

### 6. Up/Download chương trình

Luật:

```suricata
sid:1000020  Request Download 0x1a
sid:1000021  PLC requests Download Block data 0x1b
sid:1000022  Download Ended 0x1c
sid:1000023  Start Upload 0x1d
sid:1000024  Upload Block 0x1e
sid:1000025  End Upload 0x1f
sid:1000026  Client sends Download Block data 0x1b
```

Lý do xây dựng:

- Theo Siemens, download là client gửi chương trình xuống PLC, upload là client lấy chương trình từ PLC về.
- Các block OB/DB/FC/FB chứa logic và dữ liệu chương trình. Việc upload có thể làm lộ logic điều khiển; download có thể thay đổi logic điều khiển.
- Bài `gmiru.com/article/s7comm-part2/` xác định nhóm function `0x1a-0x1f` là block up/download. README `attacks/down_up_program` cũng mô tả đúng chuỗi này.
- Riêng `Download Block 0x1b` là trường hợp đặc biệt: sau `Request Download`, PLC gửi Job yêu cầu block, sau đó client trả `Ack_Data` chứa dữ liệu block xuống PLC. Vì vậy có hai luật `sid:1000021` và `sid:1000026` cho hai chiều của cùng giai đoạn.

Tham số chính:

- `ROSCTR 0x01`: Job. Dùng cho `Request Download`, `Download Ended`, `Start Upload`, `Upload Block`, `End Upload`; với `sid:1000021` thì Job đi từ PLC về client.
- `ROSCTR 0x03`: Ack_Data. Dùng cho `sid:1000026` khi client gửi dữ liệu block trả lời yêu cầu download của PLC.
- `offset:17`: function code nằm ở byte đầu phần Parameter.
- `offset:19`: function code trong Ack_Data vì S7 Ack_Data có thêm 2 byte `error class` và `error code` trước phần Parameter.
- `0x1a` đến `0x1f`: từng giai đoạn trong upload/download.

Ý nghĩa cảnh báo:

- Trong môi trường production, up/download block chỉ nên xảy ra trong cửa sổ bảo trì hoặc từ engineering station được cho phép.
- Nếu xuất hiện ngoài thời điểm nạp chương trình, đây là cảnh báo mức cao.

### 7. PLC Control và PLC Stop replay

Luật:

```suricata
sid:1000030  PLC Control command
sid:1000031  replayed Start CPU P_PROGRAM
sid:1000032  PLC Stop command
sid:1000033  replayed Stop CPU P_PROGRAM
```

Lý do xây dựng:

- Trong `attacks/start_stop_plc`, payload capture từ TIA Portal được phát lại để Start/Stop CPU.
- `0x28` là `PLC Control`, dùng cho nhiều routine như start PLC, activate/delete block, compress memory, copy RAM to ROM.
- `0x29` là `PLC Stop`, routine luôn là `P_PROGRAM`.
- Chuỗi ASCII `P_PROGRAM` là PI-Service được dùng trong payload Start/Stop CPU.

Tham số chính:

- `content:"|28|"; offset:17; depth:1`: PLC Control.
- `content:"|29|"; offset:17; depth:1`: PLC Stop.
- `content:"P_PROGRAM"; distance:0; within:24`: xác nhận routine điều khiển chương trình PLC.

Ý nghĩa cảnh báo:

- `sid:1000030` và `sid:1000032` là luật tổng quát cho lệnh điều khiển/stop.
- `sid:1000031` và `sid:1000033` bám sát payload replay trong lab, giúp chứng minh tấn công Start/Stop CPU.
- Đây là nhóm cảnh báo nghiêm trọng vì có thể trực tiếp đổi trạng thái RUN/STOP của PLC.

## Lưu ý về độ chính xác

Các luật này cố ý viết tường minh bằng `content`, `offset`, `depth`, `distance`, `within` để dễ giải thích và đối chiếu trong Wireshark. Cách này phù hợp cho lab và luận văn vì chỉ rõ byte nào tạo nên cảnh báo.

Trong hệ thống thực tế cần bổ sung:

- Danh sách engineering station hợp lệ, HMI hợp lệ và PLC hợp lệ.
- Cửa sổ thời gian bảo trì được phép nạp chương trình.
- Phát hiện ARP spoofing hoặc duplicate IP/MAC ở switch/Zeek/Suricata EVE.
- Tương quan nhiều cảnh báo: ví dụ `Write Var DB1.DBW2` + nhiều `Ack_Data` + ARP bất thường sẽ mạnh hơn một cảnh báo đơn lẻ.
- Kiểm tra TCP segmentation. Nếu S7 PDU bị chia nhỏ bất thường, luật offset tuyệt đối có thể bỏ sót; khi đó nên dùng app-layer parser, Lua detection hoặc tiền xử lý PCAP để normalize.
