import json
import os

PREFIX = "."

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage")

with open(os.path.join(BASE_LD_PATH, "languages.json"), "r", encoding='utf-8') as f:
    GLOTTO_LANGUAGE_LIST = json.load(f)

LLIST = sorted(GLOTTO_LANGUAGE_LIST.keys())

def languages_csv_to_json():
    """
    loads ./external_data/glottolog/languages.csv
    creates a json {"language_name":"", "glottocode":""}
    save the json in ./external_data/glottolog_derived/languages.json
    :return:
    """
    with open("../external_data/glottolog/languages.csv", "r", encoding="utf-8") as f:
        languages = f.readlines()

    languages_json = {}
    for line in languages[1:]:  # Skip header
        parts = line.strip().split(",")
        if len(parts) >= 3:
            language_name = parts[1].strip('"')
            glottocode = parts[0].strip('"')
            languages_json[language_name] = glottocode

    with open("../external_data/glottolog_derived/languages.json", "w", encoding="utf-8") as f:
        json.dump(languages_json, f, indent=4, ensure_ascii=False)
