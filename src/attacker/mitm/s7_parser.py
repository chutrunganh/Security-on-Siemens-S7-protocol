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


def read_var_packet_ackdata(packet_data, param_offset, s7_data_len):
    """Parse Read variable response packet"""
    print("Function code:\tRead variable")
    
    if param_offset + 1 >= len(packet_data):
        return
    
    item_count = packet_data[param_offset + 1]
    print(f"Item count:\t{item_count}")
    print("-" * 93)
    print(" Error Code |  Var Type |          Count        |                  Data")
    print("-" * 93)
    
    for j in range(s7_data_len):
        if param_offset + 2 + j < len(packet_data):
            if packet_data[param_offset + 2 + j] == 0xFF:
                print()
            print(f"   0x{packet_data[param_offset + 2 + j]:02X}    ", end="")
    
    print("\n" + "-" * 93 + "\n")


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
    
    # Debug output
    debug = False
    if debug:
        print("\nTPKT:")
        for j in range(4):
            if total_headers_size + j < len(packet_data):
                print(f"0x{packet_data[total_headers_size + j]:02X} ", end="")
        
        print("\nCOTP:")
        for j in range(cotp_len):
            if total_headers_size + 4 + j < len(packet_data):
                print(f"0x{packet_data[total_headers_size + 4 + j]:02X} ", end="")
    
    print(f"\nMessage Type: {s7_msg_type}")
    
    param_offset = s7_offset + 10
    data_offset = param_offset + s7_param_len
    
    # Analyze based on message type
    if s7_msg_type == 1:  # Job Request
        print("Type:\t\tJob Request\n")
        
        if param_offset < len(packet_data):
            func_code = packet_data[param_offset]
            
            if func_code == 0xF0:  # Setup comm
                setup_comm_packet(packet_data, param_offset)
            elif func_code == 0x04:  # Read var
                read_var_packet_job(packet_data, param_offset, s7_param_len)
            elif func_code == 0x05:  # Write var
                write_var_packet_job(packet_data, param_offset, data_offset, s7_data_len)
    
    elif s7_msg_type == 2:  # Ack
        print("Type:\t\tAck\n")
    
    elif s7_msg_type == 3:  # Ack-Data
        print("Type:\t\tAck-Data\n")
        
        if param_offset < len(packet_data):
            func_code = packet_data[param_offset]
            
            if func_code == 0x04:  # Read var response
                read_var_packet_ackdata(packet_data, param_offset, s7_data_len)
    
    elif s7_msg_type == 7:  # Userdata
        print("Type:\t\tUserdata\n")
    
    print(f"Param length:\t{s7_param_len}")
    print("Parameters:\t", end="")
    for j in range(param_offset, min(data_offset, len(packet_data))):
        print(f"0x{packet_data[j]:02X} ", end="")
    
    print(f"\nData length:\t{s7_data_len}")
    print("Data:\t\t", end="")
    for j in range(data_offset, min(data_offset + s7_data_len, len(packet_data))):
        print(f"0x{packet_data[j]:02X} ", end="")
    
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
