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
import os

import pandas as pd
import streamlit as st
import json
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import openai_vector_store_utils as ovsu
from libs import sentence_queue_utils as squ

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_LD_PATH = "./ld/"

if "indi_language" not in st.session_state:
    st.session_state["indi_language"] = "Abkhaz-Adyge"
if "indi_glottocode" not in st.session_state:
    st.session_state["indi_glottocode"] = "abkh1242"
if "l1_language" not in st.session_state:
    st.session_state.l1_language = ""
if "request_text" not in st.session_state:
    st.session_state.request_text = ""
if "bayesian_data" not in st.session_state:
    st.session_state.bayesian_data = None
if "has_bayesian" not in st.session_state:
    st.session_state.has_bayesian = False
if "has_docs" not in st.session_state:
    st.session_state.has_docs = False
if "new_docs_uploaded" not in st.session_state:
    st.session_state.new_docs_uploaded = False
if "has_vector_store" in st.session_state:
    st.session_state.has_vector_store = False
if "has_pairs" not in st.session_state:
    st.session_state.has_pairs = False
if "has_monolingual" not in st.session_state:
    st.session_state.has_monolingual = False
if "info_doc" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json")) as f:
        st.session_state.info_doc = json.load(f)
if "selected_pairs_filename" not in st.session_state:
    st.session_state.selected_pairs_filename = ""


def check_enrichment_progress(selected_pairs_filename) -> None:
    """Update session state based on ongoing background jobs."""
    if os.path.exists(JOB_INFO_FILE):
        with open(JOB_INFO_FILE, "r") as f:
            info = json.load(f)
        total = info.get("total", 0)
        temp_file = info.get("temp_file", "tmp_augmented_" + selected_pairs_filename)
        processed = 0
        if os.path.exists(temp_file):
            with open(temp_file, "r") as tf:
                processed = sum(1 for _ in tf)
        st.session_state.enriching_pairs = processed < total
        st.session_state.jobs_total = total
        st.session_state.jobs_processed = processed
        if processed >= total and total > 0:
            with open(temp_file, "r") as tf:
                st.session_state.enriched_pairs = [json.loads(line) for line in tf]
            os.remove(JOB_INFO_FILE)
            st.session_state.enriching_pairs = False
    else:
        st.session_state.enriching_pairs = False
        st.session_state.jobs_total = 0
        st.session_state.jobs_processed = 0


with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home2.py", label="Home", icon=":material/home:")

st.header("Dashboard")
st.write("Combine your language data and generate descriptions and grammar lessons")

colq, colw = st.columns(2)
selected_language = colq.selectbox("What language are we working on?", gu.GLOTTO_LANGUAGE_LIST)
if st.button("Select {}".format(selected_language)):
    st.session_state.indi_language = selected_language
    st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi_language,
                                                                   "glottocode not found")
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "r") as f:
        st.session_state.info_doc = json.load(f)
st.markdown("*glottocode* {}".format(st.session_state.indi_glottocode))

st.session_state.l1_language = colw.selectbox("What is the language of the readers?",
                                              ["Bislama", "English", "French", "German", "Japanese", "Swedish",
                                               "Tahitian"])

st.sidebar.divider()
st.sidebar.write("✅ CQ Ready" if st.session_state.has_bayesian else "CQ: No Data")
st.sidebar.write("✅ Docs Ready" if st.session_state.has_docs else "Docs: No Data")
st.sidebar.write("✅ Pairs Ready" if st.session_state.has_pairs else "Pairs: No Data")
st.sidebar.write("✅ Mono Ready" if st.session_state.has_monolingual else "Mono: No Data")
st.sidebar.divider()

st.markdown("#### Using the tabs below, add information about {}".format((st.session_state.indi_language)))

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["CQ Inferences", "Documents", "Sentence Pairs", "Monolingual text"])
with tab1:
    st.markdown("""
    If you don't have created Conversational Questionnaires yet, you can do it with "Enter CQ Translations". 
    If you have CQ translations, you can go to "Generate CQ Knowledge". You will be directed back here once the CQ
    Knowledge is built. 
    """)
    st.page_link("pages/record_cq_transcriptions.py", label="Enter CQ translations", icon=":material/contract_edit:")
    st.page_link("pages/infer_from_knowledge_and_cqs.py", label="Generate CQ Knowledge from existing CQs",
                 icon=":material/contract_edit:")

    if st.session_state.indi_language in os.listdir(BASE_LD_PATH):
        if "cq" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language)):
            if "cq_knowledge" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq")):
                if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                                                  "cq",
                                                                  "cq_knowledge")):

                    st.success("**There is an existing CQ Knowledge file, use it?**")
                    if st.button("Yes, Use existing CQ Knowledge in {}".format(st.session_state.indi_language)):
                        with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                               "cq",
                                               "cq_knowledge",
                                               "cq_knowledge.json"), "r") as f:
                            st.session_state.bayesian_data = json.load(f)
                        st.session_state.has_bayesian = True
                        st.rerun()

    cq_knowledge_file = st.file_uploader("Upload a CQ Knowledge JSON file")
    if cq_knowledge_file is not None:
        with open(cq_knowledge_file, "r") as f:
            st.session_state.bayesian_data = json.load(f)
        st.session_state.has_bayesian = True

    if st.session_state.has_bayesian:
        st.success("✅ CQ knowledge ready")

with tab2:
    st.write("""
            The Document Knowledge is created by indexing the content of the documents you are providing in 
            so-called **'vector stores'**.
            These documents will be uploaded to be indexed, and their indexing stored on a remote server. 
            Use only documents that are public, or that you have the right to use. Rename your documents to make 
            their title and author(s) explicit in the document name. Avoid using spaces or punctuation in the name. 
            For example: author_noam_chomsky_title_the_architecture_of_language.pdf
             """
             )

    # DOCUMENTS
    available_documents = os.listdir(os.path.join(BASE_LD_PATH,
                                                  st.session_state.indi_language,
                                                  "descriptions",
                                                  "sources"))
    available_documents = [d for d in available_documents if d[-3:] in ["txt", "ocx", "pdf"]]
    vectorized_documents = st.session_state.info_doc["documents"]["vectorized"]
    if available_documents == []:
        st.write("No document uploaded yet")
    else:
        st.write("{} available documents: ".format(len(available_documents)))
        for d in available_documents:
            st.markdown("- **{}**".format(d))

    new_documents = st.file_uploader(
        "Add new documents from your computer (pdf, txt)",
        accept_multiple_files=True
    )

    if new_documents:
        if st.button("Add these documents to available documents on the server"):
            dest_dir = os.path.join(
                BASE_LD_PATH,
                st.session_state.indi_language,
                "descriptions",
                "sources"
            )
            for new_doc in new_documents:
                dest_path = os.path.join(dest_dir, new_doc.name)
                with open(dest_path, "wb") as f:
                    f.write(new_doc.read())
                st.success(f"Saved `{new_doc.name}` to server.")

            st.rerun()

    # VECTOR STORE
    available_oa_vector_store = ovsu.list_vector_stores()
    if st.session_state.indi_language + "_documents" in available_oa_vector_store.keys():
        st.session_state.has_vector_store = True
        st.success("There is an existing vector store for {}".format(st.session_state.indi_language))
        if st.session_state.info_doc["documents"]["vectorized"] == available_documents:
            st.success("The vector store includes all available documents.")
        else:
            doc_status_dict = {
                "available_and_vectorized": [],
                "available_but_not_vectorized": [],
                "vectorized_but_not_available": []
            }
            for d in available_documents:
                if d in st.session_state.info_doc["documents"]["vectorized"]:
                    doc_status_dict["available_and_vectorized"].append(d)
                else:
                    doc_status_dict["available_but_not_vectorized"].append(d)
            for d in st.session_state.info_doc["documents"]["vectorized"]:
                if d not in available_documents:
                    doc_status_dict["vectorized_but_not_available"].append(d)
            st.write(doc_status_dict)


    else:
        st.write("No vector store yet")

    if available_documents != [] and st.button("Create a vector store with all available documents"):
        vs_id = ovsu.add_all_files_from_folder_to_vector_store(vs_name=st.session_state.indi_language + "_documents",
                                                               folder_path=os.path.join(BASE_LD_PATH,
                                                                                        st.session_state.indi_language,
                                                                                        "descriptions",
                                                                                        "sources")
                                                               )
        # update info_json
        st.session_state.info_doc["documents"]["vectorized"] = [fn for fn in os.listdir(os.path.join(BASE_LD_PATH,
                                                                                                     st.session_state.indi_language,
                                                                                                     "descriptions",
                                                                                                     "sources")) if
                                                                fn[-3:] in ["txt", "pdf"]]
        st.session_state.info_doc["documents"]["oa_vector_store_name"] = st.session_state.indi_language + "_documents"
        st.session_state.info_doc["documents"]["oa_vector_store_id"] = vs_id
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w") as f:
            json.dump(st.session_state.info_doc, f)

    if st.button("check vector store status, make sure it is ready before you use it"):
        status = ovsu.check_vector_store_status(vs_name=st.session_state.indi_language + "_documents")
        if status == "completed":
            st.success("Vector store {} ready for use".format(st.session_state.indi_language + "_documents"))
            st.session_state.has_docs = True
            st.rerun()

        else:
            st.warning("Vector store not ready yet... come back in a few minutes and try again.")

with tab3:
    PAIRS_BASE_PATH = os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs")
    JOB_INFO_FILE = os.path.join(PAIRS_BASE_PATH, "job_progress.json")
    st.write("""
    1. Sentence pairs must be organized in a JSON file [{"source":"sentence in English", 
    "target": "sentence in the target language"}, ...]. 
    2. DIG4EL *augments* these pairs using a LLM, adding a grammatical description and a semantic graph. 
    It is a long process. The *augmented pairs* file is then stored for future use, on the server and you
    should also keep a copy on your computer.
    3. The *augmented pair* file is then used to provide relevant augmented pairs to grammatical descriptions 
    (Retrieval-Augmented Generation, or RAG). 
    """)
    available_pairs = st.session_state.info_doc["pairs"]
    available_pairs_filenames = []
    if available_pairs == []:
        st.write("No sentence pair file available")
    else:
        available_pairs_filenames = [p["filename"] for p in st.session_state.info_doc["pairs"]]
        df_display = pd.DataFrame(st.session_state.info_doc["pairs"])
        st.markdown("**Available sentence pairs files**")
        st.dataframe(df_display)

    new_pair_file = st.file_uploader(
        "Add a new sentence pair JSON to the server",
        accept_multiple_files=False
    )

    # Upload sentence pairs file
    if new_pair_file and new_pair_file.name.endswith(".json"):
        if new_pair_file.name in available_pairs_filenames:
            replace_ok = st.checkbox("This file is already on the server, replace it?", value=False)
        else:
            replace_ok = True
        if replace_ok:
            info_entered = False
            name = st.text_input("Name this corpus")
            origin = st.text_input("Origin of the corpus")
            author = st.text_input("Author/owner of the corpus")
            if name and origin and author:
                info_entered = True
            valid_file = False
            if info_entered and st.button("Add this file to sentence pairs on the server"):
                try:
                    sentence_pairs = json.load(new_pair_file)
                    if "source" in sentence_pairs[0].keys() and "target" in sentence_pairs[0].keys():
                        valid_file = True
                    else:
                        st.write(
                            "This is a JSON file, but not a sentence pair file formatted as a list of 'source' and 'target' keys()")
                except:
                    st.write("Not a correctly formatted JSON file.")
            if valid_file:
                st.success("Adding {} to the server".format(new_pair_file.name))
                with open(os.path.join(PAIRS_BASE_PATH, "pairs", new_pair_file.name), "w") as f:
                    json.dump(sentence_pairs, f)
                st.success(f"Saved `{new_pair_file.name}` on the server.")

                # UPDATE INFO_DOC
                if new_pair_file.name in available_pairs_filenames:
                    i = [i for i in st.session_state.info_doc["pairs"].index if
                         st.session_state.info_doc["pairs"]["filename"] == new_pair_file.name][0]
                    del (st.session_state.info_doc["pairs"][i])

                st.session_state.info_doc["pairs"].append(
                    {
                        "filename": new_pair_file.name,
                        "name": name,
                        "origin": origin,
                        "author": author,
                        "augmented": False,
                        "vectorized": False
                    }
                )
                with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w") as f:
                    json.dump(st.session_state.info_doc, f)
                st.rerun()

    # Augment sentence pairs file
    if "sentence_pairs" not in st.session_state:
        st.session_state.sentence_pairs = None
    if "enriching_pairs" not in st.session_state:
        st.session_state.enriching_pairs = False
    if "enriched_pairs" not in st.session_state:
        st.session_state.enriched_pairs = []
    st.subheader("Augment sentence pairs with automatic grammatical descriptions")
    st.markdown("""Sentence pairs are augmented with grammatical descriptions, so they can be used efficiently.
    This is a long process (around 30 seconds per sentence pair) that will run in the background once started.  
    """)
    if len(st.session_state.info_doc["pairs"]) > 0:
        st.session_state.selected_pairs_filename = st.selectbox("Select a sentence pairs file to augment",
                                                                [item["filename"]
                                                                 for item in st.session_state.info_doc["pairs"]])

        with open(os.path.join(PAIRS_BASE_PATH, "pairs", st.session_state.selected_pairs_filename), "r") as f:
            st.session_state.sentence_pairs = json.load(f)
        create_btn = st.button(
            "Augment {} (long process, LLM use)".format(st.session_state.selected_pairs_filename),
            disabled=st.session_state.enriching_pairs,
        )
        if create_btn and not st.session_state.enriching_pairs:
            st.session_state.enriching_pairs = True
            if os.path.exists(
                    os.path.join(PAIRS_BASE_PATH, "tmp_augmented_" + st.session_state.selected_pairs_filename)):
                os.remove("tmp_augmented_" + st.session_state.selected_pairs_filename)
            info = {"total": len(st.session_state.sentence_pairs),
                    "temp_file": "tmp_augmented_" + st.session_state.selected_pairs_filename}
            with open(JOB_INFO_FILE, "w") as jf:
                json.dump(info, jf)
            st.session_state.jobs_total = len(st.session_state.sentence_pairs)
            st.session_state.jobs_processed = 0
            for pair in st.session_state.sentence_pairs:
                squ.enqueue_sentence_pair(pair, os.path.join(PAIRS_BASE_PATH,
                                                             "tmp_augmented_" + st.session_state.selected_pairs_filename))

    if st.session_state.enriching_pairs:
        st.markdown("""The sentence augmentation will continue even if you close this page. 
        Keeping the page open will allow you to monitor the progress. The augmented sentence file 
        will be saved on the server once augmentation is finished, ready for use.""")
        total = st.session_state.get("jobs_total", 0)
        processed = st.session_state.get("jobs_processed", 0)
        st.progress(processed / total if total else 0.0, "Sentence augmentation in progress...")
        st.write("Processed {}/{}".format(processed, total))
        if st.button("Show progress update"):
            st.rerun()

    if not st.session_state.enriching_pairs and st.session_state.enriched_pairs is not None:
        st.download_button(
            label="Download and store the augmented sentence pairs file",
            data=st.session_state.enriched_pairs,
            file_name="augmented_sentence_pairs.json"
        )
        if st.checkbox("Explore augmented sentences"):
            tdf = pd.DataFrame(st.session_state.enriched_pairs,
                               columns=["source", "description_text", "grammatical_keywords"])
            st.dataframe(tdf)

with tab4:
    tab4.write("**Monolingual Text**")

st.divider()
