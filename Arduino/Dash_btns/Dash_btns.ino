//PyDashV.1 -- Dash_btns
//Tyler Currier - December 7, 2025

//Destription -----
//This program takes the input from two momentary buttons mounted to the dash and sends their binary data over
//serial to the main program.

//BTN 1 will function as something
//BTN 2 will functions as something
//I suppose what they do doesent matter here as it is configurable in PyDashMain

// Pin setup
const int BUTTON1_PIN = 2;
const int BUTTON2_PIN = 3;

// State storage
int lastButton1State = HIGH;
int lastButton2State = HIGH;

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON1_PIN, INPUT_PULLUP);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);

  digitalWrite(BUTTON1_PIN, HIGH);
  digitalWrite(BUTTON2_PIN, HIGH);

  // Send initial state at startup
  Serial.print("working");
  Serial.print(!lastButton1State);
  Serial.print(",");
  Serial.println(!lastButton2State);
}

void loop() {
  int b1 = digitalRead(BUTTON1_PIN);
  int b2 = digitalRead(BUTTON2_PIN);

  Serial.print(b1);
  Serial.print(",");
  Serial.println(b2);

  delay(200);
}