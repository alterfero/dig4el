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

import streamlit as st
import time
import os
import pandas as pd
import json
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import openai_vector_store_utils as ovsu
from libs import sentence_queue_utils as squ
from libs import semantic_description_utils as sdu
from libs import retrieval_augmented_generation_utils as ragu
from libs import grammar_generation_agents as gga
import streamlit.components.v1 as components
from libs import utils as u
from libs import stats

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage")


if "aa_path_check" not in st.session_state:
    fmu.create_ld(BASE_LD_PATH, "Abkhaz-Adyge")

if "indi_path_check" not in st.session_state:
    st.session_state.indi_path_check = False

if "indi_language" not in st.session_state:
    st.session_state["indi_language"] = "Abkhaz-Adyge"
if "indi_glottocode" not in st.session_state:
    st.session_state["indi_glottocode"] = "abkh1242"
if "delimiters" not in st.session_state:
    st.session_state.delimiters = None
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
if "has_vector_store" not in st.session_state:
    st.session_state.has_vector_store = False
if "vsid" not in st.session_state:
    st.session_state.vsid = None
if "has_pairs" not in st.session_state:
    st.session_state.has_pairs = False
if "has_monolingual" not in st.session_state:
    st.session_state.has_monolingual = False
if "info_doc" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json")) as f:
        st.session_state.info_doc = json.load(f)
if "selected_pairs_filename" not in st.session_state:
    st.session_state.selected_pairs_filename = ""
if "sentence_pairs_signatures" not in st.session_state:
    st.session_state.sentence_pairs_signatures = []
if "sentence_pairs" not in st.session_state:
    st.session_state.sentence_pairs = None
if "enriching_pairs" not in st.session_state:
    st.session_state.enriching_pairs = False
if "batch_id" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"), "r") as f:
        content = json.load(f)
    st.session_state.batch_id = content.get("batch_id", "no batch ID in batch_id_store")
if "enriched_pairs" not in st.session_state:
    st.session_state.enriched_pairs = []
if "pairs_in_queue" not in st.session_state:
    st.session_state.pairs_in_queue = []
if "jobs_processed" not in st.session_state:
    st.session_state.jobs_processed = []
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "staged_docs" not in st.session_state:
    st.session_state.ready_to_vec_docs = []
if "vectorized_docs" not in st.session_state:
    st.session_state.vectorized_docs = []
if "file_status_list" not in st.session_state:
    st.session_state.file_status_list = {}
if "vector_store_status" not in st.session_state:
    st.session_state.vector_store_status = None
if "available_vector_stores" not in st.session_state:
    st.session_state.available_vector_stores = ovsu.list_vector_stores_sync()

PAIRS_BASE_PATH = os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs")
CURRENT_JOB_SIG_FILE = os.path.join(PAIRS_BASE_PATH, "current_job_sig.json")
JOB_INFO_FILE = os.path.join(PAIRS_BASE_PATH, "job_progress.json")


if "index.pkl" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs", "vectors")):
    st.session_state.has_pairs = True

def save_info_dict():
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w") as fdi:
        json.dump(st.session_state.info_doc, fdi)

def generate_sentence_pairs_signatures(sentence_pairs: list[dict]) -> list[str]:
    sig_list = []
    for sentence_pair in sentence_pairs:
        sig_list.append(u.clean_sentence(sentence_pair["source"], filename=True))
    return sig_list


with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/generate_grammar.py", label="Generate grammar", icon=":material/bolt:")

st.header("Sources Dashboard")
st.write("Upload and create sources for grammatical descriptions")

colq, colw = st.columns(2)
selected_language = colq.selectbox("What language are we working on?", gu.GLOTTO_LANGUAGE_LIST)
if st.button("Select {}".format(selected_language)):
    st.session_state.indi_language = selected_language
    st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi_language,
                                                                   "glottocode not found")
    fmu.create_ld(BASE_LD_PATH, st.session_state.indi_language)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "r") as f:
        st.session_state.info_doc = json.load(f)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "delimiters.json"), "r") as f:
        st.session_state.delimiters = json.load(f)
    PAIRS_BASE_PATH = os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs")
    CURRENT_JOB_SIG_FILE = os.path.join(PAIRS_BASE_PATH, "current_job_sig.json")
    JOB_INFO_FILE = os.path.join(PAIRS_BASE_PATH, "job_progress.json")

st.markdown("*glottocode* {}".format(st.session_state.indi_glottocode))

st.markdown("#### Using the tabs below, add information about {}".format((st.session_state.indi_language)))

st.divider()
tab1, tab2, tab3 = st.tabs(["CQ Inferences", "Documents", "Sentence Pairs"])
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
            These documents you share will be 
            1) **Upload**: Documents are uploaded to our server.
            2) **Staging**: Documents are staged to be used by remote LLM processes.
            3) **Vectorization**: Documents are divided into short parts, and each part is indexed. The technical
            term for this step is **vectorization**. We will use this term to avoid confusion with other types of indexing used. 
            At the end of the process, the documents are stored in a **vector store**. 
            
            **Use only documents that are public**. They will not be shared, but their content will be used 
             and their origin referenced. 
             
             Rename your documents to make their title and author(s) explicit in the document name. Avoid using spaces or punctuation in the name. 
            For example: author_noam_chomsky_title_the_architecture_of_language.pdf
            
             """
             )

    # DOCUMENTS
    st.divider()
    doc_path = os.path.join(BASE_LD_PATH, st.session_state.indi_language, "descriptions", "sources")
    st.subheader("Upload new documents from your computer to our server")
    st.session_state.uploaded_docs = [d for d in os.listdir(doc_path) if d[-3:] in ["txt", "ocx", "pdf"]]

    new_documents = st.file_uploader(
        "Add new PDF documents from your computer",
        accept_multiple_files=True
    )
    if new_documents:
        if st.button("Upload these documents"):
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
            st.session_state.uploaded_docs = [d for d in os.listdir(doc_path) if d[-3:] in ["txt", "ocx", "pdf"]]
            st.rerun()

    st.divider()
    st.subheader("Status of uploaded files")
    # ========================================= PROCESS TABLE =================================
    # files on server
    st.session_state.file_status_list = [{
                                        "id": None,
                                        "filename": d,
                                        "staged": False,
                                        "vectorized": False
                                        } for d in st.session_state.uploaded_docs]

    # checking if vector store exists from api call and info, create one if needed

    vsid_from_info_dict = st.session_state.info_doc["documents"].get("oa_vector_store_id", None)
    if vsid_from_info_dict is not None and vsid_from_info_dict in [vs.id for vs in st.session_state.available_vector_stores]:
        st.session_state.vsid = vsid_from_info_dict
        print("VSID found and matches ({})".format(st.session_state.vsid))
        st.session_state.has_vector_store = True
    else:
        print("No VSID found in info_dict matching an existing VSID: Creating a vector store")
        with st.spinner("Creating new vector store"):
            st.session_state.vsid = ovsu.create_vector_store_sync(st.session_state.indi_language + "_documents")
            st.session_state.info_doc["documents"]["oa_vector_store_id"] = st.session_state.vsid
            save_info_dict()
        print("New vector store created with VSID {}".format(st.session_state.vsid))
        st.session_state.has_vector_store = True

    # list which uploaded files are staged
    with st.spinner("Listing staged files"):
        st.session_state.staged = ovsu.list_files_sync()
    for staf in st.session_state.staged:
        for sf in st.session_state.file_status_list:
            if staf.filename == sf["filename"]:
                sf["id"] = staf.id
                sf["staged"] = True

    # list files already vectorized:
    if st.session_state.has_vector_store is True:
        with st.spinner("Listing vectorized files"):
            st.session_state.vectorized_docs = ovsu.list_files_in_vector_store_sync(vid=st.session_state.vsid)
        for vecf in st.session_state.vectorized_docs:
            #st.write("vecf: {}".format(vecf))
            for sf in st.session_state.file_status_list:
                if sf["id"] == vecf.id:
                    sf["vectorized"] = True

    status_df = pd.DataFrame(st.session_state.file_status_list, columns=["filename", "staged", "vectorized"])
    st.dataframe(status_df, use_container_width=True)

    colw1, colw2 = st.columns(2)
    # Staging unstaged files
    to_stage = [f for f in st.session_state.file_status_list if not f["staged"]]
    if to_stage:
        colw1.markdown("{} files to stage".format(len(to_stage)))
        if st.button("2) Stage"):
            for f in to_stage:
                with colw1:
                    with st.spinner("staging {}".format(f["filename"])):
                        ovsu.create_file_sync(doc_path, f["filename"])
            st.rerun()
    else:
        colw1.success("All uploaded files are staged")

    # vectorizing unvectorized staged files
    to_vectorize = [f for f in st.session_state.file_status_list if f["staged"] and not f["vectorized"]]
    if to_vectorize:
        colw2.markdown("**{} staged files to vectorize**".format(len(to_vectorize)))
        if colw2.button("3) Vectorize all staged files"):
            to_vec_fids = [f["id"] for f in to_vectorize]
            with colw2:
                with st.spinner("Launching vectorization of the staged files"):
                    ovsu.add_files_to_vector_store_sync(vsid=st.session_state.vsid,
                                                        file_ids=to_vec_fids)
            st.rerun()
    elif not to_stage and not to_vectorize:
        colw2.success("All files staged and vectorized")

    if st.session_state.vectorized_docs:
        with st.spinner("Checking"):
            st.session_state.vector_store_status = ovsu.check_vector_store_status_sync(st.session_state.vsid)
        if st.session_state.vector_store_status is not None:
            if st.session_state.vector_store_status == "completed":
                st.success("All documents have been vectorized and are ready to be used.")
                st.session_state.has_docs = True
            else:
                st.warning("Documents are still being vectorized, check again in a few minutes")
                st.write("Current status: {}".format(st.session_state.vector_store_status))

    st.divider()


with tab3:

    st.write(f"""
    1. Sentence pairs must be organized in a JSON file as list [] of "source":"sentence in English", 
    "target": "sentence in the target language". 
    2. DIG4EL *augments* these pairs using a LLM, adding a grammatical description and a semantic graph. 
    It is a long process. The *augmented pairs* file is then stored for future use, on the server and you
    should also keep a copy on your computer.
    3. You are invited to connect {st.session_state.indi_language} word(s) with concept(s) in sentences.
    4. The *augmented pair* file is then used to provide relevant augmented pairs to grammatical descriptions 
    (Retrieval-Augmented Generation, or RAG). 
    """)
    st.subheader("1. Add sentence pairs files")
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
                        st.warning(
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
                        "augmented": False
                    }
                )
                with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w") as f:
                    json.dump(st.session_state.info_doc, f)
                st.rerun()

    # AUGMENT SENTENCE PAIRS

    st.subheader("2. Augment sentence pairs with automatic grammatical descriptions")
    st.markdown("""Sentence pairs are augmented with grammatical descriptions, so they can be used efficiently.
    This is a long process (up to 2 minutes per sentence) that will run in the background once started (you can
    leave this page or turn off your computer and come back later.)
    """)

    # Display available augmented pairs
    available_augmented_sentences = [fn
                                     for fn in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))
                                     if fn[-5:] == ".json"
                                     ]
    st.markdown("**{} Available augmented sentences**".format(len(available_augmented_sentences)))
    if st.checkbox("Explore augmented sentences"):
        selected_augmented_sentence = st.selectbox("Select a sentence",
                                                   [s[:-5] for s in available_augmented_sentences])
        seleced_augmented_sentence_file = selected_augmented_sentence + ".json"
        with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs", seleced_augmented_sentence_file), "r") as f:
            sas = json.load(f)

        st.markdown(f"""
        - **{st.session_state.indi_language}**: **{sas["target"]}**
        - **English**: {sas["source"]}
        - **Intent**: {sas["description"]["enunciation"]["intent"]}.
        - **Enunciation**: {sas["description"]["enunciation"]["mood"]} mood, 
        {sas["description"]["enunciation"]["mood"]} voice, 
        emphasis on {sas["description"]["enunciation"]["emphasis"]}.
        - **Short grammatical description**: {sas["description"]["grammatical_description"]}
        - **Grammatical keywords**: {sas["description"]["grammatical_keywords"]}
        - **{st.session_state.indi_language} word(s) - concept(s) connections**: 
        """)
        if sas.get("connections", {}) != {}:
            for connection in sas.get("connections", {}):
                st.write("{} --> {}".format(connection, sas["connections"][connection]))
        else:
            st.write("No connection created.")
        if sas.get("gloss", None):
            st.write(sas["gloss"])
        st.markdown("**Semantic-Structural Graph:**")
        html = sdu.plot_semantic_graph_pyvis(sas["description"])
        components.html(html, height=600, width=1000)

    # add new pairs
    if len(st.session_state.info_doc["pairs"]) > 0:
        st.session_state.selected_pairs_filename = st.selectbox("Select a sentence pairs file to augment",
                                                                [item["filename"]
                                                                 for item in st.session_state.info_doc["pairs"]])

        with open(os.path.join(PAIRS_BASE_PATH, "pairs", st.session_state.selected_pairs_filename), "r") as f:
            st.session_state.sentence_pairs = json.load(f)

        # user triggers augmentation
        create_btn = st.button(
            "Augment {} (long process, LLM use)".format(st.session_state.selected_pairs_filename),
            disabled=st.session_state.enriching_pairs,
        )
        if create_btn and not st.session_state.enriching_pairs:  # augmentation launched only if previous one done
            pairs_signatures = generate_sentence_pairs_signatures(st.session_state.sentence_pairs)
            with open(CURRENT_JOB_SIG_FILE, "w") as f:
                json.dump(pairs_signatures, f)
            # Pass jobs to Redis
            new_pairs = [pair for pair in st.session_state.sentence_pairs
                         if u.clean_sentence(pair["source"], filename=True) + ".json"
                         not in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))]
            if new_pairs != st.session_state.sentence_pairs:
                st.write("{} sentences discarded: they already have been augmented".format(
                    len(st.session_state.sentence_pairs) - len(new_pairs)
                ))

            st.session_state.batch_id = squ.enqueue_batch(new_pairs)
            with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"), "w") as f:
                json.dump({"batch_id": st.session_state.batch_id}, f)

            st.session_state.enriching_pairs = True

    progress = squ.get_batch_progress(st.session_state.batch_id)
    st.write("Queue status: {}".format(progress))
    if st.button("Save processed sentences on server"):
        n_written = squ.persist_finished_results(batch_id=st.session_state.batch_id)
        st.success("{} augmented pairs saved.")
    if st.button("Clear batch"):
        print("Clearing batch {}".format(st.session_state.batch_id))
        squ.clear_batch(batch_id=st.session_state.batch_id, delete_jobs=True)


    if progress["queued"] != progress["finished"] + progress["failed"]:
        st.markdown("""The sentence augmentation is in progress. It is a long process (up to 2 minutes per sentence)
        that will continue even if you close this page or turn off your computer. You can come back anytime 
        and press the progress update button below to check on progress and make completed augmentations 
        available for use. 
        """)

        if st.button("Show progress update (re-click to see progress)"):
            progress = squ.get_batch_progress(st.session_state.batch_id)
            st.write(progress)

    else:
        if progress["queued"] != 0:
            progress = squ.get_batch_progress(st.session_state.batch_id)
            st.markdown("""
            The last sentence pairs augmentation job is complete, you can use augmented sentences 
            and save them on your computer if you want to keep the raw form (best format to use with other software). 
            If some sentences have not been augmented, you can re-launch the same augmentation work and only the 
            non-augmented sentences will be picked up. 
                        """)
            n_to_write = progress["finished"]
            n_written = squ.persist_finished_results(batch_id=st.session_state.batch_id,
                                                     output_dir=os.path.join(BASE_LD_PATH,
                                                                             st.session_state.indi_language,
                                                                             "sentence_pairs",
                                                                             "augmented_pairs"))
            st.success("{} sentence to write, {} sentences written".format(n_to_write, n_written))

            print("Batch {} cleared".format(st.session_state.batch_id))
            squ.clear_batch(batch_id=st.session_state.batch_id, delete_jobs=True)


    # ADD WORD-CONCEPT CONNECTIONS
    st.subheader("3. Connect word(s) and concept(s) in augmented sentences")
    st.write("This step is manual and adds a lot of information to the corpus.")

    #build aug_sent_df
    aps = []
    for ap_file in [fn
                    for fn in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))
                    if fn[-5:] == ".json"]:
        with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs", ap_file), "r") as f:
            ap = json.load(f)
        aps.append(
            {
                "source": ap["source"],
                "target": ap["target"],
                "connections": ap.get("connections", {}),
                "filename": os.path.join(PAIRS_BASE_PATH, "augmented_pairs", ap_file)
            }
        )
    aps_df = pd.DataFrame(aps, columns=["source", "target", "connections"])
    selected = st.dataframe(aps_df, selection_mode="single-row", on_select="rerun", key="aps_df")

    if selected["selection"]["rows"] != []:
        selected_ap = aps[selected["selection"]["rows"][0]]
        with open(selected_ap["filename"], "r") as f:
            slap = json.load(f)
        if not slap.get("connections", None):
            slap["connections"] = {}
        st.markdown(f"**{st.session_state.indi_language}**: {slap['target']}")
        st.markdown(f"**English**: {slap['source']}")
        referents = [r["designation"]
                    for r in slap["description"]["referents"]]
        words = stats.custom_split(slap["target"], st.session_state.delimiters)

        for referent in referents:
            connected_words = st.multiselect(f"{referent} Is expressed by",
                                             words,
                                             default=slap["connections"].get(referent, []),
                                             key="cw"+referent)
            slap["connections"][referent] = connected_words
        if st.button("Submit connections"):
            with open(selected_ap["filename"], "w") as f:
                json.dump(slap, f)
                st.success("Connections saved in {}".format(selected_ap["filename"]))

    st.subheader("4. Index augmented pairs to make them ready for use")
    if st.button("Index !"):
        with st.spinner("Indexing..."):
            if sdu.get_vector_ready_pairs(st.session_state.indi_language):
                st.success("Augmented pairs prepared for vectorization")
            if ragu.vectorize_vaps(st.session_state.indi_language):
                st.success("Augmented pairs vectorized and indexed")
            ragu.create_hard_kw_index(st.session_state.indi_language)
            st.session_state.has_pairs = True
            st.rerun()

    if st.session_state.has_pairs:
        st.divider()
        st.subheader("Test sentence pairs retrieval")
        with st.spinner("Refreshing keyword index"):
            ragu.create_hard_kw_index(st.session_state.indi_language)
        with st.spinner("Loading vectors"):
            index, id_to_meta = ragu.load_index_and_id_to_meta(st.session_state.indi_language)
        if "query_results" not in st.session_state:
            st.session_state.query_results = []
        query = st.text_input("Sentence retrieval test, enter a query")

        if "hard_kw_retrieval_results" not in st.session_state:
            st.session_state.hard_kw_retrieval_results = []
        if st.button("Submit"):
            with st.spinner("Retrieving sentences from vectors"):
                st.session_state.query_results = ragu.retrieve_similar(query,
                                                                       index=index,
                                                                       id_to_meta=id_to_meta,
                                                                       k=5)
            with st.spinner("Retrieving sentences from keywords"):
                st.session_state.hard_kw_retrieval_results = ragu.hard_retrieve_from_query(query, st.session_state.indi_language)

        st.write("Vector results: ")
        st.write(st.session_state.query_results)
        st.write("Keywords results: ")
        st.write(st.session_state.hard_kw_retrieval_results)



st.sidebar.divider()
st.sidebar.write("✅ CQ Ready" if st.session_state.has_bayesian else "CQ: Not ready")
st.sidebar.write("✅ Docs Ready" if st.session_state.has_docs else "Docs: Not ready")
st.sidebar.write("✅ Pairs Ready" if st.session_state.has_pairs else "Pairs: Not ready")
#st.sidebar.write("✅ Mono Ready" if st.session_state.has_monolingual else "Mono: Not ready")
st.sidebar.divider()
if st.session_state.has_bayesian or st.session_state.has_docs or st.session_state.has_pairs:
    st.sidebar.page_link("pages/generate_grammar.py", label="Generate Grammar", icon=":material/bolt:")
