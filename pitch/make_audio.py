#!/usr/bin/env python3
"""Erzeugt die gesprochenen Folientexte (offene Sprachsynthese Piper, lokal) aus pitch/script.js.
Aufruf:  python3 pitch/make_audio.py        (aus dem Projektordner; braucht ~/.local/share/piper und ffmpeg)
script.js:  window.SCRIPT = [ {"id":"s01","speaker":"ran|rufus|jaro","text":"English text ..."}, ... ];
Ergebnis:   pitch/audio/<id>.ogg  +  pitch/audio/manifest.js  (window.AUDIO = {id: {file, duration}})"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); PIPER = os.path.expanduser("~/.local/share/piper")
VOICES = {"ran": "en_US-ryan-medium", "rufus": "en_US-joe-medium", "jaro": "en_GB-alan-medium"}
src = open(os.path.join(HERE, "script.js"), encoding="utf-8").read()
data = json.loads(re.search(r"window\.SCRIPT\s*=\s*(\[.*\])\s*;?\s*$", src, re.S).group(1))
os.makedirs(os.path.join(HERE, "audio"), exist_ok=True); manifest = {}
env = dict(os.environ, LD_LIBRARY_PATH=PIPER + "/piper")
for it in data:
    voice = VOICES.get(it.get("speaker", "ran"), VOICES["ran"]); wav = f"/tmp/pitch_{it['id']}.wav"; ogg = os.path.join(HERE, "audio", it["id"] + ".ogg")
    text = re.sub(r"\s+", " ", it["text"]).strip()
    if not text: continue
    subprocess.run([PIPER + "/piper/piper", "--model", f"{PIPER}/{voice}.onnx", "--output_file", wav], input=text.encode(), env=env, check=True, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "3", ogg], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ogg], capture_output=True, text=True).stdout.strip() or 0)
    manifest[it["id"]] = {"file": f"audio/{it['id']}.ogg", "duration": round(dur, 2)}
    print(it["id"], it["speaker"], round(dur, 1), "s")
open(os.path.join(HERE, "audio", "manifest.js"), "w").write("window.AUDIO = " + json.dumps(manifest) + ";\n")
print("Audio fertig:", len(manifest), "Folien")
