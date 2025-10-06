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

from collections.abc import Mapping, Sequence


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
    nil_list = [",", ";"]
    space_list = ["'", "’", "(", ")", ":", ".", "!", "?", "…", "—", "-", "–", "—", "«"]
    or_list = ["/", "|"]
    out = sentence.lower()
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
        out = out[:length]
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

# def get_word_stats(recordings_list):
#     word_stats = {}
#     word_count = 0
#     for entry in recordings_list:
#         cl_sent = clean_sentence(entry["recording"])
#         for word in cl_sent.split():
#             if word not in word_stats:
#                 word_stats[word] = 0
#             word_stats[word] += 1
#             word_count += 1
#     for word in word_stats:
#         word_stats[word] = word_stats[word] / word_count * 1000 # frequency per 1000 words
#     return word_stats
#
# def get_Ngrams_stats_from_recording(recordings_list):
#     """Get characters bigrams and trigrams frequencies from words from a list of recordings."""
#     monograms = {}
#     bigrams = {}
#     trigrams = {}
#     tetragrams = {}
#     monograms_count = 0
#     bigrams_count = 0
#     trigrams_count = 0
#     tetragrams_count = 0
#     for entry in recordings_list:
#         for word in tokenize(clean_sentence(entry["recording"])):
#             for char in word:
#                 monograms_count += 1
#                 if char not in monograms:
#                     monograms[char] = 0
#                 monograms[char] += 1
#             if len(word) > 1:
#                 for i in range(len(word) - 1):
#                     bigrams_count += 1
#                     bigram = word[i:i + 2]
#                     if bigram not in bigrams:
#                         bigrams[bigram] = 0
#                     bigrams[bigram] += 1
#             if len(word) > 2:
#                 for i in range(len(word) - 2):
#                     trigrams_count += 1
#                     trigram = word[i:i + 3]
#                     if trigram not in trigrams:
#                         trigrams[trigram] = 0
#                     trigrams[trigram] += 1
#             if len(word) > 3:
#                 for i in range(len(word) - 3):
#                     tetragrams_count += 1
#                     tetragram = word[i:i + 4]
#                     if tetragram not in trigrams:
#                         tetragrams[tetragram] = 0
#                     tetragrams[tetragram] += 1
#     for char in monograms:
#         monograms[char] = monograms[char] / monograms_count * 1000
#     for bigram in bigrams:
#         bigrams[bigram] = bigrams[bigram] / bigrams_count * 1000
#     for trigram in trigrams:
#         trigrams[trigram] = trigrams[trigram] / trigrams_count * 1000
#     for tetragram in tetragrams:
#         tetragrams[tetragram] = tetragrams[tetragram] / tetragrams_count * 1000
#     return {
#         "monograms": monograms,
#         "bigrams": bigrams,
#         "trigrams": trigrams,
#         "tetragrams": tetragrams,
#     }

# def list_all_recordings_in_language_l(language):
#     questionnaires_folder = "../questionnaires"
#     recordings_folder = "../recordings"
#     recordings = []
#     cq_json_list = [f for f in listdir(questionnaires_folder) if
#                     isfile(join(questionnaires_folder, f)) and f.endswith(".json")]
#     for cq in cq_json_list:
#         # determine if there is a folder with the same name as the CQ in ./recordings
#         if cq[:-5] in listdir(recordings_folder):
#             available_languages = listdir(recordings_folder + "/" + cq[:-5])
#             if language in available_languages:
#                 recordings = listdir(join(recordings_folder, cq[:-5], language))
#                 if ".DS_Store" in recordings:
#                     recordings.remove(".DS_Store")
#     return recordings

# def clean_recordings():
#     questionnaires_folder = "../questionnaires"
#     recordings_folder = "../recordings"
#     recordings = []
#     cq_json_list = [f for f in listdir(questionnaires_folder) if
#                     isfile(join(questionnaires_folder, f)) and f.endswith(".json")]
#     for cq in cq_json_list:
#         # determine if there is a folder with the same name as the CQ in ./recordings
#         if cq[:-5] in listdir(recordings_folder):
#             available_languages = listdir(recordings_folder + "/" + cq[:-5])
#             if ".DS_Store" in available_languages:
#                 available_languages.remove(".DS_Store")
#             for language in available_languages:
#                 recordings = listdir(join(recordings_folder, cq[:-5], language))
#                 if ".DS_Store" in recordings:
#                     recordings.remove(".DS_Store")
#                 for recording in recordings:
#                     recording_json = json.load(open(join(recordings_folder, cq[:-5], language, recording), encoding='utf-8'))
#                     for item in recording_json["data"]:
#                         recording_json["data"][item]["translation"] = (
#                             normalize_sentence(recording_json["data"][item]["translation"]))
#                         for concept_word in recording_json["data"][item]["concept_words"]:
#                             recording_json["data"][item]["concept_words"][concept_word] = (
#                                 normalize_sentence(recording_json["data"][item]["concept_words"][concept_word]))
#                     with open(join(recordings_folder, cq[:-5], language, recording), "w", encoding='utf-8') as f:
#                         json.dump(recording_json, f, indent=4)
#                         print("Recording {} cleaned".format(recording))

# print(clean_sentence("Have you seen pictures of my family?", filename=True))