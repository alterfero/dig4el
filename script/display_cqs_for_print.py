import json

with open("../questionnaires/cq_A family album_1716852912.json", "r") as f:
    cq = json.load(f)
with open("../data/concepts.json", "r") as f:
    concepts = json.load(f)

print("title: {}".format(cq["title"]))
print("concept: {}".format(cq["context"]))

dialog = cq["dialog"]

for index, content in dialog.items():
    ktc = content["concept"]
    dktc = [concepts[k]["description"] for k in ktc]
    try:
        print("{}, {}, {}, [{}]".format(
            content["legacy index"] if content["legacy index"] != "" else index,
            content["speaker"],
            content["text"],
            ", ".join(content["intent"] + dktc)
        ))
    except:
        pass

