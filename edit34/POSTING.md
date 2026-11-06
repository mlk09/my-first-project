# EP 27: Python File handling (cinematic, 26.5 s)

**Video:** `output/Python_ki_Pathshala_EP27_Files.mp4` (26.5 s, 1080×1920 HD, works without a voice-over)
**Thumbnails:** `output/EP27_Files_thumbnail_1080x1920.jpg` (Short) and `output/EP27_Files_thumbnail_1280x720.jpg`
**Look:** the same as EP 23–26: the animated plexus network and all the cinematic effects.
**Rebuild:** `python3 edit34/build_ep27.py` · `python3 edit34/make_thumbnail.py`
**Voice-over:** `VOICE_ELEVENLABS.md`

| Time | Scene |
|---|---|
| 0.0–3.0 | Hook: **DATA SAVE KARO** + icy glowing **open()**, the ribbon "PYTHON KI DIARY!" and the mascot saying "Likho, padho!" |
| 3.0–7.5 | An open **diary** writes "Aaj Python seekha!" by hand, then the mode chips **"w" LIKHO**, **"r" PADHO**, **"a" JODO** |
| 7.5–13.5 | Editor: `with open("diary.txt", "w") as f: f.write(...)`, then `with open(..., "r")`, `print(f.read())` (glowing boxes on "w" / "r") → Run → **Aaj Python seekha!** ✅ |
| 13.5–19.5 | Editor: `open("notes.txt", "r")` → **FileNotFoundError**, with a red flash, shake and **ERROR!**: "r KE LIYE FILE HONI CHAHIYE!" |
| 19.5–23.0 | **QUIZ:** the same file opened twice in "w", with `write("Hi")` and then `write("Bye")` → "Hi? Bye? ya HiBye?" |
| 23.0–26.5 | End screen, then **NEXT: EP 28 MODULES** |

---

## Title (pick one; paste without any ⭐)

1. **Python File Handling Kya Hai? 📒 open, read, write Examples Ke Saath | Python in Hindi #shorts** (recommended)
2. **Python Ki Diary! ✍️ File Mein Likho Aur Padho | Python ki Pathshala EP 27 #shorts**
3. **"w" Mode Ka Tricky Sawaal 🤯 Python File Handling | Python Hindi #shorts**

## Description (no angle brackets)

```
Python mein file handling kya hai? 📒 File mein data likho aur padho, examples ke saath samjho!

Python ki Pathshala, jahan coding se darr nahi, dosti hoti hai! 🐍
Program band hote hi variables ka data gayab ho jaata hai. File mein save karo to data hamesha rehta hai, bilkul diary jaisa. open() se file kholo aur mode batao: "w" likhne ke liye, "r" padhne ke liye, "a" aakhir mein jodne ke liye.

Is video mein seekho:
✅ open() aur file modes: w, r, a
✅ with open se file mein likhna (write)
✅ file se padhna (read)
✅ jo file nahi hai use "r" mein khola = FileNotFoundError

💻 Code from the video:
with open("diary.txt", "w") as f:
    f.write("Aaj Python seekha!")

with open("diary.txt", "r") as f:
    print(f.read())

🧠 Quiz: same file ko do baar "w" mode mein khola: pehle Hi likha, phir Bye. File mein kya bachega: Hi, Bye ya HiBye? Comment karo 👇

👉 Previous: EP 26, try / except
👉 Next: EP 28, Modules and pip
📚 Poori Python Basics (Hindi) playlist dekho, roz ek naya concept!

#Python #PythonFileHandling #PythonFiles #PythonInHindi #LearnPython #PythonTutorial #PythonForBeginners #PythonKiPathshala
```

## Tags

```
python file handling, file handling in python, python open file, python read file, python write file, python file modes, python with open, python filenotfounderror, python file handling in hindi, python append file, python for beginners, python tutorial in hindi, learn python, python basics, coding for beginners, python ki pathshala, python shorts
```

## Pinned comment (pin it an hour after posting)

> ✅ Quiz ka sahi answer: **Bye**! "w" mode file ko pehle khaali karta hai, phir likhta hai, isliye Hi mit gaya. Dono rakhne hain to "a" (append) mode use karo! 📒 Bonus: "a" mode mein kya bachega? 👇

(Bonus answer: **HiBye**.)
