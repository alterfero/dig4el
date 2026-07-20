import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


def write_no_wcc_json(input_path: str | Path) -> Path:
    """
    Reads a JSON file, removes all `comment` fields, clears all values in
    `concept_words`, and writes the result in the same folder with `no_wcc_`
    added at the beginning of the filename.

    Example:
        data/example.json -> data/no_wcc_example.json

    Returns the output file path.
    """
    input_path = Path(input_path)

    with input_path.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    obj = deepcopy(obj)

    def clean(node: Any) -> Any:
        if isinstance(node, dict):
            cleaned = {}

            for key, value in node.items():
                if key == "comment":
                    continue

                if key == "concept_words" and isinstance(value, dict):
                    cleaned[key] = {concept: "" for concept in value}
                else:
                    cleaned[key] = clean(value)

            return cleaned

        if isinstance(node, list):
            return [clean(item) for item in node]

        return node

    cleaned_obj = clean(obj)

    output_path = input_path.with_name(f"no_wcc_{input_path.name}")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(cleaned_obj, f, ensure_ascii=False, indent=2)

    return output_path

p = "/Users/sebastienchristian/Desktop/DIG4EL_test/component probes/Pseudo-gloss/Tahitian_e1e_sources/DCQ"
file_list = [fn for fn in os.listdir(p)
             if fn.endswith("json")]
for file in file_list:
    write_no_wcc_json(os.path.join(p, file))