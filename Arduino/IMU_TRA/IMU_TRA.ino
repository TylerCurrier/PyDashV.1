#include <Wire.h>

// Offsets (replace these with new calibration) (last calib 12/10/25 - off bike)
// offsets deal with acceleration and gyrometric forces from earch rotation and orbit. 
int16_t ax_offset = 2040;
int16_t ay_offset = 371;
int16_t az_offset = 1462;
int16_t gx_offset = -111;
int16_t gy_offset = 56;
int16_t gz_offset = -59;

float angle = 0.0;
float corrAngle = 0.0;
unsigned long lastTime;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Wake IMU
  Wire.beginTransmission(0x68);
  Wire.write(0x6B);
  Wire.write(0x00);
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

  // Apply offsets
  ax -= ax_offset;
  ay -= ay_offset;
  az -= az_offset;
  gx -= gx_offset;
  gy -= gy_offset;
  gz -= gz_offset;

  // --- Correct axis for motorcycle roll ---
  float accelAngle = atan2(ax, az) * 57.2958;

  // --- Gyro integration ---
  unsigned long now = micros();
  float dt = (now - lastTime) * 1e-6;
  lastTime = now;

  float gyroRate = gx / 131.0;

  // --- Complementary filter (improved weighting) ---
  angle = 0.95 * (angle + gyroRate * dt) + 0.05 * accelAngle;

  // --- Your offset (apply LAST) ---
  corrAngle = angle + 7.75;
  //Serial.println("lean:" + corrAngle + "," + "AX:" + ax + "AY:" + ay);
  //Serial.println(corrAngle);
  Serial.print("LEAN:"); 
  Serial.print(corrAngle);
  Serial.print(",AX");
  Serial.print(ax);
  Serial.print(",AY");
  Serial.print(ay);
  Serial.print(",BRK");
  Serial.println("0 "); //change off ln for future use

  //we do have a drift right now (very drunk while doing this) - at around 20 to 25 degrees, 5 degrees of drift is introducded...
  //not sure why, maybe toy with sensor mounting or offsets, shipping it for now
  //AND dont forget to add ax, ay, and brake press code
}
