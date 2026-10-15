# EP03 — Python Data Types: 1 Cheat Sheet (56.8 s, Hinglish, black glass board)

**Videos:**
- `output/PythonKiPathshala-EP03-Data-Types.mp4`: with the Hinglish voice-over
- `output/PythonKiPathshala-EP03-Data-Types-music-only.mp4`: music + SFX only (the video is complete without voice)

**Thumbnail:** `output/thumbnail.jpg` (frame 1 of the video is the same thumbnail, so platforms pick it as the cover)

Both videos are 1080×1920, 30 fps, -14 LUFS.

## Editing style

- **Board and writing:** a black glass board with moving reflections. Everything written on it glows (bloom), and a marker pen with a shining nib follows the writing.
- **Fixed on screen:** a yellow title box at the top ("PYTHON DATA TYPES") and a vertical yellow "EP 03" on the left.
- **List:** the cheat sheet builds ① NUMBERS → ② SEQUENCE → ③ MAPPING → ④ SET + BOOL one item at a time; nothing is erased.
- **Camera and transitions:** the camera zooms in and follows the pen while it writes, then pulls back for the full sheet. A duster wipes the board when the topic changes.
- **Mascot:** gives a hint on every type ("Poora number!", "Point wala!", "j = imaginary", "Quotes = text!", "Badal sakti hai!", "Fixed! Badlega nahi", "Key : Value jodi", "No duplicate!", "Haan ya Na!").
- **Sound:** marker squeaks while writing, a thud on every header, dings when examples finish, risers into a boom on "9 TYPES, 4 FAMILY!" and on the quiz answer, a camera shutter on "SCREENSHOT LE LO!", clock ticks for 3-2-1, clicks and a bell on the end screen, all over an original 88 BPM lo-fi bed with vinyl crackle.

## Timeline

| Time | Scene |
|---|---|
| 0–3.1 | Hook = thumbnail: PYTHON DATA TYPES, "9 TYPES • 1 CHEAT SHEET", floating chips 20 3.14 "Hi" True, EP 03 |
| 3.1–13.55 | "Data Type = data ki **KISM**": int ← 20 and str ← "Riya" drop into neon boxes; `type(20)` → `<class 'int'>`, `type("Riya")` → `<class 'str'>` |
| 13.55–17.0 | **9 TYPES, 4 FAMILY!** slam (double boom, flash, shake, sparks) + the 4 family chips |
| 17.0–43.4 | The cheat sheet builds up in sync with the voice: int, float, complex / str, list, tuple / dict / set, bool. Then "SCREENSHOT LE LO!" with a camera flash and shutter |
| 43.4–51.2 | QUIZ TIME: "3.0 ka type kya hai?" A int / B float / C str → 3-2-1 → **float ✅**, "Kyunki POINT hai!" |
| 51.2–56.8 | End screen: LIKE → LIKED!, SHARE → SHARED!, SUBSCRIBE → SUBSCRIBED, NEXT VIDEO: EP 04 input() |

## Rebuild

```bash
pip install numpy scipy opencv-python-headless pillow soundfile kokoro-onnx
python3 pathshala/ep03-data-types/make_voice.py --models <dir with kokoro files>
python3 pathshala/ep03-data-types/build.py --preview
python3 pathshala/ep03-data-types/build.py        # ~4 min
```
It reuses the mascot, fonts and sound helpers from `pathshala/ep02-print/build.py`.
To use your own voice, record each line in its time slot as `work/vo_l01.wav … vo_l12.wav` (see `VO_AT` in build.py) and rebuild.
