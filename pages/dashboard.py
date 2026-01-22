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
import copy

import streamlit as st
import time
import os
import pandas as pd
import json
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import openai_vector_store_utils as ovsu
from libs import sentence_queue_utils as squ
from libs import retrieval_augmented_generation_utils as ragu
from libs import utils
from libs import file_format_utils as ffu
from libs import display_utils as du
from libs import utils as u
from libs import stats
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import tempfile
from libs import semantic_description_agents as sda

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

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
if "is_guest" not in st.session_state:
    st.session_state.is_guest = None
if "caretaker_of" not in st.session_state:
    st.session_state.caretaker_of = []
if "caretaker_trigger" not in st.session_state:
    st.session_state.caretaker_trigger = False
if "llm_augmentation" not in st.session_state:
    st.session_state.llm_augmentation = True
if "force_augmentation" not in st.session_state:
    st.session_state.force_augmentation = False
if "admin_verbose" not in st.session_state:
    st.session_state.admin_verbose = True

# ------ AUTH SETUP --------------------------------------------------------------------------------
CFG_PATH = Path(
    os.getenv("AUTH_CONFIG_PATH") or
    os.path.join(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage", "auth_config.yaml")
)
# Cookie secret (override YAML)
COOKIE_KEY = os.getenv("AUTH_COOKIE_KEY", None)

# ---------- Load config ----------
def load_config(path: Path) -> dict:
    if not path.exists():
        print("load auth config failed, no config file")
        st.stop()  # fail fast; create it before running
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if COOKIE_KEY:
        cfg.setdefault("cookie", {})["key"] = COOKIE_KEY
    return cfg

# --- helper: atomic YAML write ---
def save_config_atomic(data: dict, path: Path):
    d = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=d, encoding="utf-8") as tmp:
        yaml.safe_dump(data, tmp, sort_keys=False, allow_unicode=True)
        tmp_path = tmp.name
    os.replace(tmp_path, path)  # atomic on POSIX

cfg = load_config(CFG_PATH)
authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"],
    auto_hash=True
)
# -------------------------------------------------------------------------------------------

PAIRS_BASE_PATH = os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs")
CURRENT_JOB_SIG_FILE = os.path.join(PAIRS_BASE_PATH, "current_job_sig.json")
JOB_INFO_FILE = os.path.join(PAIRS_BASE_PATH, "job_progress.json")

if "index.pkl" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs", "vectors")):
    st.session_state.has_pairs = True

# ================== HELPER FUNCTIONS ===========================================

def save_info_dict():
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "w", encoding='utf-8') as fdi:
        utils.save_json_normalized(st.session_state.info_doc, fdi)

def generate_sentence_pairs_signatures(sentence_pairs: list[dict]) -> list[str]:
    sig_list = []
    for sentence_pair in sentence_pairs:
        sig_list.append(u.clean_sentence(sentence_pair["source"], filename=True))
    return sig_list


# =============================================================================

with st.sidebar:
    st.image("./pics/dig4el_logo_sidebar.png")
    st.divider()
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.sidebar.page_link("pages/generate_grammar.py", label="Generate Grammar", icon=":material/bolt:")
    st.divider()

# AUTH UI AND FLOW -----------------------------------------------------------------------
if st.session_state["username"] is None:
    if st.button("Use without logging in"):
        st.session_state.is_guest = True
# ---------- Guest path: skip rendering the login widget entirely ----------
if st.session_state.is_guest:
    st.session_state["authentication_status"] = True
    st.session_state["username"] = "guest"
    st.session_state["name"] = "Guest"
else:
    authenticator.login(
        location="main",                 # "main" | "sidebar" | "unrendered"
        max_concurrent_users=20,         # soft cap; useful for small apps
        max_login_attempts=5,            # lockout window is managed internally
        fields={                         # optional label overrides
            "Form name": "Sign in",
            "Username": "email",
            "Password": "Password",
            "Login": "Sign in",
        },
        captcha=False,                    # simple built-in captcha
        single_session=True,             # block multiple sessions per user
        clear_on_submit=True,
        key="login_form_v1",             # avoid WidgetID collisions
    )

auth_status = st.session_state.get("authentication_status", None)
name        = st.session_state.get("name", None)
username    = st.session_state.get("username", None)

if auth_status:
    role = cfg["credentials"]["usernames"].get(username, {}).get("role", "guest")
    if st.session_state.indi_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
        role = "caretaker"
    title = ""
    if role in ["admin", "caretaker"]:
        title = role
    st.sidebar.success(f"Hello, {title} {name or username}")
    if role == "admin" and st.session_state.admin_verbose:
        st.session_state.admin_verbose = st.sidebar.checkbox("Admin verbose: {}".format(st.session_state.admin_verbose),
                                            value=st.session_state.admin_verbose)
    if st.session_state.is_guest:
        if st.sidebar.button("Logout", key="guest_logout"):
            for x in ("is_guest", "authentication_status", "username", "name"):
                st.session_state.pop(x, None)
            st.rerun()
    else:
        if st.sidebar.checkbox("Change password"):
            with st.sidebar:
                st.markdown("""Passwords must 
                - Be between 8 and 20 characters long, 
                - Contain at least one digit,
                - Contain at least one uppercase letter,
                - Contain at least one special character (@$!%*?&)""")
            authenticator.reset_password(username, location="sidebar")
            save_config_atomic(cfg, CFG_PATH)  # <-- persist the updated hash
            st.success("Password updated.")
        authenticator.logout(button_name="Logout", location="sidebar", key="auth_logout")

elif auth_status is False:
    role = None
    st.error("Invalid credentials")
    st.write("Try again. If you have forgotten your password, contact sebastien.christian@upf.pf")
    st.stop()

else:
    role = None
    st.info("Please log in or click on the 'Use without logging in' button")

# ------------------
ch1, ch2 = st.columns([8,2])
ch1.header("Sources Dashboard")

if "llist" not in st.session_state:
    st.session_state.llist = None

colq, colw = st.columns(2)
if role == "guest":
    st.session_state.llist = ["Tahitian"]
else:
    st.session_state.llist = gu.LLIST

# LANGUAGE SELECTION
coli1, coli2 = st.columns(2)
if st.session_state.indi_language in st.session_state.llist:
    default_language_index = st.session_state.llist.index(st.session_state.indi_language)
else:
    default_language_index = 0

selected_language_from_list = coli1.selectbox("Select the language you are working on in the list below",
                                                  st.session_state.llist,
                                                  index=default_language_index)
free_language_input = coli2.text_input("If not in the list, enter the language name here and press Enter.")
if free_language_input != "":
    if free_language_input.capitalize() in st.session_state.llist:
        st.warning("This language is already in the list! It is now selected.")
        selected_language = free_language_input.capitalize()
    else:
        selected_language = free_language_input.capitalize()
        fmu.create_ld(BASE_LD_PATH, st.session_state.indi_language)
        st.success("Adding {} to the list of languages.".format(free_language_input))
        st.markdown("Note that a pseudo-glottocode is added: {}".format(free_language_input.lower() + "+"))
        with open(os.path.join(BASE_LD_PATH, "languages.json"), "r") as fg:
            language_list_json = json.load(fg)
        language_list_json[free_language_input.capitalize()] = free_language_input + "+"
        with open(os.path.join(BASE_LD_PATH, "languages.json"), "w") as fgg:
            json.dump(language_list_json, fgg, indent=4)
else:
    selected_language = selected_language_from_list

if selected_language != st.session_state.indi_language:
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

    if st.session_state.indi_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
        role = "caretaker"
        if not st.session_state.caretaker_trigger:
            st.session_state.caretaker_trigger = True
            print("CARETAKER RERUN")
            st.rerun()


st.markdown("#### Using the tabs below, add information about {} (Glottocode {})"
            .format(st.session_state.indi_language,
                    st.session_state.indi_glottocode))
st.markdown("You can add 📝Conversational Questionnaires (CQ), 🔗Pairs of sentences and 📁Documents.")

st.markdown("""
<style>
/* TAB BAR CONTAINER */
div[data-testid="stTabs"] {
  background: #f3f4f6;
  padding: 0.35rem 0.5rem;
  border-radius: 10px;
}

/* TAB LIST */
div[data-testid="stTabs"] [role="tablist"] {
  gap: 0.35rem;
}

/* INDIVIDUAL TABS */
div[data-testid="stTabs"] button[role="tab"] {
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  border: 1px solid transparent;
  color: #6b7280;
  font-weight: 500;
}

/* HOVER */
div[data-testid="stTabs"] button[role="tab"]:hover {
  background: #e5e7eb;
  color: #111827;
}

/* ACTIVE TAB */
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: #111827;
  color: white;
  border-color: #111827;
}
</style>
""", unsafe_allow_html=True)

tab1, tab3, tab2 = st.tabs(["📝CQ", "🔗Sentence Pairs", "📁Documents", ])

with tab1:
    st.markdown("""
   - **To create new Conversational Questionnaires translations**, click on "Enter CQ Translations".
   - With or without CQ translations, click on **Process information from databases and CQs** to make dig4el build 
   upon existing knowlede and process CQs if available. 
    
   
    """)
    pl1, pl2 = st.columns(2)
    with pl1:
        st.markdown("#### 🆕 Create / resume a CQ translation")
        st.caption("Create new DIG4EL CQ translations or resume working on one.")
        if st.button("Open CQ Editor", use_container_width=True):
            st.switch_page("pages/record_cq_transcriptions.py")  # requires multipage + Streamlit that supports switch_page

    if role in ["admin", "caretaker"]:
        with pl2:
            st.markdown("#### ⬆️ Infer grammar from CQs")
            st.caption("Make DIG4EL guess the grammar of {}.".format(st.session_state.indi_language))
            if st.button("Infer grammar from CQs", use_container_width=True):
                st.switch_page("pages/infer_from_knowledge_and_cqs.py")

    if st.session_state.indi_language in os.listdir(BASE_LD_PATH):
        if "cq" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language)):
            existing_cqs = [f for f in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq", "cq_translations")) if f.endswith(".json")]
            if existing_cqs:
                st.success("{} CQ translations available: click in the table to display a CQ".format(len(existing_cqs)))
                cq_catalog = u.catalog_all_available_cqs(language=st.session_state.indi_language)
                cq_catalog_df = pd.DataFrame(cq_catalog).sort_values(by="title")
                selected_cell = st.dataframe(cq_catalog_df, hide_index=True,
                                             column_order=["title", "language", "pivot", "info"],
                                             selection_mode="single-cell", on_select="rerun")

                if selected_cell["selection"]["cells"] != []:
                    selected_cq_index_in_displayed_df = selected_cell["selection"]["cells"][0][0]
                    catalog_entry = cq_catalog_df.iloc[selected_cq_index_in_displayed_df]
                    with open(os.path.join(BASE_LD_PATH, catalog_entry["language"], "cq", "cq_translations",
                                           catalog_entry["filename"])) as fcqd:
                        cqd = json.load(fcqd)
                    du.display_cq(cqd, st.session_state.delimiters,
                                  title=catalog_entry["title"],
                                  uid=catalog_entry["uid"],
                                  gloss=False)
                else:
                    st.write("Select a CQ in the table to see its content.")

            if "cq_knowledge" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq")):
                if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                                                  "cq",
                                                                  "cq_knowledge")):

                    st.success("Inferences from CQ have been performed")
                    st.markdown("*If you add or edit CQ translations, re-compute inferences*")
            else:
                st.warning("No Inferences on CQs computed yet")

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

    if role in ["admin", "caretaker"]:
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
    else:
        st.markdown("*Only caretakers can upload documents*")
        st.markdown(f"*Contact us to propose documents*")

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
    if role == "admin" and st.session_state.admin_verbose:
        st.write("admin: vsid_from_info_dict: {}".format(vsid_from_info_dict))
    with st.spinner("Updating store list"):
        st.session_state.available_vector_stores = ovsu.list_vector_stores_sync()  # ADDED FOR TESTING
    # print("Updated VS list: {}".format(st.session_state.available_vector_stores))
    # print("VSIDs: {}".format([vs.id for vs in st.session_state.available_vector_stores]))

    if vsid_from_info_dict is not None and vsid_from_info_dict in [vs.id for vs in st.session_state.available_vector_stores]:
        st.session_state.vsid = vsid_from_info_dict
        if role == "admin" and st.session_state.admin_verbose:
            st.write("An existing vector store has been found.")
            st.write("{} VSID found and matches ({})".format(st.session_state.indi_language, st.session_state.vsid))
        st.session_state.has_vector_store = True
    else:
        if role == "admin" and st.session_state.admin_verbose:
            st.write("No VSID found in info_dict matching an existing VSID: Creating a vector store")
            st.write("No vector store found with ID {}".format(st.session_state.indi_language, st.session_state.vsid))
        with st.spinner("Creating new vector store"):
            st.session_state.vsid = ovsu.create_vector_store_sync(st.session_state.indi_language + "_documents")
            if role == "admin" and st.session_state.admin_verbose:
                st.write("admin: New VSID: {}".format(st.session_state.vsid))
            st.session_state.info_doc["documents"]["oa_vector_store_id"] = st.session_state.vsid
            with st.spinner("Updating..."):
                print("{} stores in st.session_state.available_vector_stores BEFORE update".format(len(st.session_state.available_vector_stores)))
                st.session_state.available_vector_stores = ovsu.list_vector_stores_sync()
                print("{} stores in st.session_state.available_vector_stores AFTER update".format(len(st.session_state.available_vector_stores)))

            save_info_dict()
        if role == "admin" and st.session_state.admin_verbose:
            st.write("admin: New vector store created with VSID {}".format(st.session_state.vsid))
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
    st.dataframe(status_df, width='stretch')

    colw1, colw2 = st.columns(2)
    # Staging unstaged files
    to_stage = [f for f in st.session_state.file_status_list if not f["staged"]]
    if to_stage:
        with st.spinner("Staging files..."):
            colw1.markdown("{} files to stage".format(len(to_stage)))
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
        if role == "admin" and st.session_state.admin_verbose:
            st.write("admin: Vector Store ID: {}".format(st.session_state.vsid))
            st.write([vs for vs in ovsu.list_vector_stores_sync() if vs.id == st.session_state.vsid])
            st.write("admin: Files to vectorize: ")
            st.write(to_vectorize)
        with st.spinner("admin: Vectorizing {} unvectorized staged files".format(len([f["id"] for f in to_vectorize]))):
            to_vec_fids = [f["id"] for f in to_vectorize]
            with colw2:
                ovsu.add_files_to_vector_store_sync(vsid=st.session_state.vsid,
                                                    file_ids=to_vec_fids)
        st.write("Vectorization is in progress. It can take a few minutes. You can close the page in the meantime, "
                 "or refresh it later to verify that the vectorization has been completed.")

    elif not to_stage and not to_vectorize:
        colw2.success("All files staged and vectorized")

    if role == "admin" and st.session_state.admin_verbose:
        if st.session_state.vectorized_docs and st.button("Check vectorization status"):
            st.session_state.vector_store_status = ovsu.check_vector_store_status_sync(st.session_state.vsid)
            if st.session_state.vector_store_status is not None:
                if st.session_state.vector_store_status == "completed":
                    st.success("Vectorization done.")
                    st.session_state.has_docs = True
                else:
                    st.warning("Documents are still being vectorized, check again in a few minutes")
                    st.write("Current status: {}".format(st.session_state.vector_store_status))
            else:
                st.write("No status for vector store {}".format(st.session_state.vsid))

    st.divider()


with tab3:
    with st.popover("How to create, upload and prepare sentence pairs"):
        st.write(f"""
        **Note**: If you have sentence pairs in a software (as Flex) or a database, do an export and share with us, we'll take care of the conversion.
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
        ufwc = 0
        upload_file_widget_key = "ufwk_" + str(ufwc)
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

    # ===== ADMIN CONVERSION TEST =======================================
    if role == "admin" and st.session_state.admin_verbose:
        file_to_convert = st.file_uploader("Convert file",
                                           accept_multiple_files=False,
                                           key="convert_file_upload")
        source_format = st.selectbox("Format", ["Pangloss XML"])
        if file_to_convert is not None:
            tmp_filepath = os.path.join("./", "tmp", file_to_convert.name)
            with open(tmp_filepath, "wb") as tf:
                tf.write(file_to_convert.getbuffer())
            # use pangloss_xml_to_sentence_pairs_json(pangloss_xml_filepath)
            if st.button("Convert"):
                if source_format == "Pangloss XML":
                    try:
                        converted_sentence_pairs = ffu.pangloss_xml_to_sentence_pairs_json(os.path.join("./", "tmp", file_to_convert.name))
                        st.success("File converted to sentence pairs")
                        st.download_button("Download converted sentence pairs",
                                           data=json.dumps(converted_sentence_pairs, ensure_ascii=False, indent=4),
                                           file_name="converted_sentence_pairs.json",
                                           mime="application/json")
                    except Exception as e:
                        st.error("Error converting file: {}".format(e))


    # ====== NEW PAIRS FILE UPLOAD FORM ==================================
    if role in ["guest", "user"]:
        st.markdown("*Caretakers only can upload sentence pairs. Contact us if you want to be a caretaker of {}*".format(st.session_state.indi_language))
    elif role in ["admin", "caretaker"]:
        new_pair_file = st.file_uploader(
            "Add a new sentence pair file to the server (.csv or .json)",
            accept_multiple_files=False,
            key=upload_file_widget_key
        )
        if new_pair_file:
            with st.form("Add a new sentence pair file to the server", clear_on_submit=False, enter_to_submit=False):
                valid_file = False
                server_filename = None
                if new_pair_file.name[-4:] in ["json", ".csv"]:
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
                        st.write("Not a correctly formatted JSON or CSV file.")

                    name = st.text_input("Name this corpus")
                    origin = st.text_input("Origin of the corpus")
                    author = st.text_input("Author/owner of the corpus")

                    upload_new_sentence_pairs_file_disabled = valid_file is None or server_filename is None

                new_sentence_pairs_file_submitted = st.form_submit_button("Submit",
                                                            disabled=upload_new_sentence_pairs_file_disabled)

                if new_sentence_pairs_file_submitted:
                    if author and origin and name:
                        st.success("Adding {} to the server".format(server_filename))
                        with open(os.path.join(PAIRS_BASE_PATH, "pairs", server_filename), "w", encoding='utf-8') as f:
                            utils.save_json_normalized(sentence_pairs, f)
                        st.success(f"Saved `{server_filename}` on the server.")

                        # UPDATE INFO_DOC
                        if server_filename in available_pairs_filenames:
                            i = [i for i in st.session_state.info_doc["pairs"] if
                                 i["filename"] == server_filename]
                            if i != []:
                                st.session_state.info_doc["pairs"].remove(i[0])
                                print("Remove {} from st.session_state.info_doc".format(i[0]))
                            else:
                                print("server_filename {} not found in st.session_state.info_doc {}".format(
                                    server_filename, st.session_state.info_doc
                                ))

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
                        ufwc += 1 #changing upload widget key to reset it.
                        st.rerun()
                    else:
                        st.warning("You must provide a name, an origin and an author for this corpus")

    # DISPLAY AUGMENTED SENTENCE PAIRS

    st.subheader("2. Augment sentence pairs with automatic grammatical descriptions")
    st.markdown("""Sentence pairs are augmented with grammatical descriptions, so they can be used efficiently.
    This is a long process that will run in the background once started (you can
    leave this page or turn off your computer and come back later.)
    """)

    # Display available augmented pairs
    # available_augmented_sentences = [fn
    #                                  for fn in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))
    #                                  if fn[-5:] == ".json"
    #                                  ]
    # coln, colm = st.columns(2)
    # coln.markdown("**{} Available augmented sentences**".format(len(available_augmented_sentences)))
    # if len(available_augmented_sentences) > 0 and colm.checkbox("Explore augmented sentences"):
    #     selected_augmented_sentence = st.selectbox("Select a sentence",
    #                                                [s[:-5] for s in available_augmented_sentences])
    #     selected_augmented_sentence_file = selected_augmented_sentence + ".json"
    #     with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs", selected_augmented_sentence_file), "r", encoding='utf-8') as f:
    #         sas = json.load(f)
    #
    #     st.markdown(f"""
    #     - **{st.session_state.indi_language}**: **{sas["target"]}**
    #     - **Pivot**: {sas["source"]}
    #     - **Description**: {sas["description"]}
    #     - **Grammatical keywords**: {sas["keywords"]}
    #     - **Comments**: {sas.get("comments", "")}
    #     - **Key translation concepts**: {sas["key_translation_concepts"]}
    #     - **{st.session_state.indi_language} word(s) - concept(s) connections**:
    #     """)
    #     if sas.get("connections", {}) != {}:
    #         for connection in sas.get("connections", {}):
    #             st.write("{} --> {}".format(connection, sas["connections"][connection]))
    #     else:
    #         st.write("No connection created.")
    #     if sas.get("gloss", None):
    #         st.write(sas["gloss"])

    if role == "admin" and st.session_state.admin_verbose:
        with st.sidebar:
            st.session_state.llm_augmentation = st.checkbox("ADMIN: Use LLM for augmentation",
                                                            value=st.session_state.llm_augmentation)
            st.session_state.force_augmentation = st.checkbox("ADMIN: Force re-augmentation",
                                                              value=st.session_state.force_augmentation)

            if st.button("Reset augmented pairs"):
                u.reset_augmented_pairs(st.session_state.indi_language)

            if st.button("Reset sentence pairs"):
                u.reset_pairs(st.session_state.indi_language)

    # ========= SENTENCE PAIRS AUGMENTATION ================================================

    if role in ["admin", "caretaker"]:
        if len(st.session_state.info_doc["pairs"]) > 0:
            st.session_state.selected_pairs_filename = st.selectbox("Select a sentence pairs file to augment",
                                                                    [item["filename"]
                                                                     for item in st.session_state.info_doc["pairs"]])

            with open(os.path.join(PAIRS_BASE_PATH, "pairs", st.session_state.selected_pairs_filename), "r", encoding='utf-8') as f:
                st.session_state.sentence_pairs = json.load(f)

            # user triggers augmentation
            if not st.session_state.llm_augmentation:
                st.warning("llm_augmentation is False. No LLM will be used for sentence augmentation.")
            if st.session_state.force_augmentation:
                st.warning("force_augmentation is True. Augmented sentences may be re-augmented")
            progress = squ.get_batch_progress(st.session_state.batch_id)
            create_btn = st.button(
                "Augment {} (long process, LLM use)".format(st.session_state.selected_pairs_filename))

            if create_btn:
                pairs_signatures = generate_sentence_pairs_signatures(st.session_state.sentence_pairs)
                with open(CURRENT_JOB_SIG_FILE, "w", encoding='utf-8') as f:
                    utils.save_json_normalized(pairs_signatures, f)
                if not st.session_state.force_augmentation:
                    new_pairs = [pair for pair in st.session_state.sentence_pairs
                                 if u.clean_sentence(pair["source"], filename=True) + ".json"
                                 not in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))]
                    if new_pairs != st.session_state.sentence_pairs:
                        st.write("{} sentences discarded: they already have been augmented".format(
                            len(st.session_state.sentence_pairs) - len(new_pairs)
                        ))
                else:
                    new_pairs = [pair for pair in st.session_state.sentence_pairs]

                # Pass jobs to Redis and save the batch_id in a file just in case
                if st.session_state.llm_augmentation:
                    st.session_state.batch_id = squ.enqueue_batch(new_pairs)
                    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"),
                              "w", encoding='utf-8') as f:
                        utils.save_json_normalized({"batch_id": st.session_state.batch_id}, f)
                else:
                    if st.session_state.force_augmentation:
                        new_pairs = st.session_state.sentence_pairs
                    else:
                        new_pairs = [pair for pair in st.session_state.sentence_pairs
                                     if u.clean_sentence(pair["source"], filename=True) + ".json"
                                     not in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))]
                    c = 0
                    for new_pair in new_pairs:
                        a_pair = copy.deepcopy(new_pair)
                        a_pair["description"] = ""
                        a_pair["keywords"] = []
                        a_pair["key_translation_concepts"] = []
                        # Retro-compatibility connections -> word connections. Don't ask me why.
                        if "word connections" not in a_pair.keys():
                            a_pair["word connections"] = {}
                        if "connections" in a_pair.keys():
                            a_pair["word connections"] = copy.deepcopy(a_pair["connections"])
                            del a_pair["connections"]
                        # ===
                        a_pair_filename = u.clean_sentence(a_pair["source"], filename=True)
                        with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs",
                                               a_pair_filename + ".json"), "w") as f:
                            json.dump(a_pair, f, indent=2, ensure_ascii=False)
                        c += 1
                    st.success("{} augmented sentence files created without LLM augmentation".format(c))

            if st.session_state.llm_augmentation and st.button("Save new augmented sentences"):
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
                    c, len(os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))),
                                      st.session_state.indi_language))

        progress = squ.get_batch_progress(st.session_state.batch_id)
        if role == "admin" and st.session_state.admin_verbose:
            st.markdown("**ADMIN**: batch ID {}, progress: {}".format(st.session_state.batch_id, progress))
        if progress["queued"] != progress["finished"] + progress["failed"]:
            st.markdown("""The sentence augmentation is in progress. It is a long process (up to 2 minutes per sentence)
            that will continue even if you close this page or turn off your computer. You can come back anytime 
            and press the progress update button below to check on progress and make completed augmentations 
            available for use. You can also click anytime on the "Save new augmented sentences" button 
            to retrieve new augmented sentence. 
            """)

            progress = squ.get_batch_progress(st.session_state.batch_id)
            try:
                st.progress(int(progress["percent_complete"]), "Progress {}%, {}/{}".format(progress["percent_complete"],
                                                                                                   progress["finished"],
                                                                                                progress["queued"]))
            except:
                st.write(progress)
    else:
        st.divider()
        st.markdown("*Only caretakers can trigger sentence augmentation*")

    if role == "admin" and st.session_state.admin_verbose:
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

    # EDIT CONTENT, ADD COMMENTS AND WORD-CONCEPT CONNECTIONS
    if role in ["admin", "caretaker"]:
        st.subheader("3. Add/edit comments and connect word(s) and concept(s) in augmented sentences")
        st.markdown(f"""This step is manual and adds a lot of information to the corpus.\\
        Open a sentence by clicking in the colored border on the left of the sentence, then associate one or 
        multiple target words with each proposed meaning and add any comment that helps understanding the structure 
         of the sentence in {st.session_state.indi_language}""")

        #build aug_sent_df
        aps = []
        for ap_file in [fn
                        for fn in os.listdir(os.path.join(PAIRS_BASE_PATH, "augmented_pairs"))
                        if fn[-5:] == ".json"]:
            with open(os.path.join(PAIRS_BASE_PATH, "augmented_pairs", ap_file), "r", encoding='utf-8') as f:
                ap = json.load(f)
                # Retro-compatibility connections -> word connections. Don't ask me why.
                if "word connections" not in ap.keys():
                    ap["word connections"] = {}
                if "connections" in ap.keys():
                    ap["word connections"] = copy.deepcopy(ap["connections"])
                    del ap["connections"]
                # ===
                if "key_translation_concepts" not in ap.keys():
                    ap["key_translation_concepts"] = []
            aps.append(
                {
                    "source": ap["source"],
                    "target": ap["target"],
                    "comments": ap.get("comments", ""),
                    "key_translation_concepts": ap.get("key_translation_concepts", []),
                    "word connections": ap["word connections"],
                    "keywords": ap.get("keywords", []),
                    "filename": os.path.join(PAIRS_BASE_PATH, "augmented_pairs", ap_file)
                }
            )
        aps_df = pd.DataFrame(aps, columns=["source", "target", "comments", "word connections"])
        selected = st.dataframe(aps_df, selection_mode="single-row", on_select="rerun", key="aps_df")

        if selected["selection"]["rows"] != []:
            selected_ap = aps[selected["selection"]["rows"][0]]
            with open(selected_ap["filename"], "r", encoding='utf-8') as f:
                slap = json.load(f)
                # Retro-compatibility connections -> word connections. Don't ask me why.
                if "word connections" not in slap.keys():
                    slap["word connections"] = {}
                if "connections" in slap.keys():
                    slap["word connections"] = copy.deepcopy(slap["connections"])
                    del slap["connections"]
                # ===
            if role == "admin" and st.session_state.admin_verbose:
                with st.popover("ADMIN: slap"):
                    st.write(slap)
            source = st.text_input("Edit Source", value=slap.get("source", ""))
            target = st.text_input("Edit {}".format(st.session_state.indi_language), value=slap.get("target", ""))
            comments = st.text_input("Add/edit comments", value=slap.get("comments", ""))
            with st.expander("Edit LLM content"):
                description = st.text_input("Edit description", value=slap.get("description", ""))
                keywords_string = st.text_input("Edit keywords (respect format)", value=", ".join(slap.get("keywords", [])))
                keywords = keywords_string.split(", ")
                key_translation_concepts = slap.get("key_translation_concepts", [])
                words = stats.custom_split(slap["target"], st.session_state.delimiters)
            st.markdown("**Add connections**")
            ktc_pop = []
            wc_add = []
            colc1, colc2 = st.columns(2)
            unconnected_ktc = [ktc
                               for ktc in key_translation_concepts
                               if ktc not in slap["word connections"].keys()]
            for ktc in unconnected_ktc:
                source_concept = colc1.text_input("Concept (edit if needed)", value=ktc, key="ktc_"+ktc)
                connected_words = colc2.multiselect(f"is expressed by",
                                                 words, key="cw"+ktc)
                colc1.divider()
                colc2.divider()
                if source_concept != ktc:
                    ktc_pop.append(ktc)
                slap["word connections"][source_concept] = connected_words
                slap["key_translation_concepts"].append(source_concept)

            for source_wc in slap["word connections"].keys():
                input_source_concept_wc = colc1.text_input("Concept (edit if needed)", value=source_wc,
                                                           key="connected_word" + source_wc)
                try:
                    input_connected_words_wc = colc2.multiselect(f"is expressed by",
                                                        words,
                                                        default=[item.lower() for item in slap["word connections"][source_wc]],
                                                        key="cw" + source_wc)
                except: # Default is sometimes not a word, TODO: manage it.
                    print("Discarding default of {} in {}.".format(input_source_concept_wc, source))
                    input_connected_words_wc = colc2.multiselect(f"is expressed by",
                                                                 words,
                                                                 key="cw_bis_" + source_wc)
                    print(slap)

                colc1.divider()
                colc2.divider()
                if input_source_concept_wc == source_wc:
                    slap["word connections"][source_wc] = input_connected_words_wc
                else:
                    wc_add.append({input_source_concept_wc: input_connected_words_wc})
                    ktc_pop.append(source_wc)

            print("ktc_pop: {}".format(ktc_pop))
            print("wc_add: {}".format(wc_add))

            for item in ktc_pop:
                if item in slap["word connections"]:
                    del slap["word connections"][item]
                if item in slap["key_translation_concepts"]:
                    slap["key_translation_concepts"].remove(item)
            ktc_pop = []
            for item in wc_add:
                for s in item.keys():
                    slap["word connections"][s] = item[s]

            slap["comments"] = comments
            slap["source"] = source
            slap["target"] = target
            slap["description"] = description
            slap["keywords"] = keywords

            if st.button("Submit all changes", width="stretch", key="submitting_changes_to_augmented_pair"):
                with open(selected_ap["filename"], "w", encoding='utf-8') as f:
                    utils.save_json_normalized(slap, f)
                st.success("Submitted additions and changes saved")
                time.sleep(0.5)
                st.rerun()
    else:
        st.divider()
        st.markdown("*Contact us to make word(s)-concepts connections*")

    if role == "admin" and st.session_state.admin_verbose:
        st.divider()
        with st.expander("ADMIN: Test sentence pairs retrieval"):
            with st.spinner("Refreshing keyword index"):
                ragu.create_hard_kw_index(st.session_state.indi_language)

            if "query_results" not in st.session_state:
                st.session_state.query_results = []
            query = st.text_input("Sentence retrieval test, enter a query")

            if "hard_kw_retrieval_results" not in st.session_state:
                st.session_state.hard_kw_retrieval_results = []

            if st.button("Submit", key="retrieval_test"):
                # with st.spinner("Retrieving sentences from vectors"):
                #     try:
                #         sources_index, sources_id_to_meta = ragu.load_sources_index_and_id_to_meta(
                #             st.session_state.indi_language)
                #         descriptions_index, descriptions_id_to_meta = ragu.load_descriptions_index_and_id_to_meta(
                #             st.session_state.indi_language)
                #         sources_results = ragu.retrieve_similar(query, index=sources_index,
                #                                                 id_to_meta=sources_id_to_meta, k=5)
                #         descriptions_results = ragu.retrieve_similar(query, index=descriptions_index,
                #                                                 id_to_meta=descriptions_id_to_meta, k=5)
                #         st.write("Vectorized sources results: ")
                #         st.write(sources_results)
                #         st.write("Vectorized descriptions results: ")
                #         st.write(descriptions_results)
                #     except:
                #         st.warning("No source or description vector-based results")

                with st.spinner("Retrieving sentences from keywords"):
                    st.session_state.hard_kw_retrieval_results = ragu.hard_retrieve_from_query(query, st.session_state.indi_language)

                st.write("Keywords results: ")
                st.write(st.session_state.hard_kw_retrieval_results)

                st.write("Direct LLM results: ")

                sentence_pool = []
                for sf in [fn
                           for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                                             "sentence_pairs", "augmented_pairs"))
                           if fn.endswith(".json")]:
                    with open(
                            os.path.join(BASE_LD_PATH, st.session_state.indi_language, "sentence_pairs", "augmented_pairs",
                                         sf), encoding="utf-8") as f:
                        tmpd = json.load(f)
                        sentence_pool.append(tmpd["source"])

                with st.spinner("LLM Selecting sentences"):
                    st.write("sentence pool created with {} sentences".format(len(sentence_pool)))
                    selection = sda.select_sentences_sync(query, sentence_pool)
                    st.write(selection.sentence_list)

if role == "admin" and st.session_state.admin_verbose:
    with st.sidebar:
        st.page_link("pages/File_explorer.py", label="danger zone")
