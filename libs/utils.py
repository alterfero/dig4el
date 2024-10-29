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

import re
import os
import json
from os.path import isfile, join
from os import listdir
import pandas as pd

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
    with open(concept_json_file, "r") as f:
        data = json.load(f)
    for concept in data.keys():
        data[concept][field_name] = field_value
    with open(concept_json_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Field {field_name} added to {concept_json_file}")

def get_key_by_value(d, target_value):
    return next((key for key, value in d.items() if value == target_value), None)

def is_number(s):
    """Check if a string is a number."""
    return re.match(r"^\d+$", s) is not None

def listify(string):
    return(string.split("..."))

def clean_sentence(sentence):
    """Clean a sentence."""
    nil_list = [",", ";"]
    space_list = ["'", "’", "(", ")", ":", ".", "!", "?", "…", "—", "-", "–", "—", "«"]
    out = sentence.lower()
    for item in nil_list:
        out = out.replace(item, "")
    for item in space_list:
        out = out.replace(item, " ")
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

def get_word_stats(recordings_list):
    word_stats = {}
    word_count = 0
    for entry in recordings_list:
        cl_sent = clean_sentence(entry["recording"])
        for word in cl_sent.split():
            if word not in word_stats:
                word_stats[word] = 0
            word_stats[word] += 1
            word_count += 1
    for word in word_stats:
        word_stats[word] = word_stats[word] / word_count * 1000 # frequency per 1000 words
    return word_stats

def get_Ngrams_stats_from_recording(recordings_list):
    """Get characters bigrams and trigrams frequencies from words from a list of recordings."""
    monograms = {}
    bigrams = {}
    trigrams = {}
    tetragrams = {}
    monograms_count = 0
    bigrams_count = 0
    trigrams_count = 0
    tetragrams_count = 0
    for entry in recordings_list:
        for word in tokenize(clean_sentence(entry["recording"])):
            for char in word:
                monograms_count += 1
                if char not in monograms:
                    monograms[char] = 0
                monograms[char] += 1
            if len(word) > 1:
                for i in range(len(word) - 1):
                    bigrams_count += 1
                    bigram = word[i:i + 2]
                    if bigram not in bigrams:
                        bigrams[bigram] = 0
                    bigrams[bigram] += 1
            if len(word) > 2:
                for i in range(len(word) - 2):
                    trigrams_count += 1
                    trigram = word[i:i + 3]
                    if trigram not in trigrams:
                        trigrams[trigram] = 0
                    trigrams[trigram] += 1
            if len(word) > 3:
                for i in range(len(word) - 3):
                    tetragrams_count += 1
                    tetragram = word[i:i + 4]
                    if tetragram not in trigrams:
                        tetragrams[tetragram] = 0
                    tetragrams[tetragram] += 1
    for char in monograms:
        monograms[char] = monograms[char] / monograms_count * 1000
    for bigram in bigrams:
        bigrams[bigram] = bigrams[bigram] / bigrams_count * 1000
    for trigram in trigrams:
        trigrams[trigram] = trigrams[trigram] / trigrams_count * 1000
    for tetragram in tetragrams:
        tetragrams[tetragram] = tetragrams[tetragram] / tetragrams_count * 1000
    return {
        "monograms": monograms,
        "bigrams": bigrams,
        "trigrams": trigrams,
        "tetragrams": tetragrams,
    }

def list_all_recordings_in_language_l(language):
    questionnaires_folder = "../questionnaires"
    recordings_folder = "../recordings"
    recordings = []
    cq_json_list = [f for f in listdir(questionnaires_folder) if
                    isfile(join(questionnaires_folder, f)) and f.endswith(".json")]
    for cq in cq_json_list:
        # determine if there is a folder with the same name as the CQ in ./recordings
        if cq[:-5] in listdir(recordings_folder):
            available_languages = listdir(recordings_folder + "/" + cq[:-5])
            if language in available_languages:
                recordings = listdir(join(recordings_folder, cq[:-5], language))
                if ".DS_Store" in recordings:
                    recordings.remove(".DS_Store")
    return recordings

def clean_recordings():
    questionnaires_folder = "../questionnaires"
    recordings_folder = "../recordings"
    recordings = []
    cq_json_list = [f for f in listdir(questionnaires_folder) if
                    isfile(join(questionnaires_folder, f)) and f.endswith(".json")]
    for cq in cq_json_list:
        # determine if there is a folder with the same name as the CQ in ./recordings
        if cq[:-5] in listdir(recordings_folder):
            available_languages = listdir(recordings_folder + "/" + cq[:-5])
            if ".DS_Store" in available_languages:
                available_languages.remove(".DS_Store")
            for language in available_languages:
                recordings = listdir(join(recordings_folder, cq[:-5], language))
                if ".DS_Store" in recordings:
                    recordings.remove(".DS_Store")
                for recording in recordings:
                    recording_json = json.load(open(join(recordings_folder, cq[:-5], language, recording)))
                    for item in recording_json["data"]:
                        recording_json["data"][item]["translation"] = (
                            normalize_sentence(recording_json["data"][item]["translation"]))
                        for concept_word in recording_json["data"][item]["concept_words"]:
                            recording_json["data"][item]["concept_words"][concept_word] = (
                                normalize_sentence(recording_json["data"][item]["concept_words"][concept_word]))
                    with open(join(recordings_folder, cq[:-5], language, recording), "w") as f:
                        json.dump(recording_json, f, indent=4)
                        print("Recording {} cleaned".format(recording))