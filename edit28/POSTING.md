# EP 21: Python Dictionaries

**Video:** `output/Python_ki_Pathshala_EP21_Dictionaries.mp4` (51 s, 1080×1920 HD, works without a voice-over)
**Thumbnails:** `output/EP21_Dictionaries_thumbnail_1080x1920.jpg` (Short) and `output/EP21_Dictionaries_thumbnail_1280x720.jpg`
**Format:** the same as EP 16–20 / EP 04:
- A dark charcoal grid background on every scene, including the quiz and the end screen.
- Typewriter titles and yellow ribbons.
- A code editor + terminal with Run, and punch-in cuts.
- Big captions and mascot reactions.

**Rebuild:** `python3 edit28/build_ep21.py` · `python3 edit28/make_thumbnail.py`
**Voice-over:** `VOICE_ELEVENLABS.md`

| Time | Scene |
|---|---|
| 0.0–4.0 | Hook: **PYTHON KI PHONEBOOK** + orange **{ key: value }**, the ribbon "DICTIONARY 1 MINUTE MEIN!" and the mascot saying "Naam se dhoondho!" |
| 4.0–10.5 | Phone contact cards Aman / **Riya** / Kabir (Riya lights up), then "NAAM = KEY", "NUMBER = VALUE" and `{"Riya": "97xxx 22"}` |
| 10.5–19.0 | Editor: `marks = {"Aman": 90, "Riya": 85}`, `marks["Riya"]`, `len(marks)` → Run → **85, 2** ✅ |
| 19.0–27.5 | Editor: `marks["Kabir"] = 70`, `marks["Aman"] = 95` → Run → **{'Aman': 95, 'Riya': 85, 'Kabir': 70}** ✅ "KEY HAMESHA UNIQUE HOTI HAI" |
| 27.5–36.0 | Editor: `for name, m in marks.items()` → Run → **Aman 95, Riya 85** ✅ "JSON AUR API MEIN ROZ KAAM AATA HAI" |
| 36.0–40.5 | Recap: d["key"] → NIKAALO · d["new"]=v → JODO / UPDATE · d.items() → LOOP · len(d) → KITNE JODE, then **SCREENSHOT LE LO!** |
| 40.5–46.0 | **QUIZ:** `d = {"a": 1, "a": 2}` / `print(d["a"])`, "1? 2? ya ERROR?", a big **?**, then "COMMENT MEIN BATAO!" |
| 46.0–51.0 | End screen on the same grid, then **NEXT: EP 22 FUNCTIONS** |

---

## Title (pick one; paste without any ⭐)

1. **Python Dictionary Kya Hai? 📒 Key Value Examples Ke Saath | Python in Hindi #shorts** (recommended)
2. **Python Ki Apni Phonebook! 📱 Dictionary 1 Minute Mein | Python ki Pathshala EP 21 #shorts**
3. **Same Key Do Baar? 🤯 Python Dictionary Tricky Sawaal | Python Hindi #shorts**

## Description (no angle brackets)

```
Python dictionary kya hai? 📒 Python ki apni phonebook, key aur value ke saath, examples se samjho!

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Dictionary key: value ke jodo ka collection hai. Ise curly brackets { } se banate hain, aur item ko index se nahi, key se nikaalte hain. Har key unique hoti hai.

Is video mein seekho:
✅ Dictionary banana aur key se value nikaalna
✅ Nayi key se entry jodna, purani key se update karna
✅ items() se key aur value par loop chalana
✅ len() se ginti

💻 Code from the video:
marks = {"Aman": 90, "Riya": 85}
print(marks["Riya"])        # 85
marks["Kabir"] = 70
marks["Aman"] = 95
for name, m in marks.items():
    print(name, m)

🧠 Quiz: d = {"a": 1, "a": 2} ho to print(d["a"]) kya dega: 1, 2 ya Error? Comment karo 👇

👉 Previous: EP 20, Sets
👉 Next: EP 22, Functions
📚 Poori Python Basics (Hindi) playlist dekho, roz ek naya concept!

#Python #PythonDictionary #PythonInHindi #LearnPython #PythonTutorial #PythonForBeginners #CodingForBeginners #PythonKiPathshala
```

## Tags

```
python dictionary, dictionary in python, python dictionary in hindi, python dict, key value python, python dictionary examples, python dictionary items, python dictionary update, what is dictionary in python, python dictionary explained, python interview questions, python for beginners, python tutorial in hindi, learn python, python basics, coding for beginners, python ki pathshala, python shorts
```

## Pinned comment (pin it an hour after posting)

> ✅ Sahi answer: **2**! Dictionary mein key unique hoti hai, isliye doosri "a" pehli wali ko overwrite kar deti hai → {"a": 2}. Koi error nahi aata! Kisne sahi bataya? 👇

## Posting tips

- Post a day after EP 20, at 7–9 PM IST, and add it to the **Python Basics (Hindi)** playlist.
- **Title pattern:** a question in the title + "Examples Ke Saath" (the pattern from the viral sets video), with the keywords in the first lines of the description.
- **Rules:** the description has **no angle brackets**; there are 8 hashtags, and `#shorts` goes only in the title.
