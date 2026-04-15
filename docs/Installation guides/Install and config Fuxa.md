Để đảm bảo tương thích cao nhất, trong dự án này chúng tôi chọn cài bằng Docker:

```bash
docker pull frangoteam/fuxa:snap7
docker run -d -p 1881:1881 frangoteam/fuxa:snap7
```

> [!CAUTION]
> Cần đảm bảo đã expose port `102` của máy ảo chạy OpenPLC runtime nếu chạy qua docker. Sau đó đảm bảo đã start và chườn trình đã được nạp thông qua OpenPLC Editor.

1. Truy cập Fuxa tại: http://localhost:1881

2. Thiết lập kết nối đến PLC runtime: Setting Icon > `Connections` > `+` :

![alt text](image-2.png)

Lựa chọn giao thức `Siemens S7` và nhập thông tin kết nối:

![alt text](image-12.png)

![alt text](image-14.png)

> [!NOTE]
> Nếu gặp lỗi không thể kết nối, kiểm tra lại trạng thái của PLC qua OpenPLC Editor để đảm bảo PLC đang trong trạng thái Running

![alt text](image-13.png)

3. Khai báo các HMI tags. Bấm vào `(-)`:

![alt text](image-15.png)

4. Quay lại Editor và chạy thử HMI:

![alt text](image-16.png)

Sau đó bấm Lauch Icon để chạy HMI:

![alt text](DebugFuxa.gif)

# Refernces

- https://www.youtube.com/watch?v=U5MKKHjQ1sk