# EP 20: Python Sets

**Video:** `output/Python_ki_Pathshala_EP20_Sets.mp4` (50.5 s, 1080×1920 HD, works without a voice-over)
**Format:** the same as EP 16–19 / EP 04:
- A dark charcoal grid background on every scene, including the quiz and the end screen.
- Typewriter titles and yellow ribbons.
- A code editor + terminal with Run, and punch-in cuts.
- Big captions and mascot reactions.

**Rebuild:** `python3 edit27/build_ep20.py`
**Voice-over:** `VOICE_ELEVENLABS.md`

| Time | Scene |
|---|---|
| 0.0–4.0 | Hook: **DUPLICATES HATAO** + big orange **set( )**, the ribbon "SIRF EK LINE MEIN!" and the mascot saying "Sab unique!" |
| 4.0–10.0 | The list chips apple · mango · apple · kiwi · mango appear, the **duplicates turn red and fly out**, and the rest drop into glowing **{ }**. Then "{ } = SET" and "NO DUPLICATES!" |
| 10.0–18.5 | Editor: `set([1, 2, 2, 3, 3, 3])` → Run → **{1, 2, 3}** ✅ |
| 18.5–27.0 | Editor: `s.add(4)`, `s.add(2)` → Run → **{1, 2, 3, 4}** ✅ "2 DOBARA NAHI AAYA!", "SET MEIN ORDER NAHI HOTA" |
| 27.0–35.5 | Editor: `a \| b` → **{1, 2, 3, 4}**, `a & b` → **{3}** ✅ "UNION AUR COMMON!", "INTERVIEW MEIN POOCHTE HAIN!" |
| 35.5–40.0 | Recap: set() → NO DUPLICATES · add() → JODO · a \| b → UNION · a & b → COMMON, then **SCREENSHOT LE LO!** |
| 40.0–45.5 | **QUIZ:** `s = {5, 5, 5, 7}` / `print(len(s))`, "4? ya 2?", a big **?**, then "COMMENT MEIN BATAO!" |
| 45.5–50.5 | End screen on the same grid, then **NEXT: EP 21 DICTIONARIES** |

**Thumbnail:** cut it at **0:02.6** (DUPLICATES HATAO + set( )) or **0:08.5** (chips inside { } + NO DUPLICATES!).

---

## Title (pick one; paste without any ⭐)

1. **Python Set Kya Hai? 🔥 Duplicates Ek Line Mein Hatao | Python in Hindi #shorts** (recommended)
2. **List Se Duplicates Kaise Hatayein? 🤯 Python Sets | Python ki Pathshala EP 20 #shorts**
3. **Python Set Union & Intersection 1 Minute Mein 🧠 Hindi #shorts**

## Description (no angle brackets)

```
Python set kya hai? 🔥 List ke duplicates sirf ek line mein hatao!

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Is short mein:
🧹 set(list) → duplicates apne aap gayab
➕ add() se naya item, duplicate dobara nahi aata
🔀 Set mein order nahi hota, isliye index nahi chalta
🤝 a | b = union (dono ke saare), a & b = common items

💻 Code from the video:
nums = [1, 2, 2, 3, 3, 3]
print(set(nums))          # {1, 2, 3}
a = {1, 2, 3}
b = {3, 4}
print(a | b)              # {1, 2, 3, 4}
print(a & b)              # {3}

🧠 Quiz: s = {5, 5, 5, 7} ho to print(len(s)) kya dega: 4 ya 2? Comment karo 👇

👉 Previous: EP 19, Nested loops
👉 Next: EP 21, Dictionaries
🔔 Follow Python ki Pathshala for one new Python concept every day!

#Python #PythonSet #RemoveDuplicates #PythonInHindi #LearnPython #PythonForBeginners #CodingForBeginners #PythonKiPathshala
```

## Tags

```
python set, sets in python, python set in hindi, remove duplicates from list python, python set union, python set intersection, python set add, list to set python, python unique values, python interview questions, python for beginners, python tutorial in hindi, learn python, python basics, coding for beginners, python course in hindi, python ki pathshala, python shorts
```

## Pinned comment (pin it an hour after posting)

> ✅ Sahi answer: **2**! Set mein 5 sirf ek baar rehta hai → {5, 7}, isliye length = 2. Bonus: a - b (minus) kya karta hai? Comment karo 👇

## Posting tips

- Post a day after EP 19, at 7–9 PM IST, and add it to the **Python Basics (Hindi)** playlist.
- **Searchability:** "remove duplicates from list python" is a very common search, so title 2 targets it.
- **Rules:** the description has **no angle brackets** (`|` and `&` are fine); there are 8 hashtags, and `#shorts` goes only in the title.

---

## Alternative SEO title + description (structure of a popular 2021 tutorial, wording original)

The pattern that worked: a **question in the title** + **"Explained with Examples"** + a category tag, and a description that lists **the keywords people search** (unordered, unindexed, no duplicates, curly brackets, function names).

**Title:**
Python Sets Kya Hain? Examples Ke Saath Samjho 🔥 | Python Tutorial in Hindi #shorts

**Description:**
```
Python sets kya hote hain aur kab use karte hain? 🔥 Is short mein examples ke saath samjho.

Set ek aisa collection hai jisme duplicate items nahi hote. Set unordered hota hai, isliye isme index nahi chalta, aur ise curly brackets { } se banate hain.

Is video mein seekho:
✅ set() se list ke duplicates hatana
✅ add() se naya item jodna
✅ union ( a | b ): dono sets ke saare items
✅ intersection ( a & b ): sirf common items
✅ Set unordered aur unindexed kyun hota hai

💻 Code:
nums = [1, 2, 2, 3, 3, 3]
print(set(nums))       # {1, 2, 3}

🧠 Quiz: len({5, 5, 5, 7}) kya hoga? Comment karo 👇

📚 Python ki Pathshala ki poori Python Basics (Hindi) playlist dekho, shuru se end tak, roz ek naya concept.

#Python #PythonSets #PythonInHindi #LearnPython #PythonTutorial #PythonForBeginners #CodingForBeginners #PythonKiPathshala
```
