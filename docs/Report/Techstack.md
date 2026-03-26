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