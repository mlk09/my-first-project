# EP 07: Python f-strings, print ka shortcut

**Video:** `output/Python_ki_Pathshala_EP07_fStrings.mp4` (55.6 s, 1080×1920, works without a voice-over)
**Theme:** EP 02 lightboard (glowing hand-writing, yellow title box, mascot) on a **moving neon cobalt-blue grid**
**Rebuild:** `python3 edit14/build_ep07.py`

## Reference decode: "Easy Python String Formatting with f-strings" (freeCodeCamp)

The reference is 720×1280, 30 fps, 42.9 s. I measured it with a 1 fps contact sheet, scene detection, EBU R128 loudness and a spectrogram.

| Element | What the reference does |
|---|---|
| **Look** | A **VS Code screen recording** fills the top half: `name`, `age`, then `# Old way` (string `+` and `str()`) directly above `# f-string way`. A **fixed banner** (Python logo + "Formatting Strings" + freeCodeCamp logo) sits in the lower middle the whole time. |
| **Motion** | The real cursor does the work: it **selects `name` and `{name}` in turn**, editor **hover tooltips** pop up (`str(...)`, `print(...)` docs), and at the end the code runs and the **terminal output** (`Alice, Age: 30`) appears. |
| **Cuts / pacing** | **One continuous take**, no scene cuts. The point is made in ~40 s by comparing two lines. |
| **Captions / graphics** | None besides the banner. |
| **Audio** | Voice only, -17.8 LUFS, with pauses cut out. **No music, no SFX.** |

## What EP 07 does with it (content is original)

| Time | Scene |
|---|---|
| 0.0–3.2 | **Hook / thumbnail:** PYTHON **f-STRINGS**, ribbon "PRINT KA SHORTCUT!", glowing chips `f"..."` `{naam}` `{marks}` `:.2f`, and the mascot |
| 3.2–14.0 | **Purana tareeka** (the reference's "old way"), hand-written into a code box: `print("Naam: " + naam + ", Marks: " + str(marks))`. **Red circles pop on every `+`** and a box goes around `str()`, with buzzes. *"Itne + aur str()? Thak gaye!"*, and the mascot says *"Uff! Bahut lamba"* |
| 14.0–27.0 | **f-string tareeka:** `print(f"Naam: {naam}, Marks: {marks}")`. A yellow ring and arrow mark the **f** ("quotes se pehle f"). The **{braces} light up** and the values **"Riya" and 95 fly into them**. **Output: Naam: Riya, Marks: 95**, with sparkles, a chime and the mascot saying *"Kitna easy!"* |
| 27.0–42.0 | **f-string ke 3 JADOO:** ① `f"{2 + 3}" = 5` (math inside), ② `f"{9.5:.2f}" = 9.50` (decimal control), ③ `f"{naam.upper()}" = RIYA` (function call). Then **SAVE KAR LO!** |
| 42.0–50.6 | **QUIZ:** `x = 4`, `print(f"{x * 2}")`. A) x * 2, B) 8, C) {x * 2}. A countdown, then **B (8)** ✅ |
| 50.6–55.6 | End screen: **NEXT VIDEO: EP 08 IF-ELSE** |

**Background:** a dark navy base with a **neon cobalt grid** (glowing lines) scrolling down. A bright scan band sweeps down every 4 s and dust particles drift up, so the background is always moving.

**Sound:**
- A lo-fi bed that breaks for one beat before the `+` circles.
- Marker squeaks on every line and the code box, and short buzzes on each red `+` circle.
- Whoosh and pop as each value lands in its braces, a ding on the output and a chime for the sparkles.
- Tuned notes for each trick, quiz ticks and chime, and the end-screen clicks and bell.
- **Master: -14 LUFS.**

**Thumbnail:** cut it at **0:02.2** (hook) or **0:24** (the f-string line with its output).

---

## Voice script (Hinglish, optional)

| Time | Line |
|---|---|
| 0.0–3.2 | "Print karne ka **shortcut**? f-strings!" |
| 3.2–8.6 | "Purana tareeka dekho: naam aur marks jodne ke liye plus, plus, plus…" |
| 8.6–14.0 | "Aur number ke liye str() bhi lagao. Itna lamba! Thak gaye na?" |
| 14.0–19.0 | "Ab f-string: quotes se pehle bas ek **f** lagao…" |
| 19.0–22.0 | "…aur variable ko **curly brackets** mein daal do. Value apne aap bhar jaati hai." |
| 22.0–27.0 | "Output: Naam: Riya, Marks: 95. Kitna easy!" |
| 27.0–31.5 | "Aur 3 jadoo: brackets ke andar math bhi chalta hai…" |
| 31.5–35.0 | "…colon point 2f se do decimal…" |
| 35.0–42.0 | "…aur function bhi call kar sakte ho, upper() se RIYA! Save kar lo!" |
| 42.0–50.6 | "Quiz! x = 4, f-string mein x * 2 kya print hoga? … **8!**" |
| 50.6–55.6 | "Like, share, subscribe. Agla episode: if-else!" |

---

## Title (pick one)

1. **Python f-strings 🔥 Print Ka Shortcut | Python for Beginners in Hindi #shorts** ⭐ (recommended)
2. **Plus Plus Plus Band Karo! ✋ Python f-string Trick | Python ki Pathshala EP 07 #shorts**
3. **f"{x * 2}" Kya Print Karega? 🤔 Python f-strings Easy Hindi #shorts**

## Description (no angle brackets)

```
Print mein + + + aur str() se thak gaye? 😩 f-string se ek line mein kaam khatam!

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Is short mein:
❌ Purana tareeka: "Naam: " + naam + ", Marks: " + str(marks)
✅ f-string tareeka: f"Naam: {naam}, Marks: {marks}"
👉 Bas quotes se pehle f lagao aur variable ko {curly brackets} mein daalo

✨ f-string ke 3 jadoo:
1️⃣ Math andar: f"{2 + 3}" = 5
2️⃣ Decimal control: f"{9.5:.2f}" = 9.50
3️⃣ Function call: f"{naam.upper()}" = RIYA

💻 Code from the video:
naam = "Riya"
marks = 95
print(f"Naam: {naam}, Marks: {marks}")
# Output: Naam: Riya, Marks: 95

🧠 Quiz: x = 4 ho to print(f"{x * 2}") kya dega? Comment karo 👇

👉 Previous: EP 06, Operators
👉 Next: EP 08, if-else
🔔 Follow Python ki Pathshala for one new Python concept every day!

#Python #PythonFString #PythonInHindi #LearnPython #PythonForBeginners #PythonTutorial #CodingForBeginners #PythonKiPathshala
```

## Tags (≈470 characters)

```
python f string, f-string python, python string formatting, f strings in python, python print format, python f string in hindi, python format decimal, python string tricks, python for beginners, python tutorial for beginners, python tutorial in hindi, learn python, python basics, coding for beginners, python course in hindi, python 2026, python ki pathshala, python shorts, coding in hindi
```

## Pinned comment

> 🧠 x = 4 ho to print(f"{x * 2}") kya dega? A) x * 2  B) 8  C) {x * 2}. Comment karo! 👇 Bonus: f"{10 / 3:.1f}" kya print karega? 😏

(Answers: **8**, and `f"{10 / 3:.1f}"` → **3.3**.)

## Posting tips

- Post a day after EP 06, at 7–9 PM IST, and add it to the **Python Basics (Hindi)** playlist.
- Put `#shorts` only in the title. The description has 8 hashtags.
- Reply to wrong quiz answers with "{} ke andar Python calculate karta hai 😉" to keep the thread going.
