import re
import os
import json

def add_field_to_concept_json(concept_json_file, field_name, field_value):
    """Add a field to a concept json file."""
    with open(concept_json_file, "r") as f:
        data = json.load(f)
    for concept in data.keys():
        data[concept][field_name] = field_value
    with open(concept_json_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Field {field_name} added to {concept_json_file}")


def is_number(s):
    """Check if a string is a number."""
    return re.match(r"^\d+$", s) is not None

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


def all_recordings_with(pronoun, recordings):
    return [recording for recording in recordings if pronoun in recording["cq"]["features"]]

def all_recordings_with_concept(concept, recordings):
    out_recordings = []
    for recording in recordings:
        if "concept" in recording["cq"].keys():
            if concept in recording["cq"]["concept"]:
                out_recordings.append(recording)
    return out_recordings


def concept_stats(recordings, concept):
    """knowing in which recordings a given concept is present,
    create statistics on words to make assumptions about
    the concept expression in the corpus"""
    recordings_stats = get_word_stats(recordings)
    concept_recordings = all_recordings_with_concept(concept, recordings)
    concept_words_stats = get_word_stats(concept_recordings)
    # create diff stats for words
    diff_words_stats = {}
    for word in concept_words_stats:
        diff_words_stats[word] = concept_words_stats[word] - recordings_stats[word]
    # return the word with the highest difference
    try:
        max_diff_word = max(diff_words_stats, key=diff_words_stats.get)
        max_diff_word_value = diff_words_stats[max_diff_word]
        return {
            "word": max_diff_word,
            "word_value": max_diff_word_value,
        }
    except:
        return {
            "word": "NA",
            "word_value": 0,
        }

def feature_stats(recordings, feature):
    """knowing in which recordings a given feature is present,
    create statistics on ngrams and words to make assumptions about
    the feature expression in the corpus"""
    recordings_stats = get_word_stats(recordings)
    recordings_ngrams_stats = get_Ngrams_stats_from_recording(recordings)
    feature_recordings = all_recordings_with(feature, recordings)
    feature_words_stats = get_word_stats(feature_recordings)
    feature_ngrams_stats = get_Ngrams_stats_from_recording(feature_recordings)
    # create diff stats for ngrams and words
    diff_words_stats = {}
    diff_ngrams_stats = {"monograms": {}, "bigrams": {}, "trigrams": {}, "tetragrams": {}}
    for word in feature_words_stats:
        diff_words_stats[word] = feature_words_stats[word] - recordings_stats[word]
    for monogram in feature_ngrams_stats["monograms"]:
        diff_ngrams_stats["monograms"][monogram] = feature_ngrams_stats["monograms"][monogram] - recordings_ngrams_stats["monograms"][monogram]
    for bigram in feature_ngrams_stats["bigrams"]:
        diff_ngrams_stats["bigrams"][bigram] = feature_ngrams_stats["bigrams"][bigram] - recordings_ngrams_stats["bigrams"][bigram]
    for trigram in feature_ngrams_stats["trigrams"]:
        diff_ngrams_stats["trigrams"][trigram] = feature_ngrams_stats["trigrams"][trigram] - recordings_ngrams_stats["trigrams"][trigram]
    for tetragram in feature_ngrams_stats["tetragrams"]:
        diff_ngrams_stats["tetragrams"][tetragram] = feature_ngrams_stats["tetragrams"][tetragram] - recordings_ngrams_stats["tetragrams"][tetragram]
    # return the monogram, bigram, trigram, tetragram and word with the highest difference
    # find word with highest diff:
    try:
        max_diff_word = max(diff_words_stats, key=diff_words_stats.get)
        max_diff_word_value = diff_words_stats[max_diff_word]
        # find monogram with highest diff:
        max_diff_monogram = max(diff_ngrams_stats["monograms"], key=diff_ngrams_stats["monograms"].get)
        max_diff_monogram_value = diff_ngrams_stats["monograms"][max_diff_monogram]
        # find bigram with highest diff:
        max_diff_bigram = max(diff_ngrams_stats["bigrams"], key=diff_ngrams_stats["bigrams"].get)
        max_diff_bigram_value = diff_ngrams_stats["bigrams"][max_diff_bigram]
        # find trigram with highest diff:
        max_diff_trigram = max(diff_ngrams_stats["trigrams"], key=diff_ngrams_stats["trigrams"].get)
        max_diff_trigram_value = diff_ngrams_stats["trigrams"][max_diff_trigram]
        # find tetragram with highest diff:
        max_diff_tetragram = max(diff_ngrams_stats["tetragrams"], key=diff_ngrams_stats["tetragrams"].get)
        max_diff_tetragram_value = diff_ngrams_stats["tetragrams"][max_diff_tetragram]
        return {
            "word": max_diff_word,
            "word_value": max_diff_word_value,
            "monogram": max_diff_monogram,
            "monogram_value": max_diff_monogram_value,
            "bigram": max_diff_bigram,
            "bigram_value": max_diff_bigram_value,
            "trigram": max_diff_trigram,
            "trigram_value": max_diff_trigram_value,
            "tetragram": max_diff_tetragram,
            "tetragram_value": max_diff_tetragram_value,
        }
    except:
        return {
            "word": "NA",
            "word_value": 0,
            "monogram": "NA",
            "monogram_value": 0,
            "bigram": "NA",
            "bigram_value": 0,
            "trigram": "NA",
            "trigram_value": 0,
            "tetragram": "NA",
            "tetragram_value": 0,
        }

