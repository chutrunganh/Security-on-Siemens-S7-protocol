```bash
docker pull frangoteam/fuxa:snap7
docker run -d -p 1881:1881 frangoteam/fuxa:snap7
```


Cần đảm bảo đã expose port 102 của máy ảo chạy OpenPLC runtime nếu chạy qua docker. Su đó đảm bảo đã start và chạy được chuowgn trình để nạp cho PLC tỏng PLC Editor.  


Phần IP thử laoclahost 127.0.0.1 không được, chỉ dùng được IP local 192.168.1.89.



# Refernces

https://www.youtube.com/watch?v=U5MKKHjQ1sk