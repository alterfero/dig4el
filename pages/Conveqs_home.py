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
from datetime import datetime
import pandas as pd

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

colb1, colb3 = st.columns(2, vertical_alignment="center")

# ========== CONSULT ==========================
if colb1.button("Browse Conversational Questionnaires files", width="stretch"):
    st.session_state.use = "consult"
    st.rerun()

if st.session_state.use == "consult":
    st.markdown("Click on the left of any file to display what you can do with it.")
    with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
        conveqs_index = json.load(f)
    conveqs_index_df = pd.DataFrame(conveqs_index)
    selected = st.dataframe(conveqs_index_df.style.hide(axis="index"), column_order=["language", "name", "author", "format", "uploaded by", "is_downloadable"],
                 selection_mode="single-row", on_select="rerun")
    if selected["selection"]["rows"] != []:
        selected_item = conveqs_index[selected["selection"]["rows"][0]]
        if selected_item["is_downloadable"] and role != "guest":
            with open(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]), "rb") as f:
                data = f.read()
            st.download_button("Download the file", data, file_name=selected_item["filename"])
        else:
            st.markdown("*This file can be downloaded by registered users, contact us to become one!*")
        if selected_item["uploaded by"] == username or role == "admin":
            if st.button("Delete this file"):
                del conveqs_index[selected["selection"]["rows"][0]]
                with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w") as f:
                    json.dump(conveqs_index, f)
                try:
                    os.remove(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]))
                except FileNotFoundError:
                    print("{} does not exist".format(selected_item["filename"]))
                st.rerun()

        if selected_item["filename"][-4:] == "json":
            with open(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]), "r") as f:
                selected_doc = json.load(f)
            if "cq_uid" in selected_doc.keys():
                st.write("Conversational Questionnaire, DIG4EL format")
                st.write(selected_doc)


# ========== UPLOAD ============================
if colb3.button("Upload Conversational Questionnaires", width="stretch"):
    st.session_state.use = "edit"
    st.rerun()

if st.session_state.use == "edit" and role == "guest":
    st.markdown("*Guests cannot upload or manage Conversational Questionnaires.*")
    st.markdown("*If you have Conversational Questionnaires to upload, contact us to become a registered user!*")

elif st.session_state.use == "edit" and role != "guest":

    # SELECT LANGUAGE
    colq, colw = st.columns(2)
    llist = gu.GLOTTO_LANGUAGE_LIST.keys()
    selected_language = colq.selectbox("What language are you working on?", llist)
    st.write("Active language: {}".format(st.session_state.upload_language))

    if st.button("Select {}".format(selected_language)):
        print("")
        print("*******************")
        print(selected_language)
        print("*******************")
        print("")
        st.session_state.upload_language = selected_language
        st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.upload_language,
                                                                       "glottocode not found")
        fmu.create_ld(BASE_LD_PATH, st.session_state.upload_language)
        if st.session_state.upload_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
            role = "caretaker"
            if not st.session_state.caretaker_trigger:
                st.session_state.caretaker_trigger = True
                print("CARETAKER RERUN")
                st.rerun()
        st.rerun()
    if role in ["admin", "caretaker"]:


        # Upload cq file

        with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json")) as ci:
            conveqs_index = json.load(ci)
        existing_filenames = [fn["filename"] for fn in conveqs_index]
        # FILE UPLOAD FORM
        with st.form(key="file_upload_form", clear_on_submit=True, enter_to_submit=False,
                     border=True, width="stretch", height="content"):
            sub_ready = False
            replace_ok = True
            new_cq = st.file_uploader(
                "Add a new CQ translation to the repository",
                accept_multiple_files=False,
                key="new_cq" + str(st.session_state.new_cq_counter)
            )
            info_entered = False
            name = st.text_input("Name this document (The name that will be displayed)")
            author = st.text_input("Author/owner of the corpus")
            visibility = st.selectbox("Visibility", ["Everyone", "Members only"], index=0)
            is_downloadable = st.checkbox("Can be downloaded by registered users", value=True)

            submitted = st.form_submit_button("Submit", disabled=not replace_ok)

            if submitted:
                with open(os.path.join(CONVEQS_BASE_PATH, new_cq.name), "wb") as f:
                    f.write(new_cq.read())
                st.success(f"Saved `{new_cq.name}` on the server.")

                # UPDATE CONVEQS_INDEX
                if "json" in new_cq.name:
                    format = "JSON"
                elif "xls" in new_cq.name:
                    format = "Spreadhseet"
                elif "xml" in new_cq.name:
                    format = "XML"
                elif "doc" in new_cq.name:
                    format = "Word processor"
                elif "txt" in new_cq.name:
                    format = "Text",
                elif "csv" in new_cq.name:
                    format = "CSV"
                else:
                    format = "other"

                now = datetime.now()
                readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")
                conveqs_index.append(
                    {
                        "filename": new_cq.name,
                        "format": format,
                        "visibility": visibility,
                        "is_downloadable": is_downloadable,
                        "name": name,
                        "language": st.session_state.upload_language,
                        "author": author,
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
                st.rerun()
    if role == "admin":
        with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
            st.write(json.load(f))
