import snap7
from snap7.util import *
import time

def run_plc_master():
    client = snap7.client.Client()
    
    # Kết nối tới OpenPLC (IP localhost, Rack 0, Slot 1)
    try:
        client.connect('127.0.0.1', 0, 1)
        
        if client.get_connected():
            print("--- Đã kết nối tới OpenPLC Slave thành công ---")

            # === BƯỚC 1: GỬI LỆNH NHẤN NÚT START (%MX0.0 nằm trong DB1) ===
            print("\n[Action] Đang gửi lệnh nhấn nút START...")
            
            # Đọc 1 byte từ DB1
            data_db1 = client.db_read(1, 0, 1)
            # Set bit 0 (tương ứng %MX0.0) lên True
            set_bool(data_db1, 0, 0, True)
            # Ghi lại vào PLC
            client.db_write(1, 0, data_db1)
            
            # Giữ nút nhấn trong 0.5 giây để PLC kịp quét (scan cycle)
            time.sleep(0.5)
            
            # Nhả nút START (set về False)
            set_bool(data_db1, 0, 0, False)
            client.db_write(1, 0, data_db1)
            print("[Action] Đã nhả nút START.")

            # === BƯỚC 2: GIÁM SÁT MOTOROUT (%QX0.0 nằm trong DB2) ===
            print("\n[Monitor] Bắt đầu theo dõi trạng thái Motor trong 15 giây...")
            print("(Lưu ý: Motor sẽ tự tắt sau thời gian AutoOffSetpoint của bạn)")
            
            for i in range(15):
                # Đọc 1 byte từ DB2 (Nơi chứa %QX)
                data_db2 = client.db_read(2, 0, 1)
                # Lấy bit 0 (tương ứng %QX0.0)
                motor_status = get_bool(data_db2, 0, 0)
                
                status_text = "ĐANG CHẠY [ON]" if motor_status else "ĐÃ DỪNG [OFF]"
                print(f"Giây {i+1:02d}: MotorOut (%QX0.0) là {status_text}")
                
                time.sleep(1)

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
    finally:
        if client.get_connected():
            client.disconnect()
            print("\n--- Đã ngắt kết nối ---")

if __name__ == "__main__":
    run_plc_master()