# Reel #01: "1 TAP = PARTY MODE" (rendered, 20 s)

**Video:** `output/MLexplorer-Reel01-PartyMode.mp4` (1080×1920, 9:16, 30 fps, 20.2 s, H.264 + AAC, -14 LUFS)
**Cover:** `output/cover.jpg`

This is an **animated explainer**. Everything is drawn by `build_reel.py`: the ESP32, the LED strip, the phone app, the wiring, the captions, the music and the sound effects. No stock footage, no third-party music and nothing from the reference video is used, so there are no copyright risks. It is not footage of real hardware.

## Scene timing (cuts are on the 128 BPM beat)

| Time | Scene | On screen |
|---|---|---|
| 0.0–2.4 | Hook | Tap PARTY → strip bursts into a rainbow, light rays, flash. "1 TAP = PARTY MODE" |
| 2.4–3.8 | Freeze | "KAISE? SIRF 3 CHEEZEIN" (music muffles like a paused record) |
| 3.8–7.1 | Parts | 1 ESP32 (Bluetooth built-in) · 2 WS2812B RGB strip · 3 5V 2–3 A adapter |
| 7.1–9.9 | Wiring | DATA → GPIO 5 (via 330 Ω) · 5V → strip · GND COMMON ✓ |
| 9.9–13.2 | Colours | Taps RED / GREEN / BLUE, and the whole frame washes in that colour |
| 13.2–16.4 | How it works | App sends 'R' over Bluetooth → ESP32 reads it → data wire → LEDs turn red |
| 16.4–18.3 | Finale | 'P' sent = PARTY MODE ✓, rays and sparkles |
| 18.3–20.2 | End card | NEXT EPISODE: PHONE TILT = COLOUR? · TILT ya MUSIC? COMMENT KARO · FOLLOW MLexplorer. Ends on the rainbow, so it loops into the hook |

## Adding your own voice-over (optional but recommended)

The video works with sound off (all text is on screen) and has its own music. A human Hinglish voice usually improves retention and trust. Record this script to match the timing (about 20 s, energetic):

| Time | Line |
|---|---|
| 0.0 | Ek tap… aur party mode on! |
| 2.4 | Kaise? Sirf teen cheezein. |
| 3.8 | ESP32 — Bluetooth built-in. RGB LED strip. Aur 5 volt adapter. |
| 7.1 | Data GPIO 5 pe, 5 volt strip ko, aur ground common! |
| 9.9 | App connect… Red. Green. Blue. |
| 13.2 | App bas ek letter bhejta hai — R. ESP32 padhta hai… LEDs red! |
| 16.4 | 'P' bheja — party mode! |
| 18.3 | Next: tilt ya music? Comment karo! |

Then either drop the MP4 into CapCut, add your recording and lower the music to about 30% while you speak, **or** rebuild with automatic ducking:

```bash
pip install numpy scipy opencv-python-headless pillow
python3 reels/01-esp32-party-mode/build_reel.py --voice my_voiceover.m4a
python3 reels/01-esp32-party-mode/build_reel.py --preview   # stills only, in work/
```

## Facebook upload text for this version

**Title:** One Tap = Party Mode 🎉 ESP32 Bluetooth RGB LED Control

**Caption:**
```
1 tap = PARTY MODE 🎉

How a phone controls an RGB LED strip with an ESP32 over Bluetooth:
👉 The app sends one letter (R, G, B or P)
👉 ESP32 reads it via Bluetooth Serial
👉 Every WS2812B LED has its own tiny chip, so each one can be any colour

Parts: ESP32 (WROOM-32), WS2812B strip, 5V 3A adapter, 330Ω resistor.
Tip: connect ESP32 GND and strip GND together, and power the strip from 5V — not the ESP32 pin.

(Animated explainer — real hardware build coming next!)

Next episode: TILT the phone to change colour 📱🌈 or sync to MUSIC 🎵 — which first?

#ESP32 #IoT #Arduino #Electronics #RGBLED #MITAppInventor #MLexplorer
```

**Pinned comment:** use the one in `PRODUCTION_PACKAGE.md`, section 9.

## Notes for reach (no guarantees)

- The result appears at **0.5 s** and the clip **loops** cleanly (it ends on the rainbow strip and restarts on the strip). Both help watch time and replays.
- Text stays out of the bottom ~380 px and the right ~120 px, where Facebook draws its buttons and caption.
- After 48–72 h, check **Professional Dashboard → the Reel → retention graph**. If viewers drop at "KAISE?" (2.4 s), shorten that scene in `CUTS`.
- An animation is a good first post. **Following up with a real filmed build** (same story, real board) gives you a second Reel and builds trust in the channel.
