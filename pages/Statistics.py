import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils, knowledge_graph_utils as kgu
from libs import utils
from libs import stats
import pandas as pd


st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "knowledge_graph" not in st.session_state:
    st.session_state["knowledge_graph"] = {}
if "is_kg_computed" not in st.session_state:
    st.session_state["is_kg_computed"] = False
if "is_blind_word_statistics_computed" not in st.session_state:
    st.session_state["is_blind_word_statistics_computed"] = False

st.title("Statistics and exploration")

concept_kson = json.load(open("./data/concepts.json"))

delimiters = {
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"]
}

language = st.selectbox("Select a language", [ "marquesan (Nuku Hiva)", "english", "french"], index=0)
st.session_state["knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = kgu.build_knowledge_graph(language)
st.write("total_target_word_count: {}".format(total_target_word_count))
if st.session_state["knowledge_graph"] != {}:
    st.session_state["is_kg_computed"] = True

#build statistics on target language
if st.session_state["is_kg_computed"]:
    if st.session_state["knowledge_graph"] != {}:
        st.subheader("Blind word statistics")
        blind_word_stats = stats.build_blind_word_stats_from_knowledge_graph(st.session_state["knowledge_graph"], delimiters[language])
        st.write("Knowledge graph contains {} sentences, {} words with {} unique words"
                 .format(len(st.session_state["knowledge_graph"]), total_target_word_count, len(unique_words)))
        colo, colp = st.columns(2)
        colo.metric("Type-Token Ratio (TTR)", str(round(len(unique_words)*100/total_target_word_count))+"%", "Percentage of unique words in the target language")
        with colo.popover("i"):
            st.markdown("TTR is the percentage of unique words in the target language. "
                        "Low TTR indicates a high repetition of words in the language, potentially indicating an isolating language."
                        "High TTR ratio indicates a low repetition of words, potentially indicating an inflective language")
        blind_entropy = stats.compute_average_blind_entropy(blind_word_stats)
        colp.metric("Average blind entropy", str(round(blind_entropy*100))+"%", "Overall unpredictability of word sequences")
        with colp.popover("i"):
            st.markdown("The average language entropy gives us an estimate of the overall unpredictability of word sequences in a given language. "
                        "It reflects how much information is needed, on average, to predict the next word in a sentence "
                        "based on the preceding and following words."
                        "Blind entropy does not use information from the knowledge graph, only the target language data.")
            st.markdown("Higher entropy indicates more unpredictability, meaning each word could be followed or preceded by a larger variety of words.")
        st.session_state["is_blind_word_statistics_computed"] = True

colr, colt = st.columns(2)
with colt.expander("word exploration"):
    word = st.selectbox("select a word", unique_words)
    refs = kgu.get_sentences_with_word(st.session_state["knowledge_graph"], word, language)
    st.write("{} appears in {} sentences.".format(word, len(refs)))
    for ref in refs:
        st.write("**{}**".format(st.session_state["knowledge_graph"][ref]["recording_data"]["translation"]))
        st.write("{}".format(st.session_state["knowledge_graph"][ref]["recording_data"]["cq"]))

with colr.expander("Grammar exploration"):
    if st.session_state["is_blind_word_statistics_computed"]:
        # let the user choose a grammaticalized concept to examine
        value_loc_dict = {}
        value_count_dict = {}
        available_f = ["INTENT", "PREDICATE", "EVENT TENSE", "POLARITY", "PERSONAL DEICTIC", "ASPECT"]
        selected_f = st.selectbox("Choose a concept to explore", available_f)
        f_values = graphs_utils.get_leaves_from_node(concept_kson, selected_f)

        # stats on values and their locations in the knowledge graph: value_loc_dict
        if selected_f in ["INTENT", "PREDICATE"]:
            print("Selected {}".format(selected_f))
            f = selected_f.lower()
            for v in f_values:
                value_loc_dict[v] = []
            value_loc_dict["neutral"] = []
            for entry_key in st.session_state["knowledge_graph"]:
                if f in st.session_state["knowledge_graph"][entry_key]["sentence_data"].keys():
                    local_value_list = st.session_state["knowledge_graph"][entry_key]["sentence_data"][f]
                    for local_value in local_value_list:
                        if local_value in value_loc_dict:
                            value_loc_dict[local_value].append(entry_key)
                        else:
                            print("Stats on values: Unknown value {} in entry {}".format(local_value, entry_key))
                else:
                    print("{} absent of entry {} in knowledge graph".format(f, entry_key))
            for item in value_loc_dict:
                value_count_dict[item] = len(value_loc_dict[item])
            # build sorted df
            value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(by="count", ascending=False)
            st.write(value_count_df)

        elif selected_f in ["PERSONAL DEICTIC"]:
            print("Selected {}".format(selected_f))
            for v in f_values:
                value_loc_dict[v + " AGENT"] = []
                value_loc_dict[v + " PATIENT"] = []
                value_loc_dict[v + " POSSESSOR"] = []
                value_loc_dict[v + " OTHER"] = []
            for entry_key in st.session_state["knowledge_graph"]:
                for graph_key in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"]:
                    if "value" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]:
                        if st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"] in f_values:
                            local_value = st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"]
                            # semantic role
                            if "AGENT" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["path"]:
                                value_loc_dict[local_value + " AGENT"].append(entry_key)
                            elif "PATIENT" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["path"]:
                                value_loc_dict[local_value + " PATIENT"].append(entry_key)
                            elif "POSSESSOR" in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["path"]:
                                value_loc_dict[local_value + " POSSESSOR"].append(entry_key)
                            else:
                                value_loc_dict[local_value + " OTHER"].append(entry_key)
            for item in value_loc_dict:
                value_count_dict[item] = len(value_loc_dict[item])
            # build sorted df
            value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(by="count",
                                                                                                                     ascending=False)
            st.write(value_count_df)
        else:
            print("Selected {}".format(selected_f))
            for v in f_values:
                value_loc_dict[v] = []
            value_loc_dict["neutral"] = []
            for entry_key in st.session_state["knowledge_graph"]:
                for graph_key in st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"]:
                    if selected_f in graph_key:
                        if "value" in  st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]:
                            if st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"] in f_values:
                                (value_loc_dict[st.session_state["knowledge_graph"][entry_key]["sentence_data"]["graph"][graph_key]["value"]]
                                 .append((entry_key)))
                            else:
                                value_loc_dict["neutral"].append(entry_key)
            for item in value_loc_dict:
                value_count_dict[item] = len(value_loc_dict[item])
            # build sorted df
            value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(by="count",
                                                                                                                     ascending=False)
            st.write(value_count_df)

        # statistical inferences on the way the target language expresses the selected value
        # assumption for now: A value is expressed by one or several words in the sentence.
        # first method is to compare the frequency of each word in sentences where the value is present versus those where it is not.
        v_focus = st.selectbox("choose a focus", value_loc_dict, index=0)
        v_focus_sentences = value_loc_dict[v_focus]
        st.write("{} sentence with {}".format(len(v_focus_sentences), v_focus))
        if st.checkbox("show sentences"):
            for s in v_focus_sentences:
                st.write("**{}**".format(st.session_state["knowledge_graph"][s]["recording_data"]["translation"]))
                st.write(st.session_state["knowledge_graph"][s]["recording_data"]["cq"])
        v_not_focus_sentences = []
        for v in value_loc_dict:
            if v != v_focus:
                v_not_focus_sentences += value_loc_dict[v]

        v_focus_words = []
        v_not_focus_words = []
        for v_focus_sentence in v_focus_sentences:
            v_focus_words += stats.custom_split(st.session_state["knowledge_graph"][v_focus_sentence]["recording_data"]["translation"], delimiters[language])
        for v_not_focus_sentence in v_not_focus_sentences:
            v_not_focus_words += stats.custom_split(st.session_state["knowledge_graph"][v_not_focus_sentence]["recording_data"]["translation"], delimiters[language])
        v_focus_words_count = {}
        for word in v_focus_words:
            if word in v_focus_words_count:
                v_focus_words_count[word] += 1
            else:
                v_focus_words_count[word] = 1
        v_not_focus_words_count = {}
        for word in v_not_focus_words:
            if word in v_not_focus_words_count:
                v_not_focus_words_count[word] += 1
            else:
                v_not_focus_words_count[word] = 1

        v_focus_word_frequency = {}
        for word in v_focus_words_count:
            v_focus_word_frequency[word] = v_focus_words_count[word]*1000/total_target_word_count
        v_not_focus_word_frequency = {}
        for word in v_not_focus_words_count:
            v_not_focus_word_frequency[word] = v_not_focus_words_count[word]*1000/total_target_word_count

        # diff frequencies between v and not v
        v_focus_word_diff_frequency_v_not_v = {}
        for word in v_focus_word_frequency:
            if word in v_not_focus_word_frequency:
                v_focus_word_diff_frequency_v_not_v[word] = v_focus_word_frequency[word] - v_not_focus_word_frequency[word]
            else:
                v_focus_word_diff_frequency_v_not_v[word] = v_focus_word_frequency[word]


        v_focus_word_diff_frequency_v_not_v_df = pd.DataFrame.from_dict(v_focus_word_diff_frequency_v_not_v, orient="index", columns=["frequency"]).sort_values(by="frequency", ascending=False)
        st.write("Diff frequency between v and not v in sentences where {} is present".format(v_focus))
        st.write(v_focus_word_diff_frequency_v_not_v_df)

    else:
        st.write("statistics not computed")














