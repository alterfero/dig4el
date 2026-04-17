import json
import os

p = "/Users/sebastienchristian/Desktop/DIG4EL_test/wcc effect/quechua dcqt with wcc"
po = "/Users/sebastienchristian/Desktop/DIG4EL_test/wcc effect/quechua dcqt without wcc"

dfns = [fn for fn in os.listdir(p) if fn.endswith("json")]

for dfn in dfns:
    with open(p+"/"+dfn, "r") as f:
        d = json.load(f)
    for i, s in d["data"].items():
        s["concept_words"] = {}
        s["comment"] = ""
    with open(po+"/no_wcc_"+dfn, "w") as fo:
        json.dump(d, fo)



