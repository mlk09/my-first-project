# EP02 — print(): Pehla code (25.3 s, Hinglish, light whiteboard theme)

**Videos:**
- `output/PythonKiPathshala-EP02-print.mp4`: with the Hinglish voice-over
- `output/PythonKiPathshala-EP02-print-music-only.mp4`: same video, music + SFX only

**Thumbnail:** `output/thumbnail.jpg`

Both videos are 1080×1920, 30 fps, -14 LUFS.

## Style decoded from the reference ("Python Variables + 3 Golden Rules")

| Element | Reference | This video (light) |
|---|---|---|
| Background | Dark chalkboard with chalk dust | **Whiteboard** with faint half-erased marker ghosts and an aluminium edge |
| Text | Handwritten italic chalk, typed on letter by letter; keywords in yellow/red | **Handwritten (Kalam) dark navy marker**, typed on letter by letter; keywords in red/blue/green with an **animated yellow highlighter** swipe |
| Topic tag | Outlined box top-left ("Python Variables + 3 Golden Rules") | "print() Statement + Pehla Code" box top-left |
| Side text | Vertical "PYTHON KI PATHSHALA • EP 02" on the left edge | Same |
| Mascot | Snake with a graduation cap, bottom-right, reacts in bubbles ("Galat!", "Sahi!") | My own snake mascot: bobs, blinks, reacts ("Hello!", "Yaad rakho!", "Wow!", "Sahi!", "Try karo!", "Kal milte hain!") |
| Diagrams | Chalk 3D boxes, ✗ / ✓ examples | Hand-drawn arrows that label `print`, `( )` and `" "`; a laptop and a screen drawn stroke by stroke |
| Transitions | Eraser wipes the board between topics | **Duster wipes** the board (with rubbing sound); a flash + zoom punch on the output reveal; a zoom into the end board |
| Output | Green-bordered "Output:" box | Same, with a ✓ badge and confetti |
| Engagement | QUIZ TIME with A/B/C and a 3-2-1 countdown, "Comment karo!" | **CHALLENGE TIME!**: `print("________")`, example `print("Rahul")`, a 3-2-1 countdown ring, "Comment karo!" |
| End card | Framed green board: "Agar video achha laga...", LIKE → LIKED, SHARE, SUBSCRIBE → SUBSCRIBED, cursor taps, NEXT VIDEO card | Framed **light** board with a wooden frame, the same button sequence, a "NEXT VIDEO EP 03: VARIABLES" card |
| Sound | Voice-over over a steady upbeat bed, a short drop before a big moment, SFX on reveals | Voice-over over an original 104 BPM lo-fi bed (ducked), the music cuts out with a riser before "Dekha!", impact on the reveal, typing ticks, marker squeaks, duster rub, pops, dings, clock ticks, clicks, bell |

## Timeline

| Time | Voice (Hinglish) | On screen |
|---|---|---|
| 0.0–4.6 | "Python ko bolna sikhaana hai? Chalo, apna pehla command seekhte hain!" | PYTHON / **print()** / "+ PEHLA COMMAND"; a laptop is drawn, "?" changes to `>>> print()` |
| 4.6–9.0 | "Python mein screen par kuch bhi dikhane ke liye, hum use karte hain print()." | Duster wipe → "Screen par kuch dikhana hai? = use karo print()"; `print("Hello World!")` is typed; arrows label **command**, **( ) bracket**, **" " text** |
| 9.0–13.75 | "Jaise yahan humne likha, Hello World! Python ise screen par display kar dega." | "Hello World!" gets highlighted → ▶ Run is clicked → an arrow to the screen → **Hello World!** is typed |
| 13.75–16.9 | "Dekha! Bas ek line code, aur message screen par!" | Music drop + flash punch → "Dekha! Bas **1 LINE** code!", the green Output box ✓, confetti |
| 16.9–21.1 | "Ab tum print() ka use karke, apna naam display karo!" | Duster wipe → **CHALLENGE TIME!**, `print("________")`, Ex. `print("Rahul")`, 3-2-1 countdown, "Comment karo!" |
| 21.1–25.3 | "Code samajh aaya? Follow karo Python ki next class ke liye!" | Framed end board: LIKE → LIKED!, SHARE → SHARED!, SUBSCRIBE → SUBSCRIBED, NEXT VIDEO EP 03: VARIABLES |

## Rebuild

```bash
pip install numpy scipy opencv-python-headless pillow soundfile kokoro-onnx
python3 pathshala/ep02-print/make_voice.py --models <dir with kokoro files>
python3 pathshala/ep02-print/build.py --preview
python3 pathshala/ep02-print/build.py
```

The handwriting font is Kalam Bold (SIL Open Font License; see `pathshala/assets/fonts/OFL.txt`).
