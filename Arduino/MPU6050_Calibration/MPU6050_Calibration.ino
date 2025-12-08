//this is the program for configuring the IMU

#include <Wire.h>
#include <MPU6050.h>


MPU6050 mpu;


void setup() {
    Serial.begin(115200);
    Wire.begin();


    Serial.println(F("MPU6050 Calibration"));
    Serial.println(F("Place the IMU flat and do NOT touch it..."));
    delay(2000);


    mpu.initialize();
    if (!mpu.testConnection()) {
        Serial.println(F("MPU6050 connection failed"));
        while (1);
    }


    Serial.println(F("Calibrating accelerometer and gyro..."));
    delay(1000);


    // Run calibration (10 cycles is enough)
    mpu.CalibrateAccel(10);
    mpu.CalibrateGyro(10);


    Serial.println(F("Calibration complete!"));
    Serial.println(F("Offsets:"));
    mpu.PrintActiveOffsets();
}


void loop() {
    // Nothing needed here
}
