import copy

import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu, agents
from libs import knowledge_graph_utils as kgu
from libs import cq_observers as obs
from exploration import simple_inferences as si
from libs import agents
import json
import openai

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
        "known_pk":{},
        "observed":{},
        "inferred":{}
    }
if "ga" not in st.session_state:
    st.session_state["ga"] = None
if "known_processed" not in st.session_state:
    st.session_state["known_processed"] = False
if "observations_processed" not in st.session_state:
    st.session_state["observations_processed"] = False
if "prompt_content" not in st.session_state:
    st.session_state["prompt_content"] = {
        "canonical word order": {}
    }
if "redacted" not in st.session_state:
    st.session_state["redacted"] = ""
if "obs" not in st.session_state:
    st.session_state["obs"] = {}

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

delimiters_bank = [
    " ",  # Space
    ".",  # Period or dot
    "?",  # Interrogation mark
    "!",  # Exclamation mark
    ",",  # Comma
    "·",  # Middle dot (interpunct)
    "‧",  # Small interpunct (used in some East Asian scripts)
    "․",  # Armenian full stop
    "-",  # Hyphen or dash (used in compound words or some languages)
    "_",  # Underscore (used in some digital texts and programming)
    "‿",  # Tironian sign (used in Old Irish)
    "、",  # Japanese comma
    "。",  # Japanese/Chinese full stop
    "።",  # Ge'ez (Ethiopian script) word separator
    ":",  # Colon
    ";",  # Semicolon
    "؟",  # Arabic question mark
    "٬",  # Arabic comma
    "؛",  # Arabic semicolon
    "۔",  # Urdu full stop
    "।",  # Devanagari danda (used in Hindi and other Indic languages)
    "॥",  # Double danda (used in Sanskrit and other Indic texts)
    "𐩖",  # South Arabian word divider
    "𐑀",  # Old Hungarian word separator
    "་",  # Tibetan Tsheg (used in Tibetan script)
    "᭞",  # Sundanese word separator
    "᠂",  # Mongolian comma
    "᠃",  # Mongolian full stop
    " ",  # Ogham space mark (used in ancient Irish writing)
    "꓿",  # Lisu word separator
    "፡",  # Ge'ez word separator
    "'",  # Apostrophe (used for contractions and possessives)
    "…",  # Ellipsis
    "–",  # En dash
    "—",  # Em dash
]

default_delimiters = [ " ", ".",",",";",":","!","?","\u2026","'"]

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.title("Generate grammatical descriptions")
with st.popover("i"):
    st.write("This is an early prototype of inferential outputs, enabled for testing purposes. Outputs are meant to be reviewed by a speaker of the language.")
with st.expander("Inputs"):
    if st.button("reset"):
            st.session_state["tl_name"] = ""
            st.session_state["tl_pk"] = ""
            st.session_state["tl_id"] = ""
            st.session_state["delimiters"] = []
            st.session_state["selected_topics"] = []
            st.session_state["loaded_existing"] = ""
            st.session_state["cq_transcriptions"] = []
            st.session_state["consolidated_transcriptions"] = {}
            st.session_state["tl_knowledge"] = {
                "known": {},
                "known_pk": {},
                "observed": {},
                "inferred": {}
            }
            st.session_state["ga"] = None
            st.session_state["known_processed"] = False
            st.session_state["observations_processed"] = False
            st.rerun()
    # TOPICS AND LANGUAGE
    st.session_state["selected_topics"] = st.multiselect("Choose topics", topics.keys())

    # LOADING CQ TRANSCRIPTIONS
    cqs = st.file_uploader("Load Conversational Questionnaires' transcriptions (all at once for multiple transcriptions)", type="json",
                           accept_multiple_files=True)
    if cqs is not None:
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            st.session_state["cq_transcriptions"].append(new_cq)
        st.session_state["loaded_existing"] = True
        st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))

    if st.session_state["loaded_existing"]:
        if st.session_state["cq_transcriptions"] != []:
            # Consolidating transcriptions
            st.session_state[
                "consolidated_transcriptions"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                st.session_state["cq_transcriptions"],
                st.session_state["tl_name"],
                st.session_state["delimiters"])
            st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(
                len(st.session_state["cq_transcriptions"]), len(st.session_state["consolidated_transcriptions"]),
                total_target_word_count, len(unique_words)))
            # managing language input
            st.session_state["tl_name"] = st.session_state["cq_transcriptions"][0]["target language"]
            if st.session_state["tl_name"] in wu.language_pk_id_by_name.keys():
                st.write("{} has data in WALS".format(st.session_state["tl_name"]))
                st.session_state["tl_pk"] = wu.language_pk_id_by_name[st.session_state["tl_name"]]["pk"]
                st.session_state["tl_id"] = wu.language_pk_id_by_name[st.session_state["tl_name"]]["id"]
            else:
                st.write("{} is not in WALS".format(st.session_state["tl_name"]))
                st.session_state["tl_pk"] = None
                st.session_state["tl_id"] = None
            # managing delimiters
            if "delimiters" in st.session_state["cq_transcriptions"][0].keys():
                st.session_state["delimiters"] = st.session_state["cq_transcriptions"][0]["delimiters"]
                print("Word separators have been explicitly entered in the transcription.")
            elif st.session_state["tl_name"] in wu.language_pk_id_by_name.keys():
                with open("./data/delimiters.json", "r") as f:
                    delimiters_dict = json.load(f)
                    st.session_state["delimiters"] = delimiters_dict[st.session_state["tl_name"]]
                    print("Word separators are retrieved from the .")
            else:
                st.session_state["delimiters"] = default_delimiters
            st.multiselect("Edit word separators if needed", delimiters_bank, default=st.session_state["delimiters"])

    show_details = st.toggle("Show details")

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
                    st.session_state["tl_knowledge"]["known_pk"][p_name] = str(known_value)
    if len(st.session_state["tl_knowledge"]["known"]) != 0 and show_details:
        st.markdown("#### Retrieving **known** information")
        st.markdown("**{}** is documented in WALS with {} parameters pertaining to {}".format(st.session_state["tl_name"],
                                                                                            len(st.session_state[
                                                                                                    "tl_knowledge"][
                                                                                                    "known"]),
                                                                                            "& ".join(st.session_state["selected_topics"])))
        show_params = st.toggle("Show known parameters")

        if show_params:
            st.write(st.session_state["tl_knowledge"]["known"])
    st.session_state["known_processed"] = True

# PROCESSING TRANSCRIPTIONS

if st.session_state["consolidated_transcriptions"] != {}:
    # oberving svo word order
    st.session_state["obs"]["Order of Subject, Object and Verb"] = obs.observer_order_of_subject_object_verb(st.session_state["consolidated_transcriptions"],
                                                        st.session_state["tl_name"],
                                                        st.session_state["delimiters"],
                                                        canonical=True)
    st.session_state["obs"]["Order of Subject and Verb"] = obs.observer_order_of_subject_and_verb(st.session_state["consolidated_transcriptions"],
                                                        st.session_state["tl_name"],
                                                        st.session_state["delimiters"],
                                                        canonical=True)
    st.session_state["obs"]["Order of Adjective and Noun"] = obs.observer_order_of_adjective_and_noun(
                                                        st.session_state["consolidated_transcriptions"],
                                                        st.session_state["tl_name"],
                                                        st.session_state["delimiters"],
                                                        canonical=False)

    st.session_state["tl_knowledge"]["observed"]["Order of Subject, Object and Verb"] = st.session_state["obs"]["Order of Subject, Object and Verb"]["agent-ready observation"]
    st.session_state["tl_knowledge"]["observed"]["Order of Subject and Verb"] = st.session_state["obs"]["Order of Subject and Verb"]["agent-ready observation"]
    st.session_state["tl_knowledge"]["observed"]["Order of Adjective and Noun"] = st.session_state["obs"]["Order of Adjective and Noun"]["agent-ready observation"]
    st.session_state["observations_processed"] = True
    #st.write(st.session_state["tl_knowledge"])
    #st.write(st.session_state["obs"])

    if show_details:
        st.markdown("#### Retrieving **observed** information in Conversational Questionnaires")
        show_observed_details = st.toggle("Show details about observations")

        if show_details and show_observed_details:
            for pobs in st.session_state["obs"]:
                if len(st.session_state["obs"][pobs]["observations"]) != 0:
                    st.markdown("#### {}".format(pobs))
                    for de_name, details in st.session_state["obs"][pobs]["observations"].items():
                        if details["count"] != 0:
                            st.write("---------------------------------------------")
                            st.write("**{}** in ".format(de_name))
                            for occurrence_index, context in details["details"].items():
                                st.markdown("- ***{}***".format(st.session_state["consolidated_transcriptions"][occurrence_index]["recording_data"]["translation"]))
                                st.write(st.session_state["consolidated_transcriptions"][occurrence_index]["sentence_data"]["text"])
                                gdf = kgu.build_gloss_df(st.session_state["consolidated_transcriptions"], occurrence_index, st.session_state["delimiters"])
                                st.dataframe(gdf)
                                st.write("context: {}".format(", ".join(context)))
                    st.markdown("-------------------------------------")


if st.session_state["known_processed"] and st.session_state["observations_processed"]:
    # RUNNING INFERENCES
    infospot = st.empty()
    if show_details:
        st.write("Launching inferential engine: General Agent")
        st.write("Prior knowledge is based on statistics over all languages.")
    ga_param_name_list = list(topics["Canonical word orders"]["obs"].keys()) + list(topics["Canonical word orders"]["nobs"].keys())
    st.session_state["ga"] = agents.GeneralAgent("canonical word order",
                                         parameter_names=ga_param_name_list,
                                         language_stat_filter={})
    if show_details:
        st.write("Agent created with {} parameters".format(len(st.session_state["ga"].language_parameters)))
        st.write("{} parameters will be locked as known: {}".format(len(st.session_state["tl_knowledge"]["known"]), st.session_state["tl_knowledge"]["known"]))
        st.write("{} parameters have been observed: {}".format(len(st.session_state["tl_knowledge"]["observed"]), st.session_state["tl_knowledge"]["observed"]))
        st.write("Injecting Observations")
    for observed_param_name in st.session_state["tl_knowledge"]["observed"]:
        st.session_state["ga"].add_observations(observed_param_name,
                                                st.session_state["tl_knowledge"]["observed"][observed_param_name])
    if show_details:
        st.write("Injecting known information")
    for known_p_name in st.session_state["tl_knowledge"]["known_pk"].keys():
        depk = st.session_state["tl_knowledge"]["known_pk"][known_p_name]
        st.session_state["ga"].language_parameters[known_p_name].inject_peak_belief(str(depk), 1, locked=True)
    if show_details:
        st.write("Running inferences...")
    for i in range(5):
        st.session_state["ga"].run_belief_update_cycle()

    if show_details:
        st.markdown("#### Beliefs of the General Agent")
        show_beliefs = st.toggle("Show the inferred beliefs of the general agent")
        if show_beliefs:
            beliefs = st.session_state["ga"].get_beliefs()
            for pname in beliefs.keys():
                max_depk = max(beliefs[pname], key=beliefs[pname].get)
                depk_name = wu.get_careful_name_of_de_pk(max_depk)
                st.write("{}: {}".format(pname, depk_name))

    # LESSSON CONTENT AND PROMPT

    #known
    beliefs = st.session_state["ga"].get_beliefs()
    for pname in beliefs.keys():
        max_depk = max(beliefs[pname], key=beliefs[pname].get)
        depk_name = wu.get_careful_name_of_de_pk(max_depk)
        st.session_state["prompt_content"]["canonical word order"][pname] = {
            "main value":depk_name,
            "examples by value": {}
        }

    #examples from observations
    for p_name in beliefs.keys():
        if p_name in st.session_state["obs"].keys():
            for de_name, details in st.session_state["obs"][p_name]["observations"].items():
                st.session_state["prompt_content"]["canonical word order"][p_name]["examples by value"][de_name] = []
                if details["count"] != 0:
                    for occurrence_index, context in details["details"].items():
                        gdf = kgu.build_gloss_df(st.session_state["consolidated_transcriptions"], occurrence_index,
                                                 st.session_state["delimiters"])
                        st.session_state["prompt_content"]["canonical word order"][p_name]["examples by value"][de_name].append({
                            "english sentence":
                                st.session_state["consolidated_transcriptions"][occurrence_index]["sentence_data"]["text"],
                            "translation": st.session_state["consolidated_transcriptions"][occurrence_index]["recording_data"][
                                "translation"],
                            "gloss": gdf.to_dict(),
                            "context": context
                        })
        else:
            st.session_state["prompt_content"]["canonical word order"][pname]["examples by value"] = {}

    #st.write(st.session_state["prompt_content"])

    lesson_title = "## The order of words in " + st.session_state["tl_name"]
    lesson_intro = """
    The order of words in a sentence carries meaning.
    Here, we will focus on the order of words in the simplest situation: sentences where someone states something
    in a positive form and active voice.
    This straightforward situation, known as canonical, will serve as a foundation for understanding the basics of
    word order in """ + st.session_state["tl_name"] + "."

    lesson_svo = """Let's look at the order of the **subject, object and verb**.

    """
    main_order = st.session_state["prompt_content"]["canonical word order"]["Order of Subject, Object and Verb"]["main value"]

    st.markdown(lesson_title)
    st.markdown(lesson_intro)

    prompt = "Create a short, engaging, well-organized grammar chapter about canonical word order in " + st.session_state["tl_name"] + " that adults will use to learn grammar."
    prompt += "Don't use jargon or complicated words: he readers are not use to reading grammar lessons. Use simple, non-technical words. Don't use acronyms."
    prompt += "Use only on the material provided. Do not use or infer any additional information, examples, or rules beyond what I give. If something is unclear or missing from the input, don't fill the gaps. Focus on explaining the rules and providing examples from the material I supply."
    prompt += "Use all the examples provided. Use the gloss information to explain which word in target language means what."
    prompt += "If several word orders coexist, mention them all by order of importance."
    prompt += "Here are the information about the word order in this language (use only this information): "
    prompt += str(st.session_state["prompt_content"]["canonical word order"]) + "."
    prompt += "Don't add encouragement or personal comment."
    prompt += "Your lesson should be formatted with the github-flavored markdown as a string to display with Streamlit."
    prompt += "the output should be correctly displayed when using the streamlit.markdown() function."
    prompt += "Don't put the '''markdown''' in the output."

    if st.button("Create a grammar lesson from these inferences and examples"):
        openai.api_key = st.secrets["openai_key"]
        #print(openai.models.list())
        response = openai.chat.completions.create(
            model="chatgpt-4o-latest",
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are an assistant that writes grammar book chapters. Use only the information provided by the user. Use all the examples provided by the user. Do not introduce any additional material, even if it seems relevant. If the user-provided material is incomplete or ambiguous, ommit content. "
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ])
        st.session_state["redacted"] = response.choices[0].message.content
        st.markdown(response.choices[0].message.content)
        print(response.choices[0].message.content)

        st.download_button("Download lesson", st.session_state["redacted"], file_name="generated_grammar_lesson.txt")


    #st.write(st.session_state["prompt_content"])

