# Copyright (C) 2024 Sebastien CHRISTIAN, University of French Polynesia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations
from typing import Any
import copy
import re
import os
import json
from os.path import isfile, join
from os import listdir
import pandas as pd
import hashlib
import streamlit as st
import unicodedata
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu

from collections.abc import Mapping, Sequence

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage")


def normalize_text(text: str) -> str:
    """Normalize *text* to NFC form."""
    return unicodedata.normalize("NFC", text)


def normalize_user_strings(obj):
    """Recursively apply :func:`normalize_text` to all strings in *obj*."""
    if isinstance(obj, str):
        return normalize_text(obj)
    if isinstance(obj, Mapping):
        return {k: normalize_user_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_user_strings(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(normalize_user_strings(v) for v in obj)
    return obj


def save_json_normalized(data, fp, *args, **kwargs):
    """Wrapper around :func:`json.dump` that normalizes strings before saving."""
    kwargs.setdefault("ensure_ascii", False)
    json.dump(normalize_user_strings(data), fp, *args, **kwargs)


def dumps_json_normalized(data, *args, **kwargs):
    """Wrapper around :func:`json.dumps` that normalizes strings before serializing."""
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(normalize_user_strings(data), *args, **kwargs)

def combine_sp_files(path):
    fl = [f for f in os.listdir(path) if f.endswith("json")]
    of = []
    for f in fl:
        with open(os.path.join(path, f), "r") as ft:
            fc = json.load(ft)
        of += fc
    with open(os.path.join(path, "combined_pairs.json"), "w") as fo:
        json.dump(of, fo)




def stringify_lesson(lesson: dict[str, Any]) -> str:
    """
    Convert a lesson JSON object into a stable plain-text representation
    suitable for LLM judging.

    The goal is not pretty rendering. The goal is consistent, information-rich,
    low-ambiguity serialization.
    """

    def clean(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    def section_examples(section: dict[str, Any]) -> list[dict[str, Any]]:
        examples = section.get("example")
        if examples is None:
            examples = section.get("examples")
        if isinstance(examples, list):
            return [ex for ex in examples if isinstance(ex, dict)]
        return []

    lines: list[str] = []

    # =========================
    # Header / metadata
    # =========================
    title = clean(lesson.get("title"))
    date = clean(lesson.get("date"))
    version = clean(lesson.get("version"))

    lines.append("LESSON")
    if title:
        lines.append(f"Title: {title}")
    if date:
        lines.append(f"Date: {date}")
    if version:
        lines.append(f"Version: {version}")

    # =========================
    # Introduction
    # =========================
    introduction = clean(lesson.get("introduction"))
    if introduction:
        lines.append("")
        lines.append("INTRODUCTION")
        lines.append(introduction)

    # =========================
    # Sections
    # =========================
    sections = lesson.get("sections", [])
    if isinstance(sections, list) and sections:
        lines.append("")
        lines.append("SECTIONS")

        for i, section in enumerate(sections, start=1):
            if not isinstance(section, dict):
                continue

            focus = clean(section.get("focus"))
            description = clean(section.get("description"))
            examples = section_examples(section)

            lines.append("")
            lines.append(f"Section {i}")
            if focus:
                lines.append(f"Focus: {focus}")
            if description:
                lines.append(f"Description: {description}")

            if examples:
                lines.append("Examples:")
                for j, ex in enumerate(examples, start=1):
                    target = clean(ex.get("target_sentence"))
                    source = clean(ex.get("source_sentence"))
                    ex_description = clean(ex.get("description"))

                    lines.append(f"  Example {i}.{j}")
                    if source:
                        lines.append(f"    Source sentence: {source}")
                    if target:
                        lines.append(f"    Target sentence: {target}")
                    if ex_description:
                        lines.append(f"    Description: {ex_description}")

    # =========================
    # Conclusion
    # =========================
    conclusion = clean(lesson.get("conclusion"))
    if conclusion:
        lines.append("")
        lines.append("CONCLUSION")
        lines.append(conclusion)

    return "\n".join(lines)

lesson_string = stringify_lesson({
  "title": "Negation in Bwatoo_e2a",
  "introduction": "Across languages, negation is typically built with one of three frequent patterns: specialised negative particles (about half of the world’s languages), negative affixes (about a third), or dedicated negative verbs (about one eighth). Negation can target the whole clause (sentence negation) or only a part of it (constituent negation). Within sentence negation, we can distinguish negation of existence, location, category/equative, identification, quality/state, and process/event, and we should also watch for aspectual nuances such as ‘never’, ‘no more/anymore’, or ‘not yet’. In English, the dominant strategy is a specialised particle such as “not” (as in “This is not a dog”), and English also has negative-like morphology in words such as “im-possible”. In Bwatoo_e2a, the dominant strategy is also specialised negative particles: the clause-level negator is **cipa** (placed before the predicate), while **cau** serves as an existential/constituent negator (‘no/none, not here’) and as the standalone “No!”. Secondary resources include a negative locative predicate **ciede-** ‘not be (there/here)’ and a lexical verb **cede-** ‘cease/disappear’ that expresses ‘no more/anymore’. No productive negative affixes are evidenced in the available data. Note: the descriptive documents retrieved do not detail negation, but the sentence-level analyses and paired examples do provide consistent forms and uses.",
  "sections": [
    {
      "focus": "Most frequent pattern and placement: specialised negative particles",
      "example": [
        {
          "target_sentence": "cau! cipa zho vup",
          "source_sentence": "No, I don’t cough.",
          "description": "Clause negation with **cipa** placed before the predicate; initial **cau** is the standalone “No!”. Scope: process/event (‘cough’)."
        },
        {
          "target_sentence": "cau! cipa bu hme butriin",
          "source_sentence": "No, no! We won’t be bathing.",
          "description": "**cipa** scopes over a near-future predicate; appears clause-initial, before the subject and predicate. Shows interaction with future/near-future aspect."
        },
        {
          "target_sentence": "cipa zho hme koon",
          "source_sentence": "I can’t find it.",
          "description": "**cipa** negates an ability/finding periphrasis; it takes clausal scope over the predicate complex."
        },
        {
          "target_sentence": "cipa xahnange-ong daamin bwe-tralo",
          "source_sentence": "Well… I’m not feeling well these days.",
          "description": "**cipa** negates an adjectival/experiential predicate (quality/state)."
        },
        {
          "target_sentence": "cipa ti ne-go",
          "source_sentence": "Isn’t it your notebook?",
          "description": "**cipa** negates an equative/identificational predicate (NP predicate)."
        }
      ],
      "description": "Bwatoo_e2a primarily uses the specialised clausal negator **cipa**. It is clause-initial and precedes the predicate (verbal, adjectival, or equative/NP). The existential/constituent negator **cau** is also very frequent, and can stand alone as “No!”. The data show no productive negative affixation. Secondary negative(-like) predicates include **ciede-** ‘not be (there)’ and **cede-** ‘cease/disappear’ (‘no more/anymore’)."
    },
    {
      "focus": "Process/event negation and prohibitives with cipa",
      "example": [
        {
          "target_sentence": "cau! cipa zho vup",
          "source_sentence": "No, I don’t cough.",
          "description": "Sentence negation of a process with **cipa** before the predicate; full clausal scope."
        },
        {
          "target_sentence": "mo koon, cipa go vadanake",
          "source_sentence": "Also, don’t forget",
          "description": "Prohibitive with **cipa** + verb (‘don’t V’). **cipa** forms a negative imperative."
        },
        {
          "target_sentence": "cipa go hme vadi",
          "source_sentence": "Don’t go to work",
          "description": "Another prohibitive with **cipa** clause-initial before the verb phrase."
        },
        {
          "target_sentence": "lama-na Coujol cipa ra wanake ani u-moo-la-n nya-ko ni ma xhoomu-le nya-ko ni doote-le ma ni ma le cami",
          "source_sentence": "As for Coujol, he did not change his behavior toward the elders regarding their lands and their plantings.",
          "description": "Narrative process negation: **cipa** negates a change-of-state/process predicate. The particle appears before the predicate complex."
        }
      ],
      "description": "For processes/events, **cipa** directly precedes the predicate and takes wide scope. The same **cipa** strategy also builds prohibitives (‘don’t V’)."
    },
    {
      "focus": "Existential and constituent negation with cau (‘no/none’, negative presentative)",
      "example": [
        {
          "target_sentence": "cau! cau vadi",
          "source_sentence": "No, there’s no celebration.",
          "description": "Existential negation: **cau** as a negative presentative/quantifier with the NP (‘no celebration’)."
        },
        {
          "target_sentence": "naae, je cau xhwiaman ca bala fomwa",
          "source_sentence": "Now we have nothing left at home!",
          "description": "Constituent/existential negation: **cau** + NP conveys ‘no X (left)’. Scope is on existence/availability rather than on a possessive relation."
        },
        {
          "target_sentence": "cau! cau cahni",
          "source_sentence": "Hm, not here.",
          "description": "Locational constituent negation: **cau** + locative adverb (‘not here’)."
        },
        {
          "target_sentence": "juu cau ca ma le vwa ko-na le juu vwa-teke ma le xhwii na ni bolomakau",
          "source_sentence": "They really did not know what to do because of the damage done by the cattle.",
          "description": "Within a complex clause, **cau** functions as a negative quantifier (‘no (way/thing)’), illustrating constituent-level negation inside larger structures."
        }
      ],
      "description": "**cau** functions as a negative presentative/quantifier meaning ‘no/none’, and as the interjection ‘No!’. It commonly builds existential or NP-level negation and also negates locational adverbs (‘not here’)."
    },
    {
      "focus": "Negation of localisation: specialised predicate and presentative strategy",
      "example": [
        {
          "target_sentence": "tra ciede-a",
          "source_sentence": "It’s not there.",
          "description": "Specialised negative locative predicate **ciede-** ‘not be (there/here)’. This is a negative verb-like predicate restricted to location."
        },
        {
          "target_sentence": "cau! cau cahni",
          "source_sentence": "Hm, not here.",
          "description": "Constituent/location negation via **cau** + locative (‘not here’), an adverbial presentative strategy."
        }
      ],
      "description": "Locational negation can be expressed either by the dedicated negative locative predicate **ciede-** (‘not be located’) or by **cau** combined with a locative adverb (‘not here/there’)."
    },
    {
      "focus": "Equative and category membership negation with cipa",
      "example": [
        {
          "target_sentence": "cipa ti ne-go",
          "source_sentence": "Isn’t it your notebook?",
          "description": "Identification/equative negation: **cipa** precedes the NP predicate to negate identification with a specific referent."
        },
        {
          "target_sentence": "naae, cipa je thapia-ong, je xhoomu-ong hni",
          "source_sentence": "But I’m not a child any more, I’ve grown up.",
          "description": "Category-membership negation: **cipa** before a nominal predicate (‘not a child’). The clause adds an ‘any more’ inference (see aspectual notes)."
        }
      ],
      "description": "For equative or category predicates, **cipa** is placed before the NP predicate to negate inclusion in a category or identification with a specific referent."
    },
    {
      "focus": "Existential negation with cipa + existential predicate",
      "example": [
        {
          "target_sentence": "ni bolomakau je vwa ni nyai-le ka je hmwanija-le ka cipa vwa vala koo-le",
          "source_sentence": "Now the cattle were increasing in number, and since there was no fence,",
          "description": "Existential negation expressed with **cipa** + existential/stative predicate **vwa** plus the NP (‘no fence’). This shows that beyond **cau**, existence can be negated with **cipa** scoping over an existential predicate."
        }
      ],
      "description": "In addition to **cau**, the corpus shows existence negated via **cipa** with an existential predicate (**vwa**), yielding ‘there is not X’. This broadens the existential negation options in Bwatoo_e2a."
    },
    {
      "focus": "Possession and the scope of negation: relation vs existence",
      "example": [
        {
          "target_sentence": "ani xa-finati ne-ong, a bo waa-nyima-n cana zho cipa hme ko a ti",
          "source_sentence": "The teacher will be quite angry if I don’t have my notebook.",
          "description": "Negating the possessive relation: **cipa** + possessive predicate **hme** (‘have’) targets the relation (‘I do not have X’)."
        },
        {
          "target_sentence": "naae, je cau xhwiaman ca bala fomwa",
          "source_sentence": "Now we have nothing left at home!",
          "description": "Negating existence/availability: **cau** + NP conveys ‘no X (left)’, with scope on existence rather than on a possessive link."
        }
      ],
      "description": "Bwatoo_e2a distinguishes negation of the possessive relation (**cipa** + possessive predicate like **hme**) from negation of existence/availability (**cau** + NP ‘no X (left)’). The former says ‘I don’t have X’; the latter says ‘there is no X (for us/now)’.“},{"
    },
    {
      "focus": "Aspectual nuances: ‘never’, ‘no more/anymore’, and the gap (‘not yet’ not attested)",
      "example": [
        {
          "target_sentence": "cipa go xala-a",
          "source_sentence": "You’ve never met him.",
          "description": "‘Never’ is conveyed with **cipa** under a past/perfective context; there is no dedicated ‘never’ word in the data."
        },
        {
          "target_sentence": "cipa zho xalake ani xape-nyi-foto",
          "source_sentence": "but I’ve never seen your pictures.",
          "description": "Again, **cipa** provides ‘never’ with a perfective/past reading from context."
        },
        {
          "target_sentence": "a mwa finati a pi muci ne-a, pi cede-a",
          "source_sentence": "That was an old school that doesn’t exist anymore.",
          "description": "‘No more/anymore’ is expressed lexically by **cede-** ‘cease/disappear’, often with **pi** ‘already’."
        },
        {
          "target_sentence": "naae, je cau xhwiaman ca bala fomwa",
          "source_sentence": "Now we have nothing left at home!",
          "description": "Depleted existence (‘none left’) is expressed by **cau** + NP. This is an existential ‘no more’ reading. “}],"
        }
      ],
      "description": "Aspectually, Bwatoo_e2a marks ‘never’ with **cipa** plus past/perfective context; ‘no more/anymore’ is often lexical (**cede-**) or existential (**cau** + NP, ‘none left’). The dataset does not attest a ‘not yet’ construction. Questions may use **pi** with an ‘ever’ reading, while negative answers use **cipa** (as noted in the sentence analysis)."
    },
    {
      "focus": "Inability: periphrastic negation vs dedicated inability predicate",
      "example": [
        {
          "target_sentence": "cipa zho hme koon",
          "source_sentence": "I can’t find it.",
          "description": "Periphrastic ability is negated by **cipa** taking clausal scope over the ability/finding complex."
        },
        {
          "target_sentence": "lama je hami naai je vwathoon nya koo-le ma le cami-xaman",
          "source_sentence": "The situation became such that they could no longer cultivate their lands.",
          "description": "Dedicated inability predicate **vwathoon** ‘cannot’ is used beside the main activity; no **cipa** is required in this construction."
        }
      ],
      "description": "Bwatoo_e2a expresses inability either by negating an ability periphrasis with **cipa**, or by employing the dedicated predicate **vwathoon** ‘cannot’. Both strategies are attested."
    },
    {
      "focus": "Notes on sources and contradictions",
      "example": [
        {
          "target_sentence": "cau! cau vadi",
          "source_sentence": "No, there’s no celebration.",
          "description": "Corpus-based example showing **cau** as a negative presentative (‘no X’), contrary to the document summary that reported no explicit negation forms."
        }
      ],
      "description": "The descriptive documents retrieved report no explicit forms for negation in Bwatoo_e2a. In contrast, the sentence-level analyses and paired examples consistently show specialised negative particles (**cipa**, **cau**) and negative(-like) predicates (**ciede-**, **cede-**, **vwathoon**). The lesson above follows the attested corpus evidence while flagging the documentary gap."
    }
  ],
  "conclusion": "What to remember: Bwatoo_e2a relies on specialised negative particles. **cipa** is the core clausal negator, clause-initial, and it scopes over processes, qualities, and equatives; it also builds prohibitives. **cau** serves as a negative presentative/quantifier (‘no/none, not here’) and as the interjection ‘No!’, and it handles many existential and constituent-negation contexts. Locational negation can use the specialised predicate **ciede-** ‘not be (there/here)’. ‘No more/anymore’ is often lexical (**cede-**) or existential (**cau** + NP ‘none left’). Inability can be expressed either by **cipa** over an ability periphrasis or via **vwathoon** ‘cannot’. There is no evidence of negative affixes in the data. Keep in mind the scope contrast between negating a possessive relation (**cipa** + **hme**) and negating existence/availability (**cau** + NP).",
  "translation_drills": [
    {
      "target": "cau! cipa zho vup",
      "source": "No, I don’t cough."
    },
    {
      "target": "cipa zho hme koon",
      "source": "I can’t find it."
    },
    {
      "target": "mo koon, cipa go vadanake",
      "source": "Also, don’t forget"
    },
    {
      "target": "cipa go hme vadi",
      "source": "Don’t go to work"
    },
    {
      "target": "cipa go xala-a",
      "source": "You’ve never met him."
    },
    {
      "target": "cipa zho xalake ani xape-nyi-foto",
      "source": "but I’ve never seen your pictures."
    },
    {
      "target": "cau! cipa bu hme butriin",
      "source": "No, no! We won’t be bathing."
    },
    {
      "target": "cau! cau vadi",
      "source": "No, there’s no celebration."
    },
    {
      "target": "a mwa finati a pi muci ne-a, pi cede-a",
      "source": "That was an old school that doesn’t exist anymore."
    },
    {
      "target": "naae, je cau xhwiaman ca bala fomwa",
      "source": "Now we have nothing left at home!"
    },
    {
      "target": "ani xa-finati ne-ong, a bo waa-nyima-n cana zho cipa hme ko a ti",
      "source": "The teacher will be quite angry if I don’t have my notebook."
    },
    {
      "target": "tra ciede-a",
      "source": "It’s not there."
    },
    {
      "target": "cau! cau cahni",
      "source": "Hm, not here."
    },
    {
      "target": "cipa ti ne-go",
      "source": "Isn’t it your notebook?"
    },
    {
      "target": "cipa xahnange-ong daamin bwe-tralo",
      "source": "Well… I’m not feeling well these days."
    },
    {
      "target": "naae, cipa je thapia-ong, je xhoomu-ong hni",
      "source": "But I’m not a child any more, I’ve grown up."
    },
    {
      "target": "lama-na Coujol cipa ra wanake ani u-moo-la-n nya-ko ni ma xhoomu-le nya-ko ni doote-le ma ni ma le cami",
      "source": "As for Coujol, he did not change his behavior toward the elders regarding their lands and their plantings."
    },
    {
      "target": "ni bolomakau je vwa ni nyai-le ka je hmwanija-le ka cipa vwa vala koo-le",
      "source": "Now the cattle were increasing in number, and since there was no fence,"
    },
    {
      "target": "lama je hami naai je vwathoon nya koo-le ma le cami-xaman",
      "source": "The situation became such that they could no longer cultivate their lands."
    },
    {
      "target": "juu cau ca ma le vwa ko-na le juu vwa-teke ma le xhwii na ni bolomakau",
      "source": "They really did not know what to do because of the damage done by the cattle."
    }
  ],
  "sources": {
    "cqs": [
      "recording_cq_A family album_1716852912_Haeke_Antoine Corral_Adèle Wabéalo_1764284567.json",
      "recording_cq_where is my notebook_1716497507_Bwatoo_Antoine Corral_Adèle Wabéalo_1764483194.json",
      "recording_cq_Going fishing_1716315461_Bwatoo_Antoine Corral_Adèle Wabéalo_1764386043.json",
      "recording_cq_Preparing for the New Year_1716403492_Bwatoo_Antoine Corral_Adèle Wabéalo_1764475165.json",
      "recording_cq_At the doctor_1715973404_Bwatoo_Antoine Corral_Adèle Wabéalo_1764194244.json"
    ],
    "documents": [],
    "pairs": [
      "deuil original (AC)",
      "exode original (AC)",
      "mariage original (AC)"
    ]
  },
  "date": "Tuesday, 7 April 2026 at 03:47",
  "version": "1.1.0"
})
print(lesson_string)


def csv_to_dict(csv_file_path):
    """
    Streamlit widget: upload a CSV with columns ['source','target'] and
    convert it to a list[dict] ready for json.dumps.
    Returns:
        records (list[dict]) or None if no valid file uploaded yet.
    """

    try:
        # Read CSV; pandas handles quotes/commas inside fields
        df = pd.read_csv(csv_file_path)  # assumes comma-separated
    except Exception as e:
        st.error(f"Couldn't read CSV: {e}")
        return None

    # Validate columns
    required = {"source", "target"}
    missing = required - set(df.columns)
    if missing:
        print(f"Missing required column(s): {', '.join(sorted(missing))}")
        print(f"Found columns: {list(df.columns)}")
        return None

    # Keep only needed columns, drop fully empty rows, coerce to str, strip whitespace
    df = df[list(required)]
    df = df.dropna(how="all", subset=["source", "target"]).fillna("")
    for col in ["source", "target"]:
        df[col] = df[col].astype(str).str.strip()

    # Build records
    records = df.to_dict(orient="records")

    return records


def flatten(obj, parent_key=()):
    """
    Flatten a nested dict/list into a mapping from key‐path tuples to values.

    Args:
        obj:     The input data (dict, list/tuple, or leaf).
        parent_key:  Tuple of keys/indices leading to this obj.

    Returns:
        A dict { tuple(path): leaf_value, … }.
    """
    items = {}
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            new_key = parent_key + (k,)
            items.update(flatten(v, new_key))
    elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        for idx, v in enumerate(obj):
            new_key = parent_key + (idx,)
            items.update(flatten(v, new_key))
    else:
        items[parent_key] = obj
    return items


# Example
data = {
    "user": {"name": "Alice", "roles": ["admin", "user"]},
    "active": True
}

flat = flatten(data)


# flat == {
#   ('user','name'): 'Alice',
#   ('user','roles',0): 'admin',
#   ('user','roles',1): 'user',
#   ('active',): True
# }


def generate_hash_from_list(identifiers):
    # Step 1: Sort the list of identifiers
    sorted_identifiers = sorted(identifiers)

    # Step 2: Concatenate the identifiers into a single string
    concatenated = ''.join(sorted_identifiers)

    # Step 3: Hash the concatenated string using SHA-256
    hash_object = hashlib.sha256(concatenated.encode())
    full_hash = hash_object.hexdigest()

    # Step 4: Truncate the hash to 8 characters (optional)
    short_hash = full_hash[:16]

    return short_hash

def normalize_column(column):
    col_sum = column.sum()
    if col_sum == 0:
        # All values are 0, assign a uniform distribution
        return pd.Series([1 / len(column)] * len(column), index=column.index)
    else:
        # Normalize the column
        return column / col_sum

def csv_to_dict(file_path):
    df = pd.read_csv(file_path)
    return df.to_dict(orient='records')

def add_field_to_concept_json(concept_json_file, field_name, field_value):
    """Add a field to a concept json file."""
    with open(concept_json_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    for concept in data.keys():
        data[concept][field_name] = field_value

    with open(concept_json_file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Field {field_name} added to {concept_json_file}")

def get_key_by_value(d, target_value):
    return next((key for key, value in d.items() if value == target_value), None)

def is_number(s):
    """Check if a string is a number."""
    return re.match(r"^\d+$", s) is not None

def listify(string):
    return(string.split("..."))

def clean_sentence(sentence, filename=False, filename_length=50):
    """Clean a sentence."""
    sentence = str(sentence)
    if sentence != "":
        nil_list = [",", ";"]
        space_list = ["'", "’", "(", ")", ":", ".", "!", "?", "…", "—", "-", "–", "—", "«"]
        or_list = ["/", "|"]
        try:
            out = sentence.lower()
        except:
            print("No lower() on {}".format(sentence))
        if not filename:
            for item in nil_list:
                out = out.replace(item, "")
            for item in space_list:
                out = out.replace(item, " ")
            for item in or_list:
                out = out.replace(item, " [OR] ")
        else:
            length = min(len(sentence), filename_length)
            nil_list += ["."]
            space_list += [" "]
            for item in nil_list:
                out = out.replace(item, "")
            for item in space_list:
                out = out.replace(item, "_")
            for item in or_list:
                out = out.replace(item, "_OR_")
            out = out[:length]
    else:
        out = "empty_sentence"
    return out

def normalize_sentence(sentence):
    #replace all single quotes with "'" to avoid issues with the tokenizer
    various_single_quotes_characters = ["'", "`", "’", "‘", "’", "ʼ", "ʻ", "ʽ", "ʾ", "ʿ", "ˈ", "ˊ", "ˋ", "˴", "՚", "׳", "ꞌ", "＇", "｀"]
    for single_quote in various_single_quotes_characters:
        sentence = sentence.replace(single_quote, "'")
    # remove final punctuation if any
    if len(sentence) > 0 and sentence[-1] in [".", "!", "?", ":", ";"]:
        sentence = sentence[:-1]
    #remove extra spaces at the beginning and end of the sentence
    sentence = sentence.strip()
    #small caps
    sentence = sentence.lower()
    #replace all double spaces with single spaces
    sentence = sentence.replace("  ", " ")

    return sentence
def list_folders(directory):
    """Lists all folders in the specified directory."""
    folders = []
    for item in os.listdir(directory):
        # Construct full item path
        item_path = os.path.join(directory, item)
        # Check if it's a directory and not a file
        if os.path.isdir(item_path):
            folders.append(item)
    return folders
def list_txt_files(directory):
    """Lists all .txt files in the specified directory."""
    files = []
    for item in os.listdir(directory):
        # Construct full item path
        item_path = os.path.join(directory, item)
        # Check if it's a file and not a directory
        if os.path.isfile(item_path) and item_path.endswith(".txt"):
            files.append(item)
    return files

def list_json_files(directory):
    """Lists all .txt files in the specified directory."""
    files = []
    for item in os.listdir(directory):
        # Construct full item path
        item_path = os.path.join(directory, item)
        # Check if it's a file and not a directory
        if os.path.isfile(item_path) and item_path.endswith(".json"):
            files.append(item)
    return files

def list_cqs():
    questionnaires_folder = "./questionnaires"
    return [f for f in listdir(questionnaires_folder) if
                    isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

def tokenize(sentence):
    """Tokenize a sentence."""
    return sentence.lower().split()

import os

def replace_in_file(file_path, old, new):
    """
    Open `file_path`, replace all occurrences of `old` with `new`,
    and overwrite the file if any replacements were made.
    Returns True if replacements were written, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"opened {file_path}")

    if old not in content:
        print(f"no occurrence of {old} in {file_path}")
        return False

    updated = content.replace(old, new)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated)
        print(f"replacement done, updated {file_path} saved.")
    return True


def replace_concept_name_in_tree(old_concept_name, new_concept_name, root_directory):
    """
    Recursively walks `root_directory`, finds every .json file,
    and replaces occurrences of old_concept_name with new_concept_name.
    """
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.lower().endswith(".json"):
                full_path = os.path.join(dirpath, filename)
                if replace_in_file(full_path, old_concept_name, new_concept_name):
                    print(f"Replaced in {full_path}")


def replace_concept_names_everywhere():

    print("Loading concept_name_update.json")
    with open("../data/lookup_tables/concept_name_update.json", "r", encoding='utf-8') as f:
        concept_name_update = json.load(f)
        print("Loaded concept_name_update.json")

        # 2. Flatten updates to a list of (old, new) tuples
        updates = []
        for entry in concept_name_update:
            if len(entry) != 1:
                raise ValueError(f"Expected single-key dict, got {entry}")
            old, new = next(iter(entry.items()))
            updates.append((old, new))

        # 3. Sort by descending length of the old key
        updates.sort(key=lambda pair: len(pair[0]), reverse=True)

    print("CQ files")
    cq_files = list_json_files("../questionnaires")
    for cq_file in cq_files:
        full_filename = os.path.join("../questionnaires", cq_file)
        for old_name, new_name in updates:
            if replace_in_file(full_filename, old_name, new_name):
                print(f"replacement of {old_name} to {new_name} successful in {cq_file}")

    print("available transcriptions")
    for old_name, new_name in updates:
        replace_concept_name_in_tree(old_name, new_name, "../available_transcriptions")

    print("other transcriptions")
    for old_name, new_name in updates:
        replace_concept_name_in_tree(old_name, new_name, "../CQ_transcriptions_not_shared")

    print("concepts.json")
    for old_name, new_name in updates:
        if replace_in_file("../data/concepts.json", old_name, new_name):
            print(f"replacement successful in concepts.json")


def update_concept_names_in_transcription(transcription):
    """
    As concept names change, we need to update the transcriptions users upload before they're processed,
    using the concept_name_update.json lookup table. The table is sorted by length (longer first) before use to avoid
    replacing in-name sequences.
    :param transcription: dict  # parsed JSON
    :return: dict               # updated copy
    """
    # 1. Load and sort the lookup table
    lookup_path = os.path.join(".", "data", "lookup_tables", "concept_name_update.json")
    with open(lookup_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    updates = []
    for entry in raw_list:
        if len(entry) != 1:
            raise ValueError(f"Expected single-key dict, got {entry!r}")
        old, new = next(iter(entry.items()))
        updates.append((old, new))
    # Sort so longest old‑names go first
    updates.sort(key=lambda t: len(t[0]), reverse=True)

    # 2. Deep-copy the transcription so we don't mutate the original
    new_transcription = copy.deepcopy(transcription)

    # 3. Walk through each item and rename keys in concept_words
    found_some = False
    for idx, content in new_transcription.get("data", {}).items():
        cw = content.get("concept_words")
        if not isinstance(cw, dict):
            continue  # skip if missing or malformed
        for old_name, new_name in updates:
            if old_name in cw:
                found_some = True
                # optional: warn if new_name already existed
                if new_name in cw:
                    print(f"Warning: overwriting '{new_name}' in entry {idx}")
                # pop only the single key
                cw[new_name] = cw.pop(old_name)

    return new_transcription, found_some

def catalog_all_available_cqs(language=None):
    with open("./uid_dict.json", "r") as uid:
        uid_dict = json.load(uid)
    cq_catalog = []
    if language:
        if language in os.listdir(os.path.join(BASE_LD_PATH)):
            languages = [language]
        else:
            return []
    else:
        languages = [l
                     for l
                     in os.listdir(os.path.join(BASE_LD_PATH))
                     if l in gu.GLOTTO_LANGUAGE_LIST.keys()]
    index = 0
    for language in languages:
        if "cq" in os.listdir(os.path.join(BASE_LD_PATH, language)):
            cqs = [f
                   for f in os.listdir(os.path.join(BASE_LD_PATH, language, "cq", "cq_translations"))
                   if f.endswith(".json")]
            for cq in cqs:
                try:
                    index += 1
                    with open(os.path.join(BASE_LD_PATH, language, "cq", "cq_translations", cq)) as c:
                        cqc = json.load(c)
                    if "location" not in cqc.keys():
                        cqc["location"] = "unknown"
                    cq_catalog.append({
                        "index": index,
                        "title": uid_dict.get(cqc["cq_uid"], "unknown"),
                        "language": language,
                        "pivot": cqc["pivot language"],
                        "info": cqc["interviewee"][:3]+" by "+cqc["interviewer"][:3],
                        "interviewer": cqc["interviewer"],
                        "interviewee": cqc["interviewee"],
                        "date": cqc.get("published date"),
                        "uid": cqc["cq_uid"],
                        "filename": cq,
                        "is_downloadable": True,
                        "is_displayable": True
                    })
                    with open(os.path.join(BASE_LD_PATH, language, "cq", "cq_translations", cq), "w") as cr:
                        json.dump(cqc, cr)
                except:
                    print("EXCEPTION: Error opening json CQ {} for language {}".format(cq, language))
    return cq_catalog


def reset_augmented_pairs(language):
    hard_index = {}
    curren_job_sig = []
    batch_id_store = {"batch_id": ""}
    delimiters = [" ", ".", ",", ";", ":", "!", "?", "\u2026"]
    print(f"Resetting augmented sentence pairs for language {language}")
    fmu.delete_all_files_in_folder(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "augmented_pairs"))
    fmu.delete_all_files_in_folder(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "vector_ready_pairs"))
    fmu.delete_all_files_in_folder(
        os.path.join(BASE_LD_PATH, language, "sentence_pairs", "vectors", "description_vectors"))

    with open(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "vectors", "hard_index.json"), "w") as f1:
        json.dump(hard_index, f1)
    with open(os.path.join(BASE_LD_PATH, language, "batch_id_store.json"), "w") as f2:
        json.dump(batch_id_store, f2)

    with open(os.path.join(BASE_LD_PATH, language, "info.json"), "r") as f3:
        info = json.load(f3)
    info["documents"]["vectorized"] = []
    with open(os.path.join(BASE_LD_PATH, language, "info.json"), "w") as f4:
        json.dump(info, f4)
    return True


def reset_pairs(language):
    hard_index = {}
    curren_job_sig = []
    batch_id_store = {"batch_id": ""}
    delimiters = [" ", ".", ",", ";", ":", "!", "?", "\u2026"]
    print(f"Resetting sentence pairs for language {language}")
    fmu.delete_all_files_in_folder(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "augmented_pairs"))
    fmu.delete_all_files_in_folder(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "pairs"))
    fmu.delete_all_files_in_folder(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "vector_ready_pairs"))
    fmu.delete_all_files_in_folder(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "vectors", "description_vectors"))
    with open(os.path.join(BASE_LD_PATH, language, "sentence_pairs", "vectors", "hard_index.json"), "w") as f1:
        json.dump(hard_index, f1)

    with open(os.path.join(BASE_LD_PATH, language, "batch_id_store.json"), "w") as f2:
        json.dump(batch_id_store, f2)
    with open(os.path.join(BASE_LD_PATH, language, "delimiters.json"), "w") as f3:
        json.dump(delimiters, f3)

    with open(os.path.join(BASE_LD_PATH, language, "info.json"), "r") as f4:
        info = json.load(f4)
    info["language"] = language
    info["documents"]["vectorized"] = []
    info["pairs"] = []
    with open(os.path.join(BASE_LD_PATH, language, "info.json"), "w") as f5:
        json.dump(info, f5)
    return True




def usercode(username:str)->str:
    ucode = username.replace(".","_")
    ucode = username.split("@")[0]
    return ucode
