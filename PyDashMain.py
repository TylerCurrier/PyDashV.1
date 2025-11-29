# PyDashMain V2.1
# Tyler Currier

# Imported libraries
import time
import pygame
import serial
import can
import math

# ============================================================
#              SELECT INPUT MODE ("REAL" or "FAKE")
# ============================================================

INPUT_MODE = "FAKE"  # <-- CHANGE THIS ONE VARIABLE

# ============================================================
#                  USER SETTINGS
# ============================================================
IMAGE_DIR = "images/"
SPLASH_IMAGE = IMAGE_DIR + "splash.jpg"
BG_IMAGE = IMAGE_DIR + "mainback.jpg"

SERIAL_PORT = "COM6"
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

rpm = 0
speed = 0
gear = 0
coolant = 0
iat = 0
tps = 0

# IMU / Arduino variables
imu_data = {
    "ax": 0, "ay": 0, "az": 0,
    "brake": 0,
    "lean": 0,
    "pitch": 0
}


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
            value = float(value) if "." in value else int(value)
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
#               PYGAME INIT
# ============================================================

pygame.init()
screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("PyDash V.2.1  (4 Screens)")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("Arial", 120)
font_small = pygame.font.SysFont("Arial", 60)
font_1_1 = pygame.font.SysFont("Arial", 10)
font_1_2 = pygame.font.SysFont("Arial", 22)
font_1_3 = pygame.font.SysFont("Arial", 25)
font_1_4 = pygame.font.SysFont("Arial", 40)
font_1_5 = pygame.font.SysFont("Arial", 50)
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
font_11 = pygame.font.SysFont("Arial", 180)
font_12 = pygame.font.SysFont("Arial", 220)


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


bg_main = load_bg(BG_IMAGE)


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

#Main Screen
def screen_1():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #base in
    draw_base_layout()

    #Main - specific functions
    pygame.draw.rect(screen, (0,0,0), (710, 126, 90, 50))
    pygame.draw.rect(screen, (255, 255, 255), (710, 126, 90, 50), 2)
    screen.blit(font_1_4.render(f"Main", True, (255, 255, 255)), (719, 128))

        # speed
    draw_speed(screen,speed,x_right=530, y=125)

#==============================================================================================================
#Laptimer Screen
def screen_2():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #base in
    draw_base_layout()

    #Laptimer - specific functions
    pygame.draw.rect(screen, (0, 0, 0), (655, 126, 145, 50))
    pygame.draw.rect(screen, (255, 255, 255), (655, 126, 145, 50), 2)
    screen.blit(font_1_4.render(f"Laptimer", True, (255, 255, 255)), (665, 128))

    draw_laptimer()

#==============================================================================================================
#Lean Screen
def screen_3():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #base in
    draw_base_layout()

    #Lean - specific functions
    pygame.draw.rect(screen, (0, 0, 0), (710, 126, 90, 50))
    pygame.draw.rect(screen, (255, 255, 255), (710, 126, 90, 50), 2)
    screen.blit(font_1_4.render(f"Lean", True, (255, 255, 255)), (719, 128))

    draw_lean()

#==============================================================================================================
#GForce Screen
def screen_4():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #base in
    draw_base_layout()

    #GForce - specific functions
    pygame.draw.rect(screen, (0, 0, 0), (665, 126, 135, 50))
    pygame.draw.rect(screen, (255, 255, 255), (665, 126, 135, 50), 2)
    screen.blit(font_1_4.render(f"G-Force", True, (255, 255, 255)), (673, 128))

    draw_gforce()

#==============================================================================================================
#Trail Screen
def screen_5():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #base in
    draw_base_layout()

    #Trail - specific functions
    pygame.draw.rect(screen, (0, 0, 0), (723, 126, 77, 50))
    pygame.draw.rect(screen, (255, 255, 255), (723, 126, 77, 50), 2)
    screen.blit(font_1_4.render(f"Trail", True, (255, 255, 255)), (730, 128))

    draw_trail()


# ============================================================
#               RPM BAR FUNCTION
# ============================================================

flash_state = True
last_flash = 0
flash_interval = 0.10


def draw_rpm_bar(surface, rpm, max_rpm=16000):
    global flash_state, last_flash

    x, y, width, height = 0, 0, 800, 100
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
    #tick marks major
    pygame.draw.line(screen, (255,255,255), (50,107), (50,80), 2)
    pygame.draw.line(screen, (255,255,255), (100,107), (100,80), 2)
    pygame.draw.line(screen, (255,255,255), (150,107), (150,80), 2)
    pygame.draw.line(screen, (255,255,255), (200,107), (200,80), 2)
    pygame.draw.line(screen, (255, 255, 255), (250,98), (250,60), 2)
    pygame.draw.line(screen, (255,255,255), (300,107), (300,80), 2)
    pygame.draw.line(screen, (255,255,255), (350, 107), (350, 80), 2)
    pygame.draw.line(screen, (255,255,255), (400, 107), (400, 80), 2)
    pygame.draw.line(screen, (255,255,255), (450, 107), (450, 80), 2)
    pygame.draw.line(screen, (255, 255, 255), (500, 98), (500, 60), 2)
    pygame.draw.line(screen, (255,255,255), (550, 107), (550, 80), 2)
    pygame.draw.line(screen, (255,255,255), (600, 107), (600, 80), 2)
    pygame.draw.line(screen, (255,255,255), (650, 107), (650, 80), 2)
    pygame.draw.line(screen, (255,255, 255), (700, 107), (700, 80), 2)
    pygame.draw.line(screen, (255, 255, 255), (750, 98), (750, 60), 2)
    pygame.draw.line(screen, (255,255,255), (800, 107), (800, 80), 2)


# ============================================================
#               COOLANT TEMP FUNCTION
# ============================================================

def draw_coolant_temp(screen, coolant, x_right, y):
    # --- Pick color based on temperature ---
    if coolant < 80:
        color = (100, 180, 255)   # light blue
    elif coolant < 100:
        color = (255, 255, 255)   # white
    else:
        color = (255, 150, 0)     # orange

    # --- Render text ---
    text = font_1_5.render(f"{coolant}", True, color)

    # --- Right alignment: shift left by text width ---
    text_x = x_right - text.get_width()

    # --- Draw on screen ---
    screen.blit(text, (text_x, y))

    screen.blit(font_1_5.render(f" C", True, (255, 255, 255)), (90, 421))


# ============================================================
#               SPEED FUNCTION
# ============================================================

def draw_speed(screen, speed, x_right, y):

    #Draw bounding box
    pygame.draw.rect(screen, (0, 0, 0), (200, 150, 440, 210))
    pygame.draw.rect(screen, (255, 255, 255), (200, 150, 440, 210), 4)

    #Render text
    text = font_12.render(f"{speed}", True, (255,255,255))

    #Right alignment: shift left by text width
    text_x = x_right - text.get_width()

    # Draw Speed on screen
    screen.blit(text, (text_x, y))

    #Vertical MPH text #MPH variable may be kph from can so may need to be converted earlier in code
    screen.blit(font_2.render(f" M", True, (255, 255, 255)), (563, 141))
    screen.blit(font_2.render(f" P", True, (255, 255, 255)), (563, 209))
    screen.blit(font_2.render(f" H", True, (255, 255, 255)), (563, 276))


# ============================================================
#               LAPTIMER FUNCTION
# ============================================================

def draw_laptimer():

# ============================================================
#               GFORCE FUNCTION
# ============================================================

def draw_gforce():


# ============================================================
#               LEAN FUNCTION
# ============================================================

def draw_lean():

# ============================================================
#               TRAIL FUNCTION
# ============================================================

def draw_trail():


# ============================================================
#               BASE LAYOUT FUNCTION
# ============================================================

def draw_base_layout():
#Base layout rectangles
        #rpm bar and values
    pygame.draw.rect(screen, (0, 0, 0), (0, 0, 800, 128))  # filled black box
    pygame.draw.rect(screen, (255, 255, 255), (0, 0, 800, 128), 2)  # white outline (3px thick)
        #Gear
    pygame.draw.rect(screen, (0, 0, 0), (0, 120, 140, 160))
    pygame.draw.rect(screen, (255, 255, 255), (0, 120, 140, 160), 3)
        #temps
    pygame.draw.rect(screen, (0, 0, 0), (0, 420, 140, 60))
    pygame.draw.rect(screen, (255, 255, 255), (0, 420, 140, 60), 3)
        #time
    pygame.draw.rect(screen, (0, 0, 0), (640, 420, 160, 60))
    pygame.draw.rect(screen, (255, 255, 255), (640, 420, 160, 60), 3)
        #connections
    pygame.draw.rect(screen, (0, 0, 0), (480, 420, 160, 60))
    pygame.draw.rect(screen, (255, 255, 255), (480, 420, 160, 60), 3)

    #Base Layout data
        #Gear
    display_gear = "N" if gear == 0 else str(gear)
    gear_color = (0, 255, 0) if display_gear == "N" else (255, 255, 255)
    screen.blit(font_10.render(display_gear, True, gear_color), (25, 100))
        #RPM
    draw_rpm_bar(screen, rpm)
        #RPM values
    screen.blit(font_1_2.render(f"5", True, (255, 255, 255)), (245, 100))
    screen.blit(font_1_2.render(f"10", True, (255, 255, 255)), (492, 100))
    screen.blit(font_1_2.render(f"15", True, (255, 255, 255)), (742, 100))

        #Coolant Temp
    draw_coolant_temp(screen, coolant, x_right=90, y=421)

        #Time
    #need to get the can hat to see the rtc and which one it is.
        #Connections




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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    current_screen = 1 if current_screen == 5 else current_screen + 1
                elif event.key == pygame.K_LEFT:
                    current_screen = 5 if current_screen == 1 else current_screen - 1

        # SERIAL ONLY — no filtering applied
        read_serial(ser)

        if INPUT_MODE == "REAL" and bus:
            msg = bus.recv(timeout=0.01)
            if msg:
                process_can_frame(msg)

        if current_screen == 1: #Main
            screen_1()
        elif current_screen == 2: #Laptimer
            screen_2()
        elif current_screen == 3: #Lean
            screen_3()
        elif current_screen == 4: #Gforce
            screen_4()
        elif current_screen == 5: #Trail
            screen_5()

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
