```
$$$$$$$\            $$$$$$$\   $$$$$$\   $$$$$$\  $$\   $$\       $$\    $$\    $$\
$$  __$$\           $$  __$$\ $$  __$$\ $$  __$$\ $$ |  $$ |      $$ |   $$ | $$$$ |
$$ |  $$ |$$\   $$\ $$ |  $$ |$$ /  $$ |$$ /  \__|$$ |  $$ |      $$ |   $$ | \_$$ |
$$$$$$$  |$$ |  $$ |$$ |  $$ |$$$$$$$$ |\$$$$$$\  $$$$$$$$ |      \$$\  $$  |   $$ |
$$  ____/ $$ |  $$ |$$ |  $$ |$$  __$$ | \____$$\ $$  __$$ |       \$$\$$  /    $$ |
$$ |      $$ |  $$ |$$ |  $$ |$$ |  $$ |$$\   $$ |$$ |  $$ |        \$$$  /     $$ |
$$ |      \$$$$$$$ |$$$$$$$  |$$ |  $$ |\$$$$$$  |$$ |  $$ |         \$  /$$\ $$$$$$\
\__|       \____$$ |\_______/ \__|  \__| \______/ \__|  \__|          \_/ \__|\______|
          $$\   $$ |
          \$$$$$$  |
           \______/
```


``Author: Tyler Currier |||
Latest Revision: November 1st, 2025 |||
All material is intellectual property of authors and organization``

This is the collection of programs to run a dashboard / datalogger on a motorcycle from a Raspberry Pi.
Currently configured to take CAN-BUS data from the CopperHill Pi4B CanHat RTC. It also takes sensor data from an arduino nano with 6-axis IMU and 5V Transducer... As well as GPS data from MIKROE-3922 and active external GNSS antenna.
Screen functions are controllable from an arduino nano with momentary button inputs.
The main program is intended to run on the Raspberry Pi as its only feature, and starts on boot.
Included in the repository is the Main code, sensor input sniffing codes, and all the code to run the external sensors.

