# S7comm Lab — hai ứng dụng GUI riêng

## 1. Attack Tool (kịch bản tấn công)

```powershell
python -m tools.s7comm_gui.attack_app
```

Hoặc: `tools\run_attack_gui.bat`

- Chạy recon / write / DoS / malformed / Start-Stop qua SSH Attacker (`ubuntu@172.16.16.5`)
- Chỉ log thực thi tấn công — **không** bắt alert Suricata ở đây

## 2. Rules Tool (quản lý luật Suricata)

```powershell
python -m tools.s7comm_gui.rules_app
```

Hoặc: `tools\run_rules_gui.bat`

- Xem/sửa 32 luật trong `detect/rules/`
- Deploy, validate, trạng thái IDS
- **Bắt alert Suricata**, tcpdump mirror (tab Alert Suricata)

## Mở cả hai cùng lúc

## Mở cả hai cùng lúc

Double-click: **`tools\run_s7_gui.bat`** — mở **2 cửa sổ** (Attack + Rules).

Nếu chỉ thấy 1 app: bạn có thể đang chạy `run_attack_gui.bat` (chỉ Attack). Dùng **`run_s7_gui.bat`**.

Lỗi im lẫn (pythonw): xem `tools/s7comm_gui/launch_errors.log`.

## Topology lab (IP cố định)

| Máy | IP |
|-----|-----|
| PLC | 172.16.16.3 |
| Attacker | 172.16.16.5 |
| HMI | 172.16.16.6 |
| IDS | 172.16.16.7 |

## Attack Tool

**SSH → Attacker (172.16.16.5, `ubuntu:ubuntu`)** — chạy script tấn công tới **PLC (172.16.16.3)**.

## Rules Tool — giám sát Suricata

**SSH → IDS (172.16.16.7, `lubuntu:lubuntu`)**:

- **Bắt alert Suricata** — `tail -f fast.log`
- **Dừng alert** — tắt luồng đọc
- **Tcpdump gói :102** — chụp gói mirror Attacker→PLC

```
[Attack Tool] --SSH--> [Attacker .5] --S7/102--> [PLC .3]
                              │
                         mirror SPAN
                              ▼
[Rules Tool]  --SSH--> [IDS .7 Suricata]
```

## Cài đặt

```powershell
pip install paramiko
pythonw -m tools.s7comm_gui.attack_app
pythonw -m tools.s7comm_gui.rules_app
```

**Cảnh báo:** Chỉ dùng trên lab cô lập.
