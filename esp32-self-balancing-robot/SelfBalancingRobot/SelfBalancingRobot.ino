/*
  ESP32 Self-Balancing Robot  -  MPU6050 + PID + 2x TT gear motors
  by The IOT Engineer (YouTube)

  Hardware
    - ESP32 DevKit (30/38 pin)
    - MPU6050 (GY-521)             SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND
    - Motor driver TB6612FNG  (or L298N, same pins: PWM = ENA/ENB, IN1..IN4)
        Left  motor : PWMA -> GPIO25, AIN1 -> GPIO26, AIN2 -> GPIO27
        Right motor : PWMB -> GPIO13, BIN1 -> GPIO33, BIN2 -> GPIO32
        STBY (TB6612 only) -> GPIO4   (L298N: leave unconnected)
    - 2x TT yellow gear motors + wheels, 4x AA (6 V) or 2S Li-ion (7.4 V) for the motors
    - Common GND between ESP32, driver and battery!

  How it works
    1. On power-up keep the robot still for 2 s -> gyro calibration.
    2. Hold the robot upright. When it is within +-5 deg for 0.5 s  -> "Entering Balancing Mode".
    3. If it falls past +-40 deg the motors stop ("Balancing: OFF") until you stand it up again.

  Live PID tuning over Serial Monitor (115200 baud, "Newline"):
    p30     -> Kp = 30
    i0.8    -> Ki = 0.8
    d1.2    -> Kd = 1.2
    t-1.5   -> target angle offset = -1.5 deg (fix forward/backward drift)
    s       -> print current values
  Tuning order (Part 2.1): Ki = 0, Kd = 0 -> raise Kp until it oscillates, then add Kd until the
  shaking stops, then a little Ki so it stops drifting. Adjust t if it keeps running one way.
*/

#include <Wire.h>

// ------------------------------------------------------------ pins
const int PWMA = 25, AIN1 = 26, AIN2 = 27;     // left motor
const int PWMB = 13, BIN1 = 33, BIN2 = 32;     // right motor
const int STBY = 4;                            // TB6612 standby (ignored by L298N)
const int MPU_ADDR = 0x68;

// ------------------------------------------------------------ settings you may need to change
float Kp = 30.0, Ki = 0.8, Kd = 1.2;           // starting values for TT gear motors
float targetAngle = 0.0;                       // balance point offset (deg)
const bool INVERT_ANGLE = false;               // true if angle goes negative when the robot tips forward
const bool INVERT_MOTORS = false;              // true if the wheels drive the wrong way (robot falls faster)
const int  MOTOR_DEADBAND = 60;                // min PWM that actually turns your motors (0..255)
const float FALL_ANGLE = 40.0;                 // stop motors beyond this
const float START_ANGLE = 5.0;                 // start balancing inside this
const float ALPHA = 0.98;                      // complementary filter (gyro weight)
const unsigned long LOOP_US = 5000;            // 200 Hz control loop

// ------------------------------------------------------------ state
float angle = 0, gyroBias = 0, integral = 0;
bool balancing = false;
unsigned long lastLoop = 0, uprightSince = 0, lastPrint = 0;

// ------------------------------------------------------------ PWM helpers (ESP32 core 2.x and 3.x)
const int PWM_FREQ = 20000, PWM_RES = 8;
void pwmSetup(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, PWM_FREQ, PWM_RES);
#else
  ledcSetup(ch, PWM_FREQ, PWM_RES);
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

// ------------------------------------------------------------ MPU6050 (no extra library needed)
void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

bool mpuRead(int16_t &ax, int16_t &ay, int16_t &az, int16_t &gx) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, 14) != 14) return false;
  ax = Wire.read() << 8 | Wire.read();
  ay = Wire.read() << 8 | Wire.read();
  az = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read();                    // temperature
  gx = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); Wire.read(); Wire.read();   // gy, gz (not used)
  return true;
}

// Pitch from the accelerometer (deg). If your MPU is mounted differently, change ay/az here.
float accelAngle(int16_t ay, int16_t az) {
  float a = atan2((float)ay, (float)az) * 180.0 / PI;
  return INVERT_ANGLE ? -a : a;
}

float gyroRate(int16_t gx) {                   // deg/s around the wheel axis
  float r = gx / 131.0 - gyroBias;
  return INVERT_ANGLE ? -r : r;
}

// ------------------------------------------------------------ motors
void setMotor(int pwmPin, int ch, int in1, int in2, int speed) {
  if (INVERT_MOTORS) speed = -speed;
  int duty = abs(speed);
  if (duty > 0) duty = map(duty, 1, 255, MOTOR_DEADBAND, 255);   // jump over the dead zone
  duty = constrain(duty, 0, 255);
  digitalWrite(in1, speed > 0 ? HIGH : LOW);
  digitalWrite(in2, speed < 0 ? HIGH : LOW);
  pwmWrite(pwmPin, ch, duty);
}

void drive(int speed) {
  setMotor(PWMA, 0, AIN1, AIN2, speed);
  setMotor(PWMB, 1, BIN1, BIN2, speed);
}

void stopMotors() {
  drive(0);
}

// ------------------------------------------------------------ serial tuning
void handleSerial() {
  if (!Serial.available()) return;
  String s = Serial.readStringUntil('\n');
  s.trim();
  if (s.length() == 0) return;
  char c = tolower(s.charAt(0));
  float v = s.substring(1).toFloat();
  if (c == 'p') Kp = v;
  else if (c == 'i') { Ki = v; integral = 0; }
  else if (c == 'd') Kd = v;
  else if (c == 't') targetAngle = v;
  Serial.printf("Kp=%.2f  Ki=%.2f  Kd=%.2f  target=%.2f\n", Kp, Ki, Kd, targetAngle);
}

// ------------------------------------------------------------ setup
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);
  pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT); pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT); digitalWrite(STBY, HIGH);
  pwmSetup(PWMA, 0);
  pwmSetup(PWMB, 1);
  stopMotors();

  Wire.begin(21, 22);
  Wire.setClock(400000);
  mpuWrite(0x6B, 0x00);                        // wake up
  mpuWrite(0x1B, 0x00);                        // gyro +-250 deg/s
  mpuWrite(0x1C, 0x00);                        // accel +-2 g
  mpuWrite(0x1A, 0x03);                        // DLPF ~44 Hz (less motor noise)

  Serial.println("Keep the robot still... calibrating gyro");
  delay(500);
  long sum = 0;
  int n = 0;
  int16_t ax, ay, az, gx;
  for (int k = 0; k < 500; k++) {
    if (mpuRead(ax, ay, az, gx)) { sum += gx; n++; }
    delay(3);
  }
  if (n == 0) {
    Serial.println("MPU6050 not found! Check SDA=21, SCL=22, VCC=3V3, GND.");
    while (true) delay(1000);
  }
  gyroBias = (sum / (float)n) / 131.0;
  mpuRead(ax, ay, az, gx);
  angle = accelAngle(ay, az);
  Serial.printf("Gyro bias = %.3f deg/s\n", gyroBias);
  Serial.println("Balancing: -- OFF --   (hold the robot upright to start)");
  lastLoop = micros();
}

// ------------------------------------------------------------ loop (200 Hz)
void loop() {
  handleSerial();
  unsigned long now = micros();
  if (now - lastLoop < LOOP_US) return;
  float dt = (now - lastLoop) / 1e6;
  lastLoop = now;

  int16_t ax, ay, az, gx;
  if (!mpuRead(ax, ay, az, gx)) { stopMotors(); return; }
  float rate = gyroRate(gx);
  angle = ALPHA * (angle + rate * dt) + (1 - ALPHA) * accelAngle(ay, az);   // complementary filter
  float error = angle - targetAngle;

  if (!balancing) {
    stopMotors();
    if (fabs(error) < START_ANGLE) {
      if (uprightSince == 0) uprightSince = millis();
      if (millis() - uprightSince > 500) {
        balancing = true;
        integral = 0;
        Serial.println("Entering Balancing Mode...  Balancing: -- ON --");
      }
    } else {
      uprightSince = 0;
    }
  } else if (fabs(error) > FALL_ANGLE) {
    balancing = false;
    uprightSince = 0;
    stopMotors();
    Serial.println("Fell over!  Balancing: -- OFF --");
  } else {
    integral = constrain(integral + error * dt, -50.0, 50.0);
    float output = Kp * error + Ki * integral + Kd * rate;   // D on the gyro rate = less noise
    drive((int)constrain(output, -255, 255));
  }

  if (millis() - lastPrint > 200) {                          // for Serial Plotter / debugging
    lastPrint = millis();
    Serial.printf("angle:%.2f  target:%.2f  bal:%d\n", angle, targetAngle, balancing);
  }
}
