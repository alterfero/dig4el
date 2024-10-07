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
        "canonical word order":
            {"grammatical features": {}}
    }
if "redacted" not in st.session_state:
    st.session_state["redacted"] = ""
if "svo_obs" not in st.session_state:
    st.session_state["svo_obs"] = {}

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
    tl = st.selectbox("Language name?", ["not in the list"] + list(wu.language_pk_id_by_name.keys()))
    if tl == "not in the list":
        st.session_state["tl_name"] = st.text_input("If the language is not in the list: Language name?")
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
                #st.write("Delimiters found for {}: {}".format(tl, st.session_state["delimiters"]))
            else:
                st.session_state["delimiters"] = default_delimiters
                #st.write("Using default delimiters: {}".format(st.session_state["delimiters"]))

    # LOADING CQ TRANSCRIPTIONS
    cqs = st.file_uploader("Load Conversational Questionnaires' transcriptions", type="json", accept_multiple_files=True)
    if cqs is not None:
        st.session_state["cq_transcriptions"] = []
        for cq in cqs:
            new_cq = json.load(cq)
            st.session_state["cq_transcriptions"].append(new_cq)
        st.session_state["loaded_existing"] = True
        st.write("{} files loaded.".format(len(st.session_state["cq_transcriptions"])))
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
if show_details:
    st.markdown("#### Retrieving **observed** information in Conversational Questionnaires")
    show_observed_details = st.toggle("Show details about observations")
if st.session_state["cq_transcriptions"] != []:
    # Consolidating transcriptions
    st.session_state["consolidated_transcriptions"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                                        st.session_state["cq_transcriptions"],
                                        st.session_state["tl_name"],
                                        st.session_state["delimiters"])
    st.write("{} Conversational Questionnaires: {} sentences, {} words with {} unique words".format(len(st.session_state["cq_transcriptions"]),len(st.session_state["consolidated_transcriptions"]), total_target_word_count, len(unique_words)))

    # oberving svo word order
    st.session_state["svo_obs"] = obs.observer_order_of_subject_object_verb(st.session_state["consolidated_transcriptions"],
                                                        st.session_state["tl_name"],
                                                        st.session_state["delimiters"])

    # Keep only canonical sentences
    # TODO: This should be refactored somewhere else
    canonical_obs = copy.deepcopy(st.session_state["svo_obs"])
    for p in canonical_obs["observations"].keys():
        for k,d in canonical_obs["observations"][p]["details"].items():
            if d[0] != "ASSERT":
                del(st.session_state["svo_obs"]["observations"][p]["details"][k])
    for order in st.session_state["svo_obs"]["observations"].keys():
        depk = st.session_state["svo_obs"]["observations"][order]["depk"]
        count = len(st.session_state["svo_obs"]["observations"][order]["details"])
        st.session_state["svo_obs"]["agent-ready observation"][depk] = count
    #st.write(st.session_state["svo_obs"])


    if show_details and show_observed_details:
        for de_name, details in st.session_state["svo_obs"]["observations"].items():
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
    st.session_state["tl_knowledge"]["observed"]["Order of Subject, Object and Verb"] = st.session_state["svo_obs"]["agent-ready observation"]
    st.session_state["observations_processed"] = True
else:
    st.session_state["observations_processed"] = True

if st.session_state["known_processed"] and st.session_state["observations_processed"]:
    # RUNNING INFERENCES
    infospot = st.empty()
    if show_details:
        st.write("Launching inferential engine")
    ga_param_name_list = list(topics["Canonical word orders"]["obs"].keys()) + list(topics["Canonical word orders"]["nobs"].keys())
    st.session_state["ga"] = agents.GeneralAgent("canonical word order",
                                         parameter_names=ga_param_name_list,
                                         language_stat_filter={})
    if show_details:
        st.write("Agent created with {} parameters".format(len(st.session_state["ga"].language_parameters)))
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

    # building prompt
    # st.session_state["prompt_content"] = {
    #     "canonical word order":
    #         {"grammatical features": {
    #         "main value":value,
    #         "examples by value":{examples}
    #         }
    # }

    #known
    beliefs = st.session_state["ga"].get_beliefs()
    for pname in beliefs.keys():
        max_depk = max(beliefs[pname], key=beliefs[pname].get)
        depk_name = wu.get_careful_name_of_de_pk(max_depk)
        st.session_state["prompt_content"]["canonical word order"]["grammatical features"][pname] = {
            "main value":depk_name,
            "examples by value": {}
        }

    #observed
    for pname in beliefs.keys():
        if st.session_state["cq_transcriptions"] != []:
            # TODO: REMOVE IF CLAUSE AND GENERALIZE ONCE MULTIPLE OBSERVERS IN PLACE
            if pname == "Order of Subject, Object and Verb":
                for de_name, details in st.session_state["svo_obs"]["observations"].items():
                    st.session_state["prompt_content"]["canonical word order"]["grammatical features"][pname][
                        "examples by value"][de_name] = []
                    if details["count"] != 0:
                        for occurrence_index, context in details["details"].items():
                            gdf = kgu.build_gloss_df(st.session_state["consolidated_transcriptions"], occurrence_index,
                                                     st.session_state["delimiters"])
                            st.session_state["prompt_content"]["canonical word order"]["grammatical features"][pname]["examples by value"][de_name].append({
                                "english sentence":
                                    st.session_state["consolidated_transcriptions"][occurrence_index]["sentence_data"]["text"],
                                "translation": st.session_state["consolidated_transcriptions"][occurrence_index]["recording_data"][
                                    "translation"],
                                "gloss": gdf.to_dict(),
                                "context": context
                            })
        else:
            st.session_state["prompt_content"]["canonical word order"]["grammatical features"][pname]["examples by value"] = {}

    #st.write(st.session_state["svo_obs"])
    #st.write(st.session_state["prompt_content"])

    lesson_title = "## The order of words in " + st.session_state["tl_name"]
    lesson_intro = """
    The order of words in a sentence carries part of its meaning.
    Here, we will focus on the order of words in the simplest situation: sentences where someone states something
    in a positive form and active voice.
    This straightforward situation, known as canonical, will serve as a foundation for understanding the basics of
    word order in """ + st.session_state["tl_name"] + "."

    lesson_svo = """Let's look at the order of the **subject, object and verb**.
    
    """
    main_order = st.session_state["prompt_content"]["canonical word order"]["grammatical features"]["Order of Subject, Object and Verb"]["main value"]
    if main_order in st.session_state["prompt_content"]["canonical word order"]["grammatical features"]["Order of Subject, Object and Verb"]["examples by value"].keys():
        lesson_svo_example = st.session_state["prompt_content"]["canonical word order"]["grammatical features"][
            "Order of Subject, Object and Verb"]["examples by value"][main_order][0]
        lesson_svo += """Here is an example: 
        """
        lesson_svo += str(lesson_svo_example)

    st.markdown(lesson_title)
    st.markdown(lesson_intro)

    prompt = "Create a short, engaging, well-organized grammar lesson about canonical word order in " + st.session_state["tl_name"] + " to a group of adult second-language learners."
    prompt += "No jargon, the readers are not use to reading grammar lessons."
    prompt += "Use only on the material provided. Do not use or infer any additional information, examples, or rules beyond what I give. If something is unclear or missing from the input, don't fill the gaps. Focus on explaining the rules and providing examples from the material I supply."
    prompt += "Use all the examples provided. When a gloss is available, use it."
    prompt += "Here are the information about the word order in this language (use only this information): "
    prompt += str(st.session_state["prompt_content"]["canonical word order"]["grammatical features"]) + "."
    prompt += "Don't add encouragement or personal comment."
    prompt += "Your lesson should be formatted with the github-flavored markdown as a string to display with Streamlit."
    prompt += "the output should be correctly displayed when using the streamlit.markdown() function."
    prompt += "Don't put the '''markdown''' in the output."

    if st.button("Create a grammar lesson from these inferences and examples"):
        openai.api_key = st.secrets["openai_key"]
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are an assistant that creates language learning grammar lessons. Use only the information provided by the user. Use all the examples provided by the user. Do not introduce any additional material, even if it seems relevant. If the user-provided material is incomplete or ambiguous, ommit content. "
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




