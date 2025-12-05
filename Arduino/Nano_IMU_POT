//Language = Arduino
//This will be the main code for the ard nano running the IMU and brake transducer


#include <Wire.h>


//Offsets from the calibration program:
int16_t ax_offset = -1628;
int16_t ay_offset = 273;
int16_t az_offset = 3274;
int16_t gx_offset = -197;
int16_t gy_offset = 32;
int16_t gz_offset = 17;


float angle = 0.0;
unsigned long lastTime;


void setup() {
  Serial.begin(115200);
  Wire.begin();


  // Wake up MPU6050
  Wire.beginTransmission(0x68);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);


  lastTime = micros();
}


void loop() {
  int16_t ax, ay, az, gx, gy, gz;


  // --- Read accelerometer ---
  Wire.beginTransmission(0x68);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(0x68, 6, true);
  ax = Wire.read() << 8 | Wire.read();
  ay = Wire.read() << 8 | Wire.read();
  az = Wire.read() << 8 | Wire.read();


  // --- Read gyro ---
  Wire.beginTransmission(0x68);
  Wire.write(0x43);
  Wire.endTransmission(false);
  Wire.requestFrom(0x68, 6, true);
  gx = Wire.read() << 8 | Wire.read();
  gy = Wire.read() << 8 | Wire.read();
  gz = Wire.read() << 8 | Wire.read();


  // --- Apply offsets ---
  ax -= ax_offset;
  ay -= ay_offset;
  az -= az_offset;
  gx -= gx_offset;
  gy -= gy_offset;
  gz -= gz_offset;


  // --- Calculate accelerometer lean angle (in degrees) ---
  float accelAngle = atan2(ay, az) * 57.2958;


  // --- Gyro integration ---
  unsigned long now = micros();
  float dt = (now - lastTime) / 1000000.0;
  lastTime = now;


  float gyroRate = gx / 131.0;   // deg/s for ±250°/s


  // --- Complementary filter ---
  angle = 0.98 * (angle + gyroRate * dt) + 0.02 * accelAngle;


  Serial.println(angle);

  //Make new program at this point, but integrate earlier code. Angle is outputting correctly, but also need to make sure we are also putting out acceleration data.
  //As well as adding in transducer code, set up now as a rotary potentiometer 0-1900 psi
  //man this aint even the code like wtf, update this shit
}


