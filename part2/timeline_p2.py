"""Shared timeline for "Bolt's Spooky Tales Part 2: The Mystery of the Midnight Candy".

Everything is original: Bolt, Boo (the haunted bag), Granny Gloom and the
Wisplings. scene_p2.py, audio_p2.py and post_p2.py all read their timing here.
"""
FPS = 24
DURATION = 180.0
NFRAMES = int(DURATION * FPS)

# (start, end, name). One camera set-up per shot.
SHOTS = [
    (0.0, 4.0, "episode card"), (4.0, 9.0, "the wink"), (9.0, 15.0, "title"),
    (15.0, 21.0, "candy pile"), (21.0, 25.0, "midnight"), (25.0, 29.0, "yawn"),
    (29.0, 33.0, "candy vanishes"), (33.0, 37.0, "it's gone"), (37.0, 42.0, "footprints"),
    (42.0, 46.0, "let's follow"), (46.0, 48.0, "card WHO TOOK"), (48.0, 53.0, "graveyard"),
    (53.0, 57.0, "the claw"), (57.0, 61.0, "the house"), (61.0, 65.0, "the door"),
    (65.0, 67.0, "card THE CANDY"), (67.0, 72.0, "inside"), (72.0, 77.0, "the shadow"),
    (77.0, 81.0, "who are you"), (81.0, 86.0, "granny reveal"), (86.0, 91.0, "our candy"),
    (91.0, 97.0, "granny sorry"), (97.0, 103.0, "wisplings"), (103.0, 108.0, "boo remembers"),
    (108.0, 113.0, "bolt's idea"), (113.0, 115.0, "card TOGETHER"), (115.0, 119.0, "montage hic"),
    (119.0, 123.0, "montage parade"), (123.0, 127.0, "montage flight"), (127.0, 132.0, "pumpkins scared"),
    (132.0, 137.0, "the offer"), (137.0, 139.5, "fast: candy ring"), (139.5, 142.0, "fast: wisplings dance"),
    (142.0, 144.5, "fast: spin"), (144.5, 149.0, "group hug"), (149.0, 155.0, "the lesson"),
    (155.0, 160.0, "no feet"), (160.0, 164.0, "freeze"), (164.0, 170.0, "the eyes"),
    (170.0, 175.0, "part 3 card"), (175.0, 180.0, "final gag"),
]

# Joins between shots, applied in post: cut | whip | flash | dip | trunk | glitch
TRANSITIONS = {4.0: "glitch", 9.0: "flash", 15.0: "dip", 21.0: "trunk", 37.0: "whip",
               46.0: "dip", 48.0: "dip", 57.0: "flash", 65.0: "dip", 67.0: "dip",
               81.0: "whip", 113.0: "dip", 115.0: "flash", 119.0: "whip", 123.0: "whip",
               137.0: "whip", 139.5: "whip", 142.0: "whip", 160.0: "cut", 164.0: "trunk",
               170.0: "dip", 175.0: "dip"}

# Trailer-style gold text cards (start, end, text) drawn full-frame in post.
CARDS = [(46.15, 47.9, "WHO TOOK"), (65.15, 66.9, "THE CANDY?"), (113.15, 114.9, "TOGETHER")]

# Dialogue: (start, who, line). Voices: bolt (robot), boo (giggly ghost),
# granny (crackly old ghost), shadow (granny, deep and distorted).
LINES = [
    (5.0, "boo", "Hehe!"),
    (33.4, "bolt", "Our candy! It's GONE!"),
    (39.6, "boo", "Ooooh..."),
    (42.4, "bolt", "Come on, Boo! Let's follow them!"),
    (53.7, "boo", "EEEEK!"),
    (74.4, "shadow", "WHO'S THERE?"),
    (77.3, "bolt", "We're looking for our candy!"),
    (81.7, "granny", "Oh my! Visitors! Come in, dearies!"),
    (86.6, "boo", "Our candy!"),
    (88.5, "bolt", "You took it?"),
    (91.6, "granny", "I'm sorry. I only took it for the little ones."),
    (97.6, "granny", "Nobody shares with them. Everyone thinks they're too spooky."),
    (108.3, "bolt", "Then let's share with EVERYONE!"),
    (110.6, "bolt", "We can't do it alone... but TOGETHER we can!"),
    (127.8, "bolt", "They're not scary. They're just little!"),
    (149.4, "granny", "Thank you, dearies. Sharing makes everything sweeter."),
    (155.3, "bolt", "Wait... Granny, you float."),
    (157.6, "bolt", "Ghosts don't have FEET!"),
    (176.4, "bolt", "HEY!"),
]

# Story-book captions in the lower letterbox bar (start, end, text): narration
# plus the dialogue, so young viewers can read along.
NARRATION = [
    (15.3, 20.8, "Bolt and Boo had the biggest candy pile in the whole forest."),
    (21.3, 24.8, "Then... the clock struck midnight."),
    (29.2, 32.8, "Pop... pop... POP!"),
    (37.3, 41.8, "Glowing footprints led into the fog."),
    (48.3, 52.8, "They followed the footprints past the old graveyard..."),
    (57.3, 60.8, "...all the way to the haunted house."),
    (67.3, 71.8, "Inside, it was very, very quiet."),
    (103.3, 107.8, "Boo remembered how it felt to be left out."),
    (115.3, 126.8, "So everyone worked together."),
    (132.3, 136.8, "A tiny Wispling shared the very first candy."),
    (160.3, 163.8, "..."),
    (164.3, 169.8, "So who made the footprints?"),
]

# Story-poem narrator (spoken + captioned): (start, latest end, text). Rhyming
# couplets placed in the gaps between dialogue so kids can follow along.
NARRATOR = [
    (0.4, 3.7, "Welcome back to Bolt's Spooky Tales,"),
    (6.45, 9.0, "where the moon shines bright, and the wind wails!"),
    (10.0, 14.7, "Today's story is called... The Mystery of the Midnight Candy!"),
    (15.4, 20.9, "Bolt and Boo had a candy pile, so big and so tall, the yummiest pile of all!"),
    (21.4, 24.9, "Then the old clock struck midnight... bong, bong, bong!"),
    (25.4, 28.8, "Bolt gave a yawn... but something was wrong!"),
    (29.4, 33.2, "Pop, pop, POP! went the candy, one by one!"),
    (35.3, 37.1, "Who took the treats?"),
    (37.3, 39.4, "Glowing footprints... from mysterious feet!"),
    (46.2, 47.9, "Who took..."),
    (48.3, 52.9, "Past the old graveyard they crept, oh so slow,"),
    (55.2, 56.9, "Just a branch! Silly Boo!"),
    (57.8, 60.9, "to a creepy old house where the cold winds blow."),
    (61.4, 64.9, "Cree-eak went the door... and in they go!"),
    (65.2, 66.9, "...the candy?"),
    (67.3, 71.9, "Inside, it was quiet... as quiet as can be."),
    (95.1, 97.4, "Granny wasn't greedy. Her heart was kind."),
    (103.1, 107.9, "Boo remembered being left out... and left behind."),
    (115.5, 118.9, "Bolt and Boo shared their candy, one, two, three,"),
    (119.3, 122.9, "and the little Wisplings giggled with glee!"),
    (123.3, 127.6, "Up, up they flew, through the starry night sky!"),
    (130.5, 136.9, "A tiny Wispling shared the very first sweet, and the pumpkins smiled. What a wonderful treat!"),
    (137.3, 140.6, "Sharing is caring, and caring is fun,"),
    (140.8, 144.4, "there's always enough when we share with everyone!"),
    (144.7, 149.2, "A great big hug, for the big and the small!"),
    (160.3, 163.9, "Hmm... if Granny floats... and has no feet..."),
    (164.4, 168.4, "...then WHO made those glowing footprints?"),
    (170.4, 174.8, "Find out in Part Three... if you dare!"),
]
