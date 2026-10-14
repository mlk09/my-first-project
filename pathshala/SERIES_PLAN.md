# Python Ki Pathshala — Python Basics series (Facebook Reels / YouTube Shorts)

**Format for every episode:** 20–25 s, 9:16, Hinglish voice-over, light theme (cream background, dark navy captions, yellow keyword highlight), with the same motion and sound kit as EP01: a hook in the first 1 s → a problem → a beat drop on the answer → a code example → a ✓ → a "NEXT EP + FOLLOW" end card that loops back to the hook.

**Teaching rule:** one concept per reel, one real-life Indian example (chai, cricket, mausam, marks, UPI), one runnable line of code on screen, and the output shown on screen.

## Full roadmap (30 episodes, ~5 weeks of daily posting)

### Module 1 — Shuruaat (Getting started)
| EP | Title | Hook (first line) | Code on screen |
|---|---|---|---|
| 01 | Python kya hai? ✅ *made* | "Computer sirf 0 aur 1 samajhta hai!" | `if mausam == "barish": print(...)` |
| 02 | print() — Pehla code | "Ek line likho, computer bolega!" | `print("Namaste Duniya!")` |
| 03 | Python install / online kaise chalayein | "Laptop nahi hai? Phone pe bhi Python!" | Online editor + `print(2+3)` |
| 04 | Comments `#` | "Code mein secret note kaise likhein?" | `# yeh computer ignore karega` |
| 05 | Variables | "Variable = ek dabba jismein naam likha ho" | `naam = "Rahul"` |

### Module 2 — Data ke types
| EP | Title | Hook | Code |
|---|---|---|---|
| 06 | Data types: int, float, str, bool | "Har cheez ka ek type hota hai!" | `type(10)` |
| 07 | input() — user se poochho | "Computer tumse sawaal poochhega!" | `naam = input("Naam?")` |
| 08 | Type casting | "'5' + '5' = 55?! 😱" | `int("5") + 5` |
| 09 | Math operators | "Python = sabse tez calculator" | `10 // 3`, `10 % 3`, `2 ** 10` |
| 10 | f-strings | "Text mein variable kaise ghusayein?" | `f"Hello {naam}"` |
| 11 | String tricks | "Naam ko CAPITAL mein badlo, 1 line mein" | `.upper()`, `.replace()` |
| 12 | Indexing & slicing | "Python 0 se ginti kyun karta hai?" | `naam[0]`, `naam[::-1]` |

### Module 3 — Decision lena
| EP | Title | Hook | Code |
|---|---|---|---|
| 13 | Comparison operators | "Computer haan/na kaise bolta hai?" | `5 > 3 → True` |
| 14 | if / else | "Barish ho toh chhata, warna chashma!" | `if ... else` |
| 15 | elif — marks se grade | "90 pe A, 75 pe B… Python decide karega" | `elif marks >= 75:` |
| 16 | and / or / not | "Paisa AUR time dono ho toh hi movie!" | `if paisa and time:` |
| 17 | Indentation | "Ek space ki galti, poora code fail!" | IndentationError demo |

### Module 4 — Loops
| EP | Title | Hook | Code |
|---|---|---|---|
| 18 | for loop | "100 baar 'Sorry' likhna hai? 1 line!" | `for i in range(100):` |
| 19 | range() | "range(1, 11) mein 11 kyun nahi aata?" | `range(start, stop, step)` |
| 20 | while loop | "Jab tak sahi password nahi, tab tak!" | `while pwd != "1234":` |
| 21 | break & continue | "Loop ko beech mein kaise rokein?" | `break` / `continue` |
| 22 | Table generator project | "Kisi bhi number ka pahada 2 sec mein" | `for i in range(1,11): print(n*i)` |

### Module 5 — Collections
| EP | Title | Hook | Code |
|---|---|---|---|
| 23 | List | "Ek variable mein 100 cheezein!" | `fruits = ["aam", "kela"]` |
| 24 | List methods | "Shopping list mein add/remove" | `.append()`, `.remove()` |
| 25 | Tuple | "List jo kabhi badal nahi sakti" | `(lat, long)` |
| 26 | Dictionary | "Python ki phonebook!" | `{"Rahul": 98765}` |
| 27 | Set | "Duplicate hatao, 1 line mein" | `set([1,1,2])` |

### Module 6 — Functions + mini projects
| EP | Title | Hook | Code |
|---|---|---|---|
| 28 | Functions `def` | "Code ko baar baar mat likho!" | `def greet(naam):` |
| 29 | return vs print | "Beginners ki sabse badi galti!" | `return a + b` |
| 30 | Project: Number guessing game | "10 line mein apna game banao!" | `random.randint(1, 10)` |

After EP30: Module 7 (errors & try/except), Module 8 (files), Module 9 (mini projects: calculator, password generator, QR code, WhatsApp-style automation, ChatGPT-style chatbot basics).

---

## Full scripts — EP01 to EP05

Each script uses the EP01 beat grid (128 BPM). Timings are approximate. **Bold** = the word highlighted on a yellow box in the caption.

### EP01 — Python kya hai? (made: `ep01-python-kya-hai/`)
See `ep01-python-kya-hai/README.md` for the full timeline.

### EP02 — print(): Pehla code (≈24 s)
| Time | Voice-over (Hinglish) | Visual / motion | SFX |
|---|---|---|---|
| 0–2.5 | "Ek line likho… aur computer **bolega**!" | A blank screen; a cursor blinks, then "Namaste!" bursts out in a speech bubble from the monitor | pop + whoosh |
| 2.5–5 | "Python ka pehla magic word hai…" | The camera creeps in, the filter closes, a riser plays | riser, snare roll |
| 5–6.5 | "**print**!" | DROP: flash + rays, a giant `print()` sticker | impact |
| 6.5–11 | "print ke brackets mein jo bhi **quotes** mein likhoge, woh screen pe dikhega." | The editor types `print("Namaste Duniya!")`; the quotes glow yellow; the terminal output slides up | typing ticks, ding |
| 11–15 | "Numbers ke liye quotes **nahi** chahiye — print(2 + 3) dega 5!" | Split: `print("2+3")` → 2+3 ✗ vs `print(2+3)` → 5 ✓ | ding / buzz |
| 15–19 | "Ek se zyada cheezein? **Comma** lagao!" | `print("Score:", 100)` → Score: 100; the comma bounces | pop |
| 19–22 | "Bas! Tumne apna pehla Python code likh diya — **congrats**!" | Confetti, "LEVEL 1 ✓" badge | impact |
| 22–24 | "Next: **Variables**. Follow karo!" | End card NEXT • EP 03, cursor clicks FOLLOW | click |

### EP03 — Python kahan chalayein? (Laptop nahi? No problem) (≈23 s)
| Time | Voice-over | Visual | SFX |
|---|---|---|---|
| 0–2.5 | "Laptop **nahi** hai? Phone pe bhi Python chalta hai!" | A phone pops in, a Python badge lands on its screen | pop |
| 2.5–5 | "Teen easy tarike hain…" | Three empty slots 1-2-3 | riser |
| 5–9 | "Ek: **online editor** — browser kholo, code likho, Run dabao." | A browser card, a Run button press, the output appears | click, ding |
| 9–13 | "Do: phone pe **Pydroid** jaisi app." | A phone mock-up with an editor | whoosh |
| 13–18 | "Teen: laptop pe python.org se **install** — 'Add to PATH' tick karna mat bhoolna!" | The installer checkbox gets a big tick, a red arrow points to it | ding |
| 18–21 | "Test karo: **print(2+3)** — 5 aaya? Ready ho!" | Terminal output 5 ✓, confetti | impact |
| 21–23 | "Next: **Comments**. Follow karo!" | End card | click |

### EP04 — Comments `#`: Code ke secret notes (≈22 s)
| Time | Voice-over | Visual | SFX |
|---|---|---|---|
| 0–2.5 | "Code mein **secret note** kaise likhein?" | A sticky note flies onto the code card | whoosh |
| 2.5–5 | "Jo computer **padhe hi nahi**…" | The computer wears sunglasses and ignores it 😎 | riser |
| 5–6.5 | "**Hash** sign se!" | DROP: a giant `#` slam | impact |
| 6.5–11 | "# ke baad jo bhi likho, Python use **ignore** karta hai." | `# yeh line skip` turns gray; `print("Hi")` runs | typing, ding |
| 11–16 | "Comments tumhare **future self** ke liye hain — 6 mahine baad code samajh aayega." | A calendar flips 6 months; a confused face → ✓ | flip, pop |
| 16–20 | "Pro tip: kisi line ko band karna ho? Uske aage # laga do." | A line gets "commented out", the output changes | click |
| 20–22 | "Next: **Variables** — Python ka dabba. Follow!" | End card | click |

### EP05 — Variables: Python ka dabba (≈24 s)
| Time | Voice-over | Visual | SFX |
|---|---|---|---|
| 0–2.5 | "Python ki **memory** kaise kaam karti hai?" | A brain icon → a row of empty boxes | pop |
| 2.5–5 | "Socho ek dabba, jis pe **naam** likha ho…" | A box with a label sticker drops in | thud, riser |
| 5–6.5 | "Yahi hai **variable**!" | DROP: the box opens, rays | impact |
| 6.5–11 | "naam = 'Rahul' — ab 'naam' wale dabbe mein Rahul **store** ho gaya." | "Rahul" flies into the box labelled naam | whoosh, ding |
| 11–15 | "Dabba **badal** bhi sakta hai: naam = 'Priya'." | Rahul pops out, Priya goes in | pop, pop |
| 15–20 | "Rules: naam number se **shuru nahi**, aur space nahi — underscore use karo." | `1naam ✗`, `mera naam ✗`, `mera_naam ✓` | buzz, buzz, ding |
| 20–22 | "Ab print(naam) likho — **Priya**!" | Terminal output | ding |
| 22–24 | "Next: **Data types**. Follow karo!" | End card | click |

---

## Posting kit — titles, descriptions, hashtags

**Hashtag set (use 5–8 per reel; mix 2 broad, 3 niche, 1–2 brand):**
Broad: `#Python #Coding #Programming #LearnToCode #Reels`
Niche/Hinglish: `#PythonInHindi #PythonForBeginners #CodingInHindi #HinglishCoding #PythonTutorial #CodingForBeginners #ComputerScience #StudentsOfIndia #BTech #BCA #Class11 #Class12`
Brand: `#PythonKiPathshala #RozKaPython`

### EP01 — Python kya hai?
**Title / reel caption line:** Python kya hai? 🐍 25 second mein samjho! | EP 01
**Description:**
> Computer sirf 0 aur 1 samajhta hai… toh hum usse baat kaise karein? 🤔
> Jawab: PYTHON! 🐍
> Python ek programming language hai jisse hum computer ko kaam bolte hain — aur yeh bilkul English jaisi simple hai.
> Isse bante hain Websites 🌐 AI 🤖 Data 📊 Automation ⚙️
> 👉 Roz ek naya Python concept — Python Ki Pathshala ko FOLLOW karo!
> Next: EP 02 — print() se pehla code ✍️
> 💬 Comment karo: tum Python kyun seekhna chahte ho?

**Hashtags:** `#Python #PythonInHindi #PythonForBeginners #CodingInHindi #LearnToCode #Programming #PythonKiPathshala #Reels`

**Pinned comment:** "📌 Python Basics series — roz 1 episode. Kal EP02: print()! Notifications ON kar lo 🔔"

### EP02 — print(): Pehla code
**Title:** Apna PEHLA Python code likho — sirf 1 line! ✍️ | EP 02
**Description:**
> print() Python ka pehla magic word hai ✨
> print("Namaste Duniya!") → screen pe Namaste Duniya!
> Text ke liye quotes " " lagao, numbers ke liye nahi.
> Try karo aur output comment mein likho 👇
> Next: EP 03 — Python kahan chalayein (phone pe bhi!)
> Follow Python Ki Pathshala 🐍

**Hashtags:** `#Python #PrintFunction #PythonForBeginners #PythonInHindi #CodingInHindi #FirstCode #PythonKiPathshala #Reels`

### EP03 — Python kahan chalayein?
**Title:** Laptop nahi hai? Phone pe Python chalao! 📱🐍 | EP 03
**Description:**
> Python seekhne ke liye mehenga laptop zaroori nahi!
> 1️⃣ Online editor (browser) 2️⃣ Phone app 3️⃣ Laptop pe python.org
> ⚠️ Install karte waqt "Add to PATH" tick karna mat bhoolna!
> Test: print(2+3) → 5 ✅
> Next: EP 04 — Comments #
> Follow karo — roz ek naya concept 🚀

**Hashtags:** `#Python #PythonInstall #CodingOnPhone #PythonForBeginners #PythonInHindi #LearnToCode #PythonKiPathshala #Reels`

### EP04 — Comments
**Title:** Code mein SECRET note kaise likhein? 🤫 # | EP 04
**Description:**
> # ke baad jo bhi likho — Python ignore kar deta hai!
> Comments = tumhare future self ke liye notes 📝
> Pro tip: kisi line ko temporarily band karna ho toh aage # laga do.
> Next: EP 05 — Variables (Python ka dabba 📦)
> Follow Python Ki Pathshala 🐍

**Hashtags:** `#Python #PythonComments #CleanCode #PythonForBeginners #CodingInHindi #ProgrammingTips #PythonKiPathshala #Reels`

### EP05 — Variables
**Title:** Variable = Python ka DABBA 📦 | EP 05
**Description:**
> naam = "Rahul" → 'naam' naam ke dabbe mein Rahul store ho gaya!
> Dabba badal bhi sakta hai: naam = "Priya" ✅
> Rules: ❌ 1naam ❌ mera naam ✅ mera_naam
> Quiz: x = 5, x = x + 2, print(x) → output kya hoga? Comment karo 👇
> Next: EP 06 — Data Types
> Follow karo 🐍🚀

**Hashtags:** `#Python #PythonVariables #PythonForBeginners #PythonInHindi #CodingInHindi #LearnToCode #PythonKiPathshala #Reels`

### Title formula for EP06–EP30
`[Curiosity hook or emoji] + [concept in plain Hinglish] + | EP xx`
Examples: "'5' + '5' = 55?! 😱 Type Casting | EP 08" · "100 baar Sorry, 1 line mein 🔁 for loop | EP 18" · "Beginners ki SABSE BADI galti ❌ return vs print | EP 29"
