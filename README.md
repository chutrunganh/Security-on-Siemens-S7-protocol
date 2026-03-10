# Techstack

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

https://github.com/thiagoralves/OpenPLC_v3

OpenPLC là một nền tảng mã nguồn mở cho phép  mô phỏng một PLC (Programmable Logic Controller) vật lý trên máy tính (tương thích với Windows, Linux, macOS, Raspberry Pi). Nó hỗ trợ chương trình điều khiển theo chuẩn **IEC 61131-3**, cho phép kết nối với SCADA, HMI, Modbus, hoặc thiết bị công nghiệp thật.


OpenPLC tuân theo chuẩn IEC 61131-3, chuẩn này định nghĩa 5 ngôn ngữ PLC chính:

1. **Structured Text (ST)**: Là các dòng mã thuần văn bản, có dạng gần giống C / Pascal. Nó sử dụng các cấu trúc như `IF...THEN`, `FOR`, `WHILE`. Ví dụ:

```
IF Input1 THEN
    Output1 := NOT Output1;
END_IF;
```

2. **Ladder Diagram (LD)**: Ngôn ngữ đồ họa dạng mạch relay. Nó gồm hai thanh dọc (thanh nguồn) và các "bậc thang" nằm ngang. Trên đó có các tiếp điểm (Contacts) và cuộn dây (Coils). Ví dụ:

```
|--| |------( )--|
|  | |           |
|--| |           |
```

3. **Function Block Diagram (FBD)**: Logic bằng block function. Các khối hình chữ nhật với đầu vào bên trái và đầu ra bên phải, được nối với nhau bằng các đường kẻ (dây tín hiệu). Ví dụ:

```
Input1 --| AND |--- Output1
         |_____|
```

4. **Sequential Function Chart (SFC)**: Giống như một lưu đồ (flowchart) gồm các bước (Steps) và các điều kiện chuyển bước (Transitions). Ví dụ:

```
Step1 --[Transition1]--> Step2 --[Transition2]--> Step3
``` 

5. **Instruction List (IL)**: Ngôn ngữ cấp thấp, tương tự như Assembly. Tức gồm một danh sách các lệnh viết tắt theo cột dọc. Ví dụ: 

```
LD Input1 (Load Input 1)
AND Input2 (And với Input 2)
ST Output1 (Store vào Output 1)
```

OpenPLC có 2 phần chính:

- **OpenPLC Runtime**: đây là PLC engine, nó sẽ chạy logic PLC, mở các protocol công nghiệp như: Modbus, DNP3, EtherNet/IP

- **OpenPLC Editor**: Đây là IDE để viết chương trình PLC, dùng để viết code và complie chương trình. Nếu code là  

