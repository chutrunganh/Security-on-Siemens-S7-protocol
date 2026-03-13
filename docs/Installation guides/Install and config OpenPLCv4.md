*Write by cta*

Cài đặt tại: https://autonomylogic.com/runtime

Github: https://github.com/Autonomy-Logic/openplc-runtime/

Khác với OpenPLC v3 Runtime khi chạy sẽ mở 2 port (mặc định chưa enable thêm protocol nào khác):

- Port 8080: Web server để cấu hình và giám sát PLC runtime 

- Port **8443**: RESTful API (được chay bởi Flask server) để giao tiếp với PLC runtime (ví dụ như để upload chương trình PLC, đọc/ghi dữ liệu, ...). OpenPLC Editor sử dụng API này để giao tiếp với Runtime.

OpenPLC v4 đã loại bỏ giao diện quản trị web trên port 8080, thay vào đó chỉ còn RESTful API trên port 8443, bởi vì giờ đây toàn bộ các chức năng cấu hình, giám sát runtime của web quản trị đều có thể được thực hiện thông qua API này. OpenPLC Editor v4 đã hỗ trợ đầy đủ các API này thông qua GUI.




Kết nối với PLC runtime `Devies` > `Configuration`:


![alt text](image.png)


Như này là đã kết nối xong với PLC rumtime, giờ ta muốn PLC sẽ chạy như một server để chờ client kết nối tới `+` > `Server` > Thêm tên và chọn giao thức `Siemens S7comm`:

![alt text](image-1.png)

Xác nhận PLC đã chạy Siemens S7 thành công trên port 102.

![alt text](image-2.png)


IF StartBtn THEN
    RunLatch := TRUE;
    {printf("S7 Master requested START\n")}
END_IF;

IF StopBtn THEN
    RunLatch := FALSE;
    {printf("S7 Master requested STOP\n")}
END_IF;

AutoOffTimer(IN := RunLatch, PT := AutoOffSetpoint);
IF AutoOffTimer.Q THEN
    RunLatch := FALSE;
    {printf("Motor AUTO OFF by Timer\n")}
END_IF;

MotorOut := RunLatch;

VAR
	StartBtn : bool AT %MX0.0; (* Nút Start - Master ghi vào đây *)
	StopBtn : bool AT %MX0.1; (* Nút Stop - Master ghi vào đây *)
	MotorOut : bool AT %QX0.0; (* Đầu ra Motor - Master đọc từ đây *)
	RunLatch : bool := FALSE; (* Biến chốt nội bộ *)
	AutoOffTimer : TON; (* Bộ định thời tự tắt *)
	AutoOffSetpoint : time := T#10s; (* Thời gian chạy tối đa *)
END_VAR