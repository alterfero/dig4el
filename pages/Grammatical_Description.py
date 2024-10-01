import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu, agents
from libs import knowledge_graph_utils as kgu
from exploration import simple_inferences as si
import json

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "tl_name" not in st.session_state:
    st.session_state["tl_name"] = ""
if "tl_pk" not in st.session_state:
    st.session_state["tl_pk"] = ""
if "tl_id" not in st.session_state:
    st.session_state["tl_id"] = ""
if "delimiters" not in st.session_state:
    st.session_state["delimiters"] = []
if "selected_topics" not in st.session_state:
    st.session_state["selected_topics"] = []
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = ""
if "cq_transcriptions" not in st.session_state:
    st.session_state["cq_transcriptions"] = []
if "consolidated_transcriptions" not in st.session_state:
    st.session_state["consolidated_transcriptions"] = {}

if "tl_knowledge" not in st.session_state:
    st.session_state["tl_knowledge"] = {
        "known":{},
        "observed":{},
        "inferred":{}
    }

topics = {"Canonical word orders": {
"obs": {
  "Order of Subject, Object and Verb": 81,
  "Order of Subject and Verb": 82,
  "Order of Object and Verb": 83,
  "Order of Adjective and Noun": 87,
  "Order of Demonstrative and Noun": 88,
  "Order of Numeral and Noun": 89,
  "Order of Relative Clause and Noun": 90
            },
"nobs": {
  "Order of Object, Oblique, and Verb": 84,
  "Order of Adposition and Noun Phrase": 85,
  "Order of Adverbial Subordinator and Clause": 94,
  "Order of Genitive and Noun": 86,
  "Order of Degree Word and Adjective": 91
            }
        }
    }
ppks_of_interest = list(topics["Canonical word orders"]["obs"].values()) + list(topics["Canonical word orders"]["nobs"].values())

default_delimiters = [ " ", ".",",",";",":","!","?","\u2026","'"]

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base Features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

    st.write("**Advanced features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.title("Generate grammatical descriptions")
st.subheader("Topic")

# TOPICS AND LANGUAGE
st.session_state["selected_topics"] = st.selectbox("Choose topics", topics.keys())
tl = st.selectbox("Language name?", ["not in the list"] + list(wu.language_pk_id_by_name.keys()))
if tl == "not in the list":
    st.session_state["tl_name"] = st.text_input("Language name?")
    st.session_state["tl_pk"] = None
    st.session_state["tl_id"] = None
    st.session_state["delimiters"] = default_delimiters
else:
    st.session_state["tl_name"] = tl
    st.session_state["tl_pk"] = wu.language_pk_id_by_name[tl]["pk"]
    st.session_state["tl_id"] = wu.language_pk_id_by_name[tl]["id"]
    with open ("./data/delimiters.json", "r") as f:
        delimiters_dict = json.load(f)
        if tl in delimiters_dict.keys():
            st.session_state["delimiters"] = delimiters_dict[tl]
            st.write("Delimiters found for {}: {}".format(tl, st.session_state["delimiters"]))
        else:
            st.session_state["delimiters"] = default_delimiters
            st.write("Using default delimiters: {}".format(st.session_state["delimiters"]))

# LOADING CQ TRANSCRIPTIONS
cqs = st.file_uploader("Load Conversational Questionnaires' transcriptions", type="json", accept_multiple_files=True)
if cqs is not None:
    st.session_state["cq_transcriptions"] = []
    for cq in cqs:
        new_cq = json.load(cq)
        st.session_state["cq_transcriptions"].append(new_cq)
    st.session_state["loaded_existing"] = True
    st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))

# RETRIEVING TOPICAL DATA FROM WALS
if st.session_state["tl_name"] != "":
    # if tl in WALS, get known values
    if st.session_state["tl_pk"] is not None:
        if st.session_state["tl_pk"] in wu.domain_elements_by_language.keys():
            known_values =  wu.domain_elements_by_language[st.session_state["tl_pk"]]
            for known_value in known_values:
                if int(wu.param_pk_by_de_pk[str(known_value)]) in ppks_of_interest:
                    p_name = wu.parameter_name_by_pk[wu.param_pk_by_de_pk[str(known_value)]]
                    de_name = wu.domain_element_by_pk[str(known_value)]["name"]
                    st.session_state["tl_knowledge"]["known"][p_name] = de_name
    if len(st.session_state["tl_knowledge"]["known"]) != 0:
        st.write("{} known parameters of interest in {}.".format(len(st.session_state["tl_knowledge"]["known"]), st.session_state["tl_name"]))
        if st.checkbox("See known parameters of interest"):
            st.write(st.session_state["tl_knowledge"])

# PROCESSING TRANSCRIPTIONS
if st.session_state["cq_transcriptions"] != []:
    # Consolidating transcriptions
    st.session_state["consolidated_transcriptions"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                                        st.session_state["cq_transcriptions"],
                                        st.session_state["tl_name"],
                                        st.session_state["delimiters"])
    # computing word order stats
    word_order_stats = si.analyze_word_order(st.session_state["consolidated_transcriptions"], st.session_state["delimiters"])

    # displaying details
    with st.expander("Detailed observations on word order of transcriptions"):
        colc, colv = st.columns(2)
        colc.subheader("Order of the Subject, Object and Verb")
        colc.write("Intransitive events")
        colc.write(
            "Distribution of {} intransitive events with known target representations in the knowledge graph:".format(
                len(word_order_stats["intransitive"])))
        iwo_df = pd.DataFrame.from_dict(word_order_stats["stats"]["intransitive_word_order"], orient="index",
                                        columns=["count"]).sort_values(
            by="count", ascending=False).T
        colc.dataframe(iwo_df)

        colv.write("Transitive events")
        colv.write(
            "Distribution of {} transitive events with known target representations in the semantic graph:".format(
                len(word_order_stats["transitive"])))
        two_df = pd.DataFrame.from_dict(word_order_stats["stats"]["transitive_word_order"], orient="index",
                                        columns=["count"]).sort_values(by="count", ascending=False).T
        colv.dataframe(two_df)

        s = st.selectbox("select order", list(word_order_stats["index_lists_by_order"].keys()))
        for index in word_order_stats["index_lists_by_order"][s]:
            df = kgu.build_gloss_df(st.session_state["consolidated_transcriptions"], index, st.session_state["delimiters"])
            st.dataframe(df)

if st.session_state["tl_name"] == "Marquesan":
    if st.checkbox("Show example of output on the order of words, with a focus on the order of subject, object and verb. "):
        m1 = """
        #### The order of words in Marquesan
        
        In Marquesan, the order of words is a little different from what you might expect in English. 
        For example, when talking about **possession**, Marquesan places the thing being owned before the owner. 
        When describing something with a **relative clause** (like 'the house that Jack built'), 
        the noun comes first, followed by the description, so you’d say 'the house' before adding the details. 
        **Numbers** come before nouns, so you’d say 'two dogs' and adjectives follow the noun, like 'dog big' instead of 'big dog'. 
        The language uses **prepositions**, just like in English, so words like 'in' or 'on' come before the noun. 
        When forming sentences, the **verb** usually comes first, followed by the subject and then the object (this is called VSO order). 
        For example, you might say 'ate he fish' instead of 'he ate fish'
        """
        m2 = """
        #### Let's look at some examples:
    
        1. **Marquesan: ua 'ite 'oe i te ata o to'u hua'a**  (Have you seen pictures of my family?)
           In this sentence the word for "seeing" (*ua 'ite*) comes first, followed by the subject "you" (*'oe*), and then the object "pictures of my family" (*te ata o to'u hua'a*). Marquesan also uses prepositions like "of" (*o*) before the noun they describe.
    
        2. **Marquesan: ua 'ite 'oe ia 'aua**  (I have met them)
           In this sentence the verb "meeting" (*ua 'ite*) comes first, followed by "you" (*'oe*) and then "them" (*'aua*).
    
        3. **Marquesan: ua 'ite au i to 'oe mata me katakata**  
           In the sentence "I recognized your eyes and your smile," the same pattern holds: the verb "recognizing" (*ua 'ite*) comes first, the subject "I" (*au*) follows, adjectives come after nouns, and "and" (*me*) connects two things ("your eyes" and "your smile").
    
        This shows how Marquesan sentences are structured with the verb first and other words following in a set order.
        """
        st.markdown(m1)
        st.markdown(m2)