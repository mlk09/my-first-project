# MLexplorer Reel #01: "Phone = Party Remote" (ESP32 + Bluetooth + RGB LED strip)

The full production package for the first MLexplorer Reel. It is built from the reference clip
`ESP32 + MIT App = Tap to light! Control LEDs from your smartphone! #roboarmy #smartlight #MIT.mp4`.

---

## 1. Reference video analysis

**What I measured** (ffprobe, frame contact sheets at 2 fps, loudness/silence detection):

| Property | Value |
|---|---|
| Duration | **10.6 s** |
| Format | 720 × 1280 (9:16), 30 fps |
| Audio | Very quiet (-33.5 LUFS integrated). Only handling clicks and taps, with silences of 0.5–1.4 s. **No voice-over and no music.** |
| On-screen text | **None** except a "ROBO ARMY" watermark (top right) |
| Shots | 2 setups: (1) handheld close-up of an ESP32 DevKit while the USB cable is plugged in (0–3.5 s); (2) static locked-off wide shot of the ESP32 in front of a phone on a stand (3.5–10.6 s) |

**What happens, second by second**

- **0–3.5 s:** A black-gloved hand brings an ESP32 DevKit (WROOM-32, 30-pin) into frame and plugs in a blue micro-USB cable. The red power LED comes on.
- **3.5–7.5 s:** The phone is on a stand. The user swipes down quick settings, turns Bluetooth on and opens an MIT App Inventor app.
- **7.5–10.6 s:** The app has two plain grey buttons, **ON** and **OFF**. A tap on ON lights the **on-board blue LED (GPIO 2)**. That is the only payoff.

> **Note:** Your brief describes "different LED colours and Party Mode", but this clip only toggles the single blue on-board LED. There is no RGB strip, no colours and no party mode. So the Reel below **adds** those features as the upgrade, and that upgrade is the main reason the new Reel can beat the reference.

**What works (keep it)**

- The **visual style:** a saturated blue/purple tabletop, a branded backdrop, black gloves (they look clean and "lab-like" and hide fingerprints), hardware in sharp close-up, and the phone + board in the same frame so cause and effect read at a glance.
- The **concept** is instantly understandable: tap on phone → light on board.
- It is **short**, so it is easy to watch twice.

**Weaknesses (fix them)**

1. **The payoff comes last and is tiny.** For 7.5 s viewers watch a cable go in and Bluetooth settings. The reward is a 3 mm LED that is barely visible on a small screen.
2. **No hook text or voice.** Nothing in the first second tells the viewer why to keep watching.
3. **Dead time.** The quick-settings swipe and the app-opening steps are boring and add nothing.
4. **The app UI is unreadable.** Grey default buttons on a white screen, filmed from a distance.
5. **No explanation.** Viewers never learn *how* it works, so there is no "I learned something" value, no reason to save it, and nothing to comment on.
6. **Ordinary lighting.** The room is bright, so LEDs can't glow. Glowing light is the whole point of an LED video.
7. **No ending or CTA.** It just stops.

**Style to carry forward:** a futuristic lab desk, a dark room with coloured LED glow, macro hardware shots, the phone in frame, bold caps captions, and fast hard cuts.

---

## 2. Three new Reel ideas

| # | Idea | Curiosity gap | Visual payoff | Difficulty |
|---|---|---|---|---|
| **A** | **"Phone = Party Remote"**: ESP32 + WS2812B RGB strip, controlled over Bluetooth from your own app with RED / GREEN / BLUE / PARTY buttons | "How does one tap change 30 lights at once?" | A dark desk bursting into a moving rainbow | Easy. It is the reference project, upgraded |
| **B** | **"Light that knows you're there"**: a PIR motion sensor + LDR night lamp (turns on only when it's dark AND someone moves) | "Why doesn't it turn on in the daytime?" | You walk in, the room lights up; you cover the LDR, the behaviour changes | Easy |
| **C** | **"Tilt your phone, change the colour"**: the phone's accelerometer (MIT App Inventor `AccelerometerSensor`) sends tilt values to the ESP32 and the strip's hue follows the phone's angle | "Wait, the phone isn't even touching anything?" | The colour sweeps smoothly as the phone tilts. Very satisfying | Medium. It builds directly on A |

I didn't use any trend or search-volume data. These are ranked on visual payoff, how easily a beginner can follow them, and how well they build a series.

---

## 3. Recommended idea: **A, "Phone = Party Remote"**

- **Topic:** controlling an addressable RGB LED strip from a smartphone over Bluetooth with an ESP32.
- **Audience:** Indian engineering and diploma students, Arduino/ESP32 beginners, and hobbyists who want a room-décor project.
- **What viewers learn:** (1) the ESP32 has built-in Bluetooth, (2) the app sends a single character like `R` or `P`, (3) the ESP32 reads it and sets the colours of a WS2812B strip, where every LED has its own chip and can be any colour.
- **Why they stop scrolling:** the Reel opens on the result. A dark frame explodes into a moving rainbow at the moment a thumb taps "PARTY".
- **Main visual payoff:** the party-mode rainbow chase across 30+ LEDs, reflected on the desk.
- **Why it's the right first Reel:** you already own most of the hardware (ESP32 + the MIT App Inventor workflow). It fixes every weakness of the reference. It sets up a series (Idea C becomes Episode 2, "now control it with a tilt").
- **Realistic viral potential: moderate to good.** LED and colour content is visually strong and easy to understand without sound, which matters because many people watch with sound off. On the other hand, phone-controlled LED videos are a common genre. The edge has to come from execution: the payoff in the first second, a 3-step explanation, a clean branded look. No result can be guaranteed. Judge it by its 3-second hold rate and average watch time in Professional Dashboard, not by views alone.

### Hardware (real, filmable)

| Part | Note |
|---|---|
| ESP32 DevKit (original **ESP32-WROOM-32**) | Must be the original ESP32. **ESP32-C3 / S3 / C6 do not support Bluetooth Classic**, which MIT App Inventor's `BluetoothClient` uses. |
| WS2812B strip, 30 LEDs (5 V) | 60 LEDs also work with a bigger supply |
| 5 V adapter, 2–3 A | Full white can draw up to ~60 mA per LED (30 LEDs ≈ 1.8 A). **Do not power the strip from the ESP32's 3V3 pin.** |
| 330 Ω resistor | In series on the data line |
| 1000 µF capacitor | Across 5 V / GND at the strip input |
| Optional: 74AHCT125 level shifter | 3.3 V data usually works with a short wire, but it isn't guaranteed |

**Wiring:** strip **DIN** ← 330 Ω ← **GPIO 5**. Strip **5 V** ← adapter +5 V. Strip **GND** ← adapter GND **and** ESP32 GND (common ground is mandatory). Power the ESP32 from USB while filming.

### Firmware (Arduino IDE, ESP32 core + Adafruit NeoPixel)

```cpp
#include "BluetoothSerial.h"
#include <Adafruit_NeoPixel.h>

#define LED_PIN   5
#define NUM_LEDS  30

BluetoothSerial BT;
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

char mode = 'O';
uint16_t hue = 0;

void fillAll(uint32_t c) {
  for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, c);
  strip.show();
}

void setup() {
  BT.begin("MLexplorer-LED");      // name shown in the phone's Bluetooth list
  strip.begin();
  strip.setBrightness(80);         // ~30% keeps current low and avoids camera clipping
  fillAll(0);
}

void loop() {
  if (BT.available()) {
    char c = BT.read();
    if (c != '\n' && c != '\r') mode = c;
  }
  switch (mode) {
    case 'R': fillAll(strip.Color(255, 0, 0)); break;
    case 'G': fillAll(strip.Color(0, 255, 0)); break;
    case 'B': fillAll(strip.Color(0, 0, 255)); break;
    case 'P':                                   // party: rainbow chase
      for (int i = 0; i < NUM_LEDS; i++)
        strip.setPixelColor(i, strip.gamma32(
          strip.ColorHSV((uint16_t)(hue + i * 65536L / NUM_LEDS))));
      strip.show();
      hue += 512;
      delay(15);
      break;
    default:  fillAll(0); break;              // 'O' or anything else = off
  }
}
```

**MIT App Inventor app:** a `ListPicker` (pick the paired device → `BluetoothClient.Connect`) and 5 big buttons: RED, GREEN, BLUE, **PARTY** and OFF. Each button calls `BluetoothClient.SendText` with `R` / `G` / `B` / `P` / `O`. Make the app look good, because it is on camera: a black background, buttons coloured to match their LED colour, ≥ 60 dp tall, a rounded shape, and an "MLexplorer" label at the top. Pair the phone with "MLexplorer-LED" in Android Bluetooth settings first (do this off camera).

---

## 4. Three hooks (first 1–2 seconds)

1. **Visible result:** Thumb taps PARTY → the dark desk explodes into a rainbow.
   Text: **"1 TAP = PARTY MODE 🎉"** · VO: *"Ek tap… aur poora desk party mode mein!"*
2. **Challenge:** A dark desk and a phone. Text: **"YE PHONE 30 LIGHTS CHALAYEGA 👀"** · VO: *"Is phone mein koi remote nahi… phir bhi ye 30 lights control karega."* → tap → burst.
3. **Curiosity:** Fast RED → GREEN → BLUE → rainbow flashes, one per beat. Text: **"WIRE KAHAN HAI? 🤔"** · VO: *"Phone aur lights ke beech koi wire nahi… toh signal ja kaise raha hai?"*

**Use Hook 1** for this Reel. Save Hook 3 for an A/B re-edit later.

---

## 5. Storyboard (31 s, 9:16, 1080 × 1920)

All hardware shots are **filmed for real**. AI is only used for the optional data-flow graphic (S7). Keep text inside the **safe zone**: 140 px from the top, **≥ 380 px from the bottom** (caption/CTA overlay), and ≥ 120 px from the right (the like/comment/share buttons).

| # | Time | Visual action | Camera | On-screen text | Voice-over (Hinglish) | SFX / transition | AI prompt |
|---|---|---|---|---|---|---|---|
| S1 | 0.0–2.0 | Dark desk. A gloved thumb taps **PARTY** on the phone (phone in the left foreground, strip coiled on the desk behind it). The strip bursts into a rainbow chase. | Low angle, 45°, phone sharp in the foreground and the strip glowing behind. 1.0 → 1.1 zoom punch on the burst | **1 TAP = PARTY MODE 🎉** (centre, yellow "PARTY") | "Ek tap… aur poora desk party mode mein!" | Tap click → bass hit + sparkle on the burst. Music starts on the hit | — |
| S2 | 2.0–4.0 | Same shot, rainbow running. Freeze-frame for 0.3 s, then a quick rewind effect to a dark frame | Static | **KAISE? 3 CHEEZEIN 👇** | "Kaise? Sirf teen cheezein." | Record-scratch / rewind whoosh | — |
| S3 | 4.0–7.0 | Flat-lay: ESP32, the WS2812B reel, the 5 V adapter. Each one slides in or is placed by a gloved hand on a beat | Top-down, slow push-in | Labels pop next to each part: **ESP32 · RGB STRIP · 5V ADAPTER** | "ESP32 — jisme Bluetooth already built-in hai. RGB LED strip. Aur 5 volt adapter." | Pop on each label | — |
| S4 | 7.0–11.0 | Macro of the wiring: the data wire into DIN, then a pan along to GND | Macro, slow slide left → right | **DATA → GPIO 5** then **GND COMMON ✅** | "Strip ka data pin ESP32 ke GPIO 5 pe. Aur ground dono ka common — ye bhoolna mat!" | Soft whoosh, ding on "✅" | — |
| S5 | 11.0–14.0 | Phone screen recording: open the app → tap "Connect" → select **MLexplorer-LED** → "Connected" | Screen recording, scaled to ~85% with rounded corners over a blurred desk background | **APP → BLUETOOTH CONNECT** | "Phone pe apna app — MIT App Inventor se banaya. Connect kiya…" | UI clicks | — |
| S6 | 14.0–20.0 | Three fast taps: RED → GREEN → BLUE. Each one is a hard cut to the strip filling the room with that colour (the desk and the wall wash in that colour) | Split: phone (top 40%) / strip (bottom 60%), or alternate 1 s cuts between a phone close-up and a wide strip shot | **RED** · **GREEN** · **BLUE**, each word in its own colour | "…aur ab — red. Green. Blue." | Beat-synced hits on each colour | — |
| S7 | 20.0–25.0 | Explainer: phone icon → a Bluetooth wave → an ESP32 icon → the strip. A letter **"R"** travels along the path. Then the strip lights red | 2D motion graphic over the dimmed real footage | **PHONE sends 'R' → ESP32 reads → LEDs = RED** (3 lines appear in turn) | "Andar ka scene simple hai: app bas ek letter bhejta hai — R. ESP32 use padhta hai, aur strip ki har LED ko red bana deta hai. Har LED ke andar apna chhota chip hota hai!" | Data-blip SFX moving along the path | **P-S7** (optional) |
| S8 | 25.0–28.5 | Final: a tap on PARTY, then a slow orbit around the glowing strip on the desk with the MLexplorer logo on the backdrop | Slow handheld orbit or slider move, shallow depth of field | **PARTY MODE ✅** | "Aur 'P' bheja — toh rainbow party mode!" | Music peaks, sparkle | — |
| S9 | 28.5–31.0 | End card: the strip glowing behind, the MLexplorer logo, and a question | Static, slight blur on the background | **NEXT: PHONE TILT = COLOR? 📱🌈**<br>**Comment: TILT ya MUSIC?** | "Next video mein phone ko tilt karke colour badlenge, ya music pe nachayenge? Comment karo — aur MLexplorer follow karo!" | Soft riser, then cut on the beat (it loops back to S1 nicely) | — |

---

## 6. Final voice-over script

### Hinglish (main, ~31 s at an energetic pace)

> Ek tap… aur poora desk party mode mein!
> Kaise? Sirf teen cheezein.
> ESP32 — jisme Bluetooth already built-in hai. RGB LED strip. Aur 5 volt adapter.
> Strip ka data pin ESP32 ke GPIO 5 pe. Aur ground dono ka common — ye bhoolna mat!
> Phone pe apna app — MIT App Inventor se banaya. Connect kiya… aur ab — red. Green. Blue.
> Andar ka scene simple hai: app bas ek letter bhejta hai — R. ESP32 use padhta hai, aur strip ki har LED ko red bana deta hai. Har LED ke andar apna chhota chip hota hai!
> Aur 'P' bheja — toh rainbow party mode!
> Next video mein phone ko tilt karke colour badlenge, ya music pe nachayenge? Comment karo — aur MLexplorer follow karo!

### English (for an international re-edit)

> One tap… and the whole desk goes party mode!
> How? Just three things.
> An ESP32 — Bluetooth is built right in. An RGB LED strip. And a 5-volt adapter.
> Strip data goes to GPIO 5. And connect both grounds together — don't skip that!
> On the phone, my own app built with MIT App Inventor. Connect… and now — red. Green. Blue.
> Here's the trick: the app sends just one letter — R. The ESP32 reads it and turns every LED red. Each LED has its own tiny chip inside!
> Send 'P' — rainbow party mode!
> Next: tilt the phone to change colours, or sync it to music? Tell me in the comments — and follow MLexplorer!

**Recording tips:** record on your phone in a quiet room, 15–20 cm from the mouth, with a cloth or blanket around you to cut echo. Smile while you speak (it comes through as energy). Record each line 2–3 times and keep the best.

---

## 7. AI visual prompts

Film all hardware for real. A generated ESP32 will have wrong pins and unreadable silkscreen, and viewers in this niche notice. Use AI only for these optional supporting shots:

**P-S7: Data-flow explainer (5 s).** This is easier to make as a CapCut/Canva graphic than with a video model. If you do use AI:
> Vertical 9:16 motion graphic, 5 seconds, dark navy background (#0A0F2C) with subtle grid lines. Left: a flat neon-cyan smartphone icon. Middle: animated Bluetooth wave arcs in electric blue pulsing outward. Right: a simple flat illustration of a black ESP32 development board icon, then a horizontal LED strip of 10 circles. A glowing white letter "R" travels from the phone along the wave to the board; as it arrives, the LED circles turn red one after another from left to right. Clean flat vector style, soft glow, no extra text, no logos, smooth 30 fps motion, centered composition with empty space at top and bottom for captions.

**P-ALT-1: Cinematic B-roll for intros (3 s, use sparingly, e.g. a future channel trailer).**
> Vertical 9:16, 3 seconds, dark futuristic electronics lab desk at night, deep blue and purple ambient light, a coiled addressable RGB LED strip on a matte black desk emitting a smooth rainbow color chase, colored light reflecting on the desk surface, shallow depth of field, slow dolly-in from 50 cm to 30 cm, realistic physics, no people, no text, no logos, cinematic, 30 fps.

**P-ALT-2: End-card background (3 s, loopable).**
> Vertical 9:16, 3 seconds, seamless loop, abstract out-of-focus bokeh of rainbow LED lights on a dark navy background, slow drift, soft glow, empty center area for a logo and text, no text, no objects.

**Continuity rules for any AI shot:** use the same navy/purple base, the same rainbow palette as the real strip, and no visible hardware that contradicts your real build (same strip type, same board colour).

---

## 8. Editing instructions (CapCut)

**Before filming**

- Room lights **off**, with one soft dim lamp behind the camera at ~20%. Strip brightness 80/255 (as in the code) so the camera doesn't clip.
- Phone camera: 1080p or 4K at 30 fps, **lock exposure and focus** (long-press on the screen) on the lit strip, and turn HDR off. If the phone allows it, set white balance to ~4000 K.
- Phone screen brightness at maximum; enable dark mode for the app.
- Wear the black gloves (the same look as the reference, and on brand).
- Shoot each shot 3 times. Film S1 last, once everything works.

**Timeline**

1. Canvas **9:16**, 1080 × 1920, 30 fps.
2. Clips in storyboard order (S1–S9). **Cut every 1–3 s.** Remove every pause longer than 0.2 s.
3. Add the voice-over first and cut the visuals to it. Then sync the colour cuts (S6) to the music beats.
4. **Text:** Montserrat Black (already in `edit/assets/fonts/`) or CapCut's "Bold" sans. ALL CAPS, white fill, 6–8 px black stroke, soft shadow. Highlight 1 keyword per line in yellow (#FFD400) or in the matching LED colour. Size 90–110 px for hooks and 70 px for labels. Use the **"Pop" in-animation (0.2 s), no fades**. Keep text in the middle band (y = 450–1450 px).
5. **Subtitles:** Auto Captions (Hindi/Hinglish) → fix the spellings by hand. Use 2–4 words per caption in a smaller white style (55 px) placed **below** the main headline text. Make sure no caption overlaps the bottom 380 px.
6. **Transitions:** hard cuts mostly. One "Zoom in" on S1 → S2, a "Whip" between S3 and S4, a flash on the PARTY taps. Nothing else.
7. **Effects:** a 1.0 → 1.1 zoom punch on S1's burst and S8's tap. No glitch filters or lens flares (the LEDs are the effect).
8. **Colour:** Contrast +10, Saturation +10, slight Vignette. Don't over-saturate the reds.
9. **Music:** upbeat electronic or synth-pop, 120–128 BPM, **licensed**. Use **Meta Sound Collection** (Creator Studio / Professional Dashboard), or add music inside the Facebook Reels editor when you upload. Keep it at -18 to -20 dB under the voice (ducking on), and let it rise for S8.
10. **SFX:** tap clicks, pop on labels, a bass hit on the S1 burst, a whoosh on S2, dings on ✅, and a soft riser into S9.
11. **Watermark:** a small "MLexplorer" logo at the top left (not the bottom, where Facebook overlays the UI), at 70% opacity.
12. **Ending:** cut S9 on a beat so it loops cleanly into S1.

**Export:** 1080p, 30 fps, high bitrate (CapCut "Recommended" or ~12–16 Mbps), H.264, AAC 44.1/48 kHz. No CapCut end-screen or watermark.

---

## 9. Facebook upload package

**Title options**

1. One Tap = Party Mode 🎉 ESP32 Bluetooth RGB LED Control
2. My Phone Controls 30 RGB LEDs, No Wires! (ESP32 + MIT App Inventor)
3. How Does One Tap Change 30 LEDs? ESP32 Bluetooth Explained

**Recommended:** **One Tap = Party Mode 🎉 ESP32 Bluetooth RGB LED Control**

**Caption (ready to paste)**

```
1 tap = PARTY MODE 🎉

I built a phone app that controls a 30-LED RGB strip over Bluetooth using an ESP32.
👉 The app sends one letter (R, G, B or P)
👉 ESP32 reads it via Bluetooth Serial
👉 WS2812B LEDs change colour instantly — each LED has its own tiny chip!

Parts: ESP32 (WROOM-32), WS2812B LED strip, 5V 3A adapter, 330Ω resistor.
Tip: Always connect the ESP32 GND and the strip GND together, and power the strip from 5V — not the ESP32 pin.

ESP32 Bluetooth LED control | MIT App Inventor project | RGB LED strip project | IoT project for beginners

Next episode: control colours by TILTING the phone 📱🌈 or sync to MUSIC 🎵 — which one should I build first?

#ESP32 #IoT #Arduino #Electronics #RGBLED #MITAppInventor #MLexplorer
```

**CTA:** *"Tilt control or music sync — which one should I build next? Tell me in the comments."* This is a real choice that decides the next episode, so it is a genuine question and not engagement bait.

**Hashtags (7):** `#ESP32 #IoT #Arduino #Electronics #RGBLED #MITAppInventor #MLexplorer`

**Cover / thumbnail**

- Frame: S8, with the rainbow strip glowing and the phone in the foreground showing the PARTY button.
- Cover text (2 lines, centre, inside the safe zone): **"1 TAP ="** in white, **"PARTY MODE 🎉"** in yellow.
- Small tag at the top left: **"ESP32 + BLUETOOTH"**.
- Don't put text in the bottom 25% of the cover.

**Pinned comment**

```
🔧 Build notes from MLexplorer:
• Board must be original ESP32 (WROOM-32) — ESP32-C3/S3 don't support Bluetooth Classic, which MIT App Inventor uses.
• 30 LEDs at full white can pull ~1.8A → use a 5V 2–3A adapter + common GND.
• Brightness set to 80/255 in code to keep it cool and camera-friendly.

Questions about wiring or code? Ask below 👇 Want the .aia app file + code? Tell me and I'll make a full tutorial.
```

Only offer the code/app file if you're ready to share it. You could put it in a public GitHub repo and add the link later.

**Keywords to work into the caption:** ESP32 Bluetooth LED control, ESP32 RGB LED strip, WS2812B ESP32, MIT App Inventor Bluetooth, smartphone controlled LED, IoT project for beginners, Arduino LED project, party lights DIY.

**Category / topic:** If Facebook offers a topic or category picker, use **Science & Technology** (or "Technology" / "Education"). Set your Page category to something like *Science, Technology & Engineering* or *Education* if it isn't already.

---

## 10. Publishing and quality checklist

**Video quality**

- [ ] 1080 × 1920, 9:16, 30 fps, 25–35 s
- [ ] The payoff (rainbow burst) is visible within **1 s**
- [ ] No pause longer than 0.2 s; something changes every 1–3 s
- [ ] Exposure locked, LEDs not clipped to white, phone screen readable
- [ ] Text inside the safe zone (not in the bottom 380 px or the right 120 px)
- [ ] Watched once with **sound off**: it still makes sense from the text alone

**Originality and copyright**

- [ ] **All footage is filmed by you.** Don't reuse any frames from the RoboArmy reference. It was a style reference only.
- [ ] Music is from Meta Sound Collection or added in the Facebook editor (licensed for Facebook). No trending songs pulled from elsewhere.
- [ ] Your own voice and your own script. The app UI is your own build.
- [ ] No other creator's watermark visible anywhere

**Technical accuracy**

- [ ] The video says "original ESP32" (Bluetooth Classic), not ESP32-C3/S3
- [ ] Common GND and the 5 V supply are shown correctly in S4
- [ ] The code on screen (if any) matches what actually ran

**Captions and copy**

- [ ] Auto-captions proof-read (Hinglish spellings fixed)
- [ ] Title and cover match what actually happens (no misleading claims)
- [ ] 5–8 relevant hashtags only

**Publishing**

- [ ] Upload as a **Reel** from the MLexplorer Page (not a personal profile)
- [ ] Add the cover, title, caption and topic, then pin the comment right after posting
- [ ] Reply to the early comments in the first hour with real answers
- [ ] After 48–72 h, check in **Professional Dashboard**: 3-second views, average watch time, retention graph (where do viewers drop?), shares and follows. Use the drop point to plan the next edit.
- [ ] Monetization: check **Professional Dashboard → Monetization** for current eligibility and policy status. Requirements change and nothing is automatic. Consistent original uploads (2–4 Reels/week in this series) are the sustainable path.

---

## Series plan (next 3 Reels)

1. **EP02:** Tilt control (Idea C), using the same strip and app plus the accelerometer
2. **EP03:** Motion + darkness night lamp (Idea B)
3. **EP04:** No app needed: control the same strip from a browser via the ESP32 Wi-Fi web server
