//PyDashV.1 -- Fake_DASH_input
//Tyler Currier - December 7, 2025


//Destription -----
// This program sends generated data over serial to the Raspberry Pi for GUI and general troubleshooting purposes. Both Ard and CAN signals are generated


// Configurations
unsigned long updateInterval = 50;   // ms between updates (20 Hz output)
float sweepSpeed = 0.02;            // speed of oscillation for most sensors

unsigned long lastUpdate = 0;
float t = 0.0;                      // global time value for oscillation

// Gear cycling variables
int gear = 0;                       // 0 = Neutral
unsigned long lastGearChange = 0;
unsigned long gearInterval = 1500;  // ms between automatic gear changes


void setup() {
  delay(5000);                      // startup delay for your UI system
  Serial.begin(115200);
  Serial.println("Starting fake motorcycle data generator...");
}


void loop() {
  unsigned long now = millis();

  // Update sensor data periodically
  if (now - lastUpdate >= updateInterval) {
    lastUpdate = now;
    t += sweepSpeed;

    // Generate Fake Sensor Data

    // RPM: oscillates between 2000 and 16000
    int rpm = map(sin(t) * 1000, -1000, 1000, 2000, 16000);

    // Speed: 0 → 180 mph
    int speed = map(sin(t * 0.7) * 1000, -1000, 1000, 0, 180);

    // Gear: cycles N → 1 → 6 → back to N
    if (now - lastGearChange > gearInterval) {
      lastGearChange = now;
      gear++;
      if (gear > 6) gear = 0;
    }

    // Throttle: 0–100%
    int throttle = map(sin(t * 2.0) * 1000, -1000, 1000, 0, 100);

    // Brake pressure: 0–150 psi
    int brake = map(abs(sin(t * 3.0)) * 1000, 0, 1000, 0, 150);

    // Coolant & IAT: fluctuate between 200–215°F
    int coolant = 200 + (sin(t * 0.4) * 7.5 + 7.5);
    int iat     = 200 + (cos(t * 0.5) * 7.5 + 7.5);

    // Lean angle: –30° → +30°
    float lean = sin(t * 1.3) * 30.0;

    // Pitch angle: –10° → +10°
    float pitch = sin(t * 0.9) * 10.0;

    // Longitudinal accel: –1g → +1g
    float accelLong = sin(t * 2.5);

    // Lateral accel: –1g → +1g
    float accelLat = cos(t * 2.2);

    // Serial Output

    Serial.print("RPM:");           Serial.print(rpm);
    Serial.print(",SPD:");          Serial.print(speed);
    Serial.print(",GEAR:");         Serial.print(gear);
    Serial.print(",THR:");          Serial.print(throttle);
    Serial.print(",BRK:");          Serial.print(brake);
    Serial.print(",CLT:");          Serial.print(coolant);
    Serial.print(",IAT:");          Serial.print(iat);
    Serial.print(",LEAN:");         Serial.print(lean, 2);
    Serial.print(",PITCH:");        Serial.print(pitch, 2);
    Serial.print(",AX:");           Serial.print(accelLong, 2);
    Serial.print(",AY:");           Serial.print(accelLat, 2);
    Serial.println();
  }
}
