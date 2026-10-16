# EP04 — input(): user se baat karo (Facebook reel, 55 s, glass-board theme)

**Videos** (both 1080×1920, 30 fps, -14 LUFS):
- `output/PythonKiPathshala-EP04-Input.mp4`: with the Hinglish voice-over
- `output/PythonKiPathshala-EP04-Input-music-only.mp4`: music + SFX only

**Thumbnail:** `output/thumbnail.jpg`. The video also opens with it for 1 s, so Facebook uses it as the cover.

The content is the EP04 Input short (`edit11` on `claude/great-mayer-mbbsdw`), rebuilt in the EP03 look with the shared engine `pathshala/glassboard.py`:
- black glass board with glowing writing and a shining marker nib
- yellow title box and a vertical "EP 04"
- camera that follows the cursor while code is typed
- duster wipes between boards
- the mascot's reactions
- lo-fi music with key clicks, marker squeaks, thuds and dings
- LIKE / SHARE / SUBSCRIBE end screen

## Timeline (video time = lesson time + 1 s)

| Lesson time | Scene |
|---|---|
| 0–3.6 | Hook: PYTHON MEIN **input()** typed, "USER SE BAAT KARO!", floating chips |
| 3.6–9.0 | `input("Prompt")` → **SAWAAL jo screen pe dikhega** → **User ka JAWAB = variable mein** → "Program RUKTA hai jab tak user ENTER na dabaye" |
| 9.0–21.0 | Editor: `name = input("Naam kya hai? ")`, `print("Namaste", name)` → ▶ Run → terminal **waiting...** → *Aman* typed → ENTER keycap → **Namaste Aman ✅** |
| 21.0–26.0 | `input()` → **STRING** (hamesha!) + `20 = "20"` card |
| 26.0–44.5 | `age = input("Age? ")`, `print(age + 1)` → Run → 20 → **TypeError** (red flash, shake, buzzer, glitch, ERROR! stamp) → fix: `int(` … `)` inserted and highlighted → Run → **21 ✅** → "3.5 ke liye: float(input())" |
| 44.5–49.0 | Recap ①②③: `input()` → TEXT, `int(input())` → NUMBER, `float(input())` → DECIMAL, **SCREENSHOT LE LO!** + camera flash |
| 49.0–54.0 | End screen, NEXT VIDEO: EP 05 TYPE CASTING |

## Rebuild
```bash
python3 pathshala/ep04-input/make_voice.py --models <kokoro dir>   # optional voice
python3 pathshala/ep04-input/build.py --preview
python3 pathshala/ep04-input/build.py
```
