# Contens

1. Cài đặt và cấu hình OpenPLCv4 runtime, OpenPLC Editor v4 tại [đây](./Install%20and%20config%20OpenPLCv4%20runtime.md)

2. Cài đặt và cấu hình HMI Fuxa tại [đây](./Install%20and%20config%20Fuxa.md)


> [!NOTE]
> Trong trường hợp thay vì dùng OpenPLC runtime để mô phỏng PLC, Fuxa cho HMI/SCADA thì có thể dùng luôn bộ phần mền của Siemens để mô phỏng, với **TIA Portal** để lập trình PLC và WinCC để thiết kế HMI/SCADA, với **PLC Sim Advaced** để mô phỏng chính xác PLC Siemens (*lưu ý với PLC Sim chỉ có thể mô phỏng PLC nội bộ chạy được trong Tia Poral, cần dùng PLC Sim Advance mới có thể chạy được instance PLC có thể truy cập từ các phần mền khác trong cùng mạng LAN*): https://www.youtube.com/watch?v=WhElH-YijIQ. Tuy nhiên các phần mềm này sẽ yêu cầu bản quyển (nhưng dễ crack), chỉ chạy trên Windows và yêu cầu cấu hình đáng kể để chạy.

# Refer

- [What is OpenPLC, how it actually simulates a PLC](./Siemens%20Protocol%20driver%20for%20OpenPLC.pdf)

- [Install OpenPLC, connect to Fuxa, ScadaBR and other SCADA/HMI](./OpenPLC%20Connect%20to%20SCADA.pdf)