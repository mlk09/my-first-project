# EP 16: Python Lists (final: EP 04 design, English fruit names)

**Final video:** `output/Python_ki_Pathshala_EP16_Lists.mp4` (47 s, 1080×1920 HD) → **upload this one**
**Look (on request):** the **EP 04 input() design**:
- A dark charcoal grid background on every scene, including the quiz and the end screen.
- Typewriter title cards (white text + big orange code) and a yellow ribbon.
- A real code editor + terminal with a Run button, punch-in cuts, and big bottom captions with yellow keywords.

**Pace:** slower (about 42 s of content) so it's easy to follow. The fruits are **apple, banana, mango → grapes, + orange**.
**Rebuild:** `python3 edit23/build_ep16_v2.py`
**Voice-over:** `VOICE_ELEVENLABS.md`

| Time | Scene |
|---|---|
| 0.0–4.0 | Hook: **100 VARIABLES?** gets struck out, then the big orange **list[ ]**, the ribbon "EK LIST KAAFI HAI!" and the mascot saying "Sab ek jagah!" |
| 4.0–11.0 | `fruits = [ ]`: "apple" "banana" "mango" fly in, the commas pop, and the pills "[ ] = SQUARE BRACKETS" and ", = ITEMS ALAG KARO" appear |
| 11.0–20.0 | Editor: `fruits[0]`, `fruits[-1]` → Run → **apple, mango** ✅ |
| 20.0–28.5 | Editor: `fruits[1] = "grapes"` → Run → **['apple', 'grapes', 'mango']** ✅, "ISE KEHTE HAIN MUTABLE", "INTERVIEW MEIN POOCHTE HAIN!" |
| 28.5–36.5 | Editor: `fruits.append("orange")`, `print(len(fruits))` → **4** ✅ |
| 36.5–42.0 | **QUIZ TIME!** `print(fruits[-2])`: the 4 chips with -4…-1 under them, a big **?**, then "COMMENT MEIN BATAO!" |
| 42.0–47.0 | End screen on the same grid background, then **NEXT: EP 17 LIST METHODS** |

The earlier 30-second neon cut (`Python_ki_Pathshala_EP16_Lists_30s.mp4`, `build_ep16.py`) is kept as an alternative.

---

## Title (pick one; paste without any ⭐)

1. **Python List Kya Hai? 🛍️ 100 Variables Ki Jagah 1 List | Python in Hindi #shorts** (recommended)
2. **Python Lists Explained 🔥 append, index, mutable | Python ki Pathshala EP 16 #shorts**
3. **List vs Tuple? Interview Mein Zaroor Poochte Hain 🧠 Python List Hindi #shorts**

## Description (no angle brackets)

```
Python list kya hai? 🛍️ 100 variables mat banao, ek list banao!

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Is short mein:
📦 List = square brackets [ ] aur comma se alag items
0️⃣ Index 0 se shuru, -1 = aakhri item
🔁 List badal sakti hai (mutable): banana ki jagah grapes
➕ append() se naya item jodo, len() se ginti

💻 Code from the video:
fruits = ["apple", "banana", "mango"]
print(fruits[0])          # apple
fruits[1] = "grapes"
fruits.append("orange")
print(len(fruits))        # 4

🧠 Quiz: print(fruits[-2]) kya dega? Comment karo, sahi answer pin hoga 👇

👉 Previous: EP 15, String slicing
👉 Next: EP 17, List methods
🔔 Follow Python ki Pathshala for one new Python concept every day!

#Python #PythonList #PythonInHindi #LearnPython #PythonForBeginners #PythonInterview #CodingForBeginners #PythonKiPathshala
```

## Tags

```
python list, python lists, list in python, python list in hindi, python list tutorial, python list append, python list index, list vs tuple python, python interview questions, mutable vs immutable python, python for beginners, python tutorial in hindi, learn python, python basics, coding for beginners, python course in hindi, python ki pathshala, python shorts
```

## Pinned comment (pin it an hour after posting)

> ✅ Sahi answer: **"mango"**! List thi ["apple", "grapes", "mango", "orange"], aur -2 = peeche se doosra. Kisne sahi bataya? 👇 Next: append, remove, sort aur aur bhi list methods!

---

# Earlier version: 30 s neon cut (kept for reference)

# EP 16: Python Lists in 30 seconds

**Video:** `output/Python_ki_Pathshala_EP16_Lists_30s.mp4` (**30.0 s**, 1080×1920 HD, works without a voice-over)
**Look:** the series' **single background** (navy + grid + moving floor + triangles + symbol watermark) on **every** scene, including the quiz and the end screen.
**Rebuild:** `python3 edit23/build_ep16.py`
**Voice-over:** `VOICE_ELEVENLABS.md`

## Reference decode (2 stills)

| Element | What the references do |
|---|---|
| **Ref 1: interview card** | A flat light-blue background, a **red handwritten-style question** ("Explain the difference between a list and a tuple in Python"), a black handwritten answer (lists mutable, tuples immutable) and a cartoon interviewer + candidate. |
| **Ref 2: neon explainer** | Dark navy, a **letter-spaced neon cyan headline** `list_name = [ ]`, a **glowing yellow code line** (`fruits = ["apple", "banana", "mango"]`), and cyan captions ("square brackets", "comma"). |

## Built for retention (30 s)

- **The hook lands in the first second:** a flood of `marks1 = 90 … marks23` lines, a big red ❌, then **NAHI! → EK LIST!**
- **Something new every 1.5–2 s:** a pop, a flip, a fly-in or a counter, and a **whip-pan** every ~5 s (heavy horizontal motion blur).
- **One visual idea throughout:** a **shopping bag = glowing [ ] brackets** holding item boxes, and the same object changes in every scene (index → change → append).
- **It ends on a question with no reveal** ("COMMENT KARO!", "Answer pin hoga!"), which drives comments, then a 3.5 s end screen.

| Time | Scene |
|---|---|
| 0.0–2.4 | **Hook:** a variable flood, **100 VARIABLES?**, a red ❌ (boom + buzz + shake), **NAHI!**, then neon **EK LIST!** |
| 2.4–8.0 | Neon **`list = [ ]`**, glowing `thaila = ["aam", "kela", "seb"]` types on, the brackets slam in and 3 boxes drop in. "[ ] = square brackets", ", = items alag karo" |
| 8.0–13.0 | **INDEX:** 0 1 2 pop in, `thaila[0]` lifts **aam** → Output "aam", then -3 -2 -1, `thaila[-1]` → **"seb"**, "Aage 0, peeche -1" |
| 13.0–18.5 | **BADLO:** `thaila[1] = "angoor"`, **kela flips to angoor** ✨, **MUTABLE!**, and a handwritten **interview card** (ref-1 nod): "List vs Tuple? List = badal sakti hai, Tuple = fixed (EP 18)" |
| 18.5–23.0 | **JODO:** `thaila.append("chai")`, the boxes re-space and **chai flies in** from the right, then `len(thaila)` → a big **4** |
| 23.0–26.5 | **QUIZ!** `print(thaila[-2])`, a pulsing pink **?** over the box, **COMMENT KARO!**, "Answer pin hoga!" |
| 26.5–30.0 | End screen on the same background (Like → Share → Subscribe → NEXT: EP 17 LIST METHODS) |

**Sound:**
- A typing burst under the flood, then **boom + buzz** on the ❌, a pop on NAHI and a chime on EK LIST.
- A **whoosh on every whip**, key clicks on the code, a thud + rising pops as the boxes drop in, and dings on each index hit.
- A swap chime on the flip, a whoosh + chime on the append, and a boom + ding on the 4.
- A riser + boom into the quiz, then the end-screen sounds at 1.25× speed.
- **Master: -14 LUFS.**

**Thumbnail:** cut it at **0:01.1** (100 VARIABLES? + red ❌) or **0:15.5** (angoor flip + MUTABLE!).

---

## Title (pick one; paste without any ⭐)

1. **Python List 30 Second Mein 🔥 100 Variables Ki Jagah 1 List | Python in Hindi #shorts** (recommended)
2. **Python Lists Explained in 30 Seconds 🛍️ | Python ki Pathshala EP 16 #shorts**
3. **List vs Tuple? Interview Mein Zaroor Poochte Hain 🧠 Python List Hindi #shorts**

## Description (no angle brackets)

```
Python list 30 second mein! 🔥 100 variables mat banao, ek list banao.

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Is short mein:
🛍️ List = square brackets [ ] aur comma se alag items
0️⃣ Index 0 se shuru, -1 = last item
🔁 List badal sakti hai (mutable): kela ki jagah angoor
➕ append() se naya item jodo, len() se ginti

💻 Code from the video:
thaila = ["aam", "kela", "seb"]
print(thaila[0])          # aam
thaila[1] = "angoor"
thaila.append("chai")
print(len(thaila))        # 4

🧠 Quiz: print(thaila[-2]) kya dega? Comment karo, sahi answer pin hoga 👇

👉 Previous: EP 15, String slicing
👉 Next: EP 17, List methods
🔔 Follow Python ki Pathshala for one new Python concept every day!

#Python #PythonList #PythonInHindi #LearnPython #PythonForBeginners #PythonInterview #CodingForBeginners #PythonKiPathshala
```

## Tags

```
python list, python lists, list in python, python list in hindi, python list tutorial, python list append, python list index, list vs tuple python, python interview questions, mutable vs immutable python, python for beginners, python tutorial in hindi, learn python, python basics, coding for beginners, python in 30 seconds, python ki pathshala, python shorts
```

## Pinned comment (post it after a few comments come in)

> ✅ Sahi answer: **"seb"**! List thi ["aam", "angoor", "seb", "chai"], aur -2 = peeche se doosra. Kisne sahi bataya? 👇 Next: append, remove, sort aur 4 aur list methods!

## Posting tips

- **30 s is ideal for loops and completion:** the end screen leads back into the hook, so many viewers watch twice.
- Post at 7–9 PM IST and add it to the **Python Basics (Hindi)** playlist.
- **Pin the answer an hour later:** before that, the comments fill up with guesses (more comments → more reach).
- **Rules:** the description has **no angle brackets**; there are 8 hashtags, and `#shorts` goes only in the title.
