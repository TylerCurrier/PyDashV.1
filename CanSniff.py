#CAN Input Sniffing tool for setting up main code

"""f
CAN Sniffer Tool for Raspberry Pi
--------------------------------
Use this to discover:
- CAN IDs
- Raw data bytes
- Message frequency
- Which ID changes with RPM, Speed, etc.
"""

#Make sure bike is running when you run this program to get data

import can
import time

CAN_CHANNEL = "can0"

def main():
    print("Starting CAN sniffer...")
    print("Press CTRL+C to stop.\n")

    try:
        bus = can.interface.Bus(channel=CAN_CHANNEL, interface='socketcan')
    except Exception as e:
        print("ERROR: Could not connect to CAN bus:", e)
        return

    while True:
        try:
            msg = bus.recv(timeout=1)

            if msg is None:
                continue

            # Pretty print message
            data_str = " ".join([f"{b:02X}" for b in msg.data])
            print(f"ID: 0x{msg.arbitration_id:03X}  DLC:{msg.dlc}  Data: {data_str}")

        except KeyboardInterrupt:
            print("\nSniffer stopped by user.")
            break

if __name__ == "__main__":
    main()
