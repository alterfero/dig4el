import json
import os

p = "/Users/sebastienchristian/Desktop/DIG4EL_test/wcc_effect/iaai_sap_with_wcc"
po = "/Users/sebastienchristian/Desktop/DIG4EL_test/wcc_effect/iaai_sap_without_wcc"

dfns = [fn for fn in os.listdir(p) if fn.endswith("json")]

for dfn in dfns:
    with open(p+"/"+dfn, "r") as f:
        d = json.load(f)
    for s in d:
        s["word connections"] = {}
    with open(po+"/no_wcc_"+dfn, "w") as fo:
        json.dump(d, fo)



