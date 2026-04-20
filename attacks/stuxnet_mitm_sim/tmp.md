## ATT&CK của Stuxnet

![alt text](image.png)

- `Discovery`:
    - `Network sniffing`: MITM để sniff được traffic mạng

    - `Remote System Information Discovery`: Thực hiện các kỹ thuật tấn coogn quét mạng trình bày bên dưới

- `Init Access`: 
    - `Exploit of Remote Services`: Không khai thác các phần mềm, các dịch vụ từ xa -> Bỏ

    - `Remote Services`: Không sử dụng các dịch vụ từ xa -> Bỏ

    - `Replication Through Removable Media`: Không mô phỏng thông qua USB -> Bỏ

- `Execution`:
    - `Modify Controller Tasking`: Thay đổi giá trị trong Datablock của PLC để thay đổi hành vi của hệ thống điều khiển


Viết thành file Python để chạy  ???

Thêm bước check Process để xem có là PLC/HMI không thì chạy ??? Cài trên máy OpenPLC editor -> checklog để tìm địa chỉ IP của PLC.

Khi này sẽ can thiệp gói tin trên máy HMI luôn thay vì cần MITM ?