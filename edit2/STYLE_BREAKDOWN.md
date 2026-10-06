# vid01.mp4: editing style breakdown

Reference: `vid01.mp4` ("How astronauts sleep in space", 59.3 s, 720×1280, 30 fps). Measured with ffmpeg scene detection, contact sheets at 1.5 fps and 10 fps around each transition, spectrograms and EBU R128 loudness.

| Element | What the reference does |
|---|---|
| **3D animation** | The whole video is CG: a character inside the ISS, a sleeping bag, Earth and the station. Lighting is soft and realistic, with glossy surfaces and space backgrounds. Nothing is live-action, and the 3D shows the idea instead of a talking head. |
| **Camera / motion** | Slow, continuous cinematic moves on every shot: dolly-ins, orbits, crane-ups and fly-throughs, with motion blur on fast moves. Crash zooms into a subject, and tumbling, rotating fly-throughs between spaces. |
| **Motion graphics** | Graphics live *inside* the 3D world, not as flat stickers: chevron arrows orbiting Earth, an orbit line, and red 3D labels with a white outline ("24 Hours", "90 minutes") that track with the camera. |
| **Cuts / pacing** | Few hard cuts (16 in 59 s); the energy comes from constant camera movement. Shots last 2–12 s and the picture is never static. |
| **Captions** | Only a **title card** at the start: a white bold caps line plus black text on a **yellow box**, in an Arial-style bold font, top-centre, fading out after about 2.3 s. After that, no subtitles; the in-scene 3D labels carry the key words. |
| **Transitions** | ① a **diagonal slide-wipe** (the new shot pushes up along a diagonal edge), ② a **spinning, motion-blurred whip / fly-through**, ③ a **3D card-flip** (the shot turns away like a card and the next one turns in), plus a few straight cuts. |
| **Music** | A continuous cinematic bed under the narration, wall to wall (-15.2 LUFS, LRA 1.3 LU, heavily compressed and dense in the low-mids). |
| **SFX** | Whooshes on the camera moves and transitions, subtle impacts on reveals, all sitting under the voice. |

## How it was applied to `SerialBegin.mp4`

The content is yours and unchanged: your **own voiceover** is the narration, and every visual is a 3D version of your whiteboard explanation.

| Time | Shot (Blender, built from scratch in `scene3d.py`) |
|---|---|
| 0.0–2.9 s | **Hook:** 3D chrome "Serial.begin(9600)" with a giant glowing green **9600** and a yellow **?**. The camera pushes in, then crash-zooms into the 9600. Reference-style title card: **SERIAL.BEGIN(9600)** over a yellow box **YE 9600 KYA HAI?** |
| 2.9–6.1 s | Diagonal slide-wipe into a 3D **Arduino Uno** (PCB, ATmega chip, headers, USB, blinking LED) and a **laptop** on a glossy stage, joined by a USB cable. The camera cranes up; **TX** and **RX** labels pop in. |
| 6.1–9.1 s | Tracking shot along the cable as glowing **1/0 bits** fly from the Arduino to the laptop. **9600 / bits / second** pops up in 3D. |
| 9.1–12.2 s | Spin-whip in. Two **baud-rate dials** float above the devices and tick **in sync**. A dashed **CLOCK WIRE** gets a red ✕ (there is no clock wire). |
| 12.2–15.0 s | Laptop close-up: the screen shows `code 9600 ≠ monitor 115200`, garbage characters type out, and the laptop dial reads **115200**, spinning 8× too fast. |
| 15.0–17.7 s | A giant red **✕** slams in, with a red alarm flash, screen shake, buzzer and boom. |
| 17.7–21.3 s | Spin-whip in. The laptop dial flips to **9600** and eases back into sync, the screen turns green (`code 9600 = monitor 9600`), **Hello World!** types out, and a green ✓ pops with a chime. |
| 21.3–23.5 s | 3D card-flip into a wide orbit. Both dials read 9600, and **SAME NUMBER!** appears in 3D. |
| 23.5–26.3 s | The camera pushes into the laptop screen showing your CTA: **FOLLOW — roz 1 IoT concept · @The IOT Engineer**. |

**Pacing:** the one long breath pause (0.64 s at 15.1 s) was removed, giving 26.3 s. Every shot keeps the camera moving.

**Audio:**
- **Voice:** your voice, EQ'd and compressed, at -16 LUFS.
- **Music:** an original cinematic-tech bed (Dm–B♭–F–C pads, a pulsing sub, a soft kick, a 16th-note arp and sidechain pump), ducked about 11 dB under the voice.
- **SFX:** all synthesised in code: an opening boom, a riser into the crash zoom, a whoosh on every cut, data blips for each bit (high pitch for 1, low for 0), clock ticks (fast and frantic at 115200), glitch bursts, an error buzzer, keyboard clicks for "Hello World!" and a success chime.
- **Master:** -14 LUFS with a true peak of -1 dBTP. All music and SFX are generated, so there are no copyright claims.

**Rendering:** Blender 5.0 Cycles at 720×1280 (the reference's own resolution), with motion blur and OIDN denoising. Frames are upscaled to 1080×1920 and given bloom, a light sharpen, a vignette and film grain. `scene3d.py` uses an NVIDIA GPU (OptiX/CUDA) automatically if it finds one, so on an RTX laptop the same command renders much faster.

## Rebuild

```bash
pip install bpy numpy scipy opencv-python-headless pillow
python3 edit2/make_screens.py      # laptop screen textures
python3 edit2/scene3d.py           # render 788 frames  (--preview for a quick low-res pass)
python3 edit2/build_final.py       # audio mix + compositing -> edit2/output/SerialBegin-3D-EDIT.mp4
```
