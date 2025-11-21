# PyDashMain V1.0
# Tyler Currier
# November 21, 2025

#Libraries
import time
import pygame
import serial
import can

# ============================================================
#                  USER SETTINGS
# ============================================================

#startup screen
SPLASH_IMAGE = "splash.jpg"

# Backgrounds for each screen
BG_MAIN = "bg_main.jpg"
BG_TRAIL = "bg_trail.jpg"
BG_LEAN = "bg_lean.jpg"
BG_ENGMAG = "bg_engmag.jpg"

#port definition for serial connection to ard nano sensors
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 115200

#channel defenisition car Can Hat input
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
#               GLOBAL DATA
# ============================================================

#variable setup for usable daya
rpm = 0
speed = 0
gear = 0
coolant = 0
iat = 0
tps = 0

imu_data = {"ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0,
            "mx": 0, "my": 0, "mz": 0, "brake": 0}

#!!!!!!!!!!!!!!! Will need to add a fusion algorithm to compute lean angle (likely madgwick filter) on BNO055 IMU 9 axis

# ============================================================
#                    CAN FUNCTIONS
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
#                SERIAL / IMU FUNCTIONS
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
#                    PYGAME INIT
# ============================================================

pygame.init()
screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("PyDash V.2  (4 Screens)")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("Arial", 120)
font_small = pygame.font.SysFont("Arial", 60)
font_1 = pygame.font.SysFont("Arial", 40)
font_2 = pygame.font.SysFont("Arial", 60)
font_3 = pygame.font.SysFont("Arial", 80)
font_4 = pygame.font.SysFont("Arial", 100)
font_5 = pygame.font.SysFont("Arial", 120)

# ============================================================
#                  LOAD BACKGROUND IMAGES
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
#                      SPLASH
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
#                      SCREEN 1: MAIN
# ============================================================

def screen_1():
    if bg_main: screen.blit(bg_main, (0, 0))
    else: screen.fill((0, 0, 0))

    screen.blit(font_4.render(f"RPM: {rpm}", True, (0, 0, 0)), (50, 50))
    screen.blit(font_4.render(f"{speed} ", True, (0, 0, 0)), (300, 180))
    screen.blit(font_4.render(f" mph", True, (0, 0, 0)), (380, 180))
    screen.blit(font_5.render(f"{gear}", True, (0, 0, 0)), (50, 170))
    screen.blit(font_small.render(f"{coolant} C ", True, (0, 0, 0)), (30, 385))

# ============================================================
#                      SCREEN 2: TRAIL
# ============================================================

def screen_2():
    if bg_trail: screen.blit(bg_trail, (0, 0))
    else: screen.fill((20, 20, 20))

    screen.blit(font_big.render("TRAIL DATA", True, (255, 200, 0)), (250, 40))
    screen.blit(font_small.render(f"Speed: {speed}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"Brake PSI: {imu_data['brake']:.1f}", True, (255, 180, 180)), (50, 260))

# ============================================================
#                      SCREEN 3: LEAN
# ============================================================

def screen_3():
    if bg_lean: screen.blit(bg_lean, (0, 0))
    else: screen.fill((40, 0, 40))

    screen.blit(font_big.render("LEAN ANGLE", True, (0, 255, 255)), (250, 40))
    screen.blit(font_small.render(f"AX: {imu_data['ax']:.2f}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"AY: {imu_data['ay']:.2f}", True, (255, 255, 255)), (50, 260))
    screen.blit(font_small.render(f"GY: {imu_data['gy']:.2f}", True, (255, 255, 255)), (50, 320))

# ============================================================
#                      SCREEN 4: ENGINE MAG
# ============================================================

def screen_4():
    if bg_engmag: screen.blit(bg_engmag, (0, 0))
    else: screen.fill((0, 30, 60))

    screen.blit(font_big.render("ENGINE MAG", True, (255, 255, 0)), (240, 40))

    screen.blit(font_small.render(f"Mag X: {imu_data['mx']:.2f}", True, (255, 255, 255)), (50, 200))
    screen.blit(font_small.render(f"Mag Y: {imu_data['my']:.2f}", True, (255, 255, 255)), (50, 260))
    screen.blit(font_small.render(f"Mag Z: {imu_data['mz']:.2f}", True, (255, 255, 255)), (50, 320))

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
        # EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    current_screen += 1
                    if current_screen > 4:
                        current_screen = 1
                if event.key == pygame.K_LEFT:
                    current_screen -= 1
                    if current_screen < 1:
                        current_screen = 4

        # CAN DATA
        if bus:
            msg = bus.recv(timeout=0.01)
            if msg:
                process_can_frame(msg)

        # IMU DATA
        read_serial(ser)

        # DRAW SCREEN
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
