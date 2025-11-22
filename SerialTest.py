#use this to probe for a serial input from the arduino

import serial, time

try:
    print("Opening COM6...")
    ser = serial.Serial("COM6", 115200, timeout=1)
    time.sleep(2)
    print("Connected OK!")
    print("Testing read...")
    line = ser.readline()
    print("Read:", line)
except Exception as e:
    print("ERROR:", e)
