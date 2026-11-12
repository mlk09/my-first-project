/*
  JARVIS Part 2 - Voice controlled ESP32 Self-Balancing Robot
  by The IOT Engineer (YouTube)

  Same robot + wiring as SelfBalancingRobot.ino (MPU6050 + TB6612FNG/L298N + 2x TT motors).
  NEW: Bluetooth voice commands. A phone app turns your voice into text and sends it over
  Bluetooth; the robot keeps balancing while it drives, turns, spins or dances.

  Board: classic ESP32 DevKit (BluetoothSerial needs the original ESP32, not S3 / C3).
  Phone: pair with "JARVIS-Robot", then use any "Bluetooth voice control for Arduino" app
         (it sends the spoken text over Bluetooth serial). To test without voice, use the
         app "Serial Bluetooth Terminal" and type the commands.

  Commands (Hinglish or English, words can be anywhere in the sentence):
    "Jarvis, aage chalo"  / forward   -> drive forward 2 s
    "peeche aao"          / back      -> drive back 2 s
    "left mudo" / "baaye" / left      -> turn left
    "right mudo" / "daaye" / right    -> turn right
    "ghoom jao"           / spin      -> 360 spin
    "dance karo" / "naach"/ dance     -> wiggle dance
    "ruk jao"             / stop      -> stop and just balance
  Tuning over the same Bluetooth / USB serial: p30  i0.8  d1.2  t-1.5
*/

#include <Wire.h>
#include "BluetoothSerial.h"

// ------------------------------------------------------------ pins (same as Part 2.1)
const int PWMA = 25, AIN1 = 26, AIN2 = 27;     // left motor
const int PWMB = 13, BIN1 = 33, BIN2 = 32;     // right motor
const int STBY = 4;
const int LED = 2;                             // on-board LED blinks when a command is heard
const int MPU_ADDR = 0x68;

// ------------------------------------------------------------ settings
float Kp = 30.0, Ki = 0.8, Kd = 1.2;
float targetAngle = 0.0;                       // balance point (deg)
const bool INVERT_ANGLE = false;
const bool INVERT_MOTORS = false;
const bool INVERT_TURN = false;                // true if "left" turns right
const int  MOTOR_DEADBAND = 60;
const float FALL_ANGLE = 40.0, START_ANGLE = 5.0, ALPHA = 0.98;
const unsigned long LOOP_US = 5000;            // 200 Hz
const float MOVE_LEAN = 2.5;                   // deg of lean used to drive forward / back
const int TURN_PWM = 70, SPIN_PWM = 130;

// ------------------------------------------------------------ state
BluetoothSerial BT;
float angle = 0, gyroBias = 0, integral = 0;
float moveOffset = 0, moveGoal = 0;            // lean offset (smoothed)
int turn = 0;
bool balancing = false;
unsigned long lastLoop = 0, uprightSince = 0, actionUntil = 0, ledUntil = 0;
enum Action { IDLE, FORWARD, BACK, LEFT, RIGHT, SPIN, DANCE };
Action action = IDLE;
unsigned long actionStart = 0;

// ------------------------------------------------------------ PWM (ESP32 core 2.x and 3.x)
void pwmSetup(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, 20000, 8);
#else
  ledcSetup(ch, 20000, 8);
  ledcAttachPin(pin, ch);
#endif
}
void pwmWrite(int pin, int ch, int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(ch, duty);
#endif
}

// ------------------------------------------------------------ MPU6050
void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}
bool mpuRead(int16_t &ay, int16_t &az, int16_t &gx) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, 14) != 14) return false;
  Wire.read(); Wire.read();                    // ax (not used)
  ay = Wire.read() << 8 | Wire.read();
  az = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read();                    // temperature
  gx = Wire.read() << 8 | Wire.read();
  for (int i = 0; i < 4; i++) Wire.read();     // gy, gz
  return true;
}

// ------------------------------------------------------------ motors
void setMotor(int pwmPin, int ch, int in1, int in2, int speed) {
  if (INVERT_MOTORS) speed = -speed;
  int duty = abs(speed);
  if (duty > 0) duty = map(duty, 1, 255, MOTOR_DEADBAND, 255);
  duty = constrain(duty, 0, 255);
  digitalWrite(in1, speed > 0 ? HIGH : LOW);
  digitalWrite(in2, speed < 0 ? HIGH : LOW);
  pwmWrite(pwmPin, ch, duty);
}
void drive(int left, int right) {
  setMotor(PWMA, 0, AIN1, AIN2, constrain(left, -255, 255));
  setMotor(PWMB, 1, BIN1, BIN2, constrain(right, -255, 255));
}

// ------------------------------------------------------------ replies (shown / spoken by the phone app)
void say(const char *msg) {
  BT.println(msg);
  Serial.println(msg);
  ledUntil = millis() + 400;
}

// ------------------------------------------------------------ commands
bool has(const String &s, const char *word) { return s.indexOf(word) >= 0; }

void startAction(Action a, unsigned long ms, const char *reply) {
  action = a;
  actionStart = millis();
  actionUntil = millis() + ms;
  say(reply);
}

void handleCommand(String s) {
  s.trim();
  s.toLowerCase();
  if (s.length() == 0) return;
  char c = s.charAt(0);                                       // tuning: p30 i0.8 d1.2 t-1.5
  if ((c == 'p' || c == 'i' || c == 'd' || c == 't') && s.length() > 1 && (isDigit(s.charAt(1)) || s.charAt(1) == '-' || s.charAt(1) == '.')) {
    float v = s.substring(1).toFloat();
    if (c == 'p') Kp = v;
    if (c == 'i') { Ki = v; integral = 0; }
    if (c == 'd') Kd = v;
    if (c == 't') targetAngle = v;
    char buf[80];
    snprintf(buf, sizeof(buf), "Kp=%.2f Ki=%.2f Kd=%.2f t=%.2f", Kp, Ki, Kd, targetAngle);
    say(buf);
    return;
  }
  if (!balancing) { say("Boss, pehle mujhe seedha khada karo!"); return; }
  if (has(s, "ruk") || has(s, "stop") || has(s, "ruko")) { action = IDLE; say("Ji Boss! Ruk gaya."); }
  else if (has(s, "ghoom") || has(s, "ghum") || has(s, "spin") || has(s, "round")) startAction(SPIN, 2600, "Ji Boss! Ghoom raha hoon!");
  else if (has(s, "dance") || has(s, "naach") || has(s, "nach")) startAction(DANCE, 4000, "Boss, ye mera best move hai!");
  else if (has(s, "aage") || has(s, "age") || has(s, "forward") || has(s, "front")) startAction(FORWARD, 2000, "Ji Boss! Aage chal raha hoon.");
  else if (has(s, "peeche") || has(s, "piche") || has(s, "pichhe") || has(s, "back")) startAction(BACK, 2000, "Ji Boss! Peeche aa raha hoon.");
  else if (has(s, "left") || has(s, "baaye") || has(s, "baye") || has(s, "bae")) startAction(LEFT, 800, "Ji Boss! Left.");
  else if (has(s, "right") || has(s, "daaye") || has(s, "daye") || has(s, "dae")) startAction(RIGHT, 800, "Ji Boss! Right.");
  else say("Sorry Boss, samajh nahi aaya.");
}

void readCommands() {
  static String usbBuf, btBuf;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { handleCommand(usbBuf); usbBuf = ""; } else usbBuf += ch;
  }
  while (BT.available()) {
    char ch = BT.read();
    if (ch == '\n' || ch == '\r' || ch == '#') { handleCommand(btBuf); btBuf = ""; } else btBuf += ch;
  }
  // some voice apps send text without a newline: treat a short pause as the end of a command
  static unsigned long lastBt = 0;
  static size_t lastLen = 0;
  if (btBuf.length() != lastLen) { lastLen = btBuf.length(); lastBt = millis(); }
  if (btBuf.length() > 0 && millis() - lastBt > 300) { handleCommand(btBuf); btBuf = ""; lastLen = 0; }
}

// what the current action asks for: lean offset (drive) and turn (steer)
void updateAction() {
  unsigned long now = millis();
  if (action != IDLE && now > actionUntil) action = IDLE;
  float t = (now - actionStart) / 1000.0;
  moveGoal = 0;
  turn = 0;
  switch (action) {
    case FORWARD: moveGoal = MOVE_LEAN; break;
    case BACK:    moveGoal = -MOVE_LEAN; break;
    case LEFT:    turn = -TURN_PWM; break;
    case RIGHT:   turn = TURN_PWM; break;
    case SPIN:    turn = SPIN_PWM; break;
    case DANCE:                                               // forward-back wiggle + side twists
      moveGoal = MOVE_LEAN * sin(t * 2 * PI * 1.2);
      turn = (int)(90 * sin(t * 2 * PI * 0.6));
      break;
    default: break;
  }
  if (INVERT_TURN) turn = -turn;
  moveOffset += constrain(moveGoal - moveOffset, -0.05, 0.05);   // smooth lean changes
}

// ------------------------------------------------------------ setup
void setup() {
  Serial.begin(115200);
  BT.begin("JARVIS-Robot");
  pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT); pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT); digitalWrite(STBY, HIGH);
  pinMode(LED, OUTPUT);
  pwmSetup(PWMA, 0);
  pwmSetup(PWMB, 1);
  drive(0, 0);

  Wire.begin(21, 22);
  Wire.setClock(400000);
  mpuWrite(0x6B, 0x00);
  mpuWrite(0x1B, 0x00);
  mpuWrite(0x1C, 0x00);
  mpuWrite(0x1A, 0x03);

  Serial.println("Keep the robot still... calibrating gyro");
  delay(500);
  long sum = 0;
  int n = 0;
  int16_t ay, az, gx;
  for (int k = 0; k < 500; k++) {
    if (mpuRead(ay, az, gx)) { sum += gx; n++; }
    delay(3);
  }
  if (n == 0) {
    Serial.println("MPU6050 not found! Check SDA=21, SCL=22, VCC=3V3, GND.");
    while (true) delay(1000);
  }
  gyroBias = (sum / (float)n) / 131.0;
  mpuRead(ay, az, gx);
  angle = atan2((float)ay, (float)az) * 180.0 / PI;
  if (INVERT_ANGLE) angle = -angle;
  Serial.println("JARVIS ready. Pair Bluetooth 'JARVIS-Robot' and hold the robot upright.");
  lastLoop = micros();
}

// ------------------------------------------------------------ loop
void loop() {
  readCommands();
  digitalWrite(LED, millis() < ledUntil ? HIGH : LOW);
  unsigned long now = micros();
  if (now - lastLoop < LOOP_US) return;
  float dt = (now - lastLoop) / 1e6;
  lastLoop = now;

  int16_t ay, az, gx;
  if (!mpuRead(ay, az, gx)) { drive(0, 0); return; }
  float rate = gx / 131.0 - gyroBias;
  float acc = atan2((float)ay, (float)az) * 180.0 / PI;
  if (INVERT_ANGLE) { rate = -rate; acc = -acc; }
  angle = ALPHA * (angle + rate * dt) + (1 - ALPHA) * acc;

  updateAction();
  float error = angle - (targetAngle + moveOffset);

  if (!balancing) {
    drive(0, 0);
    if (fabs(angle - targetAngle) < START_ANGLE) {
      if (uprightSince == 0) uprightSince = millis();
      if (millis() - uprightSince > 500) {
        balancing = true;
        integral = 0;
        moveOffset = 0;
        action = IDLE;
        say("JARVIS online. Balancing ON!");
      }
    } else {
      uprightSince = 0;
    }
  } else if (fabs(angle - targetAngle) > FALL_ANGLE) {
    balancing = false;
    uprightSince = 0;
    drive(0, 0);
    say("Boss, main gir gaya! Balancing OFF.");
  } else {
    integral = constrain(integral + error * dt, -50.0, 50.0);
    float output = Kp * error + Ki * integral + Kd * rate;
    int base = (int)constrain(output, -255, 255);
    drive(base + turn, base - turn);
  }
}
