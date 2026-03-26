#!/usr/bin/env python3
"""
Siemens S7 Protocol Parser
Convert PCAP file containing S7comm packets and analyze them
"""

import sys
from scapy.all import rdpcap, IP, TCP, Raw


def setup_comm_packet(packet_data, param_offset):
    """Parse Setup configuration packet"""
    print("Function code:\tSetup configuration")
    fields = [
        "Function code", "Reserved", "Max AMQ Caller i", "Max AMQ Caller ii",
        "Max AMQ Callee i", "Max AMQ Callee ii", "PDU Length i", "PDU Length ii"
    ]
    
    for i, field in enumerate(fields):
        if param_offset + i < len(packet_data):
            print(f"{field}:\t0x{packet_data[param_offset + i]:02X}")


def read_var_packet_job(packet_data, param_offset, s7_param_len):
    """Parse Read variable request packet"""
    print("Function code:\tRead variable")
    
    if param_offset >= len(packet_data):
        return
    
    item_count = packet_data[param_offset + 1] if param_offset + 1 < len(packet_data) else 0
    print(f"Item count:\t{item_count}")
    print("-" * 83)
    print(" SpecType  |  Length   | Syntax ID | Var. Type |         Count         |        DB Number      |    Area   |              Address")
    print("-" * 83)
    
    for j in range(s7_param_len):
        if param_offset + 2 + j < len(packet_data):
            if packet_data[param_offset + 2 + j] == 0x12:
                print()
            print(f"   0x{packet_data[param_offset + 2 + j]:02X}    ", end="")
    
    print("\n" + "-" * 83 + "\n")


TRANSPORT_SIZE_MAP = {
    0x03: "BIT",
    0x04: "BYTE/WORD/DWORD",
    0x05: "INT",
    0x06: "DINT",
    0x07: "REAL",
    0x08: "DATE",
    0x09: "OCTET STRING",
}

ERROR_CLASS_MAP = {
    0x00: "No error",
    0x81: "Application relationship error",
    0x82: "Object definition error",
    0x83: "No resources available error",
    0x84: "Error on service processing",
    0x85: "Error on supplies",
    0x87: "Access error",
}


def read_var_packet_ackdata(packet_data, param_offset, data_offset, s7_data_len):
    """Parse Read variable response packet data"""
    func_code = packet_data[param_offset] if param_offset < len(packet_data) else 0x00
    item_count = packet_data[param_offset + 1] if param_offset + 1 < len(packet_data) else 0

    print("  Parameter: (Read Var)")
    print(f"    Function: Read Var (0x{func_code:02x})")
    print(f"    Item count: {item_count}")

    print("  Data")
    current_offset = data_offset
    item_idx = 1

    while current_offset < data_offset + s7_data_len and current_offset < len(packet_data):
        if current_offset + 3 >= len(packet_data):
            break

        return_code = packet_data[current_offset]
        transport_size = packet_data[current_offset + 1]
        length = (packet_data[current_offset + 2] << 8) | packet_data[current_offset + 3]

        # BIT (0x03) and BYTE/WORD/DWORD (0x04) both encode length in BITS.
        # All other transport sizes (REAL, INT, OCTET STRING …) encode length in BYTES.
        if transport_size in (0x03, 0x04):
            byte_length = (length + 7) // 8  # ceil(bits → bytes)
        else:
            byte_length = length

        # S7 data items are padded to even byte boundaries with a 0x00 fill byte.
        has_fill_byte = byte_length % 2 != 0

        header_len = 4
        data_start = current_offset + header_len
        data_end = min(data_start + byte_length, len(packet_data))

        ret_msg = "Success" if return_code == 0xFF else "Error"
        print(f"    Item [{item_idx}]: ({ret_msg})")
        print(f"      Return code: {ret_msg} (0x{return_code:02x})")

        ts_msg = TRANSPORT_SIZE_MAP.get(transport_size, f"Unknown (0x{transport_size:02x})")
        print(f"      Transport size: {ts_msg} (0x{transport_size:02x})")
        print(f"      Length: {byte_length}")  # display as bytes, like Wireshark

        print("      Data: ", end="")
        for i in range(data_start, data_end):
            print(f"{packet_data[i]:02x}", end="")
        print()

        item_idx += 1
        current_offset += header_len + byte_length
        if has_fill_byte and current_offset < data_offset + s7_data_len and current_offset < len(packet_data):
            current_offset += 1


def write_var_packet_job(packet_data, param_offset, data_offset, data_len):
    """Parse Write variable request packet"""
    print("Function code:\tWrite variable")
    
    if param_offset + 1 >= len(packet_data):
        return
    
    item_count = packet_data[param_offset + 1]
    print(f"Item count:\t{item_count}")
    
    fields = [
        "Spec Type:", "Length:", "Syntax ID:", "Variable Type:", "Count:",
        "\t", "DB Number:", "\t", "Area:", "Address:", "\t", "\t"
    ]
    
    for j in range(item_count):
        print(f"\nItem number {j + 1}")
        for k in range(12):
            idx = param_offset + 2 + 12 * j + k
            if idx < len(packet_data):
                print(f"{fields[k]} \t0x{packet_data[idx]:02X}")
    
    print("Data:")
    for j in range(data_len):
        if data_offset + j < len(packet_data):
            print(f"0x{packet_data[data_offset + j]:02X} ", end="")
    print("\n")


def s7_analysis(packet_data, total_headers_size, header):
    """Analyze S7 protocol packet"""
    
    # Check TPKT version
    if total_headers_size >= len(packet_data) or packet_data[total_headers_size] != 3:
        return
    
    # Check COTP length
    if total_headers_size + 4 >= len(packet_data):
        return
    
    cotp_len_byte = packet_data[total_headers_size + 4]
    if cotp_len_byte <= 0:
        return
    
    cotp_len = cotp_len_byte + 1
    s7_offset = total_headers_size + 4 + cotp_len
    
    # Check if we have enough data for S7comm header
    if s7_offset + 10 >= len(packet_data):
        return
    
    cotp_flag = packet_data[s7_offset - 1]
    s7comm_flag = packet_data[s7_offset]
    s7_msg_type = packet_data[s7_offset + 1]
    
    # Extract parameter and data lengths
    if s7_offset + 9 >= len(packet_data):
        return
    
    s7_param_len = (packet_data[s7_offset + 6] << 8) + packet_data[s7_offset + 7]
    s7_data_len = (packet_data[s7_offset + 8] << 8) + packet_data[s7_offset + 9]
    
    # Check for valid S7comm packet
    if s7comm_flag != 0x32 or cotp_flag != 0x80:
        return
    
    print("=" * 80)
    print("S7 Protocol Packet Detected")
    print("=" * 80)

    pdu_ref = (packet_data[s7_offset + 4] << 8) | packet_data[s7_offset + 5]
    reserved = (packet_data[s7_offset + 2] << 8) | packet_data[s7_offset + 3]

    msg_type_name = {1: "Job", 2: "Ack", 3: "Ack_Data"}.get(s7_msg_type, f"Unknown ({s7_msg_type})")

    print(f"\nS7 Communication")
    print(f"  Header: ({msg_type_name})")
    print(f"    Protocol Id: 0x{packet_data[s7_offset]:02x}")
    print(f"    ROSCTR: {msg_type_name} ({s7_msg_type})")
    print(f"    Redundancy Identification (Reserved): 0x{reserved:04x}")
    print(f"    Protocol Data Unit Reference: {pdu_ref}")
    print(f"    Parameter length: {s7_param_len}")
    print(f"    Data length: {s7_data_len}")

    # Ack-Data header has 2 extra bytes (error class + error code) before the parameter section.
    # Job/Ack headers are 10 bytes; Ack-Data headers are 12 bytes.
    if s7_msg_type == 3:
        error_class = packet_data[s7_offset + 10] if s7_offset + 10 < len(packet_data) else 0
        error_code  = packet_data[s7_offset + 11] if s7_offset + 11 < len(packet_data) else 0
        ec_str = ERROR_CLASS_MAP.get(error_class, f"Unknown (0x{error_class:02x})")
        print(f"    Error class: {ec_str} (0x{error_class:02x})")
        print(f"    Error code: 0x{error_code:02x}")
        param_offset = s7_offset + 12
    else:
        param_offset = s7_offset + 10

    data_offset = param_offset + s7_param_len

    # Analyze based on message type
    if s7_msg_type == 1:  # Job Request
        print(f"  [Job Request]")

        if param_offset < len(packet_data):
            func_code = packet_data[param_offset]

            if func_code == 0xF0:  # Setup comm
                setup_comm_packet(packet_data, param_offset)
            elif func_code == 0x04:  # Read var
                read_var_packet_job(packet_data, param_offset, s7_param_len)
            elif func_code == 0x05:  # Write var
                write_var_packet_job(packet_data, param_offset, data_offset, s7_data_len)

    elif s7_msg_type == 2:  # Ack
        print(f"  [Ack]")

    elif s7_msg_type == 3:  # Ack-Data
        if param_offset < len(packet_data):
            func_code = packet_data[param_offset]
            if func_code == 0x04:  # Read var response
                read_var_packet_ackdata(packet_data, param_offset, data_offset, s7_data_len)
            elif func_code == 0x05:  # Write var response
                print(f"  Parameter: (Write Var)")
                print(f"    Function: Write Var (0x{func_code:02x})")
            else:
                print(f"  Parameter: (Function 0x{func_code:02x})")

    print("\n" + "=" * 80 + "\n")


def process_pcap(input_file, packet_index):
    """Process PCAP file and analyze specific S7 packet"""
    
    try:
        packets = rdpcap(input_file)
        s7_packet_count = 0
        
        print(f"Reading PCAP file: {input_file}")
        print(f"Total packets: {len(packets)}\n")
        
        for idx, packet in enumerate(packets):
            # Check if packet has IP and TCP layers
            if IP not in packet or TCP not in packet:
                continue
            
            # Extract payload
            if Raw not in packet:
                continue
            
            payload = packet[Raw].load
            
            # Calculate headers size
            # Ethernet: 14 bytes, IP: 20 bytes (minimum), TCP: 20 bytes (minimum)
            ethernet_header_length = 14
            ip_header_length = (packet[IP].ihl) * 4
            tcp_header_length = (packet[TCP].dataofs) * 4
            total_headers_size = ethernet_header_length + ip_header_length + tcp_header_length
            
            # Create full packet bytes for analysis
            # For scapy packets, we reconstruct the data
            full_packet = bytes(packet)
            
            # Check if this is an S7 packet
            is_s7 = False
            try:
                if total_headers_size < len(full_packet) and full_packet[total_headers_size] == 3:
                    is_s7 = True
            except:
                pass
            
            if is_s7:
                s7_packet_count += 1
                print(f"Found S7 packet #{s7_packet_count} (packet index {idx})")
                
                # If this is the requested packet, analyze it
                if s7_packet_count == packet_index:
                    print(f"\nAnalyzing S7 packet #{packet_index}:\n")
                    s7_analysis(full_packet, total_headers_size, packet)
                    return
        
        if s7_packet_count == 0:
            print("No S7 packets found in PCAP file")
        else:
            print(f"\nTotal S7 packets found: {s7_packet_count}")
            print(f"Error: S7 packet #{packet_index} not found (only {s7_packet_count} S7 packets available)")
    
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing PCAP file: {e}")
        sys.exit(1)


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python s7_parser.py <input_pcap> <packet_number>")
        print("Example: python s7_parser.py capture.pcap 1")
        print("         python s7_parser.py capture.pcap 5")
        sys.exit(1)
    
    input_file = sys.argv[1]
    try:
        packet_index = int(sys.argv[2])
        if packet_index < 1:
            print("Error: packet number must be >= 1")
            sys.exit(1)
    except ValueError:
        print("Error: packet number must be an integer")
        sys.exit(1)
    
    process_pcap(input_file, packet_index)


if __name__ == "__main__":
    main()
