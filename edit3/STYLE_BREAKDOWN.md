# "How does Swiggy deliver your order?": editing style breakdown

Reference: `How does Swiggy deliver your order?.mp4` (90.9 s, 720×1280, 30 fps). Measured with ffmpeg scene detection, contact sheets (every 2 s, plus 10 fps strips around the transitions), spectrograms and EBU R128 loudness.

| Element | What it does |
|---|---|
| **Backbone** | A talking head (presenter at a desk) cut against inserts. About 27 cuts in 91 s, so the picture changes roughly every 3 s. |
| **3D animation** | Short CG inserts of 2–4 s with a slow push or orbit: a glowing green "matrix-code" laptop on a circuit board, blue isometric server blocks joined by arrows, a 3D "?" made of light. |
| **Motion graphics** | Flat 2D overlays: an animated scooter with a delivery box, a phone with a map route, Swiggy → API → server icons on dashed lines, a hand-drawn arrow, a confused-person sticker, an "ACCEPT" button with a cursor click, and a full-screen **white card where a green ✓ draws itself** ("Yay! Order Received"). |
| **Captions** | No word-by-word subtitles. **Step labels** in the lower third: a small yellow "STEP-1" over a white bold title that **types on letter by letter**. **Keyword wheels**: yellow words scroll up like a drum, with the active word bright and its neighbours faded (Restaurant → Items → Location → Payment). |
| **Transitions** | Mostly **light-leak / film-burn flashes** (a warm orange-white glow sweeping across), a flash to white, quick dissolves, and a few straight cuts. |
| **Music** | A soft, steady background bed, quiet and calm (-19.5 LUFS overall, LRA 3.4). |
| **SFX** | A whoosh or soft impact on each light leak, **sparkle/shimmer** as caption words appear, and clicks on the button and ✓. |

## How it was applied: `millis-vs-delay-SHORT.mp4` (40 s, 1080×1920)

The concept is taken from your 10-minute Tinkercad tutorial, and your own screen recording is the footage. Your Tinkercad screen takes the place of Swiggy's talking head.

| Time | Shot |
|---|---|
| 0.0–3.5 s | **3D hook:** Arduino plus a ticking chrome stopwatch, with **millis()** vs **delay()** popping in. Lower third: *ARDUINO / millis() vs delay()*. |
| 3.5–10.5 s | **STEP-1 · millis():** your clip from 4:09, with the counter racing (94 → 800+). The code line gets a yellow highlight box, and an arrow draws down to the Serial Monitor. Keyword wheel: *Board ON → Time count → milliseconds*. |
| 10.5–15.5 s | **3D:** a giant counter (0 → 9,000+ ms) above the Arduino, with green arrows orbiting it, labelled "kabhi nahi rukta". Wheel: *Kabhi rukta nahi → Background mein → Hamesha chalta*. |
| 15.5–22.5 s | **STEP-2 · delay(1000):** your clip from 8:50, printing once per second (2000, 3001, 4002…) with a tick each second. Wheel: *1 second WAIT → Program RUKA → Kuch nahi hota*. |
| 22.5–30.0 s | **STEP-3 · DIFFERENCE (3D):** two lanes. On the **delay()** lane, task cubes hit a red wall, "WAIT 1000 ms", and freeze for 1 s. On the **millis()** lane, cubes keep flowing while LEDs keep blinking. |
| 30.0–36.0 s | **White result card**, Swiggy "Order Received" style: a red ✕ draws for *delay(1000): Program RUK jaata hai*, then a green ✓ draws for *millis(): Program CHALTA rehta hai*. |
| 36.0–40.0 s | **Follow card:** *ARDUINO · CODE KA RAAZ #3, FOLLOW — roz 1 IoT concept, @The IOT Engineer*. |

- **Transitions:** a warm light-leak flash with a whoosh on every one of the 6 cuts.
- **Music:** an original calm explainer bed at 96 BPM (Cmaj7–Am7–Fmaj7–G7 soft keys, a light beat from bar 2).
- **SFX:** stopwatch ticks, a fast ticking counter, a slow tick each second during delay, a sparkle per caption and keyword, typing clicks on the step labels, a thud when a delay cube hits the wall, a soft buzz on ✕ and a chime on ✓. All synthesised in code, so there are no copyright claims. Master: -14 LUFS, -1 dBTP.

## Voiceover script (optional, about 40 s, timed to the cuts)

The short works without a voiceover: the step labels and keyword wheels carry the explanation. To add your voice, record these lines (roughly one line per segment) and upload the file. The mix ducks the music under it automatically.

| Time | Line |
|---|---|
| 0.0–3.5 | "millis() aur delay(): dono time ke liye hain, par kaam bilkul alag!" |
| 3.5–10.5 | "millis() batata hai board ON hone ke baad kitne milliseconds ho gaye." |
| 10.5–15.5 | "Ye counter background mein chalta rehta hai, kabhi rukta nahi." |
| 15.5–22.5 | "delay(1000) likha, toh poora program 1 second ke liye ruk jaata hai." |
| 22.5–30.0 | "delay mein Arduino kuch aur nahi kar sakta; millis ke saath baaki kaam chalte rehte hain." |
| 30.0–36.0 | "Simple rule: chhota wait chahiye toh delay, multitasking chahiye toh millis!" |
| 36.0–40.0 | "Aise hi roz ek IoT concept ke liye follow karo!" |

## Rebuild

```bash
python3 edit3/scene3d.py        # 3D inserts (465 frames; uses an NVIDIA GPU automatically if present)
python3 edit3/build_short.py    # music + SFX + Swiggy-style compositing -> edit3/output/millis-vs-delay-SHORT.mp4
```
