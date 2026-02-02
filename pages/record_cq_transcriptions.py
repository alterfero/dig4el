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
import json
import os
from os import listdir, mkdir
from os.path import isfile, join
import time
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import tempfile
from datetime import datetime
from libs import utils as u
from libs import graphs_utils
from libs import utils, stats, wals_utils as wu
from libs import output_generation_utils as ogu
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu

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
delimiters = json.load(open("./data/delimiters.json", encoding='utf-8'))
delimiters_bank = [
    " ",
    ".",
    "?",
    "!",
    ",",
    "·",
    "‧",
    "․",
    "-",
    "_",
    "‿",
    "、",
    "。",
    "።",
    ":",
    ";",
    "؟",
    "٬",
    "؛",
    "۔",
    "।",
    "॥",
    "𐩖",
    "𐑀",
    "་",
    "᭞",
    "᠂",
    "᠃",
    " ",
    "꓿",
    "፡",
    "'",
    "…",
    "–",
    "—"
]
key_counter = 0

questionnaires_folder = "./questionnaires"
# cq_list is the list of json files in the questionnaires folder
cq_list = [f for f in listdir(questionnaires_folder) if isfile(join(questionnaires_folder, f)) and f.endswith(".json")]

concepts_kson = json.load(open("./data/concepts.json", encoding='utf-8'))
available_pivot_languages = list(wu.language_pk_id_by_name.keys())
questionnaires_folder = "./questionnaires"

if "indi_language" not in st.session_state:
    st.session_state["indi_language"] = "Abkhaz-Adyge"
if "indi_glottocode" not in st.session_state:
    st.session_state["indi_glottocode"] = "abkh1242"
if "llist" not in st.session_state:
    st.session_state.llist = gu.LLIST
if "concepts" not in st.session_state:
    with open("./data/concepts.json", "r", encoding='utf-8') as f:
        st.session_state["concepts"] = json.load(f)
if "predicates_list" not in st.session_state:
    st.session_state["predicates_list"] = graphs_utils.get_leaves_from_node(st.session_state["concepts"], "PREDICATE")
if "current_cq" not in st.session_state:
    st.session_state["current_cq"] = cq_list[0]
if "cq_is_chosen" not in st.session_state:
    st.session_state["cq_is_chosen"] = False
if "current_sentence_number" not in st.session_state:
    st.session_state["current_sentence_number"] = 1
if "delimiters" not in st.session_state:
    st.session_state["delimiters"] = delimiters["English"]
if "pivot_language" not in st.session_state:
    st.session_state.pivot_language = "English"
if "counter" not in st.session_state:
    st.session_state["counter"] = 1
if "recording" not in st.session_state:
    st.session_state["recording"] = {"target language": st.session_state.indi_language,
                                     "delimiters": st.session_state["delimiters"],
                                     "pivot language": "English", "cq_uid": "xxx", "data": {},
                                     "interviewer": "", "interviewee": ""}
if "loaded_existing_transcription" not in st.session_state:
    st.session_state["loaded_existing_transcription"] = False
if "existing_filename" not in st.session_state:
    st.session_state["existing_filename"] = ""
if "cq_id_dict" not in st.session_state:
    cq_id_dict = {}
    for cq in cq_list:
        cq_json = json.load(open(join(questionnaires_folder, cq), encoding='utf-8'))
        cq_id_dict[cq_json["uid"]] = {"filename": cq, "content": cq_json}
    st.session_state["cq_id_dict"] = cq_id_dict
if "is_guest" not in st.session_state:
    st.session_state.is_guest = None
if "caretaker_of" not in st.session_state:
    st.session_state.caretaker_of = []
if "caretaker_trigger" not in st.session_state:
    st.session_state.caretaker_trigger = False
if "tmp_save_path" not in st.session_state:
    if "none" not in os.listdir(os.path.join(BASE_LD_PATH)):
        mkdir(os.path.join(BASE_LD_PATH, "none"))
    st.session_state.tmp_save_path = os.path.join(BASE_LD_PATH, "none")

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


# ------ HELPER FUNCTIONS -------------------------------------------------------------------------

def save_config_atomic(data: dict, path: Path):
    d = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=d, encoding="utf-8") as tmp:
        yaml.safe_dump(data, tmp, sort_keys=False, allow_unicode=True)
        st.session_state.tmp_save_path = tmp.name
    os.replace(st.session_state.tmp_save_path, path)  # atomic on POSIX

def save_tmp():
    with open(os.path.join(st.session_state.tmp_save_path, "tmp_cq.json"), "w") as sf:
        utils.save_json_normalized(st.session_state["recording"], sf)

cfg = load_config(CFG_PATH)
authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"],
    auto_hash=True
)

def language_selection(role):
    # default index
    if st.session_state.indi_language in st.session_state.llist:
        default_language_index = st.session_state.llist.index(st.session_state.indi_language)
    else:
        default_language_index = 0
    coli1, coli2 = st.columns(2)
    selected_language_from_list = coli1.selectbox("Select the language of the translation in the list below",
                                                  st.session_state.llist if role != "guest" else ["Tahitian"],
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
            with open(os.path.join(".", BASE_LD_PATH,"languages.json"), "r") as fg:
                language_list_json = json.load(fg)
            language_list_json[free_language_input.capitalize()] = free_language_input.lower() + "+"
            with open(os.path.join(BASE_LD_PATH, "languages.json"), "w") as fgg:
                json.dump(language_list_json, fgg, indent=4)
    else:
        selected_language = selected_language_from_list

    if selected_language != st.session_state.indi_language:
        st.session_state.indi_language = selected_language
        st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi_language,
                                                                       "no glottocode")
        fmu.create_ld(BASE_LD_PATH, st.session_state.indi_language)
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "info.json"), "r", encoding='utf-8') as f:
            st.session_state.info_doc = json.load(f)
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "delimiters.json"), "r",
                  encoding='utf-8') as f:
            st.session_state.delimiters = json.load(f)
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "batch_id_store.json"), "r",
                  encoding='utf-8') as f:
            content = json.load(f)
        if st.session_state.indi_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
            role = "caretaker"
            if not st.session_state.caretaker_trigger:
                st.session_state.caretaker_trigger = True
                print("CARETAKER RERUN")
            st.rerun()
# -------------------------------------------------------------------------------------------
st.title("Create Conversational Questionnaires translations")

with st.sidebar:
    st.image("./pics/dig4el_logo_sidebar.png")

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
        location="main",  # "main" | "sidebar" | "unrendered"
        max_concurrent_users=20,  # soft cap; useful for small apps
        max_login_attempts=5,  # lockout window is managed internally
        fields={  # optional label overrides
            "Form name": "Sign in",
            "Username": "email",
            "Password": "Password",
            "Login": "Sign in",
        },
        captcha=False,  # simple built-in captcha
        single_session=True,  # block multiple sessions per user
        clear_on_submit=True,
        key="login_form_v1",  # avoid WidgetID collisions
    )

auth_status = st.session_state.get("authentication_status", None)
name = st.session_state.get("name", None)
username = st.session_state.get("username", None)

if auth_status:
    role = cfg["credentials"]["usernames"].get(username, {}).get("role", "guest")
    if st.session_state.indi_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
        role = "caretaker"
    title = ""
    if role in ["admin", "caretaker"]:
        title = role
    st.sidebar.success(f"Hello, {title} {name or username}")
    usercode = u.usercode(username)
    if "ztmp" not in os.listdir(os.path.join(BASE_LD_PATH)):
        mkdir(os.path.join(BASE_LD_PATH, "ztmp"))
    if usercode not in os.listdir(os.path.join(BASE_LD_PATH, "ztmp")):
        mkdir(os.path.join(BASE_LD_PATH, "ztmp", usercode))
    st.session_state.tmp_save_path = os.path.join(BASE_LD_PATH, "ztmp", usercode)

    if st.session_state.is_guest:
        usercode = "guest"
        if "ztmp" not in os.listdir(os.path.join(BASE_LD_PATH)):
            mkdir(os.path.join(BASE_LD_PATH, "ztmp"))
        if usercode not in os.listdir(os.path.join(BASE_LD_PATH, "ztmp")):
            mkdir(os.path.join(BASE_LD_PATH, "ztmp", usercode))
        st.session_state.tmp_save_path = os.path.join(BASE_LD_PATH, "ztmp", usercode)
        if st.sidebar.button("Logout", key="guest_logout"):
            for x in ("is_guest", "authentication_status", "username", "name"):
                st.session_state.pop(x, None)
            st.rerun()
    else:
        authenticator.logout(button_name="Logout", location="sidebar", key="auth_logout")

elif auth_status is False:
    usercode = "none"
    if "ztmp" not in os.listdir(os.path.join(BASE_LD_PATH)):
        mkdir(os.path.join(BASE_LD_PATH, "ztmp"))
    if usercode not in os.listdir(os.path.join(BASE_LD_PATH, "ztmp")):
        mkdir(os.path.join(BASE_LD_PATH, "ztmp", usercode))
    st.session_state.tmp_save_path = os.path.join(BASE_LD_PATH, "ztmp", usercode)
    role = None
    st.error("Invalid credentials")
    st.write("Try again. If you have forgotten your password, contact sebastien.christian@upf.pf")
    st.stop()

else:
    role = None
    st.info("Please log in or click on the 'Use without logging in' button")

# ==================== VISUAL STEPPER ==========================

st.markdown(
    """
<style>
/* container */
.dig4el-stepper {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin: 0.25rem 0 0.75rem 0;
}

/* step card */
.dig4el-step {
  position: relative;
  padding: 16px 16px 14px 16px;
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 18px;
  background: #A3998E;
  min-height: 140px;
  overflow: hidden;
}

/* subtle top highlight */
.dig4el-step:before{
  content:"";
  position:absolute;
  inset:-2px -2px auto -2px;
  height: 42px;
  background: radial-gradient(closest-side, rgba(255,255,255,0.16), rgba(255,255,255,0));
  pointer-events:none;
}

/* number badge */
.dig4el-badge{
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.14);
  margin-right: 10px;
}

/* header line */
.dig4el-head{
  display:flex;
  align-items:center;
  margin-bottom: 10px;
}

/* icon bubble */
.dig4el-icon{
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
}

/* title + text */
.dig4el-title{
  margin: 10px 0 6px 0;
  font-weight: 700;
  font-size: 16px;
  line-height: 1.15;
}
.dig4el-text{
  margin: 0;
  opacity: 0.86;
  font-size: 13px;
  line-height: 1.35;
}

/* arrow between steps (desktop only) */
.dig4el-step:not(:last-child)::after{
  content: "➜";
  position: absolute;
  top: 16px;
  right: -16px;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display:flex;
  align-items:center;
  justify-content:center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  color: rgba(255,255,255,0.75);
  font-size: 14px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.18);
}

/* responsive */
@media (max-width: 1100px){
  .dig4el-stepper{ grid-template-columns: repeat(2, 1fr); }
  .dig4el-step:not(:last-child)::after{ display:none; }
}
@media (max-width: 650px){
  .dig4el-stepper{ grid-template-columns: 1fr; }
  .dig4el-step{ min-height: auto; }
}

/* optional: progress bar look */
.dig4el-progress{
  height: 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  overflow:hidden;
  margin: 0.2rem 0 0.8rem 0;
}
.dig4el-progress > div{
  height: 100%;
  width: 100%;
  background: linear-gradient(90deg, rgba(255,255,255,0.18), rgba(255,255,255,0.06));
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="dig4el-progress"><div></div></div>

<div class="dig4el-stepper">
  <div class="dig4el-step">
    <div class="dig4el-head">
      <span class="dig4el-badge">1</span>
      <span class="dig4el-icon">🌍</span>
    </div>
    <div class="dig4el-title">Select a language</div>
    <p class="dig4el-text">Pick the target language you’re working on.</p>
  </div>

  <div class="dig4el-step">
    <div class="dig4el-head">
      <span class="dig4el-badge">2</span>
      <span class="dig4el-icon">📂</span>
    </div>
    <div class="dig4el-title">Start or load a CQ</div>
    <p class="dig4el-text">Recover your last session, upload a CQ from your computer, or start a new one from scratch.</p>
  </div>

  <div class="dig4el-step">
    <div class="dig4el-head">
      <span class="dig4el-badge">3</span>
      <span class="dig4el-icon">✍️</span>
    </div>
    <div class="dig4el-title">Translate & connect</div>
    <p class="dig4el-text">Enter/edit translations and add the linguistic connections needed for DIG4EL to learn from the data.</p>
  </div>

  <div class="dig4el-step">
    <div class="dig4el-head">
      <span class="dig4el-badge">4</span>
      <span class="dig4el-icon">🚀</span>
    </div>
    <div class="dig4el-title">Publish and download</div>
    <p class="dig4el-text">File the CQ to share it with others and DIG4EL, or download it as a portable, shareable package.</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
# -----------------------------------------------------------------------------



# ===============================================================

with st.sidebar:
    st.divider()
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/dashboard.py", label="Back to Dashboard", icon=":material/home:")
    with open("./templates/cq_spreadsheets/cq_templates.zip", "rb") as f:
        zip_bytes = f.read()
    st.download_button(
        label="📥 Download Excel transcription sheets for all CQs",
        data=zip_bytes,
        file_name='cq_templates.zip',
        mime="application/zip")

# Language selection
st.markdown("#### 1. Select language")
language_selection(role=role)

#========================== LOADING CQ ========================================================================
st.markdown("#### 2. Start or resume a CQ")
if not st.session_state["loaded_existing_transcription"]:
    # RECOVER
    if role != "guest":
        if st.button("Recover your last auto-save"):
            if "tmp_cq.json" in os.listdir(st.session_state.tmp_save_path):
                try:
                    with open(os.path.join(st.session_state.tmp_save_path, "tmp_cq.json"), "r") as rf:
                        st.session_state["recording"] = json.load(rf)
                    st.session_state.indi_language = st.session_state["recording"]["target language"]
                    st.session_state.pivot_language = st.session_state["recording"]["pivot language"] \
                        if st.session_state["recording"]["pivot language"] != "" \
                        else "English"
                    st.success("Your last autosave has been recovered, in language: {}. You can directly scroll down and continue working on it!".format(st.session_state.indi_language))
                    # update concept labels
                    st.session_state["recording"], found_old_labels = utils.update_concept_names_in_transcription(
                        st.session_state["recording"])
                    if role == "admin" and found_old_labels:
                        st.success("admin: Some concept labels have been updated to the latest version.")
                    st.session_state["loaded_existing_transcription"] = True

                except:
                    st.write("No saved work available.")
                    if role == "admin":
                        st.warning("admin: There is a tmp_cq.json file but opening it raised an error")
            else:
                st.write("No saved work available.")
    # UPLOAD
    with st.expander("Upload a CQ translation in {} from your computer"
                     .format(st.session_state.indi_language)):
        st.markdown("You can upload a **DIG4EL JSON** file (that you would have saved on your computer from this interface) or a **DIG4EL Excel** file (that you would have downloaded empty from this interface and completed).")
        existing_recording = st.file_uploader("Load an existing DIG4EL CQ translation in {}"
                                              .format(st.session_state.indi_language))

        if existing_recording is not None:
            recname = str(existing_recording.name)
            if recname[-5:] == ".json":
                st.session_state["recording"] = json.load(existing_recording)
                print("Existing CQ translation loaded: ", existing_recording.name)
                st.session_state["existing_filename"] = existing_recording.name
                # update concept labels
                st.session_state["recording"], found_old_labels = utils.update_concept_names_in_transcription(
                    st.session_state["recording"])
                if role=="admin" and found_old_labels:
                    st.success("admin: Some concept labels have been updated to the latest version.")
                st.session_state["loaded_existing_transcription"] = True
            elif recname[-5:] == ".xlsx":
                try:
                    # uploaded is an UploadedFile; pass its bytes or file-like object
                    cq_translation = ogu.cq_translation_from_transcription_xlsx(existing_recording.getvalue())
                    st.session_state["recording"] = cq_translation
                    st.session_state["loaded_existing_transcription"] = True
                except Exception as e:
                    st.error(f"Failed to parse the workbook: {e}")
                    st.stop()
            else:
                st.warning(f"File format not compatible: {existing_recording.name}")

# FILL DEFAULTS ACCORDING TO RECOVERED OR UPLOADED
if st.session_state["loaded_existing_transcription"]:
    default_interviewer = st.session_state["recording"]["interviewer"]
    default_interviewee = st.session_state["recording"]["interviewee"]
    default_target_language = st.session_state["recording"]["target language"]
    st.session_state.indi_language = st.session_state["recording"]["target language"]
    st.session_state.pivot_language = st.session_state["recording"]["pivot language"] \
        if st.session_state["recording"]["pivot language"] \
        else "English"
    try:
        default_delimiters = st.session_state["recording"]["delimiters"]
    except KeyError:
        st.session_state["recording"]["delimiters"] = delimiters["English"]
        default_delimiters = delimiters["English"]
    default_pivot_language = st.session_state["recording"]["pivot language"]
    if default_pivot_language == "english":
        default_pivot_language = "English"
        st.session_state["recording"]["pivot language"] = "English"

    default_cq_uid = st.session_state["recording"]["cq_uid"]
    default_data = st.session_state["recording"]["data"]

else:  ## if not loaded_existing_transcription
    default_target_language = "English"
    default_delimiters = delimiters["English"]
    if st.session_state["recording"]["interviewer"] == "":
        default_interviewer = ""
    else:
        default_interviewer = st.session_state["recording"]["interviewer"]
    if st.session_state["recording"]["interviewee"] == "":
        default_interviewee = ""
    else:
        default_interviewee = st.session_state["recording"]["interviewee"]
    if st.session_state["recording"]["pivot language"] == "English":
        default_pivot_language = "English"
    else:
        default_pivot_language = st.session_state["recording"]["pivot language"]
    if st.session_state["recording"]["cq_uid"] == "xxx":
        default_cq_uid = ""
    else:
        default_cq_uid = st.session_state["recording"]["cq_uid"]
    if st.session_state["recording"]["data"] == {}:
        default_data = {}
    else:
        default_data = st.session_state["recording"]["data"]

# START A NEW TRANSLATION
if not st.session_state["cq_is_chosen"] and not st.session_state["loaded_existing_transcription"]:
    st.markdown("**...or directly start a new CQ translation in {} below.**".format(st.session_state.indi_language))
if role == "guest":
    st.markdown(
        """You are using the system as a guest, 
        CQ translations will not be saved on the server: 
        ***Don't forget to save your translation on your computer using the 
        'Save' button at the bottom of the page!***""")
st.divider()
interviewer = st.text_input("Interviewer", value=default_interviewer, key="interviewer" + str(key_counter))
key_counter += 1
st.session_state["recording"]["interviewer"] = interviewer

interviewee = st.text_input("Interviewee", value=default_interviewee, key="interviewee" + str(key_counter))
key_counter += 1
st.session_state["recording"]["interviewee"] = interviewee

st.session_state["recording"]["target language"] = st.session_state.indi_language

st.session_state["recording"]["delimiters"] = st.multiselect("verify and edit word separators if needed",
                                                             delimiters_bank, default=default_delimiters)
st.session_state["delimiters"] = st.session_state["recording"]["delimiters"]

pl = st.text_input("What language did you use with the speaker if not English?")
if pl != "" and st.session_state.pivot_language != pl:
    st.session_state.pivot_language = pl
    st.session_state["recording"]["pivot language"] = pl

if not st.session_state["loaded_existing_transcription"]:  # if starting fresh, choose a cq
    select_cq = st.selectbox("Choose a CQ", cq_list, index=cq_list.index(st.session_state["current_cq"]))
    if st.button("select CQ"):
        st.session_state["current_cq"] = select_cq
        st.session_state["cq_is_chosen"] = True
else:  # if loaded_existing_transcription
    st.session_state["current_cq"] = st.session_state["cq_id_dict"][default_cq_uid]["filename"]
    st.session_state["cq_is_chosen"] = True

if st.session_state["cq_is_chosen"]:
    st.markdown("#### 3. Translate & Connect")
    # load the json file
    cq = json.load(open(join(questionnaires_folder, st.session_state["current_cq"]), encoding='utf-8'))
    number_of_sentences = len(cq["dialog"])
    st.session_state["recording"]["cq_uid"] = cq["uid"]

    st.session_state["recording"]["recording_uid"] = str(int(time.time()))

    xlsx_file = ogu.generate_transcription_xlsx(cq, st.session_state.indi_language,
                                               st.session_state.pivot_language)
    with st.sidebar:
        st.download_button(
            label="📥 Download an Excel transcription sheet for this CQ",
            data=xlsx_file,
            file_name=f'{cq["title"]}_transcription_sheet.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    colt1, colt2 = st.columns([3, 1])
    colt1.subheader('"{}" in {}'.format(cq["title"], st.session_state.indi_language))
    colt1.write("Context: {}".format(cq["context"]))
    with colt1.popover("See the full dialog"):
        for i in range(1, len(cq["dialog"]) + 1):
            st.write(cq["dialog"][str(i)]["speaker"] + " : " + cq["dialog"][str(i)]["text"])
    st.divider()

    counter_string = "Segment {}".format(str(st.session_state.counter))
    if "legacy index" in cq["dialog"][str(st.session_state["counter"])]:
        if cq["dialog"][str(st.session_state["counter"])]["legacy index"] != "":
            counter_string += ", legacy index {}".format(cq["dialog"][str(st.session_state["counter"])]["legacy index"])
    #st.write(st.write(f'Current position: {counter_string}.'))
    colq, colw, cole = st.columns([1, 3, 1])
    if colq.button("Previous"):
        save_tmp()
        if st.session_state["counter"] > 1:
            st.session_state["counter"] = st.session_state["counter"] - 1
            st.rerun()
    if colw.button("Current position {}".format(counter_string)):
        pass
    if cole.button("Next"):
        save_tmp()
        if st.session_state["counter"] < number_of_sentences:
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()
    jump_to = colw.slider(f"Jump to segment", 1, number_of_sentences, value=st.session_state["counter"])
    if jump_to != st.session_state["counter"]:
        save_tmp()
        st.session_state["counter"] = jump_to
        st.rerun()

    colz, colx = st.columns(2, gap="large")
    colz.subheader(cq["dialog"][str(st.session_state["counter"])]["speaker"] + ' says: "' +
                   cq["dialog"][str(st.session_state["counter"])]["text"] + '"')
    # create the dialog context view on the right column
    colx.markdown("#### Local dialog context")
    start_index = max(1, st.session_state["counter"] - 2)
    stop_index = min(len(cq["dialog"]) + 1, start_index + 10)
    for i in range(start_index, stop_index):
        if i == st.session_state["counter"]:
            colx.markdown(f'**{cq["dialog"][str(i)]["speaker"] + ": " + cq["dialog"][str(i)]["text"]}**')
        else:
            colx.markdown(f'{cq["dialog"][str(i)]["speaker"] + ": " + cq["dialog"][str(i)]["text"]}')

    # a recording exists at this index
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        translation_default = st.session_state["recording"]["data"][str(st.session_state["counter"])]["translation"]
        # alernate pivot
        if "alternate_pivot" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            alternate_pivot_default = st.session_state["recording"]["data"][str(st.session_state["counter"])][
                "alternate_pivot"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["alternate_pivot"] = ""
            alternate_pivot_default = ""
        # LEBT
        if "lebt" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            default_lebt = st.session_state["recording"]["data"][str(st.session_state["counter"])]["lebt"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["lebt"] = ""
            default_lebt = ""
        # comment
        if "comment" in st.session_state["recording"]["data"][str(st.session_state["counter"])].keys():
            default_comment = st.session_state["recording"]["data"][str(st.session_state["counter"])]["comment"]
        else:
            st.session_state["recording"]["data"][str(st.session_state["counter"])]["comment"] = ""
            default_comment = ""
    # no recording at this index
    else:
        translation_default = ""
        alternate_pivot_default = ""
        default_comment = ""
        default_lebt = ""

    # if pivot language is not english, store the pivot form
    if st.session_state.pivot_language != "English":
        alternate_pivot = colz.text_input(
            "Enter here the expression you used in {}".format(st.session_state.pivot_language,
                                                              value=alternate_pivot_default),
            value=alternate_pivot_default)
    else:
        alternate_pivot = ""

    translation_raw = colz.text_input("Equivalent in {}".format(st.session_state.indi_language),
                                      value=translation_default,
                                      key=str(st.session_state["counter"]) + str(key_counter))
    key_counter += 1
    translation = utils.normalize_sentence(translation_raw)
    segmented_target_sentence = stats.custom_split(translation, st.session_state["recording"]["delimiters"])

    # Early sentence validation
    if colz.button("Validate translation", key="early_validation" + str(key_counter)):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "legacy index": cq["dialog"][str(st.session_state["counter"])]["legacy index"],
            "cq": cq["dialog"][str(st.session_state["counter"])]["text"],
            "alternate_pivot": alternate_pivot,
            "translation": translation,
            "concept_words": {},
            "comment": ""
        }
        save_tmp()

    # for each base concept, display a multiselect tool to select the word(s) that express (part of) this concept in the target language
    # the word(s) are stored as strings in the json, separated by "...", but must be a list for the multiselect tool to work.
    concept_words = {}
    colz.write(
        "In this sentence, would you know which word(s) would contribute to the expression the following concepts?")
    concept_list = cq["dialog"][str(st.session_state["counter"])]["intent"]

    # Concepts
    is_negative_polarity = False
    for concept, properties in cq["dialog"][str(st.session_state["counter"])]["graph"].items():
        if concept[-8:] == "POLARITY":
            if properties["value"] == "NEGATIVE":
                concept_list.append("Negative Polarity")
    concept_list += cq["dialog"][str(st.session_state["counter"])]["concept"]
    for concept in concept_list:
        concept_default = []
        if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
            print("YYY concept {} keys {}".format(concept, st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"].keys()))
            if concept in st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"].keys():
                print("XXX {}:{}".format(concept, st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"]))
                target_word_list = utils.listify(
                    st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"][concept])
                if all(element in segmented_target_sentence for element in target_word_list):
                    concept_default = target_word_list
        else:
            concept_default = []
        # Multiselect input. The displayed concept string is the description of the concept from concept.json
        concept_translation_list = colz.multiselect("{} : ".format(concepts_kson[concept]["description"]),
                                                    segmented_target_sentence, default=concept_default,
                                                    key=concept + str(st.session_state["counter"]) + str(key_counter))
        key_counter += 1
        concept_words[concept] = "...".join(concept_translation_list)

    # Predicate
    predicate_default = ""
    predicate_index_default = st.session_state["predicates_list"].index("PROCESSIVE PREDICATE")
    predicate_words_default = []
    if str(st.session_state["counter"]) in st.session_state["recording"]["data"].keys():
        # identify the predicate key in the concept_words dict
        for k in st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"]:
            if k in st.session_state["predicates_list"]:
                predicate_default = k
                predicate_index_default = st.session_state["predicates_list"].index(predicate_default)
                predicate_words_list = \
                    utils.listify(
                        st.session_state["recording"]["data"][str(st.session_state["counter"])]["concept_words"][k])
                if all(element in segmented_target_sentence for element in predicate_words_default):
                    predicate_words_default = predicate_words_list
                    if "" in predicate_words_list:
                        predicate_words_list.remove("")

    # type_of_predicate = colz.selectbox(
    #     "If it makes sense, select the type of predicate used in the sentence in {}".format(
    #         st.session_state.indi_language),
    #     st.session_state["predicates_list"],
    #     index=predicate_index_default)
    #
    # predicate_words = colz.multiselect("Which word(s) indicate(s) the type of predicate?",
    #                                    segmented_target_sentence, default=predicate_words_default,
    #                                    key="predicate_" + str(st.session_state["counter"]) + str(key_counter))
    # concept_words[type_of_predicate] = "...".join(predicate_words)
    # if type_of_predicate != predicate_default and predicate_default in concept_words.keys():
    #     del concept_words[predicate_default]

    # Literal English Back-Translation
    with colz:
        lebt = st.text_input("What would be the literal English translation of this {} sentence? (Relevant if you judge that the sentence in {} differs significantly from the English original)".format(st.session_state.indi_language, st.session_state.indi_language),
                             value=default_lebt, key="lebt" + str(st.session_state["counter"]))
    # Comments
    comment = colz.text_input("Comments/Notes", value=default_comment, key="comment" + str(st.session_state["counter"]))

    # Validate Sentence
    if colz.button("Validate expression and connections"):
        st.session_state["recording"]["data"][str(st.session_state["counter"])] = {
            "legacy index": cq["dialog"][str(st.session_state["counter"])]["legacy index"],
            "cq": cq["dialog"][str(st.session_state["counter"])]["text"],
            "alternate_pivot": alternate_pivot,
            "translation": translation,
            "concept_words": concept_words,
            "lebt": lebt,
            "comment": comment
        }
        save_tmp()
        if st.session_state["counter"] < number_of_sentences - 1:
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()
        else:
            st.subheader("End of the CQ, congratulations!")
            st.balloons()

    st.divider()
    # st.write(st.session_state["recording"])
    filename = ("recording_"
                + st.session_state["current_cq"].replace(".json", "") + "_"
                + st.session_state.indi_language + "_"
                + st.session_state["recording"]["interviewer"] + "_"
                + st.session_state["recording"]["interviewee"] + "_"
                + str(int(time.time())) + ".json")

    st.markdown("#### 4. Publish and/or Download")
    st.markdown("Published CQs will become visible to other ConveQs and DIG4EL users, and be used by DIG4EL to generate grammatical descriptions.")
    st.markdown("Re-publishing the same CQ translation replaces the previous version on the server.")
    st.markdown("Downloaded CQs are not saved on the server, but can be re-uploaded to continue working on them.")
    colf, colg, colh = st.columns(3)
    colf.download_button(label="**Download your CQ translation**",
                         data=utils.dumps_json_normalized(st.session_state["recording"], indent=4), file_name=filename)
    if role in ["admin", "caretaker"]:
        if colg.button("**Publish this CQ translation**"):
            now = datetime.now()
            readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")
            st.session_state["recording"]["published by username"] = username
            st.session_state["recording"]["published by name"] = name
            st.session_state["recording"]["published date"] = readable_date_time

            existing_published_cqs = os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq", "cq_translations"))
            same_cqs = [fn
                       for fn in existing_published_cqs
                       if fn[:-15] in filename
                       ]
            if same_cqs != []:
                for same_cq in same_cqs:
                    os.remove(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq", "cq_translations", same_cq))
                    if role == "admin":
                        st.warning("admin: CQ duplicate. erasing {}".format(same_cq))

            with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq", "cq_translations", filename), "w") as fp:
                u.save_json_normalized(data=st.session_state["recording"], fp=fp)
            st.success("Your CQ has been added to the CQs of language {}".format(st.session_state.indi_language))
        if colh.button("Compute inferences"):
            pass
    else:
        colg.markdown("Only caretakers can publish CQs.")
        colg.markdown("Send us a mail at sebastien.christian@upf.pf to be added as a caretaker of {}"
                      .format(st.session_state.indi_language))

