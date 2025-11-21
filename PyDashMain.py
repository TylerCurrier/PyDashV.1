#start code commit pushf
# !/usr/bin/env python3
"""
Motorcycle Dash Display for Raspberry Pi
----------------------------------------
Features:
- Startup splash screen (JPG)
- Display State 1 (primary dashboard)
- Reads engine data from CAN bus
- Reads IMU + brake pressure from Arduino over serial
- Modular structure to add multiple display states later
"""

import time
import pygame
import serial
import can

# ============================================================
#                  USER SETTINGS (EDIT THESE)
# ============================================================

SPLASH_IMAGE = "splash.jpg"  # <-- Your startup JPG
SERIAL_PORT = "/dev/ttyUSB0"  # <-- Arduino serial port
SERIAL_BAUD = 115200  # <-- Arduino baud rate

# CAN interface (must match can0 config)
CAN_CHANNEL = "can0"
CAN_BITRATE = 500000

FPS = 30  # Screen update rate


# ============================================================
#                  INITIALIZE CAN BUS
# ============================================================

def init_can():
    """Set up the CAN interface on the Pi."""
    try:
        bus = can.interface.Bus(
            channel=CAN_CHANNEL,
            bustype='socketcan'
        )
        print("[CAN] Connected to CAN bus.")
        return bus
    except Exception as e:
        print("[ERROR] Could not connect to CAN bus:", e)
        return None


# ============================================================
#               READ CAN DATA (EDIT CAN IDs HERE)
# ============================================================

# These are example CAN IDs — replace with your bike’s IDs once you sniff them.
CAN_ID_RPM = 0x100
CAN_ID_SPEED = 0x101
CAN_ID_GEAR = 0x102
CAN_ID_COOLANT = 0x103
CAN_ID_IAT = 0x104
CAN_ID_TPS = 0x105

# Variables that the display will use
rpm = 0
speed = 0
gear = 0
coolant = 0
iat = 0
tps = 0


def process_can_frame(msg):
    """Decode CAN messages and update global variables."""
    global rpm, speed, gear, coolant, iat, tps

    if msg.arbitration_id == CAN_ID_RPM:
        # Example: rpm = (byte0<<8 | byte1) / 2
        rpm = (msg.data[0] << 8 | msg.data[1])

    elif msg.arbitration_id == CAN_ID_SPEED:
        speed = msg.data[0]  # 1 byte speed

    elif msg.arbitration_id == CAN_ID_GEAR:
        gear = msg.data[0]

    elif msg.arbitration_id == CAN_ID_COOLANT:
        coolant = msg.data[0]

    elif msg.arbitration_id == CAN_ID_IAT:
        iat = msg.data[0]

    elif msg.arbitration_id == CAN_ID_TPS:
        tps = msg.data[0]


# ============================================================
#          SERIAL (IMU + Brake Pressure from Arduino)
# ============================================================

arduino_imu = None
imu_data = {"ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0, "mx": 0, "my": 0, "mz": 0, "brake": 0}


def init_serial():
    """Open serial port to Arduino."""
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
        print("[SERIAL] Connected to Arduino.")
        return ser
    except:
        print("[ERROR] Could not open serial port.")
        return None


def read_serial():
    """Expect Arduino data in format: ax,ay,az,gx,gy,gz,mx,my,mz,brake"""
    global imu_data

    if not arduino_imu:
        return

    line = arduino_imu.readline().decode(errors='ignore').strip()
    if "," not in line:
        return

    try:
        vals = line.split(",")
        imu_data = {
            "ax": float(vals[0]),
            "ay": float(vals[1]),
            "az": float(vals[2]),
            "gx": float(vals[3]),
            "gy": float(vals[4]),
            "gz": float(vals[5]),
            "mx": float(vals[6]),
            "my": float(vals[7]),
            "mz": float(vals[8]),
            "brake": float(vals[9])
        }
    except:
        pass


# ============================================================
#                   PYGAME DISPLAY SETUP
# ============================================================

pygame.init()
screen = pygame.display.set_mode((800, 480))  # Adjust to Pi screen
pygame.display.set_caption("Motorcycle Dashboard")
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("Arial", 60)
font_small = pygame.font.SysFont("Arial", 40)


# ============================================================
#               DISPLAY: SPLASH SCREEN
# ============================================================

def show_splash():
    """Display splash image on start."""
    try:
        img = pygame.image.load(SPLASH_IMAGE)
        img = pygame.transform.scale(img, (800, 480))
        screen.blit(img, (0, 0))
        pygame.display.update()
        time.sleep(2)  # Show splash for 2 seconds
    except:
        print("[ERROR] Splash image missing.")


# ============================================================
#               DISPLAY: STATE 1 (MAIN DASH)
# ============================================================

def display_state_1():
    """Main dashboard layout."""
    screen.fill((0, 0, 0))

    # RPM
    rpm_txt = font_big.render(f"RPM: {rpm}", True, (255, 255, 255))
    screen.blit(rpm_txt, (50, 50))

    # Speed
    spd_txt = font_big.render(f"Speed: {speed} km/h", True, (255, 255, 255))
    screen.blit(spd_txt, (50, 150))

    # Gear
    gear_txt = font_big.render(f"Gear: {gear}", True, (255, 255, 255))
    screen.blit(gear_txt, (50, 250))

    # Temperatures
    temp_txt = font_small.render(f"Coolant: {coolant}°C   IAT: {iat}°C", True, (200, 200, 200))
    screen.blit(temp_txt, (50, 350))

    # Throttle
    tps_txt = font_small.render(f"TPS: {tps}%", True, (200, 200, 200))
    screen.blit(tps_txt, (50, 420))

    # Brake pressure
    brake_txt = font_small.render(f"Brake: {imu_data['brake']} psi", True, (200, 200, 200))
    screen.blit(brake_txt, (450, 350))

    # IMU example
    imu_txt = font_small.render(f"Lean: {imu_data['ax']:.2f}", True, (200, 200, 200))
    screen.blit(imu_txt, (450, 420))


# ============================================================
#                        MAIN LOOP
# ============================================================

def main():
    global arduino_imu

    show_splash()

    bus = init_can()
    arduino_imu = init_serial()

    running = True
    current_state = 1

    while running:
        # Handle exiting the program
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Read CAN frame if available
        if bus:
            msg = bus.recv(timeout=0.01)
            if msg:
                process_can_frame(msg)

        # Read Arduino IMU data
        read_serial()

        # === DISPLAY STATE HANDLING ===
        if current_state == 1:
            display_state_1()

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
