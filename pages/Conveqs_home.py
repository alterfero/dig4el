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
import os
import json
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import tempfile
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import utils as u
from libs import display_utils as du
from libs import knowledge_graph_utils as kgu
from libs import stats
from libs import output_generation_utils as ogu
from datetime import datetime
import pandas as pd
import plotly.express as px
from pyvis.network import Network

# TODO: Save alert / Autosave
# TODO: Explain the difference between the original file and the local file.

st.set_page_config(
    page_title="ConveQs",
    page_icon="C",
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

if "indi_path_check" not in st.session_state:
    st.session_state.indi_path_check = False
if "upload_language" not in st.session_state:
    st.session_state.upload_language = "Abkhaz-Adyge"
if "indi_glottocode" not in st.session_state:
    st.session_state["indi_glottocode"] = "abkh1242"
if "is_guest" not in st.session_state:
    st.session_state.is_guest = None
if "caretaker_of" not in st.session_state:
    st.session_state.caretaker_of = []
if "caretaker_trigger" not in st.session_state:
    st.session_state.caretaker_trigger = False
if "use" not in st.session_state:
    st.session_state.use = "consult"
if "new_cq_counter" not in st.session_state:
    st.session_state.new_cq_counter = 0
if "knowledge_graph" not in st.session_state:
    st.session_state.knowledge_graph = {}
if "cq_transcriptions" not in st.session_state:
    st.session_state.cq_transcriptions = []
if "active_language" not in st.session_state:
    st.session_state.active_language = None
if "delimiters" not in st.session_state:
    st.session_state.delimiters = None
if "selected_concept" not in st.session_state:
    st.session_state["selected_concept"] = ""
if "pdict" not in st.session_state:
    st.session_state["pdict"] = {}
if "pfilter" not in st.session_state:
    st.session_state["pfilter"] = {"intent": [], "enunciation": [], "predicate": {}, "ip": {}, "rp": []}
if "cdict" not in st.session_state:
    st.session_state["cdict"] = {}
if "uid_dict" not in st.session_state:
    with open("./uid_dict.json", "r") as uid:
        st.session_state.uid_dict = json.load(uid)

CONVEQS_BASE_PATH = os.path.join(BASE_LD_PATH, "conveqs")


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
st.image("./pics/conveqs_banner.png")
with st.sidebar:
    st.divider()
    st.page_link("pages/Conveqs_home.py", label="ConveQs Home", icon=":material/home:")
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
    if st.session_state.upload_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
        role = "caretaker"
    title = ""
    if role in ["admin", "caretaker"]:
        title = role
    st.sidebar.success(f"Hello, {title} {name or username}")
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
    st.info("Please log in or click on the 'Use without loging in' button")


# =========================== LOGIC AND UI =============================================



st.markdown("*Navigate features by selecting one of the tabs below*")
tab1, tab2, tab3 = st.tabs(["Browse files", "Upload CQ files", "Explore CQs", ])

# ========== CONSULT FILES ==========================
with tab1:
    st.markdown("""
        You can see below a list of all files containing CQs uploaded to ConveQs.
        - Click on any file in the table to display what you can do with it.
        - You can Edit and delete your own files, and download files from other users if they allow it.
        """)

    with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
        conveqs_index = json.load(f)
    conveqs_index_df = pd.DataFrame(conveqs_index)
    selected = st.dataframe(conveqs_index_df.style.hide(axis="index"), column_order=["language", "name", "author",
                                                                                     "format", "uploaded by",
                                                                                     "is_downloadable"],
                            hide_index=True, selection_mode="single-cell", on_select="rerun")
    if selected["selection"]["cells"] != []:
        selected_row = selected["selection"]["cells"][0][0]
        selected_item = conveqs_index[selected_row]
        st.markdown("{}, collected from **{}** by **{}**".format(
            selected_item.get("name", "*unknown*"),
            selected_item.get("informant", "*unknown*"),
            selected_item.get("field_worker", "*unknown*")
        ))
        st.markdown("On the {}, in {}".format(
            selected_item.get("collection_date", "*unknown*"),
            selected_item.get("collection_location", "*unknown*")
        ))
        st.markdown("Author(s): {}".format(selected_item.get("author", "*unknown*")))
        st.markdown("Uploaded by {} on {}".format(
            selected_item["uploaded by"],
            selected_item["date"]))

        if username == selected_item["uploaded by"]:
            st.markdown("This is **your file**, you can **download** or **delete** it")
        col1, col2 = st.columns(2)
        if selected_item["is_downloadable"] and role != "guest":
            with open(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]), "rb") as f:
                data = f.read()
            col1.download_button("You can download this file", data, file_name=selected_item["filename"])
        else:
            col1.markdown("*This file can only be downloaded by registered users, contact us to become one!*")
        if selected_item["uploaded by"] == username or role == "admin":
            if col2.button("Delete this file"):
                del conveqs_index[selected_row]
                with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w") as f:
                    json.dump(conveqs_index, f)
                try:
                    os.remove(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]))
                except FileNotFoundError:
                    print("{} does not exist".format(selected_item["filename"]))
                st.rerun()

# ========== UPLOAD FILES ============================
with tab2:
    if role == "guest":
        st.markdown("*Guests cannot upload or manage Conversational Questionnaires.*")
        st.markdown("*If you have Conversational Questionnaires to upload, contact us to become a registered user!*")

    else:
        # SELECT LANGUAGE
        colq, colw = st.columns(2)
        llist = gu.GLOTTO_LANGUAGE_LIST.keys()
        st.session_state.upload_language = colq.selectbox("What is the indigenous language in this file?", llist)
        st.markdown("*Note: If you don't find the language in this Glottolog list, write to us and indicate the name of the language and a unique identifier (ISO or other) so we can add it.")

        st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.upload_language,
                                                                       "glottocode not found")
        fmu.create_ld(BASE_LD_PATH, st.session_state.upload_language)

        if st.session_state.upload_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker",
                                                                                                     []):
            role = "caretaker"
            if not st.session_state.caretaker_trigger:
                st.session_state.caretaker_trigger = True
                print("CARETAKER RERUN")
                st.rerun()
        else:
            st.markdown("""
            Only registered *caretakers* of {} can upload CQs in this language.
            
            If you want to be a caretaker of {} on ConveQs, contact us.""".format(st.session_state.upload_language, st.session_state.upload_language))

        if role in ["admin", "caretaker"]:

            # Upload cq file

            with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json")) as ci:
                conveqs_index = json.load(ci)
            existing_filenames = [fn["filename"] for fn in conveqs_index]

            cq_list = list(st.session_state.uid_dict.values())
            cq_list.sort()
            cq_list.append("multiple")

            # FILE UPLOAD FORM
            with st.form(key="file_upload_form", clear_on_submit=True, enter_to_submit=False,
                         border=True, width="stretch", height="content"):
                sub_ready = False
                valid = False
                new_cq = st.file_uploader(
                    "Add a new CQ translation to the repository",
                    accept_multiple_files=False,
                    key="new_cq" + str(st.session_state.new_cq_counter)
                )
                name = st.selectbox("Which CQ does your document contain? Select 'multiple' if multiple",
                                       cq_list)
                author = st.text_input("Author(s) of the corpus")
                collection_date = st.date_input("Collection date")
                collection_location = st.text_input("Collection location")
                informant = st.text_input("Collected from (speaker(s) full name(s))")
                field_worker = st.text_input("Collected by (field worker's full name)")
                visibility = st.selectbox("Visibility", ["Everyone", "Members only"], index=0)
                data_format = st.selectbox("Format", ["Excel template", "FleX XML", "DIG4EL JSON", "other"])
                consent_received = st.checkbox("Written consent from the {} speaker has been received and stored".format(st.session_state.upload_language))
                is_downloadable = st.checkbox("Can be downloaded by registered users", value=True)

                submitted = st.form_submit_button("Submit")

                if submitted:
                    with open(os.path.join(CONVEQS_BASE_PATH, new_cq.name), "wb") as f:
                        f.write(new_cq.read())
                    st.success(f"Saved `{new_cq.name}` on the server.")

                    now = datetime.now()
                    readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")
                    conveqs_index.append(
                        {
                            "filename": new_cq.name,
                            "format": data_format,
                            "visibility": visibility,
                            "is_downloadable": is_downloadable,
                            "name": name,
                            "language": st.session_state.upload_language,
                            "author": author,
                            "collection_date": collection_date.strftime("%Y-%m-%d"),
                            "collection_location": collection_location,
                            "informant": informant,
                            "field_worker": field_worker,
                            "consent": consent_received,
                            "uploaded by": username,
                            "date": readable_date_time
                        }
                    )
                    if new_cq.name in existing_filenames:
                        existing_filename_index = existing_filenames.index(new_cq.name)
                        del conveqs_index[existing_filename_index]
                        print("Deleted item to replace at index {}".format(existing_filename_index))
                    with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w",
                              encoding='utf-8') as f:
                        u.save_json_normalized(conveqs_index, f)
                    st.success("{} successfully indexed.".format(new_cq.name))

                    # CQ VALIDATION
                    if data_format == "DIG4EL JSON":
                        is_valid_cq = True
                        try:
                            with open(os.path.join(CONVEQS_BASE_PATH, new_cq.name), "r") as fr:
                                test_cq = json.load(fr)
                            for key in ["target language", "delimiters", "cq_uid", "data"]:
                                if key not in test_cq.keys():
                                    is_valid_cq = False
                                    st.warning("{} is not a valid DIG4EL JSON file.".format(new_cq.name))
                        except:
                            st.warning("An exception occurred while opening {} for validation".format(new_cq.name))
                            st.warning("This does not seem to be a valid JSON file.")
                            is_valid_cq = False
                        if is_valid_cq:
                            if st.session_state.upload_language in os.listdir(os.path.join(BASE_LD_PATH)):
                                with open(os.path.join(BASE_LD_PATH,
                                                       st.session_state.upload_language,
                                                       "cq",
                                                       "cq_translations",
                                                       new_cq.name), "w") as fw:
                                    json.dump(test_cq, fw, ensure_ascii=False)
                                st.success("CQ also added to DIG4EL!")
                            else:
                                st.warning("Valid DIG4EL CQ but invalid data path to store the CQ")

        if role == "admin":
            with st.expander("Check index"):
                with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
                    st.write(json.load(f))

# ========== EXPLORE CQs =============================

with tab3:

    st.subheader("Explore available Conversational Questionnaires")
    st.markdown("""
    This page allows to display the content of all CQs that are compatible with our open format. 
    
    Interfaces to commonly-used software are being developed. 
    """)
    cq_catalog = u.catalog_all_available_cqs()
    n_language = len(set([lu["language"] for lu in cq_catalog]))
    st.markdown("{} CQs available, across {} languages.".format(len(cq_catalog), n_language))
    cq_catalog_df = pd.DataFrame(cq_catalog).sort_values(by="title")
    selected_rows = st.dataframe(cq_catalog_df, hide_index=True, column_order=["title", "language", "pivot", "index"],
                                 selection_mode="multi-row", on_select="rerun")
    selected_cqs_indexes_in_displayed_df = selected_rows["selection"]["rows"]
    selected_cqs_indexes_in_catalog = [cq_catalog_df.iloc[i]["index"] - 1 for i in selected_cqs_indexes_in_displayed_df]

    with st.expander("Display a single CQ"):
        if selected_cqs_indexes_in_catalog != []:
            # retrieving cq_catalog index in the df:
            catalog_entry = cq_catalog[selected_cqs_indexes_in_catalog[0]]
            with open(os.path.join(BASE_LD_PATH, catalog_entry["language"], "cq", "cq_translations", catalog_entry["filename"])) as fcqd:
                cqd = json.load(fcqd)
            du.display_cq(cqd, st.session_state.delimiters, catalog_entry["title"], gloss=False)
        else:
            st.write("Select a CQ in the table")


    with st.expander("Compare the same CQ in multiple languages"):
        # list available cq titles by creating the set of titles in the df
        cq_titles = list(set(cq_catalog_df["title"].tolist()))
        cq_titles.sort()
        selected_cq_title = st.selectbox("Choose a CQ", cq_titles)
        filtered_df = cq_catalog_df[cq_catalog_df["title"] == selected_cq_title]
        available_languages = filtered_df["language"].tolist()
        selected_languages = st.multiselect("Select languages to compare", available_languages)
        if selected_languages != []:
            cqs_content = []
            for lang in selected_languages:
                lang_entry = filtered_df[filtered_df["language"] == lang].iloc[0]
                with open(os.path.join(BASE_LD_PATH, lang_entry["language"], "cq", "cq_translations",
                                       lang_entry["filename"])) as fcl:
                    cqs_content.append(json.load(fcl))

            du.display_same_cq_multiple_languages(cqs_content, selected_cq_title, show_pseudo_glosses=False)