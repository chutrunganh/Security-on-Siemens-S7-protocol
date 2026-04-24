Theo khái niệm của Siemens thì hơi ngược với IT thông thường:

- **Download** là khi máy master/ client gửi chương trình điều khiển xuống salve là PLC. Đây chính là khi bấm nút nạp code trên Tia Portal

- **Upload** là khi máy master/ client lấy chương trình điều khiển từ PLC về.

Mã nguồn của chương trình điều khiển và hầu như các dữ liệu của chương trình điều khiển được lưu dưới dạng các block. Các loại block trong các thiết bị của Siemens bao gồm:

- **OB** (Organization Block): Đây là block chính để tổ chức chương trình điều khiển. Giống hàm `main () {}` trong C++.

- **(S)DB** ( (System) Data Block): Chứa dữ liệu cần dùng bởi chương trình điều khiển. DB là block dữ liệu do người dùng tạo ra, còn SDB là block dữ liệu hệ thống do Siemens tạo ra.

- **(S)FC** ( (System) Function): Chứa các hàm để có thể tái sử dụng trong chương trình điều khiển. FC là **stateless**, tức nó không lưu trạng thái/không có bộ nhớ riêng

- **(S)FB** ( (System) Function Block): Giống FC nhưng là **stateful**. Thường thì nó hay liên kết với một DB để lưu trạng thái của nó.


## Upload

```mermaid
%%{init: {'sequence': {'messageMargin': 60}} }%%
sequenceDiagram
    participant Workstation
    participant PLC

    Workstation->>PLC: Job - Start Upload: Block Address
    PLC->>Workstation: Ack Data - Start Upload: Block Length

    Workstation-->>PLC: Job - Upload Block
    PLC-->>Workstation: Ack Data - Upload Block: Block Data

    Workstation->>PLC: Job - End Upload
    PLC->>Workstation: Ack Data - End Upload
```

1. **Start Upload**: Máy client gửi lệnh để yêu cầu PLC trả về chương trình điều khiển nó đang chạy (<span style="color: blue;">Job</span > Start Upload) và PLC phản hồi lại yêu cầu đó (<span style="color: green;">ACK</span> Start Upload) . Command này bao gồm các trường theo thứ tự:

    | Trường | <span style="color: blue;">Job</span > Start Upload | <span style="color: green;">ACK</span> Start Upload |
    |--------|----------------------------------|----------------------------------|    
    | `Function Code` (1 byte) | Cố định `0x1d` | Same |
    | `Function Status` (1 byte) | - | - |
    | Không rõ (2 bytes) | `0x0000` | `0x0100`
    | `Session ID` (4 bytes) | - | Định danh cho mỗi phiên upload, được PLC trả về, dùng trong các command sau suốt một phiên Upload |
    | Tên tùy thuộc| `Filename Length` (1 byte) theo sau đó là `Filename` chỉ định tên block cần lấy về |  `Length String Length` (1 byte) theo sau đó là `Length String` là một số decimal cho biết độ dài của block mà PLC sẽ trả về trong phần data của gói tin phản hồi sau đó |

    `Filename` là cách định danh một block như sau:

    ```
    ------------------------------------------------------------------------------------------------------------------
    |  1 char - File identifier  |  2 chars - Block type | 5 chars - Block number | 1 char - Destination file system |
    ------------------------------------------------------------------------------------------------------------------
    ```

    Với:

    - `File identifier` luôn là `_`
    - `Block type` là một trong các loại block đã nêu

        | Hex | Block type |
        |-----|------------|
        | 0x08 | OB |
        | 0x0a | DB |
        | 0x0b | SDB |
        | 0x0c | FC |
        | 0x0d | SFC |
        | 0x0e | FB |
        | 0x0f | SFB |

    - `Block number` là số hiệu của block
    - `Destination file system` bao gồm `A` cho Active file system hoặc `P` cho Passive file system. Block được copy vào active file system sẽ được thực thi ngay khi PLC hoạt động, còn block được copy vào passive file system sẽ cần phải active trước khi được thực thi. 

    Ví dụ `_0800001P` là block OB có số hiệu 1 được copy vào passive file system.

2. **Upload Block**: Sau khi nhận được Start Upload, máy client sẽ gửi lệnh Upload Block để yêu cầu PLC trả về một block dữ liệu của chương trình điều khiển. PLC sẽ trả về block dữ liệu đó trong phần data của gói tin phản hồi. Command này bao gồm các trường theo thứ tự

    | Trường | <span style="color: blue;">Job</span > Upload Block | <span style="color: green;">ACK</span> Upload Block |
    |--------|----------------------------------|----------------------------------|
    | `Function Code` (1 byte) | Cố định `0x1e` | Same |
    | `Function Status` (1 byte) | - | `0x01` nếu còn nhiều block cần upload, `0x00` nếu đã hết block cần upload |
    | Không rõ (2 bytes) | `0x0000` | `0x0000` |
    | `Session ID` (4 bytes) | Dùng sessionID đã có | Same |
    |`Data`| - | Chữa code chương trình điều khiển, bao gồm `Length` (2 bytes) cho biết độ dài của phần data này, cố định `0x00fb`, `Block Data` chứa dữ liệu của block cần upload. Dữ liệu này ở dạng ASCII |

3. **End Upload**: Khi đã nhận đủ dữ liệu theo trường `Length String` của gói tin ACK Start Upload, máy client sẽ gửi lệnh End Upload để kết thúc phiên upload. PLC sẽ phản hồi lại yêu cầu đó để xác nhận đã kết thúc phiên upload thành công. Command này bao gồm các trường theo thứ tự:

    | Trường | <span style="color: blue;">Job</span > End Upload | <span style="color: green;">ACK</span> End Upload |
    |--------|----------------------------------|----------------------------------|
    | `Function Code` (1 byte) | Cố định `0x1f` | Same |

## Download

```mermaid
%%{init: {'sequence': {'messageMargin': 60}} }%%
sequenceDiagram
    participant Workstation
    participant PLC

    Workstation->>PLC: Job - Request Download: Block Address, Length
    PLC->>Workstation: Ack Data - Request Download
    
  
    PLC-->>Workstation: Job - Download Block: Block Address
    Workstation-->>PLC: Ack Data - Download Block: Block Data

    Workstation->>PLC: Job - Download Ended
    PLC->>Workstation: Ack Data - Download Ended
```

1. **Start Download**: Máy client gửi lệnh để yêu cầu PLC chuẩn bị nhận chương trình điều khiển mới (<span style="color: blue;">Job</span > Request Download) và PLC phản hồi lại yêu cầu đó (<span style="color: green;">ACK</span> Request Download) . Gói tin <span style="color: blue;">Job</span > Request Download có 2 trường mới là `Block Length` cho biết độ dài của block dữ liệu mà máy client sẽ gửi, `Payload Length` cũng thể nhưng không tính độ dài của block header


2. **Download Block**: PLC chủ động gửi request để yêu cầu máy client gửi block dữ liệu của chương trình điều khiển mới. Máy client sẽ gửi block dữ liệu đó trong phần data của gói tin phản hồi.

Các trường thông tin còn lại y hệt như trong phần Upload. Chỉ có lưu ý trong quá trình Download, `Session ID` luôn là `0x00000000`, nó không được sử dụng, thay vào đó, trong Download thì sử dụng `Filename` để định danh trong một session Download.