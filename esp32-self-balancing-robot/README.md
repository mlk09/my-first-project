# ESP32 Self-Balancing Robot 🤖 (MPU6050 + PID)

Two-wheel self-balancing robot with an **ESP32**, an **MPU6050** and two **TT yellow gear motors**.
PID OFF = it falls 💥 — PID ON = it stands! — from the **The IOT Engineer** YouTube series.

## Components
| Part | Qty |
|---|---|
| ESP32 DevKit (30 or 38 pin) | 1 |
| MPU6050 (GY-521) gyro + accelerometer | 1 |
| TB6612FNG motor driver (or L298N) | 1 |
| TT gear motor + 65 mm wheel | 2 |
| 4x AA battery box (6 V) or 2S Li-ion (7.4 V) | 1 |
| Chassis (2 decks), jumper wires, mini breadboard | — |

## Wiring
| From | To ESP32 |
|---|---|
| MPU6050 SDA | GPIO 21 |
| MPU6050 SCL | GPIO 22 |
| MPU6050 VCC / GND | 3V3 / GND |
| Driver PWMA (L298N: ENA) | GPIO 25 |
| Driver AIN1 / AIN2 (L298N: IN1 / IN2) | GPIO 26 / 27 |
| Driver PWMB (L298N: ENB) | GPIO 13 |
| Driver BIN1 / BIN2 (L298N: IN3 / IN4) | GPIO 33 / 32 |
| TB6612 STBY | GPIO 4 (not needed for L298N) |
| Driver VM (L298N: 12V) | Battery + |
| **All GNDs together** | ESP32 GND, driver GND, battery − |

TB6612: VCC → 3V3. L298N: remove the ENA/ENB jumpers so the ESP32 controls speed.
Mount the MPU6050 **flat and firmly** on the chassis, near the wheel axle.

## Upload
1. Arduino IDE → Boards Manager → install **esp32 by Espressif**.
2. Open `SelfBalancingRobot/SelfBalancingRobot.ino` (no extra libraries needed).
3. Board: **ESP32 Dev Module** → Upload.
4. Serial Monitor at **115200**, line ending **Newline**.

## First run
1. Power on with the robot lying still → gyro calibration (2 s).
2. Hold it upright → `Entering Balancing Mode...` → let go.
3. If it falls **faster** (wheels drive away from the fall) → set `INVERT_MOTORS = true`.
4. If the angle shows negative when it leans forward → set `INVERT_ANGLE = true`.

## PID tuning (Part 2.1)
Type in the Serial Monitor: `p30`, `i0.8`, `d1.2`, `t-1.5`, `s` (show values).
1. Start with `i0` and `d0`. Raise **Kp** until it fights back and starts to oscillate.
2. Add **Kd** (0.5 → 2) until the shaking stops.
3. Add a little **Ki** (0.2 → 2) so it stops slowly drifting.
4. If it keeps rolling one way, change the target: `t-1`, `t1`, …
5. Copy the final values into the top of the code so they stay after a reset.

Tips: if the motors buzz but do not turn at low speed, raise `MOTOR_DEADBAND` (60 → 80).
Fresh batteries matter — weak batteries = it cannot hold itself up.

## License
MIT — free to use, share and modify. Please credit **The IOT Engineer** if you post it. 🙏

---

# JARVIS Part 2 — Voice Control 🗣️🤖 (`JarvisVoiceControl/JarvisVoiceControl.ino`)

Same robot and wiring. Your phone turns your voice into text and sends it to the robot over Bluetooth;
the robot keeps balancing while it drives, turns, spins or dances, and replies "Ji Boss!".

**Needs:** classic ESP32 DevKit (BluetoothSerial does not work on ESP32-S3 / C3). No extra library.

## Setup
1. Upload `JarvisVoiceControl.ino` (tune Kp / Ki / Kd first with Part 2.1 and copy your values in).
2. Phone → Bluetooth → pair **JARVIS-Robot** (PIN, if asked: 1234 or 0000).
3. Install a voice app from the Play Store: search **"Bluetooth voice control Arduino"** (any app that
   sends the recognised text over Bluetooth). To test without voice: **"Serial Bluetooth Terminal"** and type.
4. Hold the robot upright → "JARVIS online. Balancing ON!" → speak.

## Commands
| Say | Robot |
|---|---|
| "Jarvis, aage chalo" / forward | drives forward 2 s |
| "peeche aao" / back | drives back 2 s |
| "left mudo" / "baaye" | turns left |
| "right mudo" / "daaye" | turns right |
| "ghoom jao" / spin | 360° spin |
| "dance karo" / "naach" | wiggle dance 😎 |
| "ruk jao" / stop | stops, keeps balancing |

## If something is the wrong way round
- "aage" makes it go backwards → change `MOVE_LEAN` to `-2.5`.
- "left" turns right → `INVERT_TURN = true`.
- Too slow / too fast → `MOVE_LEAN` (1.5 … 4 deg), `TURN_PWM`, `SPIN_PWM`.
- Falls while driving → smaller `MOVE_LEAN`, or a little more `Kd`.
