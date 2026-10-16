# EP06 — Python Operators: 5 types in 1 short (Facebook reel, 62 s, glass-board theme)

**Videos** (both 1080×1920, 30 fps, -14 LUFS):
- `output/PythonKiPathshala-EP06-Operators.mp4`: with the Hinglish voice-over
- `output/PythonKiPathshala-EP06-Operators-music-only.mp4`: music + SFX only

**Thumbnail:** `output/thumbnail.jpg`. The video also opens with it for 1 s, so Facebook uses it as the cover.

The content is the EP06 Operators short (`edit13` on `claude/great-mayer-mbbsdw`), rebuilt in the EP03 look with the shared engine `pathshala/glassboard.py`.

## Timeline (video time = lesson time + 1 s)

| Lesson time | Scene |
|---|---|
| 0–3.2 | Hook: PYTHON **OPERATORS**, "5 TYPES • 1 SHORT", glowing chips `+ // % == and **` |
| 3.2–12.6 | "Operator kya hai? = data par **KAAM** karne wala symbol" → `10` `+` `5` `=` `15` chips with *operand / OPERATOR / operand* labels |
| 12.6–15.3 | **5 TYPES!** slam (riser, double boom, flash, shake, sparks) + 5 family chips |
| 15.3–41.0 | The ①–⑤ list builds on the board (nothing erased): Arithmetic `+ - * / // % **`, Assignment `= += -= *= /=`, Comparison `== != > < >= <=`, Logical `and or not`, Membership `in, not in`, each with an example line and a mascot hint. Ends with **SAVE KAR LO!** + camera flash |
| 41.0–48.8 | Sabse **CONFUSING** teen: `7 / 2 = 3.5`, `7 // 2 = 3`, `7 % 2 = 1`, each ✅ |
| 48.8–56.7 | QUIZ: `10 % 3 = ?` A 3 / B 1 / C 3.33 → 3-2-1 → **B ✅** "10 mein 3, teen baar, aur 1 bacha!" |
| 56.7–61.0 | End screen, NEXT VIDEO: EP 07 F-STRINGS |

## Rebuild
```bash
python3 pathshala/ep06-operators/make_voice.py --models <kokoro dir>   # optional voice
python3 pathshala/ep06-operators/build.py --preview
python3 pathshala/ep06-operators/build.py
```
