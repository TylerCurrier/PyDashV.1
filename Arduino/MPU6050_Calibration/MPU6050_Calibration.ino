//PyDashV.1 -- MPU6050_Calibration
//Tyler Currier - December 7, 2025


//Destription -----
//This program collections configuration constants for use on the MOU6050, the IMU used for PyDash V.1\
//This program is run once the device is mounted and the bike is perfectly level. The constants can then be carried over to IMU_TRA.INO

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
    
}
