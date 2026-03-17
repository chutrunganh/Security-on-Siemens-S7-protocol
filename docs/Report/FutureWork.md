S7comm-plus: Giao thức Hiện đại cho S7-1200 và S7-1500
Với sự xuất hiện của các lỗ hổng bảo mật nghiêm trọng (như vụ Stuxnet), Siemens đã thay thế S7comm bằng S7comm-plus cho các dòng PLC mới hơn.18 Đây không chỉ là một bản cập nhật mà là một giao thức hoàn toàn mới, tích hợp các cơ chế bảo mật tinh vi để chống lại các cuộc tấn công phát lại (replay attack) và giả mạo lệnh.18
Cơ chế Bảo mật và Xác thực Đa tầng
S7comm-plus giới thiệu một quy trình bắt tay phức tạp để thiết lập một phiên làm việc an toàn, bao gồm việc trao đổi các thách đố (challenges) và tính toán các mã kiểm tra tính toàn vẹn (integrity checks).18
M1 (CreateObject): TIA Portal yêu cầu khởi tạo một phiên làm việc mới (ClassServerSession).21
M2 (Server Challenge): PLC phản hồi bằng một thông điệp chứa phiên bản firmware, model và quan trọng nhất là một mảng ngẫu nhiên 20 byte gọi là ServerSessionChallenge.18
M3 (Authentication): Client sử dụng một thuật toán nội bộ dựa trên mã công khai của Siemens, kết hợp với thách đố từ PLC để tạo ra một phản hồi 180 byte. Quá trình này sử dụng các thuật toán như HMAC-SHA256, AES-CTR và ECC để bảo vệ thông tin.19
M4 (Handshake Confirmation): PLC xác thực phản hồi từ Client. Nếu khớp, phiên làm việc chính thức được thiết lập.21
Mọi gói tin chức năng gửi đi sau đó đều chứa một khối 32 byte gọi là "Integrity Part".18 PLC sẽ từ chối thực thi bất kỳ lệnh nào nếu mã integrity này không khớp với kết quả tính toán dựa trên nội dung gói tin và khóa phiên đã thỏa thuận.18
Cấu trúc Gói tin S7comm-plus
Khác với tiền bối của mình, S7comm-plus bắt đầu bằng byte định danh $0x72$.18

Trường
Byte đầu
Mô tả
Start Byte
$0x72$
Định danh giao thức S7comm-plus.18
PDU Type
2
Xác định loại PDU (Kết nối: $0x01$, Phản hồi: $0x02$, Chức năng: $0x03$).18
Length
3-4
Độ dài dữ liệu (không bao gồm tiêu đề).18
Packet Type
5
Yêu cầu ($0x31$) hoặc Phản hồi ($0x32$).18
Sequence Number
7-8
Chỉ số tuần tự để quản lý gói tin.18

Một đặc điểm quan trọng là S7comm-plus sử dụng các "Attribute Blocks" bắt đầu bằng các byte $0xA3, 0x8X$ để mang dữ liệu mở rộng. Điều này cho phép giao thức rất linh hoạt trong việc truyền tải các cấu trúc dữ liệu phức tạp của TIA Portal.18
Optimized Block Access: Thách thức đối với Truy cập Truyền thống
Trong dòng S7-1200/1500, Siemens giới thiệu cơ chế truy cập khối dữ liệu tối ưu (Optimized Block Access).22 Đối với kỹ sư IT, đây là một thay đổi có tác động trực tiếp đến cách lập trình ứng dụng giao tiếp.22
So sánh Standard Access và Optimized Access

Tiêu chí
Standard Block Access
Optimized Block Access
CPU Hỗ trợ
S7-300/400/1200/1500
Chỉ S7-1200/1500.23
Quản lý dữ liệu
Cấu trúc cố định, có Offset cụ thể.23
Hệ thống tự động sắp xếp để tối ưu hiệu suất.22
Cách truy cập
Địa chỉ tuyệt đối (ví dụ: DB1.DBW10).22
Tên tượng trưng (Symbolic - ví dụ: "Data".Speed).22
Bảo mật
Dễ bị truy cập trái phép qua offset.23
An toàn hơn, hỗ trợ kiểm tra kiểu dữ liệu.23
Hiệu suất
Thấp hơn do dữ liệu bị phân mảnh.23
Cao hơn nhờ truy cập bộ nhớ trực tiếp.23

Các thư viện phổ biến như Snap7 dựa trên địa chỉ tuyệt đối và offset. Do đó, nếu một Data Block được thiết lập là "Optimized", Snap7 sẽ không thể đọc được dữ liệu.22 Để cho phép các ứng dụng IT truy cập theo cách truyền thống, người lập trình PLC phải tắt tùy chọn "Optimized block access" trong thuộc tính của khối dữ liệu và kích hoạt quyền "Permit access with PUT/GET communication from remote partner" trong cấu hình bảo mật của CPU.22
Nếu hệ thống yêu cầu duy trì tính tối ưu, giải pháp thay thế là sử dụng giao thức OPC UA, vốn được thiết kế để truy cập dữ liệu theo tên biến (tag name) thay vì địa chỉ bộ nhớ thô.22
