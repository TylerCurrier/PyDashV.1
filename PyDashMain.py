# PyDashMain V2.1
# Author: Tyler Currier
# Latest Revision 12/8/2025

# Imported libraries
import time
import pygame
import serial
import can
import math
#RTC Libs
#import board
#import busio
#import adafruit_pcf8523
#from datetime import datetime

# ============================================================
#              INPUT MODE ("REAL" or "FAKE")
# ============================================================
#Real input mode is normal operations, fake is for generated data from single arduino for GUI setup
INPUT_MODE = "REAL"  # <-- CHANGE THIS ONE VARIABLE

# ============================================================
#                  USER SETUP
# ============================================================
#Image imports
IMAGE_DIR = "images/"
SPLASH_IMAGE = IMAGE_DIR + "splash.jpg"
BG_IMAGE = IMAGE_DIR + "mainback.jpg"

#Arduino 1
SERIAL_PORT1 = "COM6" #"dev/ttyUSB0"
SERIAL_BAUD1 = 115200

#Arduino BTNs
SERIAL_PORT2 = "COM3" #"dev/ttyUSB1"
SERIAL_BAUD2 = 115200
#CAN Channel
CAN_CHANNEL = "can0"
CAN_BITRATE = 500000
FPS = 30

#CAN IDs
CAN_ID_RPM = 0x100
CAN_ID_SPEED = 0x101
CAN_ID_GEAR = 0x102
CAN_ID_COOLANT = 0x103
CAN_ID_IAT = 0x104
CAN_ID_TPS = 0x105


#i2c = busio.I2C(board.SCL, board.SDA)
#rtc = adafruit_pcf8523.PCF8523(i2c)
# ============================================================
#               RTC SETUP
# ============================================================
""" !!!A lot more code will need to be written for this - but it is of low priority
# Create an I2C connection
i2c = busio.I2C(board.SCL, board.SDA)

# Create the RTC object
rtc = adafruit_pcf8523.PCF8523(i2c)

# Read time from RTC
current_time = rtc.datetime
print("RTC Time:", current_time)

# Example: print in a formatted nice way
print("Formatted:", current_time.tm_year, current_time.tm_mon, current_time.tm_mday,
      current_time.tm_hour, current_time.tm_min, current_time.tm_sec)
"""

# ============================================================
#               GLOBAL DATA VARIABLES AND HANDLING
# ============================================================

#startup var strings
canString = ""
serArdString = ""
serBtnString = ""

#Can vars
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
#y long
#x lat
#z vert
#Remember the orientation -- and remember to correct the lateral values for lean on the arduino



#Max values have to be definied globally to prevent overwriting within functions
maxg = 0 #Max GForces
maxl = 0 #Max left lean
maxr = 0 #max right lean
maxbrake = 0 #Maximum brake pressure

#BTN variables
btn1_state = 1  #Black btn, 0 = pressed, 1 = released
btn2_state = 1  #Red btn
btn1_short_press = False
btn1_long_press = False
btn2_short_press = False
btn2_long_press = False
_btn1_press_start = None
_btn2_press_start = None
btn_serial = None  # Serial 2 object


#saving g history for g_dot usage
g_history = [] #(timestamp, x, y)

#Trail Graph Handling
graph_duration = 20.0 #seconds
lean_history = [] #list of (timestamp, value)
brake_history = []
throttle_history = []


# ============================================================
#               CAN FUNCTIONS
# ============================================================

def init_can():
    global canString
    if INPUT_MODE == "FAKE": #Checks to see if CAN should be enabled or not
        canString = "[CAN] FAKE MODE – CAN Disabled"
        print(canString)
        return None
    try:
        bus = can.interface.Bus(channel=CAN_CHANNEL, bustype='socketcan')
        canString = "[CAN] Connected."
        print(canString)
        return bus
    except Exception as e:
        canString = "[CAN ERROR]"
        print(canString, e)

        return None


def process_can_frame(msg):
    global rpm, speed, gear, coolant, iat, tps #Process can data coming over, this stuff should work if CAN IDs are set correctly
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
    global serArdString
    try:
        ser = serial.Serial(SERIAL_PORT1, SERIAL_BAUD1, timeout=0.1)
        serArdString = "[SERIAL] Connected to Arduino."
        print(serArdString)
        return ser
    except:
        serArdString = "[SERIAL ERROR] Could not connect."
        print(serArdString)
        return None

def init_button_serial():
    global btn_serial, serBtnString
    try:
        btn_serial = serial.Serial(SERIAL_PORT2, SERIAL_BAUD2, timeout=0.1)
        serBtnString = "[SERIAL-BTN] Connected."
        print(serBtnString)
    except serial.SerialException as e:
        serBtnString = "[SERIAL-BTN ERROR] Could not connect: {e}"
        print(serBtnString)
        btn_serial = None


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

def read_buttons():
    """
    Reads button states from Serial 2 and updates globals:
    btn1_state, btn2_state (0/1)
    btn1_short_press, btn1_long_press
    btn2_short_press, btn2_long_press
    """
    global btn1_state, btn2_state
    global btn1_short_press, btn1_long_press, btn2_short_press, btn2_long_press
    global _btn1_press_start, _btn2_press_start

    if btn_serial is None or btn_serial.in_waiting == 0:
        return

    try:
        line = btn_serial.readline().decode('utf-8').strip()
        line = line.replace('(', '').replace(')', '')
        values = line.split(',')
        btn1_new = int(values[0])
        btn2_new = int(values[1])
    except (ValueError, IndexError):
        return

    # --- Button 1 logic --- black btn
    if btn1_new == 0 and btn1_state == 1:  # just pressed
        _btn1_press_start = time.time()
    elif btn1_new == 1 and btn1_state == 0:  # just released
        duration = time.time() - (_btn1_press_start or time.time())
        btn1_short_press = 0.1 <= duration < 3
        btn1_long_press = duration >= 3
        _btn1_press_start = None

    # --- Button 2 logic --- red btn
    if btn2_new == 0 and btn2_state == 1:  # just pressed
        _btn2_press_start = time.time()
    elif btn2_new == 1 and btn2_state == 0:  # just released
        duration = time.time() - (_btn2_press_start or time.time())
        btn2_short_press = 0.1 <= duration < 3
        btn2_long_press = duration >= 3
        _btn2_press_start = None

    # Update states
    btn1_state = btn1_new
    btn2_state = btn2_new

# ============================================================
#               PYGAME INITIALIZATION
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
#               SPLASH SCREEN (for booting)
# ============================================================

def show_splash():
    try:
        img = pygame.image.load(BG_IMAGE)
        img = pygame.transform.scale(img, (800, 480))
        screen.blit(img, (0, 0))
        pygame.display.update()
        splash_animation(screen, char_delay=2)
        time.sleep(2)

    except:
        print("[SPLASH] Missing image.")


import pygame


def splash_animation(screen, char_delay=4, x_offset=10, y_offset=50):
    global canString, serArdString, serBtnString
    """
    Draws an ASCII logo scrolling left-to-right, top-to-bottom with optional offsets.

    :param screen: Pygame screen object
    :param char_delay: Delay in milliseconds between characters
    :param x_offset: Horizontal pixel offset for the logo
    :param y_offset: Vertical pixel offset for the logo
    """
    pygame.font.init()
    font_color = (255, 255, 255)
    font_size =15
    font = pygame.font.SysFont("Consolas", font_size, bold=True)

    # ASCII logo embedded
    ascii_art = [
        "$$$$$$$\\            $$$$$$$\\   $$$$$$\\   $$$$$$\\  $$\\   $$\\       $$\\    $$\\    $$\\",
        "$$  __$$\\           $$  __$$\\ $$  __$$\\ $$  __$$\\ $$ |  $$ |      $$ |   $$ | $$$$ |",
        "$$ |  $$ |$$\\   $$\\ $$ |  $$ |$$ /  $$ |$$ /  \\__|$$ |  $$ |      $$ |   $$ | \\_$$ |",
        "$$$$$$$  |$$ |  $$ |$$ |  $$ |$$$$$$$$ |\\$$$$$$\\  $$$$$$$$ |      \\$$\\  $$  |   $$ |",
        "$$  ____/ $$ |  $$ |$$ |  $$ |$$  __$$ | \\____$$\\ $$  __$$ |       \\$$\\$$  /    $$ |",
        "$$ |      $$ |  $$ |$$ |  $$ |$$ |  $$ |$$\\   $$ |$$ |  $$ |        \\$$$  /     $$ |",
        "$$ |      \\$$$$$$$ |$$$$$$$  |$$ |  $$ |\\$$$$$$  |$$ |  $$ |         \\$  /$$\\ $$$$$$\\",
        "\\__|       \\____$$ |\\_______/ \\__|  \\__| \\______/ \\__|  \\__|          \\_/ \\__|\\______|",
        "          $$\\   $$ |",
        "          \\$$$$$$  |",
        "           \\______/"
    ]

    rows = len(ascii_art)

    # Draw characters left-to-right, top-to-bottom
    for r in range(rows):
        for c in range(len(ascii_art[r])):
            ch = ascii_art[r][c]
            surface = font.render(ch, True, font_color)
            # apply offsets here
            screen.blit(surface, (x_offset + c * font_size * 0.6, y_offset + r * font_size))
            pygame.display.update()
            pygame.time.delay(char_delay)

            # Handle quit events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

    # setup data
    # Can
    screen.blit(font_1_3.render(f"{canString}", True, (255, 255, 255)), (50, 300))
    pygame.display.update()
    pygame.time.delay(300)
    # Serial
    screen.blit(font_1_3.render(f"{serArdString}", True, (255, 255, 255)), (50, 350))
    pygame.display.update()
    pygame.time.delay(300)
    # Serial-BTN
    screen.blit(font_1_3.render(f"{serBtnString}", True, (255, 255, 255)), (50, 400))
    pygame.display.update()
    pygame.time.delay(3000)


# ============================================================
#               SCREEN FUNCTIONS
# ============================================================

#5 Screens in order: Main, laptimer, Lean, GForces, Trail

#Main Screen
def screen_1():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #Load in base layout
    draw_base_layout()

    #Main Title
    pygame.draw.rect(screen, (0,0,0), (710, 126, 90, 50))
    pygame.draw.rect(screen, (255, 255, 255), (710, 126, 90, 50), 2)
    screen.blit(font_1_4.render(f"Main", True, (255, 255, 255)), (719, 128))

    #Speed function
    draw_speed(screen,speed,x_right=530, y=125)

#==============================================================================================================
#Laptimer Screen
def screen_2():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #Load in base layout
    draw_base_layout()

    #Laptimer title
    pygame.draw.rect(screen, (0, 0, 0), (655, 126, 145, 50))
    pygame.draw.rect(screen, (255, 255, 255), (655, 126, 145, 50), 2)
    screen.blit(font_1_4.render(f"Laptimer", True, (255, 255, 255)), (665, 128))

    #Laptimer function
    draw_laptimer()

#==============================================================================================================
#Lean Screen
def screen_3():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #Load in base layout
    draw_base_layout()

    #Lean title
    pygame.draw.rect(screen, (0, 0, 0), (710, 126, 90, 50))
    pygame.draw.rect(screen, (255, 255, 255), (710, 126, 90, 50), 2)
    screen.blit(font_1_4.render(f"Lean", True, (255, 255, 255)), (719, 128))

    #lean function
    draw_lean()

#==============================================================================================================
#GForce Screen
def screen_4():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #Load in base layout
    draw_base_layout()

    #GForce Title
    pygame.draw.rect(screen, (0, 0, 0), (665, 126, 135, 50))
    pygame.draw.rect(screen, (255, 255, 255), (665, 126, 135, 50), 2)
    screen.blit(font_1_4.render(f"G-Force", True, (255, 255, 255)), (673, 128))

    #gforce function
    draw_gforce()

#==============================================================================================================
#Trail Screen
def screen_5():
    if bg_main:
        screen.blit(bg_main, (0, 0))
    else:
        screen.fill((0, 0, 0))

    #Load in base layout
    draw_base_layout()

    #Trail title
    pygame.draw.rect(screen, (0, 0, 0), (723, 126, 77, 50))
    pygame.draw.rect(screen, (255, 255, 255), (723, 126, 77, 50), 2)
    screen.blit(font_1_4.render(f"Trail", True, (255, 255, 255)), (730, 128))

    #trail function
    draw_trail()


# ============================================================
#               RPM BAR FUNCTION
# ============================================================

flash_state = True
last_flash = 0
flash_interval = 0.10


def draw_rpm_bar(surface, rpm, max_rpm=16000):
    global flash_state, last_flash

    #bar parameters
    x, y, width, height = 0, 0, 800, 100
    pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))

    rpm = max(0, min(rpm, max_rpm))
    fill_width = int((rpm / max_rpm) * width)
    pct = rpm / max_rpm

    #percentage logic gate for changing colors and flashing
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

    #bar rendering
    pygame.draw.rect(surface, color, (x, y, fill_width, height))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 4)
    #tick marks on bar
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
    #Color picker for temperature (adjust with more research)
    if coolant < 80:
        color = (100, 180, 255)   # light blue
    elif coolant < 100:
        color = (255, 255, 255)   # white
    else:
        color = (255, 150, 0)     # orange

    #Generate text
    text = font_1_5.render(f"{coolant}", True, color)

    #Right alignment function
    text_x = x_right - text.get_width()

    #Render and raw on screen
    screen.blit(text, (text_x, y))
    screen.blit(font_1_5.render(f" C", True, (255, 255, 255)), (90, 421))


# ============================================================
#               SPEED FUNCTION
# ============================================================

def draw_speed(screen, speed, x_right, y):

    #speed is most likely imported as kph, so may need to switch to mph once i can confirm

    #Draw bounding box
    pygame.draw.rect(screen, (0, 0, 0), (200, 150, 440, 210))
    pygame.draw.rect(screen, (255, 255, 255), (200, 150, 440, 210), 4)

    #Generate text
    text = font_12.render(f"{speed}", True, (255,255,255))

    #Right alignment function
    text_x = x_right - text.get_width()

    #Render draw Speed on screen
    screen.blit(text, (text_x, y))

    #Vertical MPH text #MPH variable may be kph from can so may need to be converted earlier in code
    screen.blit(font_2.render(f" M", True, (255, 255, 255)), (563, 141))
    screen.blit(font_2.render(f" P", True, (255, 255, 255)), (563, 209))
    screen.blit(font_2.render(f" H", True, (255, 255, 255)), (563, 276))


# ============================================================
#               LAPTIMER FUNCTION
# ============================================================

def draw_laptimer():

    #Current Time
    pygame.draw.rect(screen, (0, 0, 0), (160, 135, 460, 100)) #(x,y,w,h)
    pygame.draw.rect(screen, (255, 255, 255), (160, 135, 460, 100), 2)
    screen.blit(font_1_4.render(f"C", True, (255, 255, 255)), (165, 130))
    screen.blit(font_1_4.render(f"U", True, (255, 255, 255)), (165, 161))
    screen.blit(font_1_4.render(f"R", True, (255, 255, 255)), (165, 192))
        #placeholder text -replace with function for time
    screen.blit(font_4.render(f" 00:00.000", True, (255, 255, 255)), (220, 127))

    #last Time
    pygame.draw.rect(screen, (0, 0, 0), (220, 245, 400, 80))  # (x,y,w,h)
    pygame.draw.rect(screen, (255, 255, 255), (220, 245, 400, 80), 2)
    screen.blit(font_1_3.render(f"L", True, (255, 255, 255)), (227, 244))
    screen.blit(font_1_3.render(f"A", True, (255, 255, 255)), (225, 269))
    screen.blit(font_1_3.render(f"S", True, (255, 255, 255)), (225, 294))
        #placeholder text -replace with function for time
    screen.blit(font_2.render(f" 00:00.000", True, (255, 255, 255)), (300, 240))

    #Best Time
    pygame.draw.rect(screen, (0, 0, 0), (220, 335, 400, 80))  # (x,y,w,h)
    pygame.draw.rect(screen, (255, 255, 255), (220, 335, 400, 80), 2)
    screen.blit(font_1_3.render(f"B", True, (255, 255, 255)), (225, 336))
    screen.blit(font_1_3.render(f"E", True, (255, 255, 255)), (225, 361))
    screen.blit(font_1_3.render(f"S", True, (255, 255, 255)), (225, 386))
        #placeholder text -replace with function for time
    screen.blit(font_2.render(f" 00:00.000", True, (255, 255, 255)), (300, 330))


# ============================================================
#               GFORCE FUNCTION
# ============================================================

def draw_gforce():

    #variables
    long = imu_data["ay"] #y axis
    lat = imu_data["ax"] #x axis
    global maxg
    #defining maxg

    #max function
    absoluteg = math.sqrt(long**2 + lat**2)
    if absoluteg > maxg:
        maxg = round(absoluteg,3)


    #center graph
    cx = 375 #center x coord
    cy = 303 #center y coord
    radius = 175 #Full ouside radius
    sradius = 175 / 1.5 #scaled radius for outside being 1.5 G and 175 pixels
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), radius +2, 8)
    pygame.draw.circle(screen, (0, 0, 0), (cx, cy), radius-2)  # filled
    pygame.draw.line(screen, (255,255,255), (cx - radius, cy), (cx + radius, cy), 1) #vert
    pygame.draw.line(screen, (255,255,255), (cx, cy - radius), (cx, cy + radius), 1) #hor
        #1g tick --- outer circle is 1.5, scale accordingly
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), sradius, 1)
        #g dot function
    draw_g_dot()
        #Current Values
    pygame.draw.rect(screen, (0, 0, 0), (2, 300, 180, 90))
    pygame.draw.rect(screen, (255, 255, 255), (2, 300, 180, 90), 2)
    screen.blit(font_1_4.render(f"long={long}", True, (255, 255, 255)), (10, 300))
    screen.blit(font_1_4.render(f"  lat={lat}", True, (255, 255, 255)), (10, 340))
        #max values -- fo rnow just a single max value for total g force, combined lat long
    pygame.draw.rect(screen, (0, 0, 0), (580, 200, 200, 130))
    pygame.draw.rect(screen, (255, 255, 255), (580, 200, 200, 130), 2)
    screen.blit(font_1_4.render(f"MAX - G", True, (255, 255, 255)), (600, 200))
    screen.blit(font_1_4.render(f"{maxg}", True, (255, 255, 255)), (600, 250))


# ============================================================
#               G DOT FUNCTION
# ============================================================

def draw_g_dot():
    #carry over variables -MUST be same as in GFORCE FUNCTION
    cx = 375
    cy = 303
    sradius = 175 / 1.5 #scaled radius, same as sradius from previosu function
    long = imu_data["ay"]  # y axis
    lat = imu_data["ax"]  # x axis
    global g_history #calling global g history variable

    now = time.time()

    # Compute current dot position
    x = cx + sradius * lat
    y = cy + sradius * long

    # Add the dot EVERY FRAME
    g_history.append((now, x, y))

    # Keep only the last 10 seconds
    g_history = [(t, gx, gy) for (t, gx, gy) in g_history if now - t <= 10]

    # Draw the trail
    for (t, gx, gy) in g_history:
        age = now - t  # seconds old
        fade = 1 - (age / 10)  # full fade over 10s (size/opacity)

        #Size fade (12 → 3)
        size = max(3, int(12 * fade))

        #Opacity fade (255 → 40)
        alpha = max(40, int(255 * fade))

        #Faster color fade (3-second color window)
        color_fade = max(0, 1 - (age / 3))  # 1 → 0 in 3 seconds

        #Newest = green (0,255,0)
        #Oldest = red (255,0,0)
        r = int(255 * (1 - color_fade))  # becomes red quick
        g = int(255 * color_fade)  # green disappears fast
        b = 0

        #Draw with alpha on a temporary surface
        dot_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot_surface, (r, g, b, alpha), (size, size), size)
        screen.blit(dot_surface, (gx - size, gy - size))


# ============================================================
#               LEAN FUNCTION
# ============================================================

def draw_lean():

    lean = imu_data["lean"] #grabbing lean variable from IMU arduino
    if lean >= 0:
        lean_side = 0 #=right
    else:
        lean_side = 1 #=left
    lean_corr = round(abs(lean)) #corrected lean abs and round

    global maxl, maxr #globally stored max left and max right

    #maximum reassignment... if lean is greater than current max, make it equal to current max
    if lean > maxr:
        maxr = round(abs(lean))
    if lean < maxl: #whoop
        maxl = round(lean)

    cx = 400 #center x coord
    cy = 285 #center y coord
    radius = 150 #bounding circle radius
        #lean bounding box
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), radius +2, 4)  # outline thickness 4
    pygame.draw.rect(screen, (0, 0, 0), (225, 235, 350, 100))
    pygame.draw.rect(screen, (255, 255, 255), (225, 235, 350, 100), 2)
    pygame.draw.circle(screen, (0, 0, 0), (cx, cy), radius)  # filled

    #outer radius lean ticks
    r_out = 150                  #outer radius for ticks
    r_in = 130                   #inner radius for ticks - defining tick length
    width = 2                    #tick width
    a5d = 50                     #50 degree tick
    phi5d = 90 - a5d             #50 inverted for top down lean
    a5r = math.radians(phi5d)    #50 inv converted to radians
    a4d = 40                     #40 degree tick
    phi4d = 90 - a4d             #40 inverted for top down lean
    a4r = math.radians(phi4d)    #40 inv converted to radians
    a3d = 30                     #30 degree tick
    phi3d = 90 - a3d             #30 inverted for top down lean
    a3r = math.radians(phi3d)    #30 inv converted to radians
    colour = (255,255,255)       #Tick color

    #50 ticks =======
    #Start
    sx5 = r_out*math.cos(a5r)
    sy5 = r_out*math.sin(a5r)
    #End
    ex5 = r_in*math.cos(a5r)
    ey5 = r_in*math.sin(a5r)
    pygame.draw.line(screen, colour, (cx+sx5,cy+sy5), (cx+ex5,cy+ey5), width) #q1 +x +y
    pygame.draw.line(screen, colour, (cx+sx5,cy-sy5), (cx+ex5,cy-ey5), width) #q2 +x -y
    pygame.draw.line(screen, colour, (cx-sx5,cy-sy5), (cx-ex5,cy-ey5), width) #q3 -x -y
    pygame.draw.line(screen, colour, (cx-sx5,cy+sy5), (cx-ex5,cy+ey5), width) #q4 -x +y

    #40 ticks ======
    #Start
    sx4 = r_out * math.cos(a4r)
    sy4 = r_out * math.sin(a4r)
    #End
    ex4 = r_in * math.cos(a4r)
    ey4 = r_in * math.sin(a4r)
    pygame.draw.line(screen, colour, (cx + sx4, cy + sy4), (cx + ex4, cy + ey4), width)  # q1 +x +y
    pygame.draw.line(screen, colour, (cx + sx4, cy - sy4), (cx + ex4, cy - ey4), width)  # q2 +x -y
    pygame.draw.line(screen, colour, (cx - sx4, cy - sy4), (cx - ex4, cy - ey4), width)  # q3 -x -y
    pygame.draw.line(screen, colour, (cx - sx4, cy + sy4), (cx - ex4, cy + ey4), width)  # q4 -x +y
    #30 ticks ======
    #Start
    sx3 = r_out * math.cos(a3r)
    sy3 = r_out * math.sin(a3r)
    #End
    ex3 = r_in * math.cos(a3r)
    ey3 = r_in * math.sin(a3r)
    pygame.draw.line(screen, colour, (cx + sx3, cy + sy3), (cx + ex3, cy + ey3), width)  # q1 +x +y
    pygame.draw.line(screen, colour, (cx + sx3, cy - sy3), (cx + ex3, cy - ey3), width)  # q2 +x -y
    pygame.draw.line(screen, colour, (cx - sx3, cy - sy3), (cx - ex3, cy - ey3), width)  # q3 -x -y
    pygame.draw.line(screen, colour, (cx - sx3, cy + sy3), (cx - ex3, cy + ey3), width)  # q4 -x +y

    #Zeroes
    pygame.draw.line(screen, colour, (cx,cy + radius), (cx,cy -radius), 2) #Vertical Line
    pygame.draw.line(screen, colour, (cx + 175,cy), (cx - 175,cy), 2)      #Horizontal Line

    #Drawing lean pie slices
    ncolor = (100, 255, 100)  # slice color
    steps = 1  # degrees per step

        #top slice
    points = [(cx, cy)]  # center
    # Determine direction: positive = left, negative = right
    if lean >= 0:  # left lean
        start = 0
        end = int(lean)
        step_sign = 1
    else:  # right lean
        start = 0
        end = int(lean)
        step_sign = -1
    # Generate points along the needle path across the circle
    for a in range(start, end + step_sign, step_sign):
        rad = math.radians(90 + a)  # mirror to match needle orientation
        x = cx + radius * math.cos(rad)
        y = cy - radius * math.sin(rad)
        points.append((x, y))
    # Ensure at least 3 points
    if len(points) < 3:
        points.append((cx, cy - radius))
        points.append((cx, cy + radius))

    # Draw top slice
    pygame.draw.polygon(screen, ncolor, points)
        #bottom slice
    points = [(cx, cy)]  # center
    # Determine direction: positive = left, negative = right
    if lean >= 0:  # left lean
        start = 0
        end = int(lean)
        step_sign = 1
    else:  # right lean
        start = 0
        end = int(lean)
        step_sign = -1
    # Generate points along the needle path across the circle
    for a in range(start, end + step_sign, step_sign):
        rad = math.radians(90 + a)  # mirror to match needle orientation
        x = cx - radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        points.append((x, y))
    # Ensure at least 3 points
    if len(points) < 3:
        points.append((cx, cy - radius))
        points.append((cx, cy + radius))
    # Draw bottom slice
    pygame.draw.polygon(screen, ncolor, points)


    #leading lean needle
    #lean = -- this is my variable, there are many like it but this one is mine
    leanphi = 90 - abs(lean)                #lean inverted
    leanphir = math.radians(leanphi)        #lean inv converted to radians
    nwidth = 8                              #needle width
    ncolor = (225,120,120)                  #needle color
    lx = radius*math.cos(leanphir)          #x coord of single quad value
    ly = radius*math.sin(leanphir)          #y coord of single quad value

    #logic check to see which quadrants x and y coords need to be set to
    if lean == 0: #vertical Line
        pygame.draw.line(screen, ncolor, (cx, cy + radius), (cx , cy - radius), nwidth)
    elif lean < 0: # Right Lean Q4, Q2
        pygame.draw.line(screen, ncolor, (cx - lx, cy + ly), (cx + lx, cy - ly), nwidth)
    else: #left lean Q1, Q3
        pygame.draw.line(screen, ncolor, (cx + lx, cy + ly), (cx - lx, cy - ly), nwidth)

    #lean stats
    #Current Lean
    pygame.draw.rect(screen, (0, 0, 0), (575, 235, 100, 100))
    pygame.draw.rect(screen, (255, 255, 255), (575, 235, 100, 100), 2)
    x_right = 667
    text = font_3.render(f"{lean_corr}", True, (255, 255, 255))
    text_x = x_right - text.get_width()
    screen.blit(text, (text_x, 230))

    #Lean Side
    pygame.draw.rect(screen, (0, 0, 0), (150, 235, 75, 100))
    pygame.draw.rect(screen, (255, 255, 255), (150, 235, 75, 100), 2)
    if lean_side == 0: #right
        screen.blit(font_2.render(f"R", True, (150, 150, 255)), (165, 235))
    else: #left
        screen.blit(font_2.render(f"L", True, (150, 150, 255)), (165, 235))

    #Max lean --per side
    pygame.draw.rect(screen, (0, 0, 0), (100, 340, 150, 70))
    pygame.draw.rect(screen, (255, 255, 255), (100, 340, 150, 70), 2)
    screen.blit(font_1_3.render(f"M", True, (150, 150, 255)), (108, 345))
    screen.blit(font_1_3.render(f"L", True, (150, 150, 255)), (108, 375))
    screen.blit(font_2.render(f"{abs(maxl)}", True, (150, 150, 255)), (155, 329))

    pygame.draw.rect(screen, (0, 0, 0), (550, 340, 150, 70))
    pygame.draw.rect(screen, (255, 255, 255), (550, 340, 150, 70), 2)
    screen.blit(font_1_3.render(f"M", True, (150, 150, 255)), (558, 345))
    screen.blit(font_1_3.render(f"R", True, (150, 150, 255)), (558, 375))
    screen.blit(font_2.render(f"{maxr}", True, (150, 150, 255)), (605, 329))


# ============================================================
#               TRAIL FUNCTION
# ============================================================

def draw_trail():

    # Variables
    brake_raw = imu_data["brake"]  # 0–1900 psi
    brakemaxrange = 1000  # max psi to scale to 100%
    throttle = tps  # 0–100 scale
    lean_raw = abs(imu_data["lean"])  # degrees
    leanrange = 50  # 50° = 100%
    global graph_duration
    global maxbrake

    # Convert raw data to percent
    brake = min(100, (brake_raw / brakemaxrange) * 100)
    lean = min(100, (lean_raw / leanrange) * 100)
    throttle = max(0, min(100, throttle))  # ensure 0–100

    #stored maximum brake pressure
    if brake_raw > maxbrake:
        maxbrake = brake_raw

    # Store history for graphing
    add_sample(lean_history, lean)
    add_sample(brake_history, brake)
    add_sample(throttle_history, throttle)

    # Background box
    pygame.draw.rect(screen, (0, 0, 0), (142, 130, 575, 287))
    pygame.draw.rect(screen, (255, 255, 255), (142, 130, 575, 287), 3)

    # Ticks
    pygame.draw.line(screen, (205, 205, 205), (150, 330), (670, 330), 1)
    screen.blit(font_1_2.render("25", True, (255, 255, 255)), (675, 320))
    pygame.draw.line(screen, (205, 205, 205), (150, 270), (670, 270), 1)
    screen.blit(font_1_2.render("50", True, (255, 255, 255)), (675, 260))
    pygame.draw.line(screen, (205, 205, 205), (150, 210), (670, 210), 1)
    screen.blit(font_1_2.render("75", True, (255, 255, 255)), (675, 200))
    pygame.draw.line(screen, (205, 205, 205), (150, 150), (670, 150), 1)
    screen.blit(font_1_2.render("100", True, (255, 255, 255)), (675, 140))

    # Main axes
    pygame.draw.line(screen, (245, 245, 245), (150, 390), (660, 390), 3)
    pygame.draw.line(screen, (245, 245, 245), (660, 150), (660, 390), 3)

    #Time interval
    screen.blit(font_1_2.render(f"{graph_duration} Seconds", True, (255, 255, 255)), (160, 390))

    # Draw graphs
    draw_trailing_graph(screen, lean_history, (0, 100, 255))  # blue
    draw_trailing_graph(screen, brake_history, (200, 0, 0))  # red
    draw_trailing_graph(screen, throttle_history, (0, 200, 0))  # green

    #max brake
    pygame.draw.rect(screen, (0, 0, 0), (160, 420, 300, 59))
    pygame.draw.rect(screen, (255, 255, 255), (160, 420, 300, 59), 3)
    screen.blit(font_1_3.render("Max", True, (255, 255, 255)), (172, 422))
    screen.blit(font_1_3.render("Brake", True, (255, 255, 255)), (168, 446))
    screen.blit(font_1_5.render(f"{maxbrake} psi", True, (200, 0, 0)), (265, 419))

# ============================================================
#               TRAILING GRAPH LINES
# ============================================================

def draw_trailing_graph(screen, history, color):
    now =time.time()

    x_min = 150
    x_max = 660
    width = x_max - x_min

    points = []

    for t, v in history:
        dt = now - t
        x = x_max - (dt / graph_duration) * width
        if x >= x_min:
            points.append((x, percent_to_y(v)))

    # Draw the line
    if len(points) > 1:
        pygame.draw.lines(screen, color, False, points, 4)

    # Draw current value dot (right side)
    if points:
        pygame.draw.circle(screen, color, (int(points[-1][0]), int(points[-1][1])), 5)

# ============================================================
#               TRAIL SAMPLE HELPER
# ============================================================

def add_sample(history, value):
    now = time.time()
    history.append((now, value))

    cutoff = now - graph_duration
    while history and history[0][0] < cutoff:
        history.pop(0)

# ============================================================
#               TRAIL Y MAPPING
# ============================================================

def percent_to_y(p):
    p = max(0, min(100, p))   # clamp 0–100
    # 100% = 150, 0% = 390  (range: 240px)
    return 390 - (p * (240 / 100))

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
    pygame.draw.rect(screen, (0, 0, 0), (670, 420, 130, 60))
    pygame.draw.rect(screen, (255, 255, 255), (670, 420, 130, 60), 3)
        #connections
    pygame.draw.rect(screen, (0, 0, 0), (510, 420, 160, 60))
    pygame.draw.rect(screen, (255, 255, 255), (510, 420, 160, 60), 3)

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

        #Time 24h
    #need to get the can hat to see the rtc and which one it is.
    #standin time
    draw_RTCtime()
    screen.blit(font_1_5.render(f"00:00", True, (255, 255, 255)), (685, 422))
        #Connections
    draw_connections()

# ============================================================
#               CONNECTIONS FUNCTION / And / CLOCK RTC FUNCTION
# ============================================================
def draw_connections():
    screen.blit(font_1_5.render(f"00:00", True, (255, 255, 255)), (685, 422))

def draw_RTCtime():
    screen.blit(font_1_5.render(f"1 , 2 , 3", True, (255, 255, 255)), (685, 422))


# ============================================================
#                       MAIN LOOP
# ============================================================

def main():
    bus = init_can()
    ser_imu = init_serial()
    init_button_serial()  # initialize button serial
    show_splash()
    current_screen = 1
    running = True

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:  # if key pressed
                if event.key == pygame.K_RIGHT:  # right arrow
                    current_screen = 1 if current_screen == 5 else current_screen + 1
                elif event.key == pygame.K_LEFT:  # left arrow
                    current_screen = 5 if current_screen == 1 else current_screen - 1

        # SERIAL ONLY — no filtering applied
        read_serial(ser_imu)

        # --- BUTTON INPUT HANDLING --- black right red left
        read_buttons()  # update global button states
        global btn1_short_press, btn2_short_press  # access globals
        if btn2_short_press:
            current_screen = 5 if current_screen == 1 else current_screen - 1  # left
            btn2_short_press = False  # reset immediately
        if btn1_short_press:
            current_screen = 1 if current_screen == 5 else current_screen + 1  # right
            btn1_short_press = False  # reset immediately

        if INPUT_MODE == "REAL" and bus:
            msg = bus.recv(timeout=0.01)
            if msg:
                process_can_frame(msg)

        if current_screen == 1:  # Main
            screen_1()
        elif current_screen == 2:  # Laptimer
            screen_2()
        elif current_screen == 3:  # Lean
            screen_3()
        elif current_screen == 4:  # Gforce
            screen_4()
        elif current_screen == 5:  # Trail
            screen_5()

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
