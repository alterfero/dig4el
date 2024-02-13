import streamlit as st
import json
from collections import defaultdict, Counter
from libs import utils

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "selected_language" not in st.session_state:
    st.session_state["selected_language"] = "French"
if "is_language_chosen" not in st.session_state:
    st.session_state["is_language_chosen"] = False
if "selected_corpus" not in st.session_state:
    st.session_state["selected_corpus"] = "French"
if "is_corpus_chosen" not in st.session_state:
    st.session_state["is_corpus_chosen"] = False

# The language stat builder uses any corpus in a given target language to build a language stat json file.
# The corpus must be a text file with one sentence per line.
# The language stat json file is a dictionary with the following structure:
# { "target language": "target language",
# { "word-stat": { "word": {"frequency": f, "most frequent preceding": {"word1": f1, "word2": f2, ...}, "most frequent following": {"word1": f1, "word2": f2, ...}}, ...}}
# The language stat json file is saved in the folder ./data/language_stats

def get_corpus_words_stats(file_path):
    word_stats = defaultdict(lambda: {"frequency": 0, "most frequent preceding": Counter(), "most frequent following": Counter()})
    total_word_count = 0

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            sentence = line.strip().split('\t', 1)[1]
            words = [word for word in sentence.split() if not utils.is_number(word)]

            total_word_count += len(words)

            for i, word in enumerate(words):
                word_stats[word]["frequency"] += 1

                if i > 0:
                    preceding_word = words[i - 1]
                    word_stats[word]["most frequent preceding"][preceding_word] += 1

                if i < len(words) - 1:
                    following_word = words[i + 1]
                    word_stats[word]["most frequent following"][following_word] += 1

    for word, stats in word_stats.items():
        # Convert counts to frequencies (per 1000 words)
        stats["frequency"] = (stats["frequency"] / total_word_count) * 1000

        # Process preceding and following word frequencies
        for key in ["most frequent preceding", "most frequent following"]:
            total_count = sum(stats[key].values())
            top_words = stats[key].most_common(10)
            stats[key] = {word: (count / total_count) * 1000 for word, count in top_words}

    # Convert Counters to dicts for final output
    for word, stats in word_stats.items():
        stats["most frequent preceding"] = dict(stats["most frequent preceding"])
        stats["most frequent following"] = dict(stats["most frequent following"])

    return dict(word_stats)

available_languages = utils.list_folders("./data/corpora")
selected_language = st.selectbox("Select a language", available_languages)
if st.session_state["selected_language"] != selected_language:
    st.session_state["is_language_chosen"] = False
    st.session_state["is_corpus_chosen"] = False
if st.button("Select language"):
    st.session_state["selected_language"] = selected_language
    st.session_state["is_language_chosen"] = True

if st.session_state.is_language_chosen:
    available_corpora = utils.list_txt_files("./data/corpora/{}".format(st.session_state["selected_language"]))
    selected_corpus = st.selectbox("Select a corpus", available_corpora)
    if st.button("Select corpus"):
        st.session_state["selected_corpus"] = selected_corpus
        st.session_state["is_corpus_chosen"] = True

if st.session_state["is_corpus_chosen"]:
    statistics = get_corpus_words_stats("./data/corpora/{}/{}".format(st.session_state["selected_language"], st.session_state["selected_corpus"]))
    with open("./data/language_stats/{}.json".format(st.session_state["selected_language"]), "w") as outfile:
        json.dump(statistics, outfile)
        st.write("Statistics saved")

    # display the 20 most frequent words, their frequencies and for each the 5 most frequent preceding and following words
    st.write("Statistics for corpus {} in {}".format(st.session_state["selected_corpus"], st.session_state["selected_language"]))
    for word in sorted(statistics.keys(), key=lambda x: statistics[x]["frequency"], reverse=True)[:20]:
        st.write(word, statistics[word]["frequency"])
        st.write("Preceding words:", statistics[word]["most frequent preceding"])
        st.write("Following words:", statistics[word]["most frequent following"])




