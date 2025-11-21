#!/usr/bin/env python3
"""
Motorcycle Dash Display for Raspberry Pi
GUI + Screen Switching + CAN + Arduino IMU
Background images added for each screen.
"""

import time
import pygame
import serial
import can

# ============================================================
#                  USER SETTINGS (EDIT THESE)
# ============================================================

SPLASH_IMAGE = "splash.jpg"

# Background images for screens:
BG_SCREEN1 = "bg1.jpg"
BG_SCREEN2 = "bg2.jpg"

SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 115200

CAN_CHANNEL = "can0"
CAN_BITRATE = 500000

FPS = 30

# Replace with real CAN IDs from your bike:
CAN_ID_RPM = 0x100
CAN_ID_SPEED = 0x101
CAN_ID_GEAR = 0x102
CAN_ID_COOLANT = 0x103
CAN_ID_IAT = 0x104
CAN_ID_TPS = 0x105

# ============================================================
#               GLOBAL VARIABLES (Display Data)
# ============================================================

rpm = 0
speed = 0
gear = 0
coolant = 0
iat = 0
tps = 0

imu_data = {"ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0,
            "mx": 0, "my": 0, "mz": 0, "brake": 0}

# ============================================================
#                    CAN INITIALIZATION
# ============================================================

def init_can():
    try:
        bus = can.interface.Bus(channel=CAN_CHANNEL, bustype='socketcan')
        print("[CAN] Connected.")
        return bus
    except Exception as e:
        print("[CAN ERROR]", e)
        return None

def process_can_frame(msg):
    global rpm, speed, gear, coolant, iat, tps

    if msg.arbitration_id == CAN_ID_RPM:
        rpm = (msg.data[0] << 8) | msg.data[1]

    elif msg.arbitration_id == CAN_ID_SPEED:
        speed = msg.data[0]

    elif msg.arbitration_id == CAN_ID_GEAR:
        gear = msg.data[0]

    elif msg.arbitration_id == CAN_ID_COOLANT:
        coolant = msg.data[0]

    elif msg.arbitration_id == CAN_ID_IAT:
        iat = msg.data[0]

    elif msg.arbitration_id == CAN_ID_TPS:
        tps = msg.data[0]

# ============================================================
#             ARDUINO IMU + BRAKE PRESSURE READING
# ============================================================

def init_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
        print("[SERIAL] Connected to Arduino.")
        return ser
    except:
        print("[SERIAL ERROR] Could not connect.")
        return None

def read_serial(ser):
    global imu_data
    if not ser:
        return

    line = ser.readline().decode(errors='ignore').strip()
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
#                    PYGAME INITIALIZATION
# ============================================================

pygame.init()
screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("PyDash V.1")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("Arial", 60)
font_small = pygame.font.SysFont("Arial", 40)

# ============================================================
#                   LOAD BACKGROUND IMAGES
# ============================================================

try:
    bg1 = pygame.image.load(BG_SCREEN1).convert()
    bg1 = pygame.transform.scale(bg1, (800, 480))
except:
    print("[WARNING] Missing bg1.jpg")
    bg1 = None

try:
    bg2 = pygame.image.load(BG_SCREEN2).convert()
    bg2 = pygame.transform.scale(bg2, (800, 480))
except:
    print("[WARNING] Missing bg2.jpg")
    bg2 = None

# ============================================================
#                       SPLASH SCREEN
# ============================================================

def show_splash():
    try:
        img = pygame.image.load(SPLASH_IMAGE)
        img = pygame.transform.scale(img, (800, 480))
        screen.blit(img, (0, 0))
        pygame.display.update()
        time.sleep(2)
    except:
        print("[SPLASH] Missing image.")

# ============================================================
#                     SCREEN 1 (Main Dash)
# ============================================================

def screen_1():
    if bg1:
        screen.blit(bg1, (0, 0))
    else:
        screen.fill((0, 0, 0))

    screen.blit(font_big.render(f"RPM: {rpm}", True, (255, 255, 255)), (50, 50))
    screen.blit(font_big.render(f"Speed: {speed}", True, (255, 255, 255)), (50, 150))
    screen.blit(font_big.render(f"Gear: {gear}", True, (255, 255, 255)), (50, 250))

    screen.blit(font_small.render(f"Coolant: {coolant}C", True, (220, 220, 220)), (50, 350))
    screen.blit(font_small.render(f"IAT: {iat}C   TPS: {tps}%", True, (220, 220, 220)), (50, 420))

# ============================================================
#                     SCREEN 2 (IMU Display)
# ============================================================

def screen_2():
    if bg2:
        screen.blit(bg2, (0, 0))
    else:
        screen.fill((30, 30, 30))

    screen.blit(font_big.render("IMU DATA", True, (255, 255, 0)), (300, 50))

    screen.blit(font_small.render(f"AX: {imu_data['ax']:.2f}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"AY: {imu_data['ay']:.2f}", True, (255, 255, 255)), (50, 260))
    screen.blit(font_small.render(f"AZ: {imu_data['az']:.2f}", True, (255, 255, 255)), (50, 320))

    screen.blit(font_small.render(f"Brake: {imu_data['brake']:.1f} PSI", True, (255, 100, 100)), (50, 400))

# ============================================================
#                         MAIN LOOP
# ============================================================

def main():
    show_splash()

    bus = init_can()
    ser = init_serial()

    current_screen = 1
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Keyboard screen switching
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    current_screen = 2
                if event.key == pygame.K_LEFT:
                    current_screen = 1

        # CAN frames
        if bus:
            msg = bus.recv(timeout=0.01)
            if msg:
                process_can_frame(msg)

        # Arduino IMU
        read_serial(ser)

        # Draw current screen
        if current_screen == 1:
            screen_1()
        elif current_screen == 2:
            screen_2()

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
