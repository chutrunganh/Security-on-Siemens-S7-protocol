# See instruction here: https://github.com/nikteliy/python-s7comm/tree/main
from python_s7comm import Client
from time import sleep

# Connect to PLC
client = Client()
client.connect(address="172.16.16.131", rack=0, slot=2)

def write_and_read_db(value_to_write):
    # I do not actually know why using Different data type rather than BYTE will return garbage or zero values
    client.write_area("DB1.2 BYTE 2", value_to_write.to_bytes(2, "big", signed=True))
    sleep(1) # Wait for PLC to process the write operation before reading back the values
    iSimSpeed = client.read_area("DB1.0 BYTE 2")
    iSetpoint = client.read_area("DB1.2 BYTE 2")
    bCentrifugeStatus = client.read_area("DB2.0 BYTE 1")

    # print(int.from_bytes(iSimSpeed, "big", signed=False), 
    #     "   |   ", 
    #     int.from_bytes(iSetpoint, "big", signed=False),
    #      "   |   ", 
    #     int.from_bytes(bCentrifugeStatus, "big", signed=False))

    print(iSimSpeed, "   |   ", iSetpoint, "   |   ", bCentrifugeStatus)



print("Current Speed | Setpoint Speed | Centrifuge Status")
print("--------------------------------------------------")

# Ghi setpoint = 1200 vào DB1.DBW2
write_and_read_db(1200)

sleep(5) 

# Ghi setpoint = 2000 vào DB1.DBW2
write_and_read_db(2000)

# Disconnect
client.disconnect()