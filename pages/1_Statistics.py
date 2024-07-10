import streamlit as st
import json
from os import listdir, mkdir
from os.path import isfile, join
import time
from libs import graphs_utils, knowledge_graph_utils as kgu
from libs import utils
from libs import stats
import pandas as pd
from collections import OrderedDict


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

def get_key_by_value(d, target_value):
    return next((key for key, value in d.items() if value == target_value), None)

def build_gloss_df(entry):
    sentence_display_ordered_dict = OrderedDict()
    w_list = stats.custom_split(st.session_state["knowledge_graph"][entry]["recording_data"]["translation"], delimiters[language])
    for wd in [w for w in w_list if w]:
        if wd in st.session_state["knowledge_graph"][entry]["recording_data"]["concept_words"].values():
            sentence_display_ordered_dict[wd] = get_key_by_value(
                st.session_state["knowledge_graph"][entry]["recording_data"]["concept_words"], wd)
        else:
            sentence_display_ordered_dict[wd] = ""
    # build dataframe from ordered dict
    return pd.DataFrame.from_dict(sentence_display_ordered_dict, orient="index", columns=["concept"]).T

st.title("Statistics and exploration")

concept_kson = json.load(open("./data/concepts.json"))
delimiters = json.load(open("./data/delimiters.json"))
available_target_languages = list(delimiters.keys())

language = st.selectbox("Select a language", available_target_languages, index=0)
st.session_state["knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = (
    kgu.build_knowledge_graph(language))
st.write("total_target_word_count: {}".format(total_target_word_count))
if st.session_state["knowledge_graph"] != {}:
    st.session_state["is_kg_computed"] = True

#build statistics on target language
if st.session_state["is_kg_computed"]:
    if st.session_state["knowledge_graph"] != {}:
        st.subheader("Blind word statistics")
        blind_word_stats = stats.build_blind_word_stats_from_knowledge_graph(st.session_state["knowledge_graph"], delimiters[language])
        st.write("Knowledge graph in {} contains {} sentences, {} words with {} unique words"
                 .format(language, len(st.session_state["knowledge_graph"]), total_target_word_count, len(unique_words)))
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
with colt.expander("target word exploration"):
    word = st.selectbox("select a word", unique_words)
    refs = kgu.get_sentences_with_word(st.session_state["knowledge_graph"], word, language)
    st.write("***{}*** appears in {} sentences.".format(word, len(refs)))
    # does this word have hard connections to concepts provided by user?
    connected_concepts = kgu.get_concepts_associated_to_word_by_human(st.session_state["knowledge_graph"], word, language)
    if len(connected_concepts) > 1:
        st.write("connection to concepts provided by interviewer:")
        st.dataframe(pd.DataFrame(connected_concepts), column_config={"entry_list": None})
        for cc in connected_concepts:
            st.markdown("#### Sentences with connection to {}:".format(cc))
            for ref in connected_concepts[cc]["entry_list"]:
                st.write("**{}**".format(st.session_state["knowledge_graph"][ref]["recording_data"]["translation"]))
                st.write("{}".format(st.session_state["knowledge_graph"][ref]["recording_data"]["cq"]))
                sdf = build_gloss_df(ref)
                st.dataframe(sdf, use_container_width=True)
    else:
        st.write("no connection to concepts provided by interviewer.")
        for ref in refs:
            st.write("**{}**".format(st.session_state["knowledge_graph"][ref]["recording_data"]["translation"]))
            st.write("{}".format(st.session_state["knowledge_graph"][ref]["recording_data"]["cq"]))
            sdf = build_gloss_df(ref)
            st.dataframe(sdf, use_container_width=True)

with colr.expander("Grammar exploration"):
    if st.session_state["is_blind_word_statistics_computed"]:
        # let the user choose a grammaticalized concept to examine
        available_f = ["INTENT", "PREDICATE", "EVENT TENSE", "POLARITY", "PERSONAL DEICTIC", "ASPECT"]
        selected_f = st.selectbox("Choose a concept to explore", available_f)
        value_loc_dict = kgu.get_value_loc_dict(st.session_state["knowledge_graph"], concept_kson, selected_f, delimiters[language])

        # display values of selected_f and their count
        value_count_dict = {}
        for item in value_loc_dict:
            value_count_dict[item] = len(value_loc_dict[item])
        # build sorted df
        value_count_df = pd.DataFrame.from_dict(value_count_dict, orient="index", columns=["count"]).sort_values(
            by="count",
            ascending=False)
        st.write(value_count_df)

        # statistical inferences on the way the target language expresses the selected value
        # assumption for now: A value is expressed by one or several words in the sentence.
        # first method is to compare the frequency of each word in sentences where the value is present versus those where it is not.
        v_focus = st.selectbox("choose a value", value_loc_dict, index=0)
        v_focus_sentences = value_loc_dict[v_focus]
        st.write("{} sentence with {}".format(len(v_focus_sentences), v_focus))
        if st.checkbox("show sentences"):
            for s in v_focus_sentences:
                st.write("**{}**".format(st.session_state["knowledge_graph"][s]["recording_data"]["translation"]))
                st.write(st.session_state["knowledge_graph"][s]["recording_data"]["cq"])
                sdf = build_gloss_df(s)
                st.dataframe(sdf, use_container_width=True)

        v_focus_word_diff_frequency_v_not_v = kgu.get_diff_word_statistics_with_value_loc_dict(
            st.session_state["knowledge_graph"], value_loc_dict, v_focus, total_target_word_count, delimiters[language])

        v_focus_word_diff_frequency_v_not_v_df = pd.DataFrame.from_dict(v_focus_word_diff_frequency_v_not_v, orient="index", columns=["frequency"]).sort_values(by="frequency", ascending=False)
        st.write("Diff frequency between v and not v in sentences where {} is present".format(v_focus))
        st.write(v_focus_word_diff_frequency_v_not_v_df)

    else:
        st.write("statistics not computed")














