"""Shared timeline for "Robot and the Haunted Bag" (pure Python, no bpy).

scene3d.py (3D), make_audio.py (music + SFX) and build_final.py (post, captions)
all read their timing from here, so a change in one place moves everything.
"""
FPS = 24
DURATION = 180.0
NFRAMES = int(DURATION * FPS)

# Shot boundaries in seconds. One camera set-up per shot; cuts land exactly here.
CUTS = [0, 6, 12, 17, 21, 25, 30, 35, 39, 44, 47, 50, 55, 59, 61.5, 64, 68, 71,
        74, 79, 83, 88, 93, 97, 102, 106, 112, 118, 121, 124, 129, 134, 137, 140,
        143.5, 147, 150.5, 154, 156.5, 160, 163, 166, 171, 175, 180]

# How each cut is joined in post: 'cut' (hard cut), 'whip' (motion-blurred whip),
# 'flash' (white flash), 'dip' (dip to black), 'glitch' (raw clip glitch-in),
# 'trunk' (a dark tree trunk sweeps past the lens, like the reference's last cut).
TRANSITIONS = {
    6: "glitch", 12: "dip", 50: "cut", 64: "whip", 68: "whip", 74: "whip",
    97: "flash", 106: "dip", 112: "trunk", 140: "whip", 147: "whip", 154: "dip",
    166: "trunk", 171: "dip",
}

# Story-book captions shown in the lower letterbox bar (start, end, text).
CAPTIONS = [
    (17.3, 20.8, "One foggy night, little robot Bolt was rolling home..."),
    (30.6, 34.8, "...when he found an old, patched-up bag."),
    (35.6, 38.8, "\"Hmm? Hello, little bag?\""),
    (52.4, 54.9, "But the bag was... HAUNTED!"),
    (59.4, 63.8, "\"WOOOOOO!\""),
    (64.4, 67.8, "\"AAAH! RUN, BOLT, RUN!\""),
    (79.3, 82.8, "Bolt hid behind an old gravestone..."),
    (93.3, 96.8, "Closer... and closer..."),
    (97.6, 101.8, "*HIC!* ...CANDY?!"),
    (106.4, 111.8, "The bag wasn't scary at all. It was just lonely."),
    (118.4, 123.8, "So Bolt rolled over and held out his hand."),
    (124.4, 128.8, "\"Don't be sad. I'll be your friend!\""),
    (129.4, 133.8, "The bag gave him the biggest hug ever!"),
    (134.4, 139.8, "...and shared all its candy."),
    (160.4, 165.8, "From that night on, they were best friends."),
]

# On-screen story beats used by the audio score (seconds).
BEATS = {
    "bolt_enters": 12.0, "owl_eyes": 21.0, "found_bag": 30.6, "question": 35.5,
    "poke": 44.3, "twitch": 45.8, "jump_back": 47.0, "bag_rises": 50.0,
    "eyes_open": 51.5, "lightning": 52.2, "wooo": 59.5, "flee": 64.6,
    "hide": 78.5, "search": 83.0, "spotted": 90.5, "swoop": 93.0, "hic": 97.5,
    "candy_head": 101.5, "sad": 106.0, "offer": 118.0, "hope": 124.0,
    "hug": 129.5, "candy_ring": 134.0, "fly": 140.0, "land": 148.5,
    "walk_home": 154.0, "windows_warm": 156.6, "the_end": 171.0, "wink": 175.5,
}
