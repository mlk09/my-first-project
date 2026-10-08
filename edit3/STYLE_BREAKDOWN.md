# Robot and the Haunted Bag: style breakdown and edit

## The reference: `Screenrecorder-2026-10-08-18-27-40-737.mp4`

The reference is a 21.3 s screen recording (on `main`) of a cinematic CG short: a moss-covered robot in a sunlit forest, a little yellow bird building a nest, and a woodpecker. I measured it with ffmpeg scene detection, contact sheets at 1.5 fps and 4 fps, a spectrogram and EBU R128 loudness.

| Element | What the reference does |
|---|---|
| **3D animation** | Fully CG, in a feature-film look: soft volumetric god-rays, very shallow depth of field, rich foliage, appealing characters with big readable eyes. The story is told by expressions and gestures, with no dialogue. |
| **Framing** | Letterboxed **2.39:1** with black bars top and bottom. Close-ups alternate with wides, and foreground leaves frame the subject. |
| **Camera / motion** | Slow, continuous moves on every shot (push-ins, gentle pans, a sideways truck). The picture is never static, and there are no shaky-cam or crash zooms. |
| **Cuts / pacing** | 8 shots in 21.3 s (cuts at 1.6, 5.7, 8.1, 11.2, 12.2, 15.5 and 18.3 s), so about **2.7 s per shot**. The cutting follows the action, cutting from the bird to the robot's reaction to the bird again. |
| **Transitions** | Mostly hard cuts on action. It ends on a **foreground-occlusion wipe**: the camera trucks sideways until a tree trunk fills the lens. |
| **Captions** | None. The visuals carry the story. |
| **Music** | A soft orchestral bed that swells on reveals (strings and woodwinds), with dynamics left in (−19.5 LUFS, LRA 8.2 LU). |
| **SFX** | Detailed foley: birdsong (falling chirps in the spectrogram), woodpecker taps, mechanical servo whirrs on every robot move, and a forest ambience bed. |

## How it was applied: `output/Robot-and-the-Haunted-Bag-3D.mp4`

**Your content.** The raw clip (`Screenrecorder-2026-10-08-17-57-24-640.mp4`, 0.59 s) is a screen recording of your Short *"Robot and the Haunted Bag"* (@Cadd123-q2t). Its title card is the opening beat: it glitches in at 0:06 and is replaced by the 3D title. The 3-minute story grows out of that title, about a little robot and a haunted bag, told for kids.

**The 3D.** Everything is built and animated from scratch in Blender (`scene3d.py`, about 2,000 lines, with no downloaded models):
- **Bolt**, a little robot with a screen face, expressive eyes (blink, surprised, scared, squint, ^^ happy), a lamp antenna, a rolling ball wheel and posable arms
- **the haunted bag**, a patched burlap sack with glowing eyes, a jagged grin, squash-and-stretch, a tear and a rim glow that turns from haunted green to friendly lilac
- **the set**, a misty forest with about 200 procedurally grown spooky trees, a graveyard with a broken fence, 17 jack-o'-lanterns, the haunted house on the hill, an owl tree, the moon, bats, fireflies, candy and hearts.

| Reference trait | In this edit |
|---|---|
| CG short, no dialogue | Fully 3D and told visually. Bolt "speaks" in robot beeps, and short storybook captions guide young viewers. |
| 2.39:1 letterbox | Rendered at 2.39:1 and letterboxed into 1920×1080. Captions sit **inside the lower bar**, so the picture stays clean. |
| Slow camera moves, shallow DOF | All 44 shots move (push-ins, orbits, crane-ups, tracking shots), with depth of field on every close-up. |
| ~2.7 s cutting on action | 44 shots in 180 s (about 4 s each, a little longer so kids can read the captions), cutting on action and reaction. |
| Foreground-occlusion wipe | Two trunk wipes (1:52 and 2:46), plus whip pans in the chase, dips to black between acts, a lightning flash, and a white flash on the *HIC!* gag. |
| Feature-film grade | Bloom, a teal-shadow and warm-highlight split-tone, a soft S-curve, a vignette and fine film grain (`build_final.py`). |
| Orchestral bed + foley | An original score synthesised in `make_audio.py`. The tiptoe pizzicato theme is Bolt's theme, in D minor for the spooky half and **D major** once they become friends. Under it: theremin, choir and brass hits for the haunting, a double-time chase, a heartbeat while Bolt hides, and a sad music box. |
| Detailed SFX | Wind, crickets, owl hoots, bats, wheel rolls, servo whirrs, Bolt's beeps, the bag's rustle, *WOOOO*, thunder, pumpkins igniting, whooshes, the *HIC!*, candy pops, a slide whistle, sparkles, and window chimes. |

Loudness is normalised to **−14 LUFS** (YouTube's target).

### Story (3:00)

| Time | Beat |
|---|---|
| 0:00 | Crane down from the moon through the branches; bats cross the moon. |
| 0:06 | Your Short's title card glitches in, then the 3D title **ROBOT AND THE HAUNTED BAG** glows in the fog. |
| 0:12 | Bolt's lamp appears in the fog. *"One foggy night, little robot Bolt was rolling home..."* |
| 0:21 | Owl eyes blink in a hollow tree. Bolt jumps. |
| 0:25 | He rolls past the graveyard and through the pumpkin patch. |
| 0:30 | He finds an old patched bag on a stump. *"Hmm? Hello, little bag?"* He pokes it, and it twitches. |
| 0:50 | The bag rises in front of the moon, its eyes snap open, lightning strikes. *"But the bag was... HAUNTED!"* |
| 0:59 | *"WOOOOO!"* The jack-o'-lanterns light up in a wave. |
| 1:04 | Bolt spins and runs, and the chase goes through the pumpkins into the graveyard. |
| 1:19 | Bolt hides behind a gravestone while the bag searches... closer... and closer... |
| 1:37 | *HIC!* The bag hiccups out a shower of candy, and one lands on Bolt's head (it stays there to the end). |
| 1:46 | The bag sinks down, sad. *"The bag wasn't scary at all. It was just lonely."* A tear falls. |
| 1:58 | Bolt rolls over and holds out his hand. *"Don't be sad. I'll be your friend!"* |
| 2:09 | The biggest hug, with hearts. The bag shares all its candy, which circles them like a ring. |
| 2:20 | The bag lifts Bolt and they fly over the glowing pumpkin patch, then a happy spin. |
| 2:34 | They head home together, and the haunted house lights up warm, window by window. |
| 2:51 | **THE END...?** The bag turns to the camera and winks. Subscribe card. |

## Files

| File | What it does |
|---|---|
| `timeline.py` | Shared timing: cuts, transitions, captions and story beats. |
| `scene3d.py` | Builds, animates and renders the whole 3D film (Blender `bpy`, Eevee). |
| `make_audio.py` | Synthesises the score and all SFX (numpy/scipy). |
| `build_final.py` | Grade, letterbox, transitions, raw-clip glitch, captions and encode. |
| `assets/fonts/` | Creepster and Fredoka (SIL Open Font License). |

### Rebuild on your laptop (RTX 5050)

```bash
pip install bpy==5.2.2 numpy scipy pillow     # Python 3.13 for bpy 5.2
# 3D frames (Eevee uses your RTX GPU). On a GPU you can afford real shadow maps
# and more samples; two terminals running the same command share the work.
python3 edit3/scene3d.py --frames 0 4320 --samples 16 --shadows
python3 edit3/make_audio.py
python3 edit3/build_final.py
```

This session ran in a cloud container with **no GPU**. The frames in `output/` were rendered on its CPU, with Eevee on Mesa's llvmpipe at 1280×536 and 5 samples. That's why it uses soft contact shadows instead of shadow maps (shadow maps cost about 3 s/frame on a CPU). On your RTX 5050 the same script renders far faster, so re-render with `--samples 16 --shadows` (and `--pct 150` for native 1920×804) to get a sharper, fully shadowed version.
