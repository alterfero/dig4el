import json
import os

BASE_LD_FOLDER = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', './ld')

def extract_parameter_names_from_cq_knowledge(indi_language: str):
    with open(os.path.join(BASE_LD_FOLDER, indi_language, "cq", "cq_knowledge", "cq_knowledge.json"), "r") as fi:
        cq_knowledge = json.load(fi)
    return [k["Parameter"] for k in cq_knowledge["grammar_priors"]]


def extract_and_clean_cq_alterlingua(indi_language: str) -> list[dict]:

    with open(os.path.join(BASE_LD_FOLDER, indi_language, "cq", "cq_knowledge", "cq_knowledge.json"), "r") as fi:
        cq_knowledge = json.load(fi)
    out_list = []
    for item in cq_knowledge["sentences"]:
        alterlingua = (item["alterlingua"]
                       .replace("(IP: | ", "(")
                       .replace("RP:)", ")")
                       .replace("()", "")
                       .replace("<>", "")
                       )
        out_list.append(
            {
                "source": item["source_english"],
                "target": item["target_raw"],
                "alterlingua": alterlingua,
                "comments": item.get("comments", "")
            }
        )
    return out_list

