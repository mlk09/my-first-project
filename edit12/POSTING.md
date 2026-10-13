# EP 05: Type Casting, data ka roop badlo

**Video:** `output/Python_ki_Pathshala_EP05_TypeCasting.mp4` (60 s, 1080×1920, works without a voice-over)
**Rebuild:** `python3 edit12/build_ep05.py`

## Reference decode: "Type Casting to Mix Types in Python" (Neso Academy, Quick Concepts)

The reference is 720×1280, 30 fps, 66.8 s. I measured it with a 1 fps contact sheet, scene detection and EBU R128 loudness.

| Element | What the reference does |
|---|---|
| **Look** | The same **lightboard** as Neso's naming-rules short: the teacher writes glowing text on glass over black, with a fixed yellow title box ("Mixing Types in an Expression") and vertical side text. |
| **New graphics** | Code is written inside an **outlined box**. A **yellow arrow** points up at the problem (`+`), with a hand-written note *"Cannot add string and integer"*. **"Output:" in green**, then *Error*, and a **pink warning sign with alarm lines**. |
| **Story** | Problem → error → **the same code fixed in place** (`str(age)`) → *Output: Age: 25* → a **celebration sticker** (a cartoon cheering with confetti). |
| **Cuts / pacing** | **No scene cuts** (scene detection found 0). Pauses are jump-cut out, and the problem and its fix take ~65 s. |
| **Music / SFX** | None: voice only, -17.6 LUFS. |
| **Outro** | The "Quick Concepts by Neso Academy" card. |

## What EP 05 does with it (content is original)

| Time | Scene |
|---|---|
| 0.0–3.2 | **Hook / thumbnail:** **TYPE CASTING**, ribbon "DATA KA ROOP BADLO!", a `"5"` chip that **morphs into** `5`, and the mascot |
| 3.2–12.0 | "Type Casting kya hai? = data ka **TYPE** badalna". An **`int( )` converter machine** pops in, `"20"` slides in, the machine shakes and whirrs with blinking lights, and `20` comes out ("TEXT -> NUMBER"). Then `int("20") = 20` |
| 12.0–27.0 | **Neso-style problem:** a code box is drawn with `age = 25` / `msg = "Meri age: " + age` / `print(msg)`. A yellow arrow points at the **+** with *"str + int = jud nahi sakte!"*. **Output: TypeError**, a **pulsing pink warning**, alarm beeps, and the mascot says *"Error!"* |
| 27.0–37.5 | **The fix in place:** `+ str(age)` is highlighted green, with *"str() ne 25 ko TEXT bana diya!"*. **Output: Meri age: 25**, then a **confetti burst**, a chime and the mascot saying *"Ho gaya!"* |
| 37.5–47.5 | **3 Casting Functions** list (① `int("5") = 5`, ② `float("3.5") = 3.5`, ③ `str(25) = "25"`) plus **Bonus `int(3.9) = 3`**: *"Decimal kat jaata hai, round nahi hota!"* Then **SAVE KAR LO!** |
| 47.5–55.0 | **QUIZ:** `int("7") + 3 = ?` with A 73 / B 10 / C Error, a countdown, then **B (10)** ✅ |
| 55.0–60.0 | End screen: **NEXT VIDEO: EP 06 OPERATORS** |

**Sound:** a lo-fi bed that breaks for one beat right before the error. Marker squeaks on every written line, box and arrow, and eraser swishes. The machine gets a clunk, a whirr and a ding. The error gets a boom, a buzzer and alarm beeps; the fix gets a party popper and a chime. There are note pops on the list, quiz ticks and the end-screen clicks. **Master: -14 LUFS.**

**Thumbnail:** cut it at **0:02.5** (hook) or **0:47** (the full casting list).

---

## Voice script (Hinglish, optional)

| Time | Line |
|---|---|
| 0.0–3.2 | "Data ka **roop** badalna hai? Isko kehte hain **Type Casting!**" |
| 3.2–6.0 | "Type casting matlab ek type ko doosre type mein badalna." |
| 6.0–12.0 | "Jaise text wala "20" daalo int() machine mein… aur bahar aaya asli number **20**!" |
| 12.0–16.5 | "Ab dekho yeh code: age 25 hai, aur hum likhte hain *Meri age* plus age." |
| 16.5–20.0 | "Yahan problem hai! String aur integer ko **jod nahi sakte**." |
| 20.0–27.0 | "Output? Seedha **TypeError!**" |
| 27.0–32.0 | "Fix simple hai: age ko **str()** mein daal do. Ab 25 bhi text ban gaya." |
| 32.0–37.5 | "Run karo… **Meri age: 25!** Ho gaya!" |
| 37.5–44.5 | "Teen functions yaad rakho: int text ko number banata hai, float decimal, aur str number ko text." |
| 44.5–47.5 | "Bonus: int(3.9) deta hai 3. Decimal kat jaata hai, round nahi hota!" |
| 47.5–55.0 | "Quiz! int("7") plus 3 kya hoga? … **10!**" |
| 55.0–60.0 | "Like, share, subscribe. Agla episode: Operators!" |

---

## Title (pick one)

1. **Python Type Casting 🔄 int(), float(), str() Ek Short Mein | Python in Hindi #shorts** ⭐ (recommended)
2. **"Meri age: " + 25 = ERROR? 😱 Python Type Casting Fix | Python ki Pathshala EP 05 #shorts**
3. **int(3.9) = 3? 🤯 Python Type Casting Easy Hindi | Beginners #shorts**

## Description (no angle brackets)

```
String aur number ko jodne par ERROR? 😱 Type Casting se data ka roop badlo!

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Is short mein seekho:
🔄 Type Casting = ek data type ko doosre type mein badalna
⚠️ "Meri age: " + 25 kyun TypeError deta hai
✅ str() se fix: number ko text banao
📋 3 casting functions:
   int("5")      = 5      (text se number)
   float("3.5")  = 3.5    (text se decimal)
   str(25)       = "25"   (number se text)
⭐ Bonus: int(3.9) = 3, decimal kat jaata hai, round nahi hota!

💻 Code from the video:
age = 25
msg = "Meri age: " + str(age)
print(msg)   # Meri age: 25

🧠 Quiz: int("7") + 3 = ? Answer comment mein likho 👇

👉 Previous: EP 04, input()
👉 Next: EP 06, Operators
🔔 Follow Python ki Pathshala for one new Python concept every day!

#Python #TypeCasting #PythonInHindi #LearnPython #PythonForBeginners #PythonTutorial #CodingForBeginners #PythonKiPathshala
```

## Tags (≈480 characters)

```
python type casting, type casting in python, type conversion python, python int float str, str function python, int function python, python typeerror, python type casting in hindi, python for beginners, python tutorial for beginners, python tutorial in hindi, learn python, python basics, python programming, coding for beginners, python course in hindi, python 2026, python ki pathshala, python shorts
```

## Pinned comment

> 🧠 int("7") + 3 = ? A) 73  B) 10  C) Error. Comment karo! 👇 Aur batao: int(9.99) kya dega? 😏

## Posting tips

- Post a day after EP 04, at 7–9 PM IST, and add it to the **Python Basics (Hindi)** playlist.
- Put `#shorts` only in the title. The description has 8 hashtags.
- The second question in the pinned comment (`int(9.99)` → **9**) starts a discussion, so reply to wrong answers with the "kat jaata hai" rule.
