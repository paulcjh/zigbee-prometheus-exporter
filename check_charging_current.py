import serial
import time
ser = serial.Serial('/dev/ttyUSB1', 115200, timeout=1)

while True:
    time.sleep(0.5)
    ser.writelines([b"getSolarCurrent"])
    time.sleep(0.1)
    print(ser.readline())
    
