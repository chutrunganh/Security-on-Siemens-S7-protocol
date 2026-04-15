from time import sleep
import snap7

IP_ADDRESS = '172.16.16.131'
TRACK = 0
SLOT = 2

plc = snap7.client.Client()
plc.connect(IP_ADDRESS, TRACK, SLOT)

def write_and_read_db(value_to_write):
    plc.db_write(1, 2, value_to_write.to_bytes(2, byteorder='big'))
    sleep(1)  # Wait for PLC to process the write operation before reading back the values
    iSimSpeed = plc.db_read(1, 0, 2)
    iSetpoint = plc.db_read(1, 2, 2)
    bCentrifugeStatus = plc.db_read(2, 0, 1)

    print(int.from_bytes(iSimSpeed, "big", signed=False), 
        "   |   ",
        int.from_bytes(iSetpoint, "big", signed=False),
         "   |   ",
        int.from_bytes(bCentrifugeStatus, "big", signed=False))

print("Current Speed | Setpoint Speed | Centrifuge Status")
print("--------------------------------------------------")


# Ghi setpoint = 1200 vào DB1.DBW2
write_and_read_db(1200)

sleep(5)

# Ghi setpoint = 2000 vào DB1.DBW2
write_and_read_db(2000)