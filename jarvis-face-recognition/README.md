# JARVIS Part 3 👀 — ESP32-CAM Face Recognition (The IOT Engineer)

Jarvis gets eyes: an **ESP32-CAM** recognises your face (green box, "Welcome back, Boss!") and flags an
unknown face (red box, "Alert!").

## Components (~Rs 500–700)
- ESP32-CAM (AI-Thinker) with OV2640 camera
- ESP32-CAM-MB USB programmer board (or FTDI USB-to-serial, 5 V)
- 5 V 2 A power supply

## Upload (uses the official Espressif example — face recognition is built in)
1. Arduino IDE → Boards Manager → install **esp32 by Espressif version 2.0.17**
   (face *recognition* was removed in core 3.x — use 2.0.x).
2. File → Examples → ESP32 → Camera → **CameraWebServer**.
3. In `CameraWebServer.ino`:
   - comment out every `#define CAMERA_MODEL_...` line except **`#define CAMERA_MODEL_AI_THINKER`**
   - put your WiFi name and password in `ssid` and `password`.
4. Tools → Board: **AI Thinker ESP32-CAM**, Partition Scheme: **Huge APP (3MB No OTA)**.
5. Upload (with the MB board just press Upload; with FTDI connect IO0 to GND while uploading, then remove it and press RESET).
6. Serial Monitor 115200 → it prints `Camera Ready! Use 'http://192.168.x.x' to connect`.

## Make Jarvis recognise you
1. Open that IP address in your phone / laptop browser (same WiFi).
2. Resolution: **CIF (400x296)** or smaller, then press **Start Stream**.
3. Turn ON **Face Detection** and **Face Recognition**.
4. Look at the camera and press **Enroll Face** — it saves your face (ID 0 = Boss).
5. Now your face shows a **green box + your ID**; any other face shows a **red box "Intruder Alert!"**.

## Tips
- Good front light on the face; keep 30–60 cm from the camera.
- If you see `Brownout detector was triggered`, use a stronger 5 V 2 A supply.
- Enrolled faces are kept in RAM: after a reset, enroll again.

## Part 4 idea
Connect a relay / servo to GPIO 12 or 13 and open a door lock when the Boss is recognised 🔓.
