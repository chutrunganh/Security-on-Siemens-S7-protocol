Phần này trình bày các framework, công cụ dùng để mô phỏng và nghiên cứu đồ án,

## Snap7

Snap7 là một thư viện mã nguồn mở được phát triển để kết nối, truyền và điều khiển các thiết bị tự động hóa, là một trong những thư viện **mã nguồn mở** phổ biến nhất trong ngành tự động hóa.

Snap7 hỗ trợ các giao thức truyền thông **Siemens S7 (S7comm)** để kết nối và truyền dữ liệu với các thiết bị tự động hóa Siemens. Nó cung cấp các tính năng chính như:

- Đọc và ghi các biến trong PLC
- Truy cập vào các khối DB và OB trong PLC
- Cung cấp các thông tin về trạng thái của thiết bị

Các đặc điểm của Snap7: 

- Có thể được sử dụng với nhiều ngôn ngữ lập trình phổ biến như C++, C#, Python, Java, và Delphi, cho phép lập trình viên lựa chọn ngôn ngữ phù hợp nhất với dự án của mình. 

- Hoạt động trên nhiều hệ điều hành, bao gồm Windows, Linux, và macOS, mang lại sự linh hoạt cao trong việc phát triển ứng dụng.

- Tương thích với nhiều dòng PLC S7, hỗ trợ giao tiếp với các dòng PLC S7-200, S7-300, S7-400, S7-1200, và S7-1500, giúp dễ dàng tích hợp vào các hệ thống hiện có.


## OpenPLC



OpenPLC là một nền tảng mã nguồn mở cho phép  mô phỏng một PLC (Programmable Logic Controller) vật lý trên máy tính (tương thích với Windows, Linux, macOS, Raspberry Pi). Nó hỗ trợ chương trình điều khiển theo chuẩn **IEC 61131-3**, cho phép kết nối với SCADA, HMI, Modbus, hoặc thiết bị công nghiệp thật. OpenPLC có 2 phần chính:

- [**OpenPLC Runtime**](https://autonomylogic.com/runtime): đây là PLC engine, nó sẽ chạy logic PLC, mở các protocol công nghiệp.

- [**OpenPLC Editor**](https://autonomylogic.com/download): Đây là IDE để viết chương trình PLC, dùng để viết code và complie chương trình.


> [!NOTE]
> OpenPLC Editor cần có C compiler (như MinGW trên Windows hoặc GCC trên Linux) để biên dịch chương trình PLC thành mã máy có thể chạy trên OpenPLC Runtime. 

## Coding

1. **Thiết lập Slave (Server) mô phỏng PLC**

Mô phỏng một PLC có chạy giao thức S7comm bằng cách sử dụng OpenPLC (Bản chất là phần mềm này chạy một Snap7 Server bên trong [[1]](#1)).Cho phép ảo hóa một máy tính để hoạt động như một PLC vật lý. Slave này sẽ lắng nghe các yêu cầu trên cổng 102 và phản hồi dựa trên các vùng nhớ được đăng ký.

Tutorial cài đặt: https://youtu.be/wWBvFiq3ZU8?si=tVHIa5JJPeKZMd1I



```
 * Serving Flask app 'webserver.restapi'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on https://127.0.0.1:8443
 * Running on https://192.168.1.89:8443
Press CTRL+C to quit
```

OpenPLC tạo một PLC chạy 

| Bước Triển khai | Mô tả Chi tiết |
| :---- | :---- |
| Cấp phát Bộ nhớ | Sử dụng ctypes để tạo mảng byte đại diện cho các vùng nhớ DB, Merker |
| Đăng ký Area | Gắn kết mảng bộ nhớ với một số hiệu DB cụ thể thông qua hàm register\_area |
| Quản lý Sự kiện | Sử dụng pick\_event để giám sát các yêu cầu đọc/ghi từ Master và ghi log |
| Khởi động Server | Gắn kết với địa chỉ IP của card mạng và bắt đầu lắng nghe kết nối |



### **Lập trình Master (Client) truy xuất dữ liệu**

Phần Master trong mô hình chịu trách nhiệm khởi tạo kết nối và thực hiện các thao tác logic trên Slave.12 Quy trình lập trình bao gồm việc kết nối tới địa chỉ IP của Slave với các tham số Rack và Slot phù hợp.12 Sau khi kết nối thành công, Master sử dụng các hàm như db\_read để lấy dữ liệu thô (dạng bytearray) và sau đó sử dụng các hàm tiện ích trong snap7.util để chuyển đổi sang các kiểu dữ liệu có nghĩa như Boolean, Integer hay Real.12  
Đối với các dòng PLC đời mới như S7-1200/1500, có hai rào cản kỹ thuật cần được giải quyết trong phần mềm cấu hình TIA Portal trước khi Master có thể giao tiếp: thứ nhất là phải tắt tính năng "Optimized block access" trong thuộc tính của Data Block để cho phép truy cập theo offset; thứ hai là phải bật tùy chọn "Permit access with PUT/GET communication" trong phần bảo mật của CPU.12 Nếu thiếu các thiết lập này, PLC sẽ từ chối mọi yêu cầu từ các thư viện bên thứ ba như Snap7.12


Khi bạn kết nối tới PLC qua Ethernet, bạn thực ra kết nối tới Communication Processor (CP). Một CP có thể phục vụ nhiều service và module. Do đó cần `IP + Rack + Slot` để xác định được chính xác module mà ta cần sử dụng trong PLC.

# Scada

các phần mềm SCADA thương mại như WinCC (Siemens), iFIX (GE), hoặc CitectSCADA (Schneider) thường có chi phí bản quyền cao, từ vài chục đến vài trăm triệu đồng tùy theo số lượng thiết bị kết nối.  Free SCADA: ScadaBR,  OpenSCADA, Inductive Automation (Marker Edition),  AdvancedHMI 

# Tài liệu tham khảo

<a id="1">[1]</a> Available at: https://gitlab.fing.edu.uy/gsi/tectonic-ot/openplcmd/-/blob/main/documentation/S7-Protocol/Siemens%20Protocol%20driver%20for%20OpenPLC.pdf, accessed 12 April 2026.


Siemens S7 Wiring: The Ultimate Guide to siemens diagram - PLC AI, truy cập vào tháng 3 17, 2026, https://plcai.app/plc-ai-blog/f/siemens-plc-wiring-the-ultimate-guide-to-s7-1200-and-s7-1500
A Decade After Stuxnet: How Siemens S7 is Still an Attacker's Heaven - YouTube, truy cập vào tháng 3 17, 2026, https://www.youtube.com/watch?v=4-VoLm2SXao
Siemens PLC & Python Snap7 Tutorial–Read & Write Integers in Siemens PLC (S7-1200/1500) #industry4_0 - YouTube, truy cập vào tháng 3 17, 2026, https://www.youtube.com/watch?v=Jyrbl9vCd8k
Engineer Point - YouTube, truy cập vào tháng 3 17, 2026, https://www.youtube.com/@engineerpoint2658/videos
Video Tutorial: Real-Time Collection for Siemens S7 Plus Ethernet - Blog, truy cập vào tháng 3 17, 2026, https://blog.softwaretoolbox.com/video-tutorial-siemens-s7-plus-ethernet-topserver
S7 Protocol Overview and PROFINET Differences - ALLPCB, truy cập vào tháng 3 17, 2026, https://www.allpcb.com/allelectrohub/s7-protocol-overview-and-profinet-differences


Thực hiện quét mạng và khai thác vào PLC, đọc file PDF