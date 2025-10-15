import xml.etree.ElementTree as ET
import json
from libs import utils


def pangloss_xml_to_sentence_pairs_json(pangloss_xml_filepath):

    with open(pangloss_xml_filepath, "rb") as f:
        xml_data = f.read()

    # Parse XML
    root = ET.fromstring(xml_data)

    # Extract sentences
    data = []
    for sentence in root.findall('.//S'):
        try:
            source = sentence.find('.//TRANSL').text
            target = sentence.find('.//FORM').text.strip()
            word_connections = {}

            for word in sentence.findall('.//W'):
                target_word = word.find('.//FORM').text.strip()
                source_word = word.find('.//TRANSL').text.strip()
                word_connections[source_word] = [target_word]

            data.append({
                'source': source,
                'target': target,
                'word connections': word_connections
            })
        except:
            print("issue with sentence {}".format(sentence))

    return data


# =============

import json
import re
from collections import defaultdict
from typing import Any, Dict, List

TAG_RE = re.compile(r'^[A-Z0-9.\-]+$')

def _is_taglike(s: str) -> bool:
    """Heuristic: checks if a string looks like a grammatical tag."""
    s = s.strip()
    return bool(TAG_RE.match(s)) and len(s) <= 10

def transform_gloss_json(input_path: str, output_path: str) -> None:
    """
    Read a JSON file containing glossed sentences, transform it into
    {"source", "target", "word connections"} format, and save to output_path.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    transformed = []

    for item in data:
        source = item.get("source", "")
        target = item.get("target", "")
        gloss_list = item.get("gloss", [])
        word_connections = defaultdict(list)

        for word_entry in gloss_list:
            word_form = (word_entry.get("Word") or "").strip()
            if not word_form:
                continue

            morphemes = word_entry.get("Morphemes", []) or []
            glosses = [m.get("Gloss", "").strip() for m in morphemes if m.get("Gloss")]
            if not glosses and word_entry.get("Gloss"):
                glosses = [word_entry["Gloss"].strip()]

            # fallback for punctuation
            if not glosses and word_form in {"?", "!", ",", ";", ":", ".", "…", "—", "–"}:
                glosses = [word_form]

            if not glosses:
                continue

            glosses = list(dict.fromkeys(glosses))  # remove duplicates

            # If multiple short grammatical tags, join them as composite
            if len(glosses) > 1 and all(_is_taglike(g) for g in glosses):
                composite = ">".join(glosses)
                word_connections[composite].append(word_form)
            else:
                for g in glosses:
                    word_connections[g].append(word_form)

        transformed.append({
            "source": source,
            "target": target,
            "word connections": dict(word_connections)
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transformed, f, ensure_ascii=False, indent=2)

    print(f"✅ Transformation complete. Output written to: {output_path}")

transform_gloss_json(
    "/Users/sebastienchristian/Desktop/d/01-These/language_lib/uruangnirin/5_CQs_Flex_export.json",
    "/Users/sebastienchristian/Desktop/d/01-These/language_lib/uruangnirin/5_CQs_sentence_pairs.json")