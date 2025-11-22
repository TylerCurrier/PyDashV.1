#!/usr/bin/env python3
# PyDashMain V2.1 – FULL VERSION
# Tyler Currier

import time
import pygame
import serial
import can
import math

# ============================================================
#              SELECT INPUT MODE ("REAL" or "FAKE")
# ============================================================

INPUT_MODE = "FAKE"  # <-- CHANGE THIS ONE VARIABLE
# "REAL" = CAN + Arduino
# "FAKE" = Arduino only (fake data)

# ============================================================
#                  USER SETTINGS
# ============================================================

SPLASH_IMAGE = "splash.jpg"
BG_MAIN = "bg_main.jpg"
BG_TRAIL = "bg_trail.jpg"
BG_LEAN = "bg_lean.jpg"
BG_ENGMAG = "bg_engmag.jpg"

SERIAL_PORT = "COM6"  # This will change on Linux
SERIAL_BAUD = 115200

CAN_CHANNEL = "can0"
CAN_BITRATE = 500000
FPS = 30

# CAN IDs
CAN_ID_RPM = 0x100
CAN_ID_SPEED = 0x101
CAN_ID_GEAR = 0x102
CAN_ID_COOLANT = 0x103
CAN_ID_IAT = 0x104
CAN_ID_TPS = 0x105

# ============================================================
#               GLOBAL DATA VARIABLES
# ============================================================

# CAN variables
rpm = 0
speed = 0
gear = 0
coolant = 0
iat = 0
tps = 0

# IMU / Arduino variables
imu_data = {
    "ax": 0, "ay": 0, "az": 0,
    "gx": 0, "gy": 0, "gz": 0,
    "mx": 0, "my": 0, "mz": 0,
    "brake": 0,
    "lean": 0,
    "pitch": 0
}

# Filter globals
lean_filtered = 0
pitch_filtered = 0
prev_time = None

# ============================================================
#               CAN FUNCTIONS
# ============================================================

def init_can():
    if INPUT_MODE == "FAKE":
        print("[CAN] FAKE MODE – CAN Disabled")
        return None
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
#               SERIAL / ARDUINO FUNCTIONS
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
    global rpm, speed, gear, coolant, iat, tps, imu_data
    if not ser:
        return
    line = ser.readline().decode(errors='ignore').strip()
    if not line:
        return
    parts = line.split(",")
    for p in parts:
        if ":" not in p:
            continue
        key, value = p.split(":", 1)
        try:
            if "." in value:
                value = float(value)
            else:
                value = int(value)
        except:
            continue
        if key == "RPM":
            rpm = value
        elif key == "SPD":
            speed = value
        elif key == "GEAR":
            gear = value
        elif key == "THR":
            tps = value
        elif key == "BRK":
            imu_data["brake"] = value
        elif key == "CLT":
            coolant = value
        elif key == "IAT":
            iat = value
        elif key == "LEAN":
            imu_data["lean"] = value
        elif key == "PITCH":
            imu_data["pitch"] = value
        elif key == "AX":
            imu_data["ax"] = value
        elif key == "AY":
            imu_data["ay"] = value
        elif key == "AZ":
            imu_data["az"] = value
        elif key == "GX":
            imu_data["gx"] = value
        elif key == "GY":
            imu_data["gy"] = value
        elif key == "GZ":
            imu_data["gz"] = value
        elif key == "MX":
            imu_data["mx"] = value
        elif key == "MY":
            imu_data["my"] = value
        elif key == "MZ":
            imu_data["mz"] = value

# ============================================================
#               LEAN + PITCH FILTER FUNCTION
# ============================================================

def update_lean_pitch():
    global lean_filtered, pitch_filtered, prev_time
    now = time.time()
    if prev_time is None:
        prev_time = now
    dt = now - prev_time
    prev_time = now

    # Accelerometer tilt
    lean_acc = math.degrees(math.atan2(imu_data["ay"], imu_data["az"]))
    pitch_acc = math.degrees(math.atan2(-imu_data["ax"],
                                        math.sqrt(imu_data["ay"]**2 + imu_data["az"]**2)))

    # Gyro integration
    lean_gyro = lean_filtered + imu_data["gx"] * dt
    pitch_gyro = pitch_filtered + imu_data["gy"] * dt

    # Complementary filter
    alpha = 0.98
    lean_filtered = alpha * lean_gyro + (1 - alpha) * lean_acc
    pitch_filtered = alpha * pitch_gyro + (1 - alpha) * pitch_acc

    # Store filtered values
    imu_data["lean"] = lean_filtered
    imu_data["pitch"] = pitch_filtered

# ============================================================
#               PYGAME INIT
# ============================================================

pygame.init()
screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("PyDash V.2.1  (4 Screens)")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("Arial", 120)
font_small = pygame.font.SysFont("Arial", 60)
font_1 = pygame.font.SysFont("Arial", 60)
font_2 = pygame.font.SysFont("Arial", 80)
font_3 = pygame.font.SysFont("Arial", 90)
font_4 = pygame.font.SysFont("Arial", 100)
font_5 = pygame.font.SysFont("Arial", 120)
font_6 = pygame.font.SysFont("Arial", 130)
font_7 = pygame.font.SysFont("Arial", 140)
font_8 = pygame.font.SysFont("Arial", 150)
font_9 = pygame.font.SysFont("Arial", 160)
font_10 = pygame.font.SysFont("Arial", 170)

# ============================================================
#               BACKGROUND IMAGES
# ============================================================

def load_bg(path):
    try:
        img = pygame.image.load(path).convert()
        return pygame.transform.scale(img, (800, 480))
    except:
        print(f"[WARNING] Missing {path}")
        return None

bg_main = load_bg(BG_MAIN)
bg_trail = load_bg(BG_TRAIL)
bg_lean = load_bg(BG_LEAN)
bg_engmag = load_bg(BG_ENGMAG)

# ============================================================
#               SPLASH
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
#               SCREEN FUNCTIONS
# ============================================================

def screen_1():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    draw_rpm_bar(screen, rpm)

    # Render speed text right-aligned
    speed_text = font_7.render(f"{speed}", True, (0, 0, 0))
    speed_w = speed_text.get_width()
    right_anchor = 460
    speed_x = right_anchor - speed_w
    screen.blit(speed_text, (speed_x, 150))
    screen.blit(font_1.render(" mph", True, (0, 0, 0)), (460, 265))

    # Gear display
    display_gear = "N" if gear == 0 else str(gear)
    gear_color = (0, 255, 0) if display_gear == "N" else (0, 0, 0)
    screen.blit(font_6.render(display_gear, True, gear_color), (50, 170))
    screen.blit(font_small.render(f"{coolant} C", True, (0, 0, 0)), (30, 385))

def screen_2():
    if bg_trail:
        screen.blit(bg_trail, (0, 0))
    else:
        screen.fill((20, 20, 20))
    screen.blit(font_big.render("TRAIL DATA", True, (255, 200, 0)), (250, 40))
    screen.blit(font_small.render(f"Speed: {speed}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"Brake PSI: {imu_data['brake']:.1f}", True, (255, 180, 180)), (50, 260))

def screen_3():
    if bg_lean:
        screen.blit(bg_lean, (0, 0))
    else:
        screen.fill((40, 0, 40))
    screen.blit(font_big.render("LEAN ANGLE", True, (0, 255, 255)), (230, 40))
    screen.blit(font_small.render(f"Lean: {imu_data['lean']:.1f}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"Pitch: {imu_data['pitch']:.1f}", True, (255, 255, 255)), (50, 260))

def screen_4():
    if bg_engmag:
        screen.blit(bg_engmag, (0, 0))
    else:
        screen.fill((0, 30, 60))
    screen.blit(font_big.render("ENGINE MAG", True, (255, 255, 0)), (220, 40))
    screen.blit(font_small.render(f"Mag X: {imu_data['mx']:.2f}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"Mag Y: {imu_data['my']:.2f}", True, (255, 255, 255)), (50, 260))
    screen.blit(font_small.render(f"Mag Z: {imu_data['mz']:.2f}", True, (255, 255, 255)), (50, 320))

# ============================================================
#               RPM BAR FUNCTION
# ============================================================

flash_state = True
last_flash = 0
flash_interval = 0.15

def draw_rpm_bar(surface, rpm, max_rpm=16000):
    global flash_state, last_flash
    x, y, width, height = 20, 0, 760, 100
    pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
    rpm = max(0, min(rpm, max_rpm))
    fill_width = int((rpm / max_rpm) * width)
    pct = rpm / max_rpm
    if pct < 0.7:
        color = (100, 140, 255)
    elif pct < 0.8:
        color = (0, 255, 0)
    else:
        now = time.time()
        if now - last_flash > flash_interval:
            flash_state = not flash_state
            last_flash = now
        color = (255, 0, 0) if flash_state else (120, 0, 0)
    pygame.draw.rect(surface, color, (x, y, fill_width, height))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 4)

# ============================================================
#                       MAIN LOOP
# ============================================================

def main():
    show_splash()
    bus = init_can()
    ser = init_serial()
    current_screen = 1
    running = True

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    current_screen += 1
                    if current_screen > 4:
                        current_screen = 1
                elif event.key == pygame.K_LEFT:
                    current_screen -= 1
                    if current_screen < 1:
                        current_screen = 4

        # Read serial and update lean/pitch filter
        read_serial(ser)
        update_lean_pitch()

        # CAN data in REAL mode
        if INPUT_MODE == "REAL" and bus:
            msg = bus.recv(timeout=0.01)
            if msg:
                process_can_frame(msg)

        # Draw screen
        if current_screen == 1:
            screen_1()
        elif current_screen == 2:
            screen_2()
        elif current_screen == 3:
            screen_3()
        elif current_screen == 4:
            screen_4()

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
