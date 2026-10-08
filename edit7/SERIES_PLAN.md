# Python Basics: a YouTube Shorts series in Hinglish

**Format (every episode):** 30–40 s, 9:16, the dark code-editor look with top karaoke captions (see `STYLE_BREAKDOWN.md`).
**Script shape (6 lines, so `build_short.py` can auto-sync your voice):**

1. **Hook:** a question or surprise in the first 2 seconds
2. **What is it:** one line, in simple words
3. **Analogy:** something from real life
4. **Code:** typed live on screen
5. **Output:** you run it and the result appears
6. **Punch line:** then the end card points to the next episode

**Recording tip:** take a half-second pause between lines, keep the energy up and smile while you talk (it comes through in your voice). Post daily or every other day at the same time (7–9 PM IST works well for students).

---

## Roadmap (30 episodes)

| # | Phase 1: Foundation | # | Phase 2: Logic & Loops | # | Phase 3: Data & Functions |
|---|---|---|---|---|---|
| 01 | Python kya hai? ✅ | 11 | while loop | 21 | Sets |
| 02 | Variables | 12 | for loop + range() | 22 | Dictionaries |
| 03 | Data Types | 13 | break & continue | 23 | Functions (def) |
| 04 | input() | 14 | Strings basics | 24 | Parameters & return |
| 05 | Type Casting | 15 | String methods (upper/title/len) | 25 | Default arguments |
| 06 | Operators | 16 | String slicing | 26 | lambda |
| 07 | f-strings | 17 | Lists | 27 | try / except |
| 08 | if-else | 18 | List methods | 28 | File handling |
| 09 | elif | 19 | Tuples | 29 | Modules & pip |
| 10 | and / or / not | 20 | Nested loops (pattern) | 30 | Mini project: Number Guessing Game |

Common hashtags for the whole series: `#python #pythonbasics #pythonforbeginners #coding #programming #learnpython #hinglish #codinginhindi #shorts`

---

## EP 01: Python kya hai? (rendered in `output/`)

**Script (your original, unchanged)**
1. Instagram, Netflix aur AI… in sab mein ek common cheez hai. Python!
2. Python ek programming language hai. Matlab computer ko instructions dene ki language.
3. Iski sabse badi khoobi? Yeh English jaisi simple dikhti hai. Isliye beginners ke liye best hai.
4. Python se websites banti hain, AI aur chatbots bante hain, games bante hain, aur boring kaam automatic ho jaate hain.
5. Dekho, yeh code bhi Python mein hai, aur aap isse padh kar hi samajh gaye ki yeh kya karega.
6. Yahi hai Python ki power!

**Code on screen**
```python
print("Python is used in:")
print("Websites")
print("AI")
print("Games")
print("Automation")
```

**Title options**
- Python Kya Hai? 🐍 Sirf 30 Second Mein Samjho! #shorts
- Instagram, Netflix aur AI ka SECRET = Python 🤯 #shorts
- Python Kya Hai? | Python Basics EP 01 | Hinglish #shorts

**Description**
```
Instagram, Netflix aur AI mein ek cheez common hai: PYTHON 🐍
Python Basics series ka EP 01: Python kya hai, kyun beginners ke liye best hai,
aur isse kya-kya bana sakte ho (websites, AI, games, automation).

💻 Code from the video:
print("Python is used in:")
print("Websites")
print("AI")
print("Games")
print("Automation")

👉 Next: EP 02, Variables
🔔 Follow for one new Python concept every day!

#python #pythonbasics #pythonforbeginners #learnpython #coding #programming #codinginhindi #hinglish #shorts
```

**Tags**
`python, python kya hai, what is python, python for beginners, python basics, python in hindi, python hinglish, learn python, python tutorial, python shorts, coding for beginners, programming language, python uses, python ka use, coding in hindi, python 2026`

**Pinned comment:** *"Aap Python kis cheez ke liye seekhna chahte ho? AI 🤖, Websites 🌐 ya Games 🎮? Comment karo 👇"*

---

## EP 02: Variables

**Script**
1. Agar computer ko aapka naam yaad rakhna ho… toh woh kahan rakhega?
2. Variable mein! Variable matlab ek naam waala dabba, jismein data store hota hai.
3. Jaise kitchen mein dabbe pe likha hota hai "Cheeni", waise hi code mein dabbe ka naam hota hai.
4. Dekho: name barabar "Rahul", aur age barabar 20.
5. Ab print karo, aur Python dabba khol ke value dikha deta hai!
6. Ek dabba, ek naam, aur value jab chaaho badlo. Yahi hai variable!

**Code**
```python
name = "Rahul"
age = 20
print(name, age)
```
**Output:** `Rahul 20`

**Title:** Python Variables Kya Hote Hain? 📦 Dabbe Wala Concept! | EP 02 #shorts
**Description:** `Variable = naam waala dabba jismein data store hota hai 📦 Python Basics EP 02, sabse easy explanation in Hinglish. 👉 Next: Data Types #python #variables #pythonbasics #learnpython #codinginhindi #shorts`
**Tags:** `python variables, variables in python, python variable kya hai, python basics, python for beginners, python in hindi, python hinglish, learn python, coding shorts`

---

## EP 03: Data Types

**Script**
1. 20 aur "20"… dono same dikhte hain, par Python ke liye bilkul alag hain!
2. Har value ka ek type hota hai. Isko kehte hain data type.
3. Jaise number alag cheez hai, aur naam alag cheez hai.
4. Dekho: int matlab poora number, float matlab point waala number, str matlab text, aur bool matlab True ya False.
5. type() lagao, aur Python khud bata deta hai ki value kis type ki hai!
6. Type samjho, toh bugs apne aap kam ho jaate hain!

**Code**
```python
print(type(20))
print(type(3.5))
print(type("20"))
print(type(True))
```
**Output:** `<class 'int'>` · `<class 'float'>` · `<class 'str'>` · `<class 'bool'>`

**Title:** 20 vs "20" 🤯 Python Data Types in 30 Seconds | EP 03 #shorts
**Description:** `int, float, str, bool: Python ke 4 basic data types, ek baar mein clear ✅ Python Basics EP 03 (Hinglish). 👉 Next: input() #python #datatypes #pythonbasics #learnpython #shorts`
**Tags:** `python data types, int float str bool, type function python, python basics, python for beginners, python hindi, learn python`

---

## EP 04: input()

**Script**
1. Kya aapka program aapse baat kar sakta hai? Haan!
2. input() se program user se sawaal poochta hai, aur jawab store kar leta hai.
3. Bilkul waise jaise koi form aapka naam poochta hai.
4. Dekho: name barabar input, "Naam kya hai?"
5. Aap naam likho, enter dabao, aur Python bolega: Hello, Aman!
6. Ab aapka program sirf bolta nahi, sunta bhi hai!

**Code**
```python
name = input("Naam kya hai? ")
print("Hello", name)
```
**Output:** `Naam kya hai? Aman` → `Hello Aman`

**Title:** Python Program Jo Aapse Baat Kare 😲 input() Explained | EP 04 #shorts
**Description:** `input() se Python user se sawaal poochta hai aur jawab yaad rakhta hai 🗣️ Python Basics EP 04. 👉 Next: Type Casting (5 + 5 = 55 wala bug!) #python #input #pythonbasics #learnpython #shorts`
**Tags:** `python input, input function python, user input python, python basics, python for beginners, python hindi, learn python`

---

## EP 05: Type Casting

**Script**
1. Python mein 5 plus 5… 55?! Yeh kya bug hai?
2. Kyunki input() hamesha text deta hai. Aur text plus text, bas jud jaata hai.
3. Jaise do chits jodne se "5" "5" ban jaata hai, 10 nahi.
4. Solution: int() lagao, aur text ko number mein badlo.
5. Ab 5 plus 5… poore 10!
6. Isko kehte hain type casting. Beginners ki sabse common galti, ab aap nahi karoge!

**Code**
```python
a = input()   # 5
b = input()   # 5
print(a + b)
print(int(a) + int(b))
```
**Output:** `55` → `10`

**Title:** 5 + 5 = 55?! 😱 Python Ka Sabse Common Bug | Type Casting EP 05 #shorts
**Description:** `input() hamesha string deta hai, isliye 5+5 = 55 aata hai 🤯 int() se fix karo. Python Basics EP 05. 👉 Next: Operators #python #typecasting #pythonbugs #learnpython #shorts`
**Tags:** `python type casting, int function python, python input bug, 5+5=55 python, python basics, python beginners mistakes, python hindi`

---

## EP 06: Operators

**Script**
1. Python ek super calculator bhi hai, aur iske paas kuch secret buttons hain!
2. Plus, minus, multiply, divide toh sabko pata hai.
3. Par double slash poora divide karta hai, aur percent remainder deta hai, jaise baanti hui toffee ke bache hue.
4. Dekho: 10 double slash 3 matlab 3, aur 10 percent 3 matlab 1.
5. Aur double star matlab power: 2 ki power 3, yaani 8!
6. Yeh operators har program ki neev hain!

**Code**
```python
print(10 / 3)
print(10 // 3)
print(10 % 3)
print(2 ** 3)
```
**Output:** `3.3333333333333335` · `3` · `1` · `8`

**Title:** Python Ke Secret Calculator Buttons 🧮 // % ** Explained | EP 06 #shorts
**Description:** `/ vs // vs % vs **: Python operators ka easy explanation 🧮 Python Basics EP 06. 👉 Next: f-strings #python #operators #pythonbasics #learnpython #shorts`
**Tags:** `python operators, floor division python, modulus python, power operator python, python basics, python hindi, learn python`

---

## EP 07: f-strings

**Script**
1. Print mein variables jodte-jodte thak gaye? Ek shortcut hai!
2. Isko kehte hain f-string. Bas quotes se pehle f lagao.
3. Jaise fill-in-the-blanks: khaali jagah pe value apne aap bhar jaati hai.
4. Dekho: f, quotes, aur curly brackets mein name aur marks.
5. Run karo, aur Python poora sentence bana deta hai!
6. Clean code, kam mehnat. Pro programmers yahi use karte hain!

**Code**
```python
name = "Riya"
marks = 95
print(f"{name} ne {marks} marks laaye")
```
**Output:** `Riya ne 95 marks laaye`

**Title:** Python f-string Trick Jo Pros Use Karte Hain 😎 | EP 07 #shorts
**Description:** `f-string = Python ka fill-in-the-blanks ✍️ Variables ko text mein easily jodo. Python Basics EP 07. 👉 Next: if-else #python #fstring #pythontips #learnpython #shorts`
**Tags:** `python f string, f-string python, string formatting python, python print tricks, python basics, python hindi, learn python`

---

## EP 08: if-else

**Script**
1. Kya aapka code khud decision le sakta hai? Haan, if-else se!
2. if matlab: agar condition sach hai, toh yeh karo. Warna else waala kaam karo.
3. Jaise: agar baarish ho rahi hai, toh chhata lo. Warna mat lo.
4. Dekho: age barabar 18. Agar age 18 ya usse zyada hai, toh "Vote kar sakte ho".
5. Run karo, aur Python ne khud decide kar liya!
6. Har smart app ke andar, yahi if-else chal raha hai!

**Code**
```python
age = 18
if age >= 18:
    print("Vote kar sakte ho")
else:
    print("Abhi nahi")
```
**Output:** `Vote kar sakte ho`

**Title:** Code Jo Khud Decision Le 🤔 Python if-else | EP 08 #shorts
**Description:** `if-else = agar aisa hai toh yeh, warna woh ☔ Python Basics EP 08, decisions in code. 👉 Next: elif #python #ifelse #pythonbasics #learnpython #shorts`
**Tags:** `python if else, if else in python, python conditions, python basics, python for beginners, python hindi, learn python`

---

## EP 09: elif

**Script**
1. Do se zyada options ho toh? Tab aata hai elif!
2. elif matlab "else if": ek ke baad ek condition check karo.
3. Jaise result card: 90 se upar A, 75 se upar B, 50 se upar C.
4. Dekho: marks barabar 82. if, elif, elif, aur aakhir mein else.
5. Run karo… Grade B! Python pehli sach condition pe ruk jaata hai.
6. Ab aap grade calculator bana sakte ho!

**Code**
```python
marks = 82
if marks >= 90:
    print("Grade A")
elif marks >= 75:
    print("Grade B")
elif marks >= 50:
    print("Grade C")
else:
    print("Fail")
```
**Output:** `Grade B`

**Title:** Python Mein Grade Calculator 📝 elif Explained | EP 09 #shorts
**Description:** `elif se multiple conditions check karo, aur 30 second mein grade calculator ready 📝 Python Basics EP 09. 👉 Next: and / or / not #python #elif #pythonprojects #learnpython #shorts`
**Tags:** `python elif, if elif else python, grade calculator python, python basics, python for beginners, python hindi, learn python`

---

## EP 10: and / or / not

**Script**
1. Club mein entry ke liye age bhi chahiye aur ID bhi. Python mein yeh kaise likhein?
2. Iske liye hain logical operators: and, or, not.
3. and: dono sach hone chahiye. or: ek bhi sach chalega. not: ulta kar deta hai.
4. Dekho: if age 18 se zyada and has_id True.
5. Run karo… Entry allowed! ID nahi hoti toh, entry band.
6. Teen chhote words, aur aapka code ho gaya smart!

**Code**
```python
age = 20
has_id = True
if age >= 18 and has_id:
    print("Entry allowed")
else:
    print("Entry band")
```
**Output:** `Entry allowed`

**Title:** Python and / or / not 🚪 Club Entry Example | EP 10 #shorts
**Description:** `and = dono sach, or = ek bhi sach, not = ulta 🔁 Python Basics EP 10, logical operators made easy. 👉 Next: while loop #python #logicaloperators #pythonbasics #learnpython #shorts`
**Tags:** `python and or not, logical operators python, python conditions, python basics, python for beginners, python hindi, learn python`

---

## Episodes 11–30: hooks to build on

| # | Topic | Hook line | Analogy |
|---|---|---|---|
| 11 | while loop | "Ek line ko 100 baar likhna hai? Ek loop kaafi hai!" | Alarm snooze, jab tak uth na jao |
| 12 | for + range() | "1 se 10 tak ginti, sirf 2 lines mein!" | Roll call |
| 13 | break & continue | "Loop ko beech mein rokna ho toh?" | Lift ka emergency stop |
| 14 | Strings | "Python ke liye aapka naam bas characters ki line hai" | Beads ki maala |
| 15 | upper / title / len | "Text ko ek line mein CAPITAL karo!" *(the reference's own trick, in your style)* | Auto-correct |
| 16 | Slicing | "Naam ka sirf pehla letter kaise nikaalein?" | Pizza slice |
| 17 | Lists | "100 variables? Nahi! Ek list!" | Shopping list |
| 18 | List methods | "append, remove, sort: list ke superpowers" | Playlist edit karna |
| 19 | Tuples | "Aisi list jo kabhi badal nahi sakti!" | Aadhaar number |
| 20 | Nested loops | "Code se star pattern banao ⭐" | Seats ki rows aur columns |
| 21 | Sets | "Duplicates hatao, ek line mein!" | Unique stamps collection |
| 22 | Dictionaries | "Python ki apni phonebook!" | Contacts app |
| 23 | Functions | "Code baar-baar likhna band karo!" | Maggi recipe, ek baar seekho, baar baar banao |
| 24 | return | "Function se answer wapas kaise lein?" | ATM se paisa |
| 25 | Default args | "Value na do, phir bhi chalega!" | Chai mein default cheeni |
| 26 | lambda | "Ek line ka function!" | Sticky note |
| 27 | try / except | "Program crash hone se bachao!" | Helmet |
| 28 | File handling | "Python se file likho aur padho" | Diary |
| 29 | Modules & pip | "Doosron ka code free mein use karo!" | App Store |
| 30 | Number Guessing Game | "Ab tak ka sab kuch mila ke ek game banao 🎮" | Finale |

---

## Posting checklist (every episode)

- [ ] Hook in the **first 1.5 s**: the caption and first visual should *ask* something
- [ ] Captions stay inside the safe zone (top caption at y≈330; nothing important in the bottom 400 px or the right 150 px, where the Shorts buttons are)
- [ ] Title under 60 characters, with the keyword in front, `#shorts` at the end
- [ ] Code pasted in the description (people copy it, which helps retention and saves)
- [ ] Pinned comment with a question (drives comments)
- [ ] The end card names the next episode, so viewers come back for the series
- [ ] Add each video to a **"Python Basics (Hinglish)"** playlist and turn on *Related video* → previous episode
- [ ] Thumbnail frame: pick the slam frame (Python / POWER!) as the Shorts cover
