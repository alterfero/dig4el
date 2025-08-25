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
from libs import utils
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
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), encoding='utf-8') as f:
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
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"), "r", encoding='utf-8') as f:
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
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w", encoding='utf-8') as fdi:
        utils.save_json_normalized(st.session_state.info_doc, fdi)

def generate_sentence_pairs_signatures(sentence_pairs: list[dict]) -> list[str]:
    sig_list = []
    for sentence_pair in sentence_pairs:
        sig_list.append(u.clean_sentence(sentence_pair["source"], filename=True))
    return sig_list


with st.sidebar:
    st.image("./pics/dig4el_logo_sidebar.png")
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.sidebar.page_link("pages/generate_grammar.py", label="Generate Grammar", icon=":material/bolt:")

st.header("Sources Dashboard")
with st.popover("Using the dashboard"):
    st.markdown("""
1. Select a language, then click the **Select Language** button.  
2. Explore the three available tabs:  

   - **CQ** (Conversational Questionnaires): Create or upload translations of conversational questionnaires—dialogues designed to capture detailed grammatical information about the language.  
   - **Documents**: Upload public PDF documents related to the language, such as academic papers, articles, Wikipedia pages, or any other source containing reliable grammatical information.  
   - **Sentence Pairs**: Provide sentences in a mainstream language along with their translations in the target language.  

Once data is available, the **Generate** button and corresponding menu option will appear.
    """)

colq, colw = st.columns(2)
selected_language = colq.selectbox("What language are we working on?", gu.GLOTTO_LANGUAGE_LIST)
if st.button("Select {}".format(selected_language)):
    st.session_state.indi_language = selected_language
    st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi_language,
                                                                   "glottocode not found")
    fmu.create_ld(BASE_LD_PATH, st.session_state.indi_language)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "r", encoding='utf-8') as f:
        st.session_state.info_doc = json.load(f)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "delimiters.json"), "r", encoding='utf-8') as f:
        st.session_state.delimiters = json.load(f)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"), "r", encoding='utf-8') as f:
        content = json.load(f)
    st.session_state.batch_id = content.get("batch_id", "no batch ID in batch_id_store")
    PAIRS_BASE_PATH = os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs")
    CURRENT_JOB_SIG_FILE = os.path.join(PAIRS_BASE_PATH, "current_job_sig.json")
    JOB_INFO_FILE = os.path.join(PAIRS_BASE_PATH, "job_progress.json")

st.markdown("*glottocode* {}".format(st.session_state.indi_glottocode))

st.markdown("#### Using the tabs below, add information about {}".format((st.session_state.indi_language)))

st.divider()
tab1, tab2, tab3 = st.tabs(["CQ", "Documents", "Sentence Pairs"])
with tab1:
    st.markdown("""
   To create new Conversational Questionnaires translations, head to "Enter CQ Translations".
    
    If you already entered CQ translations with DIG4EL, you can go to "Use existing translations". 
    You will be directed back here once the CQ knowledge is built. 
    """)
    st.page_link("pages/record_cq_transcriptions.py", label="👉🏽 Create new DIG4EL CQ translations")
    st.page_link("pages/infer_from_knowledge_and_cqs.py", label="👉🏽 Prepare DIG4EL CQ translations for content generation")

    if st.session_state.indi_language in os.listdir(BASE_LD_PATH):
        if "cq" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language)):
            existing_cqs = [f for f in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq", "cq_translations")) if f.endswith(".json")]
            if existing_cqs:
                st.success("{} CQ translations available: ".format(len(existing_cqs)))
                for cqfn in existing_cqs:
                    st.write("- {}".format(cqfn))
            if "cq_knowledge" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq")):
                if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                                                  "cq",
                                                                  "cq_knowledge")):

                    st.success("Knowledge from CQs has been computed.")
                    st.write("Feel free to add or edit CQ translations and re-compute inferences.")

with tab2:
    with st.popover("How to upload and prepare documents"):
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
    st.subheader("Upload new documents from your computer to DIG4EL server")
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
        st.write("An existing vector store has been found.")
        print("VSID found and matches ({})".format(st.session_state.vsid))
        st.session_state.has_vector_store = True
    else:
        print("No VSID found in info_dict matching an existing VSID: Creating a vector store")
        st.write("No vector store found with ID {}".format(st.session_state.vsid))
        with st.spinner("Creating new vector store"):
            st.session_state.vsid = ovsu.create_vector_store_sync(st.session_state.indi_language + "_documents")
            st.session_state.info_doc["documents"]["oa_vector_store_id"] = st.session_state.vsid
            save_info_dict()
        print("New vector store created with VSID {}".format(st.session_state.vsid))
        st.session_state.has_vector_store = True

    # list which uploaded files are staged
    with st.spinner("Listing staged files"):
        st.session_state.staged = ovsu.list_files_sync()
        # print("Listing staged files")
        # print(st.session_state.staged)
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
        if st.checkbox("Check details"):
            st.write("Vector Store ID: {}".format(st.session_state.vsid))
            st.write([vs for vs in ovsu.list_vector_stores_sync() if vs.id == st.session_state.vsid])
            st.write("Files to vectorize: ")
            st.write(to_vectorize)
        if colw2.button("3) Vectorize all {} unvectorized staged files".format(len([f["id"] for f in to_vectorize]))):
            to_vec_fids = [f["id"] for f in to_vectorize]
            with colw2:
                with st.spinner("Launching vectorization of staged files"):
                    ovsu.add_files_to_vector_store_sync(vsid=st.session_state.vsid,
                                                        file_ids=to_vec_fids)

    elif not to_stage and not to_vectorize:
        colw2.success("All files staged and vectorized")

    if st.session_state.vectorized_docs and st.button("Check vectorization status"):
        with st.spinner("Checking"):
            st.session_state.vector_store_status = ovsu.check_vector_store_status_sync(st.session_state.vsid)
        if st.session_state.vector_store_status is not None:
            if st.session_state.vector_store_status == "completed":
                st.success("Vectorization done.")
                st.session_state.has_docs = True
            else:
                st.warning("Documents are still being vectorized, check again in a few minutes")
                st.write("Current status: {}".format(st.session_state.vector_store_status))

    st.divider()


with tab3:
    with st.popover("How to create, upload and prepare sentence pairs"):
        st.write(f"""
        1. **Prepare sentence pairs** in a CSV (Comma-Separated Value) file with "source" and "target" columns. 
        The easiest way to create a suitable CSV file is to create a spreadsheet (Excel, Pages, Open Office...) 
        with a "source" column and a "target" column. On each line, write the sentence in the mainstream language 
        in the "source" column, and in the language you are working on in the "target" column. Then you can *save as* 
        or *export* as .csv. You can also directly upload a JSON following the downloadable template. 
        2. DIG4EL **prepares** these pairs using a LLM. It is a long process. The *augmented pairs* file is then stored for future use, on the server and you
        should also keep a copy on your computer.
        3. You are then invited to **connect {st.session_state.indi_language} word(s) with concept(s)** in sentences.
        4. Finally, click on the "Index" button. 
        The **augmented pair** file is then used to provide relevant augmented pairs to grammatical descriptions 
        (Retrieval-Augmented Generation, or RAG). 
        """)
        v1, v2, v3 = st.columns(3)
        with v1:
            st.download_button("Download an Excel template", "./templates/sentence_pairs_template.xls",
                               mime="application/vnd.ms-excel",
                               file_name="dig4el_sentence_pairs_template.xls")
            st.markdown("In Excel, do save as... csv, as shown below. ")
            st.image("./pics/excel_convert.png")
        with v2:
            st.download_button("Download a CSV template", "./templates/sentence_pairs_template.csv",
                               mime="text/csv",
                               file_name="dig4el_sentence_pairs_template.csv")
            st.markdown("A CSV file is a simple text file you can create in any text editor if you don't have a spreadsheet software available.")
        with v3:
            st.download_button("Download a JSON template", "./templates/sentence_pairs_template.json",
                               mime="application/json",
                               file_name="dig4el_sentence_pairs_template.json")
            st.markdown("A JSON file is also a simple text file you can create with a text editor.")

    st.subheader("1. Add sentence pairs files")
    available_pairs = st.session_state.info_doc["pairs"]
    available_pairs_filenames = []
    if available_pairs == []:
        st.write("No sentence pair file available yet")
    else:
        available_pairs_filenames = [p["filename"] for p in st.session_state.info_doc["pairs"]]
        df_display = pd.DataFrame(st.session_state.info_doc["pairs"])
        st.markdown("**Available sentence pairs files**")
        st.dataframe(df_display)

    new_pair_file = st.file_uploader(
        "Add a new sentence pair file to the server (.csv or .json)",
        accept_multiple_files=False
    )

    # Upload sentence pairs file
    if new_pair_file and new_pair_file.name[-4:] in ["json", ".csv"]:
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
            server_filename = None
            if info_entered and st.button("Add this file to sentence pairs on the server"):
                try:
                    if new_pair_file.name[-4:] == ".csv":
                        sentence_pairs = u.csv_to_dict(new_pair_file)
                        server_filename = new_pair_file.name[:-4] + ".json"
                    else:
                        sentence_pairs = json.load(new_pair_file)
                        server_filename = new_pair_file.name
                    if "source" in sentence_pairs[0].keys() and "target" in sentence_pairs[0].keys():
                        valid_file = True
                    else:
                        st.warning(
                            "This is a JSON file, but not a sentence pair file formatted as a list of 'source' and 'target' keys()")
                except:
                    st.write("Not a correctly formatted JSON file.")
            if valid_file:

                st.success("Adding {} to the server".format(server_filename))
                with open(os.path.join(PAIRS_BASE_PATH, "pairs", server_filename), "w", encoding='utf-8') as f:
                    utils.save_json_normalized(sentence_pairs, f)
                st.success(f"Saved `{server_filename}` on the server.")

                # UPDATE INFO_DOC
                if server_filename in available_pairs_filenames:
                    i = [i for i in st.session_state.info_doc["pairs"].index if
                         st.session_state.info_doc["pairs"]["filename"] == server_filename][0]
                    del (st.session_state.info_doc["pairs"][i])

                st.session_state.info_doc["pairs"].append(
                    {
                        "filename": server_filename,
                        "name": name,
                        "origin": origin,
                        "author": author,
                        "augmented": False
                    }
                )
                with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w", encoding='utf-8') as f:
                    utils.save_json_normalized(st.session_state.info_doc, f)
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
    coln, colm = st.columns(2)
    coln.markdown("**{} Available augmented sentences**".format(len(available_augmented_sentences)))
    if len(available_augmented_sentences) > 0 and colm.checkbox("Explore augmented sentences"):
        selected_augmented_sentence = st.selectbox("Select a sentence",
                                                   [s[:-5] for s in available_augmented_sentences])
        selected_augmented_sentence_file = selected_augmented_sentence + ".json"
        with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs", selected_augmented_sentence_file), "r", encoding='utf-8') as f:
            sas = json.load(f)

        st.markdown(f"""
        - **{st.session_state.indi_language}**: **{sas["target"]}**
        - **Pivot**: {sas["source"]}
        - **Description**: {sas["description"]}
        - **Grammatical keywords**: {sas["keywords"]}
        - **Key translation concepts**: {sas["key_translation_concepts"]}
        - **{st.session_state.indi_language} word(s) - concept(s) connections**: 
        """)
        if sas.get("connections", {}) != {}:
            for connection in sas.get("connections", {}):
                st.write("{} --> {}".format(connection, sas["connections"][connection]))
        else:
            st.write("No connection created.")
        if sas.get("gloss", None):
            st.write(sas["gloss"])


    # add new pairs
    if len(st.session_state.info_doc["pairs"]) > 0:
        st.session_state.selected_pairs_filename = st.selectbox("Select a sentence pairs file to augment",
                                                                [item["filename"]
                                                                 for item in st.session_state.info_doc["pairs"]])

        with open(os.path.join(PAIRS_BASE_PATH, "pairs", st.session_state.selected_pairs_filename), "r", encoding='utf-8') as f:
            st.session_state.sentence_pairs = json.load(f)

        # user triggers augmentation
        progress = squ.get_batch_progress(st.session_state.batch_id)
        create_btn = st.button(
            "Augment {} (long process, LLM use)".format(st.session_state.selected_pairs_filename))
        if create_btn and not st.session_state.enriching_pairs:  # augmentation launched only if previous one done
            pairs_signatures = generate_sentence_pairs_signatures(st.session_state.sentence_pairs)
            with open(CURRENT_JOB_SIG_FILE, "w", encoding='utf-8') as f:
                utils.save_json_normalized(pairs_signatures, f)
            # Pass jobs to Redis
            new_pairs = [pair for pair in st.session_state.sentence_pairs
                         if u.clean_sentence(pair["source"], filename=True) + ".json"
                         not in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))]
            if new_pairs != st.session_state.sentence_pairs:
                st.write("{} sentences discarded: they already have been augmented".format(
                    len(st.session_state.sentence_pairs) - len(new_pairs)
                ))
            st.session_state.batch_id = squ.enqueue_batch(new_pairs)
            with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"), "w", encoding='utf-8') as f:
                utils.save_json_normalized({"batch_id": st.session_state.batch_id}, f)

        if st.button("Save new augmented sentences"):
            new_pairs = [pair for pair in st.session_state.sentence_pairs
                         if u.clean_sentence(pair["source"], filename=True) + ".json"
                         not in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))]
            c = 0
            for new_pair in new_pairs:
                key = u.clean_sentence(new_pair["source"], filename=True)
                value = squ.retrieve_from_redis(key)
                if value:
                    c += 1
                    new_augmented_pair = json.loads(squ.retrieve_from_redis(key))
                    with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs",
                                           key + ".json"), "w") as f:
                        json.dump(new_augmented_pair, f, indent=2, ensure_ascii=False)
            st.success("{} new augmented pairs saved, {} augmented_pairs available now in {}".format(
                c, len(os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))) - 1,
                                  st.session_state.indi_language))

    progress = squ.get_batch_progress(st.session_state.batch_id)
    if progress["queued"] != progress["finished"] + progress["failed"]:
        st.markdown("""The sentence augmentation is in progress. It is a long process (up to 2 minutes per sentence)
        that will continue even if you close this page or turn off your computer. You can come back anytime 
        and press the progress update button below to check on progress and make completed augmentations 
        available for use. You can also click anytime on the "Save new augmented sentences" button 
        to retrieve new augmented sentence. 
        """)

        progress = squ.get_batch_progress(st.session_state.batch_id)
        st.progress("Progress", progress["percent_complete"])

    with st.sidebar:
        if st.checkbox("Redis info"):
            progress = squ.get_batch_progress(st.session_state.batch_id)
            st.write("Queue status: {}".format(progress))

            if st.button("Clear batch"):
                print("Clearing batch {}".format(st.session_state.batch_id))
                squ.clear_batch(batch_id=st.session_state.batch_id, delete_jobs=True)
            manual_batch_id = st.text_input("Enter manually a batch_id")
            if st.button("Use this batch_id"):
                st.session_state.batch_id = manual_batch_id
                st.rerun()
            ti = st.text_input("DANGER ZONE: flush all")
            if ti == "flush all":
                squ.flush_all()
                st.rerun()

            if st.button("Save new augmented sentences", key="side_save"):
                new_pairs = [pair for pair in st.session_state.sentence_pairs
                             if u.clean_sentence(pair["source"], filename=True) + ".json"
                             not in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))]
                c = 0
                for new_pair in new_pairs:
                    key = u.clean_sentence(new_pair["source"], filename=True)
                    value = squ.retrieve_from_redis(key)
                    if value:
                        c += 1
                        new_augmented_pair = json.loads(squ.retrieve_from_redis(key))
                        with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs",
                                               key + ".json"), "w") as f:
                            json.dump(new_augmented_pair, f, indent=2, ensure_ascii=False)
                st.success("{} new augmented pairs saved, {} augmented_pairs available now in {}".format(
                    c, len(os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))) - 1,
                    st.session_state.indi_language))

    # ADD WORD-CONCEPT CONNECTIONS
    st.subheader("3. Connect word(s) and concept(s) in augmented sentences")
    st.markdown("""This step is manual and adds a lot of information to the corpus.\\
    Open a sentence by clicking in the colored border on the left of the sentence, then associate one or 
    multiple target words with each proposed meaning. """)

    #build aug_sent_df
    aps = []
    for ap_file in [fn
                    for fn in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))
                    if fn[-5:] == ".json"]:
        with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs", ap_file), "r", encoding='utf-8') as f:
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
        with open(selected_ap["filename"], "r", encoding='utf-8') as f:
            slap = json.load(f)
        if not slap.get("connections", None):
            slap["connections"] = {}
        st.markdown(f"**{st.session_state.indi_language}**: {slap['target']}")
        st.markdown(f"**English**: {slap['source']}")
        key_translation_concepts = slap["key_translation_concepts"]
        words = stats.custom_split(slap["target"], st.session_state.delimiters)

        for ktc in key_translation_concepts:
            connected_words = st.multiselect(f"**{ktc}** Is expressed by",
                                             words,
                                             default=slap["connections"].get(ktc, []),
                                             key="cw"+ktc)
            slap["connections"][ktc] = connected_words
        if st.button("Submit connections"):
            with open(selected_ap["filename"], "w", encoding='utf-8') as f:
                utils.save_json_normalized(slap, f)
                st.success("Connections saved")

    st.subheader("4. Index augmented pairs to make them ready for use")
    if st.button("Index!"):
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
