# Reference decode: `Screenrecorder-2026-10-08-13-52-36-538.mp4`

This is a phone screen recording (1220×2712, about 24 fps, 54.9 s). The reference short is the first **~31 s**: *"Text Edit Tricks in Python"* by **Dark Code**. After that the recording scrolls Facebook (Itertools, Playwright and other unrelated reels), which I ignored.

I measured it with a 1 fps contact sheet, a 5 fps close-up of the caption and code area, a spectrogram and EBU R128 loudness.

| Element | What the reference does |
|---|---|
| **Look** | One full-screen **dark code editor** (VS Code / Cursor-style, file `test.py`, line numbers, Dark+ syntax colours: blue `text`, orange `"strings"`, yellow `print`, gold brackets). There's no face cam and no B-roll: the code *is* the video. |
| **Motion** | Real editing actions are the motion: the cursor moves, text is **typed live**, a **blue selection highlight** sweeps over `hello python`, `.upper()` → `.title()` → `len()` get typed in, and an inline AI ghost hint (`Chat Ctrl+L`) flickers. There are no camera moves. |
| **Graphics** | Almost none: just the editor UI and a sparkle icon. |
| **Cuts / pacing** | **No hard cuts.** It's one continuous take, and a new code change lands every **~2–3 s**. Each trick follows the same loop: question (*"What if you want every letter…"*), type the method, show the result (*"Python can do that instantly"*). |
| **Captions** | **Top-centre**, small **white bold caps**, **2–3 words at a time**, with the spoken or key word in **yellow** (`THE TEXT HELLO,` / `PYTHON. FIRST,` / `NO COUNTING. PYTHON`). A new chunk comes in every ~0.4–0.8 s, karaoke-style. |
| **Transitions** | None. The caption change and each code edit act as the "cut". |
| **Music** | A soft, continuous bed under the voice. The voice never drops into silence (no gap longer than 0.25 s below -35 dB). |
| **SFX** | Short broadband transients (keyboard clicks and soft ticks) on the edits. |
| **Voice** | Fast, clear and conversational, with no dead air. Measured at -20 LUFS on the screen capture; uploads are usually around -14. |

**Why it works:** your eyes are always on one spot (the code), the captions tell you where to look, and the yellow word repeats the key idea. The hook is a question, and the answer is shown, not described.

---

# How it's applied to *Python Basics EP 01: Python kya hai?* (the ₹20,000 version)

Your script is used **word for word**. The reference's core is kept (dark editor world, live typing, selection sweep, top karaoke captions with yellow key words), and a premium motion/sound layer is added on top:

| Layer | What `build_short.py` does |
|---|---|
| **Captions** | Poppins ExtraBold caps at the top. They come in **3 words at a time** (breaking at punctuation) with a pop-in. The spoken word lights up **yellow**, and key words (*Python, AI, English, beginners, code, power…*) get a **yellow marker box**. |
| **Motion graphics** | Every scene is built from scratch: app cards that pop and wobble, a converging-lines "?" moment, a **YOU → COMPUTER** diagram with code packets (`print()`, `if`, `for`) flying across, a "5 lines vs 1 line" comparison with ✗/✓ stamps, a 2×2 uses grid with live icons (a spinning globe, a blinking robot, a wiggling gamepad, a rotating gear) and a **POWER!** slam. |
| **Code demo** | A Dark+ editor (`uses.py`) types your 5 lines with a blinking cursor. The blue **selection sweep** is borrowed from the reference. A mouse pointer clicks **▶ Run**, the terminal slides up and the outputs stagger in. |
| **Camera** | There's a slow push-in on every scene, and the camera **follows the typing cursor**, then pulls back to frame the terminal. The background has parallax. |
| **Transitions** | A zoom-through with a flash, horizontal and vertical **whip-pans with motion blur**, and a white flash-zoom into the finale. |
| **Impacts** | Screen shake, a white flash and radial light rays on *"Python!"* and *"power!"*, and a lighter hit on the *Beginners* stamp. |
| **Background** | A dark editor colour with a per-scene accent glow, a scrolling dot grid, floating code glyphs `{ } ( ) 0 1`, a vignette and film grain. |
| **Music** | An original 112 bpm lo-fi/tech bed (Am–F–C–G). The intro is sparse, the beat **drops on "Python!"**, there's a one-beat break before **"power!"**, and it sidechain-pumps under the voice. It's all synthesised, so there are no copyright claims. |
| **SFX** | Pops plus tuned notes on each card or tile, a riser into the drop, booms on the impacts, whooshes on every transition, **a keyboard click for every typed character**, a mouse click on Run, blips for each output line, dings and the end-card follow click. |
| **Mix** | Voice: EQ, denoise and compression at -16 LUFS. Music is ducked under the voice with a sidechain. Master: **-14 LUFS, -1 dBTP** (YouTube's target). |
| **End card** | **NEXT: EP 02 – VARIABLES**, a FOLLOW button that gets clicked, *"Roz ek naya Python concept"* and the handle. |

## Your voice

1. Record the 6 lines of the script in order, with a **clear pause (about half a second) between lines**. Inside a line, talk naturally.
2. Save it as `edit7/voice/ep01.m4a` (or `.wav` / `.mp3`) and run `python3 edit7/build_short.py`.
3. The script finds the 5 longest pauses, splits your take into the 6 lines, and **stretches every scene and caption to your timing**. The output is `edit7/output/python-ep01-SHORT.mp4`.

If the split lands in the wrong place, create `edit7/voice/ep01_splits.json` with the 5 cut times in seconds, e.g. `[4.1, 8.9, 14.6, 21.8, 29.5]`.

Without a recording, the build makes `python-ep01-SHORT-record-along.mp4`: the full edit at a natural pace. You can also record yourself reading the captions as they light up.

## Rebuild

```bash
pip install numpy scipy pillow opencv-python-headless
python3 edit7/build_short.py              # full quality, 1080x1920 30fps
python3 edit7/build_short.py --preview    # fast low-quality check
python3 edit7/make_thumbnail.py           # 1080x1920 thumbnail
```

Fonts (in `assets/fonts`, SIL OFL): Poppins and JetBrains Mono.
