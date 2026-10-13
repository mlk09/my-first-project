# EP 04: input(), user se baat karo

**Video:** `output/Python_ki_Pathshala_EP04_Input.mp4` (54 s, 1080×1920, works without a voice-over)
**Rebuild:** `python3 edit11/build_ep04.py`

## Reference decode: "How to Take User Input in Python (Explained in 30 Seconds)" (ZeroBug)

The reference is 720×1280, **60 fps**, 38 s. I measured it with a 2 fps contact sheet, scene detection, EBU R128 loudness and a spectrogram.

| Element | What the reference does |
|---|---|
| **Look** | Two looks, swapped with **hard cuts** (only 4 in 38 s): a **black grid background** with **typewriter text** and a blinking cursor (white bold words, **orange code**, the Python logo), and **VS Code screen recordings** zoomed in on the code being typed, then run in the terminal. |
| **Graphics** | A minimal diagram, **`input` → (red arrow) → `String`**, typed on the grid. Nothing else. |
| **Captions** | **Small white bold caps, 1–2 words at a time**, centred in the lower middle, fading in word by word with the voice. |
| **Pacing** | A new caption every ~0.4 s and a new code character every frame. Calm, but there's no dead time. |
| **Transitions** | Straight cuts. |
| **Audio** | Voice-over (-20 LUFS) plus **keyboard typing clicks**. **No music.** |

## What EP 04 does with it (content is original)

| Time | Scene |
|---|---|
| 0.0–3.6 | **Hook / thumbnail:** "PYTHON MEIN" and an orange **`input()`** typed out, ribbon "USER SE BAAT KARO!", and the mascot asking *"Naam kya hai?"* |
| 3.6–9.0 | Grid: `input("Prompt")` typed, then an arrow to **"SAWAAL jo screen pe dikhega"** and **"User ka JAWAB = variable mein"** |
| 9.0–21.0 | Editor: `name = input("Naam kya hai? ")` and `print("Namaste", name)` are typed live while the camera follows the line. Run is clicked, the terminal shows a **waiting…** badge, *Aman* is typed slowly, an **ENTER** keycap gets pressed, then **Namaste Aman** ✅ and the mascot says *"Namaste!"* |
| 21.0–26.0 | Grid: **`input()` → STRING** (red arrow), plus a **`20 = "20"`** card |
| 26.0–35.5 | Editor: `age = input("Age? ")` and `print(age + 1)` are run, and 20 is typed. The music cuts out for one beat, then **TypeError**: red flash, screen shake, buzzer, glitch, an **ERROR!** stamp and the mascot saying *"Oops!"* |
| 35.5–44.5 | **The fix:** `int(` … `)` gets inserted and highlighted. On Run, **21** ✅ and the mascot says *"Perfect!"* Then a *"3.5 ke liye: float(input())"* chip |
| 44.5–49.0 | **Recap card** (screenshot moment): `input()` → TEXT, `int(input())` → NUMBER, `float(input())` → DECIMAL |
| 49.0–54.0 | End screen: **NEXT VIDEO: EP 05 TYPE CASTING** |

**Upgrades over the reference:**
- **Camera:** it follows the typing line, glides to the terminal, and punches in on the error. Every cut lands with a punch-in zoom and a soft flash.
- **Captions:** bigger caption chunks with colour codes (yellow = keyword, green = success, red = error).
- **Extras:** the waiting badge, the ENTER keycap, the bug and its fix, and mascot reactions.
- **Music:** a lo-fi bed that breaks for one beat right before the error.
- **SFX:** a key click for every typed character (slower and louder for the "user"), an Enter thunk, a Run click, terminal blips, a ding and chime for success, and boom + buzzer + glitch for the error. There are whooshes on the cuts and pops on the stickers.
- **Master:** -14 LUFS.

**Thumbnail:** cut it at **0:02.8** (hook) or **0:47.5** (recap card).

---

## Voice script (Hinglish, optional; say each line in its time window)

| Time | Line |
|---|---|
| 0.0–3.6 | "Kya aapka program aapse **baat** kar sakta hai? Haan!" |
| 3.6–9.0 | "`input()` function user se **sawaal** poochta hai… aur **jawab** ka intezaar karta hai." |
| 9.0–12.3 | "Code likho: name barabar input, *Naam kya hai?*" |
| 12.3–16.2 | "Run karo… dekho, program ruk gaya, aapke jawab ke liye." |
| 16.2–21.0 | "Naam likho, Enter dabao… aur Python bolega: **Namaste Aman!**" |
| 21.0–26.0 | "Par ek twist hai! `input()` **hamesha string** deta hai. 20 bhi string ban jaata hai." |
| 26.0–30.6 | "Ab age lo, aur usme plus one karo…" |
| 30.6–35.5 | "**Error!** String aur number ko jod nahi sakte." |
| 35.5–41.8 | "Fix simple hai: `int()` lagao. Run karo… **21!** Ab yeh number hai." |
| 41.8–44.5 | "Decimal chahiye? Toh `float()` use karo." |
| 44.5–49.0 | "Yeh teen lines yaad rakho, screenshot le lo!" |
| 49.0–54.0 | "Like, share, subscribe! Agle episode mein: type casting." |

---

## Title (pick one)

1. **Python input() Kaise Kaam Karta Hai? ⌨️ + Sabse Common Error | Python in Hindi #shorts** ⭐ (recommended)
2. **Program Jo Aapse Baat Kare 🤯 Python input() Explained | Python ki Pathshala EP 04 #shorts**
3. **input() se 20 + 1 = ERROR? 😱 Python User Input Easy Hindi #shorts**

## Description (no angle brackets: YouTube rejects them)

```
Program aapse baat kar sakta hai? Haan! ⌨️ Python ka input() function seekho, ek minute mein.

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Is short mein:
✅ input() user se sawaal poochta hai aur jawab ka wait karta hai
✅ Jawab ko variable mein store karo aur print karo
⚠️ Twist: input() hamesha STRING deta hai, isliye age + 1 par error aata hai
✅ Fix: int(input()) se number, float(input()) se decimal

💻 Code from the video:
name = input("Naam kya hai? ")
print("Namaste", name)

age = int(input("Age? "))
print(age + 1)   # 20 likho to 21 aayega

📸 End wala recap card screenshot kar lo!
🧠 Sawaal: float(input()) mein 7 likhoge to kya print hoga? Comment karo 👇

👉 Previous: EP 03, Data Types Cheat Sheet
👉 Next: EP 05, Type Casting
🔔 Follow Python ki Pathshala for one new Python concept every day!

#Python #PythonInput #UserInput #PythonInHindi #LearnPython #PythonForBeginners #PythonTutorial #CodingForBeginners #PythonKiPathshala
```

## Tags (≈480 characters)

```
python input, input function python, user input in python, python input in hindi, take input in python, int input python, float input python, python typeerror, python for beginners, python tutorial for beginners, python tutorial in hindi, learn python, python basics, python programming, coding for beginners, python course in hindi, python 2026, python ki pathshala, python shorts, coding in hindi
```

## Pinned comment

> 🧠 float(input()) mein 7 likhoge to output kya aayega? 🤔 Comment karo! 👇 (Hint: decimal 😉)

## Posting tips

- Post a day after EP 03, at 7–9 PM IST, and add it to the **Python Basics (Hindi)** playlist.
- Put `#shorts` only in the title. The description has 9 hashtags.
- The answer to the pinned question is **7.0**. Reply to comments with it after a few hours to keep the thread active.
