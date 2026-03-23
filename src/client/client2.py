from time import sleep
import snap7

IP_ADDRESS = '127.0.0.1'
TRACK = 0
SLOT = 2

plc = snap7.client.Client()
plc.connect(IP_ADDRESS, TRACK, SLOT)

def read_db(plc, db_number, start, size):
    try:
        data = plc.db_read(db_number, start, size)
        return data
    except Exception as e:
        print(f"Error reading DB: {e}")
        return None


def writedb(plc, db_number, start, data):
    try:
        plc.db_write(db_number, start, data)
        return True
    except Exception as e:
        print(f"Error writing DB: {e}")
        return False

while True:
    current_temp_bytes = read_db(plc, 1, 0, 2)
    max_temp_bytes = read_db(plc, 1, 2, 2)
    
    if current_temp_bytes:
        current_temp = int.from_bytes(current_temp_bytes, byteorder='big')
    else:
        current_temp = None
    
    if max_temp_bytes:
        max_temp = int.from_bytes(max_temp_bytes, byteorder='big')
    else:
        max_temp = None
    
    print("Current Temp:", current_temp)
    print("Max Limit Temp:", max_temp)
    sleep(1)



