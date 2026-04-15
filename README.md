# Contents

- [Lý thuyết](./docs/Report/Theory.md)
    - [ICS/OT là gì?](./docs/Report/Theory.md#otics-là-gì)
    - [Mô hình mạng PRUDE](./docs/Report/Theory.md#2-mô-hình-purdue-purdue-enterprise-reference-architecture---pera)
    - [PLC](./docs/Report/Theory.md#1-plc)
    - [Cấu trúc S7 Comm](./docs/Report/Theory.md#3-siemen-s7)

- [Cài đặt và cấu hình môi trường mô phỏng](./docs/Installation%20guides/README.md)

- Tấn công mô phỏng
    - [Stuxnet Man in the Middle Attack Simulation](./attacks/stuxnet_mitm_sim/README.md)

# Pending

6 Vụ tấn công vào ICS: https://icsec.pl/en/5-cyber-atakow-na-sieci-ics/, https://hackers-arise.com/scada-hacking-the-most-important-scada-ics-attacks-in-history/


Tác động của 3 loại tấn công vào ICS: https://www.sciencedirect.com/science/article/pii/S2405896324002660?ref=pdf_download&fr=RR-2&rr=9e9e152e18231fc7


Plan a a aass  as asss
 dd ddd dd
ICS Kill

# Attack Simulation

## Password Brute Force

S7-300 thì mật khẩu chì dành cho việc bảo vệ
- upload/download program
- modify block structure

> S7 Block Privacy With the S7 Block Privacy, only FBs and FCs can be protecte


# Pending

The common security challenges addressed in this project include:

Unauthorized command injection — attackers may send control commands that alter process behavior
Lack of authentication/authorization — devices may accept requests without verifying the legitimacy of the sender
Confidentiality exposure — unencrypted communication can be observed and analyzed by adversaries
Integrity and replay risk — captured traffic may be modified or replayed to trigger unintended actions
Denial-of-service (DoS) — excessive or malformed traffic can degrade availability and disrupt operations

    
The Core Problem: Industrial Protocols Were Not Designed for Security
PROFINET and S7 were engineered for reliability and determinism — not authentication or confidentiality. Two weaknesses sit at the heart of this project:

S7 PUT/GET has no source authentication.
Any device on the network that knows the PLC's IP address, rack, slot, and data block number can read from or write to PLC memory with no credentials required. There are no passwords, tokens, or certificates in the default S7 communication model.

PROFINET DCP is completely unauthenticated at Layer 2.
PROFINET uses the Discovery and Configuration Protocol (DCP) over EtherType 0x8892 to assign and manage device station names. A PLC will refuse to communicate with a field device if its name does not match the configured value — and any device on the same broadcast domain can change that name with a single Ethernet frame. One unauthenticated Layer-2 packet can drop an entire field IO channel. Conventional IP-based firewalls and IDS tools cannot see this traffic because it never reaches the IP layer.

Incidents such as Stuxnet, the Ukrainian power grid attacks, and the Triton malware have demonstrated that cyber attacks on industrial infrastructure can cause physical damage, disrupt critical services, and endanger human lives. Despite this, many OT environments continue to operate with minimal security monitoring, relying on network isolation as a primary defence.

Proposed Solution
To address the identified security gaps, this project proposes a passive, network-based intrusion detection architecture tailored for industrial environments:

Deployment of a Suricata-based IDS connected via switch port mirroring
Custom signature rules targeting S7 protocol function codes and memory manipulation
Stateful Lua-based behavioural detection for rapid parameter changes
Layer-2 inspection of PROFINET DCP traffic through EtherType-based filtering
Signature-based detection rules for Modbus TCP targeting unauthorized write operations and abnormal request rates
The IDS operates in passive mode, ensuring no traffic injection, no impact on PLC real-time performance, and full visibility of all mirrored network traffic. This architecture aims to detect process manipulation, command replay, flooding attempts, and device reconfiguration attacks — while maintaining industrial determinism.