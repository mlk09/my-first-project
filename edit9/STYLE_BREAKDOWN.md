# Reference decode: "3 Rules for Naming Variables in Python" (Neso Academy, Quick Concepts)

The reference is 720×1280, 30 fps, 83.3 s. I measured it with a 1 fps contact sheet, scene detection, EBU R128 loudness and a spectrogram.

| Element | What the reference does |
|---|---|
| **Look** | **Lightboard:** the teacher writes on a glass board in front of a **pure black** background, so the writing glows and floats. |
| **Graphics** | A **fixed yellow-outlined title box** top-left ("3 Rules for Naming Variables in Python"), and **vertical side text** on the left edge ("PYTHON PROGRAMMING • QC #11"). |
| **Build-up** | A **numbered list ①②③** that grows on screen one rule at a time and is never wiped, so by the end the whole board is a summary (perfect thumbnail frame). |
| **Colour code** | White body text, **yellow keywords** (letter, underscore, numbers), **green "Ex."**, **red "not allowed"**, examples marked with a **red dot (wrong)** or **green dot (right)**. |
| **Cuts / pacing** | **No scene cuts at all** (scene detection found 0). Pauses are jump-cut out (the spectrogram shows short gaps), and each rule takes ~20 s: state the rule, wrong example, right example. |
| **Camera** | Static framing. The presenter moves between talking to camera and writing. |
| **Music / SFX** | **None:** voice only, -16 LUFS short-term. |
| **Outro** | A clean **"Quick Concepts by Neso Academy"** brand card with social handles. |

# How it's applied to *Python ki Pathshala EP 02: Variables* (no voice-over)

The content is original: a "dabba" (box) analogy, Hinglish rules, our own examples and a quiz. All on-screen text is written so the short works **without a voice**.

| Time | Scene |
|---|---|
| 0.0–3.2 | **Hook / thumbnail frame:** PYTHON **VARIABLES** + red ribbon "3 GOLDEN RULES", a drawn box with a bouncing **?**, and the mascot. The text pops in with a boom. |
| 3.2–15.8 | **Eraser wipe**, then the **yellow title box** appears (Neso style). *"Variable kya hai? = ek naam wala DABBA"* is hand-written. Two **3D boxes are drawn line by line**, then **"Rahul"** and **20** fall into them with a thud and a bounce. `name = "Rahul"`, `age = 20` and `print(name, age)` are written, and a green **Output: Rahul 20** card pops in with a ding. |
| 15.8–19.0 | Wipe, then *"Par naam rakhne ke"* and a **3 GOLDEN RULES!** slam (riser, boom, flash, shake) with a warning sign. |
| 19.0–43.0 | The **Neso-style accumulating list:** ① *Shuru LETTER ya _ se* (`1st_name` ❌ / `first_name` ✅), ② *Sirf letters, numbers, _* (`my-age` ❌ / `my_age` ✅), ③ *SPACE allowed NAHI* (`roll no` ❌ / `roll_no` ✅), plus **Bonus: Age ≠ age** (case-sensitive). The camera pulls back to the full summary board, which is a second thumbnail frame. |
| 43.0–51.0 | **QUIZ TIME!** slam: *"Kaunsa naam SAHI hai?"* with A `2pac`, B `my name`, C `total_marks`. A **3-2-1 countdown ring** ticks, then **C** is revealed with a chime ("Comment karo!"). |
| 51.0–56.0 | The animated **Python ki Pathshala end screen** (Like → Liked, Subscribe → Subscribed, **NEXT VIDEO: EP 03 Data Types**). |

**Motion added over the reference (the ₹20k layer):**
- **Write-on hand-writing** with a glowing marker nib.
- Neon marker glow, circled numbers drawn as a sweeping arc, and pop-in ✅/❌ dots.
- The **camera follows the pen** and pulls back before each board change.
- **Felt-eraser wipes** between boards.
- Glass reflections, dust, a vignette and film grain.
- Mascot reactions: it shakes its head on ❌ (*Galat!*, *Hyphen nahi!*, *Space nahi!*) and bounces on ✅ (*Sahi!*, *Perfect!*).

**Sound** (all synthesised, so there are no copyright claims):
- **Music:** a 112 bpm lo-fi/tech bed that drops at the start, breaks before *3 GOLDEN RULES!* and dips again into the quiz.
- **SFX:** marker squeaks timed to every written line, marker-cap clicks, eraser swishes, a whoosh and **thud** for each value landing in its box, a pop and ding for ✅, a soft buzzer for ❌, a riser and boom on the slams, countdown ticks and a reveal chime.
- **End screen:** clicks, ding and bell.
- **Master:** -14.2 LUFS, -0.8 dBFS peak. Length 56 s, 1080×1920, 30 fps.

**Thumbnail:** cut it from **0:01.5** (hook) or **0:42** (the full rules board).

## Rebuild

```bash
python3 edit9/build_ep02.py            # full quality
python3 edit9/build_ep02.py --preview  # quick check
```
