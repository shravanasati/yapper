import json
from pathlib import Path
import glob
from pyperclip import copy

files = glob.glob("./highlights_*.json")
if len(files) > 1:
    print("Multiple highlights found!!")
    exit(1)
elif len(files) < 1:
    print("No highlights file found!!")
    exit(1)


highlights_path = files[0]
highlights_file = Path(highlights_path)
with open(highlights_file) as hf:
    highlights = json.load(hf)

for h in highlights:
    t = (h["title"])
    vp = (Path(f"./output/out_{h["id_"]}.mp4").absolute())
    print(t, vp, sep="\n")
    copy(str(vp))
    input()
    copy(t)
    input()
