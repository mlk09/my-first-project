# Reference short: editing style breakdown

Reference: *"You NEED to Know How Ultrasonic Sensors Work!"* (57 s, 720×1280, 29.97 fps).
Measured with ffmpeg scene detection, frame contact sheets (1 s and 0.2 s), spectrograms and EBU R128 loudness.

| Element | What the reference does |
|---|---|
| **Cuts / pacing** | Hard cuts every ~1–3 s (22 cuts in 57 s). The picture changes every 0.3–0.6 s, because the caption swaps or the zoom punches even inside a shot. No dead air: lines butt up against each other. |
| **Motion** | Constant slow push-ins, with punch-in "zoom pops" on keywords. The first frame of a new shot is a radial **zoom-blur / warp** whip. Fast handheld moves get motion blur. |
| **Captions** | 1–3 words at a time, centred mid-frame. ALL CAPS in a heavy geometric sans, white fill, thick black stroke and soft drop shadow. **One keyword per chunk is recoloured** (yellow / red / blue / green) and often set bigger on its own line. Hard swaps with a quick pop-in, no fades. |
| **Graphics** | Anime **speed-line bursts** on the hook word; **shockwave rings of spikes** on key terms; white flash / swoosh transitions; emoji stickers next to captions (🔊 ⏱️ ⚡); hand-drawn dotted waves and chevrons animated over the footage. |
| **Transitions** | Zoom-blur whips, white flashes, and a warp/twirl on the very first frame for the hook. |
| **Music** | A continuous, driving electronic bed under the whole video, wall-to-wall (≈-14 LUFS overall, LRA 1.3 LU, very compressed). Ducked under the voice but always audible. |
| **SFX** | A whoosh on every cut or zoom, pops on caption swaps, bright "ding" tones (~2.6 kHz partials visible in the spectrogram), and impact hits on big reveals. |

## How it was applied to the raw clip

Raw clip: a 27.8 s Canva whiteboard animation with a clean Hinglish voiceover and no music. The content is unchanged; only the editing was added.

- **Pacing:** the 5 breath pauses (0.2–0.35 s each) and the lead-in silence were trimmed to about 2 frames. The cut is 26.6 s long.
- **Camera:** 14 virtual "shots". Each one punch-zooms onto whatever the pen is drawing (title, then sensor, wall, 20 cm arrow, waves, echo, "Sensor ne naapa = 40 cm", the formula, a slam onto the **÷2**, "wave DO BAAR chali!", and finally the Follow CTA). Every shot keeps a slow push-in. Shots change with a radial zoom-blur whip, and the hook opens with a twist-in warp.
- **Captions:** Montserrat Black, caps, black stroke and shadow, pop-in animation, with keywords in yellow, red or blue. There is a beat zoom-bump on every caption change, plus emoji stickers (🤔 🧱 📏 🔊 😳 ⏱️).
- **Hits:** a speed-line burst on "÷2 KYUN?". A riser, then a boom, screen shake and white flash on "40 CM". A shockwave, ding and shake on "÷ 2". A flash and ding into the CTA.
- **Audio:** an original 128 BPM synth track (Am–F–C–G, kick/clap/hats, plucky arp, sidechain pump), sidechain-ducked about 12 dB under the voice. The voice is EQ'd and compressed. Whooshes, pops, booms, dings and a riser are all synthesised in the script. The master is -14 LUFS with true peak at -1 dBTP. All audio is generated, so there are no copyright claims.

## Caption text note

No speech-to-text model could be downloaded in the build environment. The caption words therefore come from **your own on-screen text** ("Code mein ÷2 kyun?", "Sensor ne naapa = 40 cm", "wave DO BAAR chali!" …) and are timed to the voice phrases, not to individual spoken words. To use your exact script, edit the `CAPTIONS` table in `build_edit.py` and re-run it.

## Rebuild

```bash
pip install numpy scipy opencv-python-headless pillow
python3 edit/build_edit.py            # all steps: tighten, audio, video
python3 edit/build_edit.py audio video   # after editing captions/shots only
```
Output: `edit/output/IoT-Short-Ultrasonic-Divide2-EDITED.mp4` (1080×1920, 30 fps, H.264 + AAC).
