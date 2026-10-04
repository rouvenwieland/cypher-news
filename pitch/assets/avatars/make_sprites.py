#!/usr/bin/env python3
"""Zeichnet die 3 Pixel-Erklaerer (Jaro, Rufus, Ran) als 32x40-PNGs (zwei Frames: ruhig + sprechend). Aufruf: python3 make_sprites.py"""
import subprocess
SKIN = "#e8b98f"; DARK = "#1a1210"; MOUTH = "#8a4a3a"; MOUTH_OPEN = "#3a1510"; TEETH = "#f4efe6"
def sprite(name, shapes, talk):
    cmds = ["magick", "-size", "32x40", "xc:none", "-fill", "none"]
    for kind, color, box in shapes:
        cmds += ["-fill", color]
        x1, y1, x2, y2 = box
        cmds += ["-draw", f"rectangle {x1},{y1} {x2},{y2}"]
    # Mund
    if talk:
        cmds += ["-fill", MOUTH_OPEN, "-draw", "rectangle 14,16 17,18", "-fill", TEETH, "-draw", "rectangle 14,16 17,16"]
    else:
        cmds += ["-fill", MOUTH, "-draw", "rectangle 14,17 17,17"]
    out = f"{name}_talk.png" if talk else f"{name}.png"
    subprocess.run(cmds + ["-filter", "point", out], check=True)
    subprocess.run(["magick", out, "-filter", "point", "-resize", "400%", f"preview_{out}"], check=True)

def base(shirt, pants, extra_arms=True):
    s = [("r", SKIN, (10, 7, 21, 18)), ("r", SKIN, (9, 9, 22, 16)),        # Kopf
         ("r", SKIN, (14, 19, 17, 20)),                                         # Hals
         ("r", shirt, (7, 21, 24, 33)), ("r", shirt, (4, 22, 6, 31)), ("r", shirt, (25, 22, 27, 31)),   # Oberkoerper + Arme
         ("r", SKIN, (4, 32, 6, 34)), ("r", SKIN, (25, 32, 27, 34)),           # Haende
         ("r", pants, (9, 34, 22, 39))]
    eyes = [("r", DARK, (13, 12, 14, 13)), ("r", DARK, (18, 12, 19, 13))]
    return s, eyes

# JARO: dunkle Seitenscheitel-Haare, graue gemusterte Cap, schwarzes Shirt, Umhaengetasche, Peace-Zeichen
def jaro():
    s, eyes = base("#17171c", "#101014")
    s += [("r", "#2b1a14", (9, 7, 22, 9)), ("r", "#2b1a14", (9, 9, 15, 11)), ("r", "#2b1a14", (9, 9, 10, 14)),   # Haare / Fransen
          ("r", "#4b5058", (10, 2, 21, 6)), ("r", "#3a3e44", (8, 6, 19, 7)),                                        # Cap + Schild
          ("r", "#6b7078", (12, 3, 13, 4)), ("r", "#6b7078", (16, 4, 17, 5)), ("r", "#6b7078", (19, 3, 20, 4)),      # Muster
          ("r", "#e6e6e6", (12, 24, 19, 25)),                                                                       # heller Streifen auf dem Shirt
          ("r", "#0d0d10", (20, 21, 22, 26)), ("r", "#0d0d10", (17, 27, 21, 31)),                                   # Gurt + Tasche
          ("r", SKIN, (25, 17, 27, 21)), ("r", SKIN, (28, 15, 28, 18)), ("r", SKIN, (26, 15, 26, 18)),               # Peace-Hand (zwei Finger)
          ("r", "#17171c", (25, 22, 27, 26))]
    return s + eyes
# RUFUS: laengere braune Haare mit hellen Straehnen, weisses Shirt mit Grafik
def rufus():
    s, eyes = base("#f1ede3", "#2b2f3a")
    s += [("r", "#4a3426", (8, 4, 23, 8)), ("r", "#4a3426", (8, 8, 11, 17)), ("r", "#4a3426", (20, 8, 23, 17)), ("r", "#4a3426", (9, 8, 17, 10)),
          ("r", "#c9a45a", (11, 5, 12, 10)), ("r", "#c9a45a", (15, 5, 16, 9)), ("r", "#c9a45a", (19, 5, 20, 8)),    # helle Straehnen
          ("r", "#1a1a1a", (12, 24, 19, 30)), ("r", "#c9a45a", (13, 25, 14, 29)), ("r", "#e03a2b", (17, 25, 18, 29))]  # Shirt-Grafik
    return s + eyes
# RAN: kurze braune Haare, Kopfhoerer um den Hals, weisses Shirt
def ran():
    s, eyes = base("#f6f6f4", "#222a36")
    s += [("r", "#4a2c1c", (10, 5, 21, 8)), ("r", "#4a2c1c", (9, 7, 10, 10)), ("r", "#4a2c1c", (21, 7, 22, 10)),
          ("r", "#15151a", (11, 19, 20, 20)), ("r", "#15151a", (9, 19, 11, 24)), ("r", "#15151a", (20, 19, 22, 24)),   # Kopfhoerer-Band + Muscheln
          ("r", "#ff6a1a", (9, 21, 10, 22)), ("r", "#ff6a1a", (21, 21, 22, 22))]
    return s + eyes

for name, fn in (("jaro", jaro), ("rufus", rufus), ("ran", ran)):
    for talk in (False, True):
        sprite(name, fn(), talk)
print("fertig")
