# Reference decode: "How does Swiggy deliver your order?"

The reference is 720×1280, 30 fps, 90.9 s. I measured it with a 1 fps contact sheet, scene detection and EBU R128 loudness.

| Element | What the reference does |
|---|---|
| **Format** | A talking head (presenter to camera) used as the spine, cut with full-screen B-roll: phone close-ups, 3D tech renders, and flat illustrations (a scooter rider on a teal gradient). |
| **Cuts / pacing** | **22 hard cuts in 91 s**, so a new shot every ~4 s. Between cuts it's a jump-cut style **punch-in**: the same shot reframed tighter or wider so the energy never drops. |
| **Structure graphics** | **"STEP-1 / PLACE ORDER"** lower thirds: a small **yellow** "STEP-N" over a **white bold caps** title, bottom-centre, typing on letter by letter. There are 4 steps, which makes the explainer feel like a checklist. |
| **Keyword wheel** | A **yellow vertical scrolling list** (Restaurant → Items → Location → Payment; Location → Time → Estimated time). The current word is bright and the neighbours fade above and below, like a slot machine. |
| **Pop-up stickers** | A confused cartoon person with **???**, an **electric glowing "?"**, a button being clicked (**"Place order" → "Placed ✨"**, **ACCEPT** with a cursor), a full white **"✓ Yay! Order Received"** card, and an API ↔ server diagram. |
| **Transitions** | **Warm light-leak flashes** (orange/pink washes) on section changes, plus hard cuts. |
| **Music / SFX** | An upbeat bed under the voice (-19.5 LUFS integrated), with whooshes and pops on graphics and clicks on the button animations. |

# How it's applied to `Python_ki_Pathshala_EP01_Short_25s.mp4`

Your 25 s cut is kept exactly as it is (same content and timing). The Swiggy-style layer goes on top:

| Time | Added |
|---|---|
| 0.0–4.6 | **Confused mascot with ??? pops up** on *"ek common cheez"*, plus a **snap punch-in** on the *Python!* slam |
| 4.6 | **Light leak** + whoosh/shimmer → reframed tighter (jump-cut feel) |
| 4.95 | **STEP-1 · PROGRAMMING LANGUAGE** typed on (with tick sounds) |
| 8.9 | Light leak → **electric glowing "?"** with crackle on *"Iski sabse badi khoobi?"* |
| 9.25 | **STEP-2 · ENGLISH JAISI SIMPLE**, plus a punch-in on the *Beginners* stamp |
| 14.43 | Light leak → **STEP-3 · PYTHON SE KYA BANTA HAI?** |
| 16.2–21.2 | **Yellow keyword wheel** rolls *Websites → AI & Chatbots → Games → Automation* in sync with the tiles |
| 21.4 | Light leak → **STEP-4 · PYTHON KI POWER**, a punch-in and **sparkles** on POWER! |
| 23.65 | The old "@The IOT Engineer" card is replaced by the **animated Python ki Pathshala end screen** (Like → Liked +1, Subscribe → Subscribed with a bell, *NEXT VIDEO: EP 02 Variables*, *"Kal milte hain!"*), joined with a crossfade and a light leak |

**Framing:** sections alternate between 100 % and 105–106 % zoom with a slow drift, so every section change feels like a new camera cut.

**Audio:** your original track, plus whoosh + shimmer on each light leak, pops and type-on ticks for the labels, whoosh-pops for the wheel, a crackle for the electric "?", and a shimmer for the sparkles. The end screen has its own clicks, ding and bell, over a short outro bed in the same key and tempo as the episode music. Master: **-14.4 LUFS, -0.8 dBFS peak**. Final length: **28.65 s**, 1080×1920, 30 fps.

## Rebuild

```bash
python3 edit8/build_swiggy_style.py
```
