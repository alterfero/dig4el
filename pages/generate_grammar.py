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
import pickle

from datetime import datetime
import streamlit as st
import json
from libs import utils as u
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import grammar_generation_agents as gga
from libs import grammar_generation_utils as ggu
from libs import output_generation_utils as ogu
from libs import retrieval_augmented_generation_utils as ragu
from libs import semantic_description_agents as sda
from libs import semantic_description_utils as sdu
from libs import semantic_description_utils
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import tempfile

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
    "storage"
)

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

if "aa_path_check" not in st.session_state:
    st.session_state.aa_path_check = False
if "indi" not in st.session_state:
    st.session_state.indi = "Tahitian"
if "readers_language" not in st.session_state:
    st.session_state.readers_language = "English"
if "vs_name" not in st.session_state:
    st.session_state.vs_name = ""
if "is_cq" not in st.session_state:
    st.session_state.is_cq = False
if "use_cq" not in st.session_state:
    st.session_state.use_cq = True
if "cq_knowledge" not in st.session_state:
    st.session_state.cq_knowledge = None
if "cq_files" not in st.session_state:
    st.session_state.cq_files = None
if "is_doc" not in st.session_state:
    st.session_state.is_doc = False
if "use_doc" not in st.session_state:
    st.session_state.use_doc = True
if "is_pairs" not in st.session_state:
    st.session_state.is_pairs = False
if "use_pairs" not in st.session_state:
    st.session_state.use_pairs = True
if "pairs_files" not in st.session_state:
    st.session_state.pairs_files = None
if "info_dict" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
        st.session_state.info_dict = json.load(f)
if "query" not in st.session_state:
    st.session_state.query = None
if "run" not in st.session_state:
    st.session_state.run_sources = False
if "run_aggregation" not in st.session_state:
    st.session_state.run_aggregation = True
if "relevant_parameters" not in st.session_state:
    st.session_state.relevant_parameters = None
if "alterlingua_contribution" not in st.session_state:
    st.session_state.alterlingua_contribution = None
if "documents_contribution" not in st.session_state:
    st.session_state.documents_contribution = None
if "selected_pairs" not in st.session_state:
    st.session_state.selected_pairs = None
if "output_dict" not in st.session_state:
    st.session_state.output_dict = None
if "is_guest" not in st.session_state:
    st.session_state.is_guest = None
if "caretaker_trigger" not in st.session_state:
    st.session_state.caretaker_trigger = False
if "readers_type" not in st.session_state:
    st.session_state.readers_type = "Adult learners"
if "document_format" not in st.session_state:
    st.session_state.document_format = "Grammar lesson"
if "polished_output" not in st.session_state:
    st.session_state.polished_output = False


# ----- HELPERS -----------------------------------------------------------------------------------
def display_lesson_output(output_dict):
    o = output_dict
    st.markdown(f"**Grammar Lesson** generated {o.get('date', 'date unknown')}, DIG4EL version {o.get('version', 'version unknown')}")
    st.title(o["title"])
    st.write(o["introduction"])
    st.divider()
    for section in o["sections"]:
        st.subheader(section["focus"])
        if isinstance(section["description"], str):
            st.markdown(section["description"])
        elif isinstance(section["description"], dict):
            st.markdown(section["description"].get("description", "..."))
        if isinstance(section.get("example"), list):
            for example in section.get("example"):
                st.markdown(f"**{example['target_sentence']}**")
                st.markdown(f"*{example['source_sentence']}*")
                st.write(example["description"])
        if isinstance(section.get("example"), dict):
            example = section["example"]
            st.markdown(f"**{example['target_sentence']}**")
            st.markdown(f"*{example['source_sentence']}*")
            st.write(example["description"])
    st.subheader("Conclusion")
    st.write(o["conclusion"])
    st.divider()
    st.subheader("More examples")
    for i, s in enumerate(o["translation_drills"]):
        st.write("{}".format(i + 1))
        st.markdown(f"**{s['target']}**")
        st.markdown(f"*{s['source']}*")
    st.divider()
    st.subheader("Sources")
    sources = o.get("sources", {})
    if "documents" in sources.keys() and sources["documents"] is not None and sources["documents"] != []:
        st.markdown("### Documents")
        for d in sources["documents"]:
            st.markdown(f"- {d}")
    if "cqs" in sources.keys() and sources["cqs"] is not None and sources["cqs"] != []:
        st.markdown("### Conversational Questionnaires")
        for d in sources["cqs"]:
            st.markdown(f"- {d}")
    if "pairs" in sources.keys() and sources["pairs"] is not None and sources["pairs"] != []:
        st.markdown("### Sentence Pairs")
        for d in sources["pairs"]:
            st.markdown(f"- {d}")

def display_sketch_output(output_dict):
    o = output_dict
    st.markdown(f"**Grammar sketch** Generated {o.get('date', 'date unknown')}, DIG4EL version {o.get('version', 'version unknown')}")
    st.title(o["title"])
    st.write(o["introduction"])
    st.divider()
    for section in o["sections"]:
        st.subheader(section["focus"])
        if isinstance(section["description"], str):
            st.markdown(section["description"])
        elif isinstance(section["description"], dict):
            st.markdown(section["description"].get("description", "..."))
        for example in section.get("examples"):
            st.markdown(f"**{example['target_sentence']}**")
            st.markdown(f"*{example['source_sentence']}*")
            st.write(example["description"])
    st.divider()
    st.subheader("Sources")
    sources = o.get("sources", {})
    if "documents" in sources.keys() and sources["documents"] is not None and sources["documents"] != []:
        st.markdown("### Documents")
        for d in sources["documents"]:
            st.markdown(f"- {d}")
    if "cqs" in sources.keys() and sources["cqs"] is not None and sources["cqs"] != []:
        st.markdown("### Conversational Questionnaires")
        for d in sources["cqs"]:
            st.markdown(f"- {d}")
    if "pairs" in sources.keys() and sources["pairs"] is not None and sources["pairs"] != []:
        st.markdown("### Sentence Pairs")
        for d in sources["pairs"]:
            st.markdown(f"- {d}")

def reset():
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
            st.session_state.info_dict = json.load(f)
    st.session_state.query = None
    st.session_state.run_sources = False
    st.session_state.run_aggregation = True
    st.session_state.relevant_parameters = None
    st.session_state.alterlingua_contribution = None
    st.session_state.documents_contribution = None
    st.session_state.selected_pairs = None
    st.session_state.output_dict = None
    st.session_state.readers_type = "Adult learners"
    st.session_state.document_format = "Grammar lesson"
    st.session_state.polished_output = False

def feedback_form():
    # Feedback survey
    st.subheader("Give feedback on this output!")
    with st.form(key="feedback_form", clear_on_submit=False, enter_to_submit=False, border=True):
        errors_form = st.slider("Are there errors in the output? (0 = no error, 9 = everything is wrong)",
                             min_value=0, max_value=9, value=0, key="final_feedback_errors")

        completeness_form = st.slider(
            "Does the description cover the topic fully? (1 = very incomplete, 9 = fully complete)",
            min_value=1, max_value=9, value=0, key="final_feedback_completeness")

        clarity_form = st.slider("Is the output clear and understandable? (1 = very unclear, 9 = very clear)",
                              min_value=1, max_value=9, value=0, key="final_feedback_clarity")

        usefulness_form = st.slider("How useful is this output for teaching/learning? (1 = useless, 9 = very useful)",
                                 min_value=1, max_value=9, value=0, key="final_feedback_usefulness")

        confidence_form = st.slider(
            "How confident are you in using this output? (1 = not at all, 9 = completely confident)",
            min_value=1, max_value=9, value=0, key="final_feedback_confidence")

        comments_form = st.text_area("What should be improved or added? (optional)", key="final_feedback_comments")
        submitted = st.form_submit_button("Submit feedback", key="feedback_submit_button")

        if submitted:
            with open(os.path.join(BASE_LD_PATH, "feedback.json"), "r") as f:
                feedback = json.load(f)
            with open(os.path.join("./", "version.json"), "r") as g:
                v = json.load(g)
                version = v["version"]
            now = datetime.now()
            readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")

            feedback.append(
                {
                    "version": version,
                    "format": "grammar lesson",
                    "date": readable_date_time,
                    "user": name,
                    "language": st.session_state.indi,
                    "prompt": st.session_state.query,
                    "errors": errors_form,
                    "completeness": completeness_form,
                    "clarity": clarity_form,
                    "usefulness": usefulness_form,
                    "confidence": confidence_form,
                    "comments": comments_form
                }
            )
            with open(os.path.join(BASE_LD_PATH, "feedback.json"), "w") as h:
                json.dump(feedback, h)
            st.success("Thank you for your feedback!")


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

with st.sidebar:
    st.image("./pics/dig4el_logo_sidebar.png")
    st.divider()
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/dashboard.py", label="Source dashboard", icon=":material/search:")
    st.divider()

# AUTH UI AND FLOW -----------------------------------------------------------------------
if st.session_state["username"] is None:
    if st.button("Use without loging in"):
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
    if st.session_state.indi in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
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

# ------------------------------------------------------------------------------------------------
colq, colw = st.columns(2)

if role == "admin":
    with open("test_lesson.json", "r") as f:
        o = json.load(f)
    docx = ogu.generate_lesson_docx_from_aggregated_output(o,
                                                           "Indi",
                                                           "English")
    st.download_button(label="Download TEST DOCX output",
                       data=docx,
                       file_name="test_lesson_DOCX.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       key="final_docx")


if "l_with_data" not in st.session_state:
    st.session_state.l_with_data = None
# languages with existing data
st.session_state.l_with_data = [l for l in os.listdir(os.path.join(BASE_LD_PATH))
                 if (os.path.isdir(os.path.join(BASE_LD_PATH, l)) and l in list(gu.GLOTTO_LANGUAGE_LIST.keys()))]
if role == "guest":
    st.session_state.l_with_data = ["Tahitian", "Mwotlap"]
    colq.markdown(
        "**Note**: *As a guest, you can perform generation on a restricted collection of language. Contact us to access more languages!*")

selected_language = colq.selectbox("What language are we generating learning content for?",
                                   st.session_state.l_with_data, index=st.session_state.l_with_data.index(st.session_state.indi))
if colq.button("Select {}".format(selected_language)):
    st.session_state.indi = selected_language
    st.session_state.is_cq = False
    st.session_state.is_doc = False
    st.session_state.is_pairs = False

    st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi,
                                                                   "glottocode not found")
    fmu.create_ld(BASE_LD_PATH, st.session_state.indi)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
        st.session_state.info_dict = json.load(f)
    if st.session_state.indi in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
        role = "caretaker"
    if not st.session_state.caretaker_trigger:
        st.session_state.caretaker_trigger = True
        print("CARETAKER RERUN")
        st.rerun()
else:
    colq.markdown(f"Working on **{st.session_state.indi}**")
    st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi,
                                                                   "glottocode not found")
    colq.markdown("*glottocode* {}".format(st.session_state.indi_glottocode))

# PROPOSING EXISTING OUTPUTS FROM PREVIOUS QUERIES
with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
    info = json.load(f)
if info["outputs"] != {}:
    st.subheader("Access stored outputs from previous queries")
    st.markdown("""
    These outputs are **raw outputs** from DIG4EL, provided for research purposes.
    **They have not been corrected** by an expert of the language and may contain errors and inaccuracies. **They 
    should not be used as is for teaching or learning** the language described. 
    """)
    slq = st.selectbox("Select a query to access the files", [q for q in info["outputs"].keys()])
    coln, colm = st.columns(2)
    if info["outputs"][slq] in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs")):
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", info["outputs"][slq]), "rb") as jsonf:
            coln.download_button(label="Download JSON file",
                                 data=jsonf,
                                 file_name=info["outputs"][slq],
                                 mime="application/json")
    if info["outputs"][slq][:-5]+".docx" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs")):
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", info["outputs"][slq][:-5]+".docx"), "rb") as docxf:
            colm.download_button(label="Download DOCX file",
                                 data=docxf,
                                 file_name=info["outputs"][slq][:-5]+".docx",
                                 mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if info["outputs"][slq] in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs")):
        with st.expander("Click here to see the output"):
            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", info["outputs"][slq]),
                      "rb") as jsonf:
                outd = json.load(jsonf)
                if "conclusion" in outd.keys():
                    display_lesson_output(outd)
                else:
                    display_sketch_output(outd)

            if role in ["user", "admin"]:
                st.subheader("Give feedback on this output!")

                errors = st.slider("Are there errors in the output? (0 = no error, 9 = everything is wrong)",
                                     min_value=0, max_value=9, value=0)

                completeness = st.slider(
                    "Does the description cover the topic fully? (1 = very incomplete, 9 = fully complete)",
                    min_value=1, max_value=9, value=5)

                clarity = st.slider("Is the output clear and understandable? (1 = very unclear, 9 = very clear)",
                                      min_value=1, max_value=9, value=5)

                usefulness = st.slider("How useful is this output for teaching/learning? (1 = useless, 9 = very useful)",
                                         min_value=1, max_value=9, value=5)

                confidence = st.slider(
                    "How confident are you in using this output? (1 = not at all, 9 = completely confident)",
                    min_value=1, max_value=9, value=5)

                comments = st.text_area("What should be improved or added? (optional)")

                if st.button("Submit feedback"):
                    with open(os.path.join(BASE_LD_PATH, "feedback.json"), "r") as f:
                        feedback = json.load(f)
                    with open(os.path.join("./", "version.json"), "r") as g:
                        v = json.load(g)
                        version = v["version"]
                    now = datetime.now()
                    readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")

                    feedback.append(
                        {
                            "version": version,
                            "date": readable_date_time,
                            "user": name,
                            "language": st.session_state.indi,
                            "prompt": slq,
                            "errors": errors,
                            "completeness": completeness,
                            "clarity": clarity,
                            "usefulness": usefulness,
                            "confidence": confidence,
                            "comments": comments
                        }
                    )
                    with open(os.path.join(BASE_LD_PATH, "feedback.json"), "w") as h:
                        json.dump(feedback, h)
                    st.success("Thank you for your feedback!")


# GATHERING MATERIAL

# cq
if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_knowledge")):
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_knowledge", "cq_knowledge.json"), "r", encoding='utf-8') as f:
        st.session_state.cq_knowledge = json.load(f)
        st.session_state.cq_files = [fn
                                     for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_translations"))
                                     if fn[-5:] == ".json"]
    st.session_state.is_cq = True
else:
    st.session_state.cq_knowledge = False
    st.session_state.cq_files = []

# documents
st.session_state.vs_name = st.session_state.info_dict["documents"]["oa_vector_store_name"]

if st.session_state.info_dict["documents"]["oa_vector_store_id"] != "":
    st.session_state.is_doc = True

# pairs
if "description_vectors" not in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                          "sentence_pairs", "vectors")):
    os.mkdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                          "sentence_pairs", "vectors", "description_vectors"))

if "index.faiss" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                          "sentence_pairs", "vectors", "description_vectors")):
    st.session_state.pairs_files = [fn
                                    for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "pairs"))
                                    if fn[-5:] == ".json"]
if [fn
    for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "augmented_pairs"))
    if fn[-5:] == ".json"]:
    st.session_state.is_pairs = True
else:
    st.warning("No augmented sentence pairs found.")

st.sidebar.write("✅ CQ Ready" if st.session_state.is_cq else "No CQ")
if st.session_state.is_cq:
    st.session_state.use_cq = st.sidebar.toggle("Use CQ", value=st.session_state.use_cq)
st.sidebar.write("✅ Docs Ready" if st.session_state.is_doc else "No documents")
if st.session_state.is_doc:
    st.session_state.use_doc = st.sidebar.toggle("Use documents", value=st.session_state.use_doc)
st.sidebar.write("✅ Pairs Ready" if st.session_state.is_pairs else "No pairs")
if st.session_state.is_pairs:
    st.session_state.use_pairs = st.sidebar.toggle("Use Pairs", value=st.session_state.use_pairs)

# ======== SELECTION OF OUTPUT PARAMETERS ==================

if ((st.session_state.is_cq and st.session_state.use_cq) or (st.session_state.is_doc and st.session_state.use_doc)
    or (st.session_state.is_pairs and st.session_state.use_pairs)):

    st.subheader("Generate a new grammatical description")
    colq1a, colq2a = st.columns(2)
    st.session_state.document_format = colq1a.selectbox("Format", ["Grammar lesson", "Grammar sketch"])
    st.session_state.readers_language = colq2a.selectbox("What is the language of readers?",
                                                     ["English","Bislama", "Chinese", "French", "Japanese", "Russian",
                                                      "Spanish", "Swedish", "Tahitian"])
    if st.session_state.document_format == "Grammar lesson":
        st.session_state.readers_type = colq1a.selectbox("The grammar is generated for...",
                                    ["Teenagers", "Adults", "Linguists"])
    else:
        st.session_state.readers_type = "Linguists"

    if st.session_state.document_format == "Grammar lesson":
        grammatical_topics_progression = [
            "Basic sentence structure",
            "Politeness and social formulas",
            "Expressing who does what to whom",
            "Asking Yes/No questions",
            "Questions asking for information",
            "Negation",
            "Referring to participants (speaker, addressee, others)",
            "Referring to things",
            "Possession",
            "Describing things",
            "Saying what something or someone is (identification)",
            "Stating existence and location",
            "Talking about actions and states in the present/general time",
            "Talking about past events",
            "Talking about the future",
            "How actions unfold: ongoing, completed, habitual...",
            "Giving orders",
            "Expressing place and direction",
            "Expressing wishes",
            "Expressing doubts",
            "Expressing beliefs",
            "Classifiers or measure words"
        ]
        colq1, colq2 = st.columns(2)
        colq1.markdown("Choose a typical lesson topic")
        query_standard = colq1.selectbox("Select a standard grammar lesson...", ["no selection"] + grammatical_topics_progression)
        colq2.markdown("Or enter your custom query")
        query_custom = colq2.text_input("... or enter your own topic.")
        if query_standard != "no selection":
            query = query_standard
        elif query_custom is not None:
            query = query_custom
        else:
            query = None
    else:
        sketch_topics = [
            "Simple verbal sentences",
            "Simple non-verbal sentences",
            "Agents and patients",
            "Marking system",
            "Nouns",
            "Personal Pronouns",
            "Verbs",
            "Adverbs",
            "Adjective",
            "Numerals",
            "Tense system",
            "Aspect system",
            "Negation",
            "Coordination",
            "Subordination",
            "References to things",
            "Expressing the position in time",
            "Expressing the position in space"]
        colq1b, colq2b = st.columns(2)
        colq1b.markdown("Choose a standard grammar sketch topic")
        query_standard = colq1b.selectbox("Select a standard grammar sketch topic", ["no selection"] + sketch_topics)
        colq2b.markdown("Or enter your custom query")
        query_custom = colq2b.text_input("query")
        if query_standard != "no selection":
            query = query_standard
        elif query_custom is not None:
            query = query_custom
        else:
            query = None

    if role == "admin":
        if st.checkbox("Post-process output?"):
            st.session_state.polished_output = True



    # =================== GENERATION LAUNCH ====================================================
    if st.button("Reset and make new generation"):
        reset()
    if ((query_custom is not None or query_standard != "no selection")
            and query is not None
            and query != st.session_state.query):
        if st.button("submit"):
            st.session_state.query = query
            st.session_state.relevant_parameters = None
            st.session_state.alterlingua_contribution = None
            st.session_state.run_sources = True

if st.session_state.run_sources:

    # cq agents
    if st.session_state.is_cq and st.session_state.use_cq:
        # grammatical parameters selection
        available_params = ggu.extract_parameter_names_from_cq_knowledge(st.session_state.indi)
        with st.spinner("Selecting relevant grammatical parameters among {} available".format(len(available_params))):
            st.session_state.relevant_parameters = gga.select_parameters_sync(query, available_params)
        # alterlingua agent
        alterlingua_sentences = ggu.extract_and_clean_cq_alterlingua(st.session_state.indi)
        with st.spinner("Generating contribution from CQ pseudo-gloss analysis"):
            st.session_state.alterlingua_contribution = gga.contribute_from_alterlingua_sync(st.session_state.query,
                                                                                             alterlingua_sentences)
    else:
        st.warning("Not using CQs.")
        st.session_state.relevant_parameters = {}
        st.session_state.alterlingua_contribution = {}

    # document agent
    if st.session_state.is_doc and st.session_state.use_doc:
        vsids = [st.session_state.info_dict["documents"]["oa_vector_store_id"]]
        with st.spinner("Generating contribution from documents"):
            full_response = gga.file_search_request_sync(st.session_state.indi,
                                                           vsids,
                                                           query)
            try:
                raw_response = full_response.output[1].content
                if raw_response is not None:
                    st.session_state.documents_contribution = {
                        "text": raw_response[0].text,
                        "sources": list(set([a.filename for a in raw_response[0].annotations]))
                    }
                else:
                    st.session_state.documents_contribution = {
                        "text": "",
                        "sources": []
                    }
                    print("Response from document retrieval is None")
            except:
                st.session_state.documents_contribution = {
                    "text": "",
                    "sources": []
                }
                print("Response from document retrieval is None")
    else:
        st.warning("Not using documents")
        st.session_state.documents_contribution = {
            "text": "",
            "sources": []
        }
    # sentence pairs selection

    # COMMENTED THE PAIR VECTORIZATION
    # if st.session_state.is_pairs and st.session_state.use_pairs:
    #     with st.spinner("Counting whales..."):
    #         if sdu.get_vector_ready_pairs(st.session_state.indi):
    #             print("Augmented pairs prepared for vectorization")
    #         if ragu.vectorize_vaps(st.session_state.indi):
    #             print("Augmented pairs blobs vectorized and indexed")
    #         if ragu.vectorize_sources(st.session_state.indi):
    #             print("Augmented pairs sources vectorized and indexed")
    #         if ragu.vectorize_descriptions(st.session_state.indi):
    #             print("Augmented pairs descriptions vectorized and indexed")
    #         ragu.create_hard_kw_index(st.session_state.indi)
    if st.session_state.is_pairs and st.session_state.use_pairs:
        with st.spinner("Retrieving a helpful selection of sentence pairs..."):
            # retrieve N sentences using embeddings XXX RULED OUT, NOT RELEVANT ENOUGH
            # index_path = os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "vectors", "description_vectors", "index.faiss")
            # index, id_to_meta = ragu.load_descriptions_index_and_id_to_meta(st.session_state.indi)
            # if index and id_to_meta:
            #     vec_retrieved = ragu.retrieve_similar(query, index, id_to_meta, k=10, min_score=0.3)
            #     vecf_retrieved = [i["filename"][:-4]+".json" for i in vec_retrieved]
                # retrieve sentences from keywords

            # HARD-RETRIEVE COMMENTED
            # kw_retrieved = ragu.hard_retrieve_from_query(query, st.session_state.indi)
            # print("KW-retrieved sentences: {}".format(kw_retrieved))

            # Direct LLM retrieve
            sentence_pool = []
            for sf in [fn
                       for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                                         "sentence_pairs", "augmented_pairs"))
                       if fn.endswith(".json")]:
                with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs",
                                       "augmented_pairs", sf), encoding="utf-8") as f:
                    tmpd = json.load(f)
                    sentence_pool.append(tmpd["source"])
            print("sentence pool created with {} sentences".format(len(sentence_pool)))
            llm_selection_raw = sda.select_sentences_sync(query, sentence_pool)
            llm_selection = llm_selection_raw.sentence_list
            llm_filenames_retrieved = []
            for sentence in llm_selection:
                expected_filename = u.clean_sentence(sentence, filename=True) + ".json"
                if expected_filename in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs",
                                                     "augmented_pairs")):
                    llm_filenames_retrieved.append(expected_filename)
                else:
                    print("no {} file in augmented sentences".format(expected_filename))
            # aggregate
            # st.session_state.selected_pairs = list(set(llm_filenames_retrieved + kw_retrieved))
            st.session_state.selected_pairs = list(set(llm_filenames_retrieved))
    else:
        st.warning("Not using sentence pairs")
        st.session_state.selected_pairs = []

    st.session_state.run_sources = False

if st.session_state.relevant_parameters and st.sidebar.checkbox("Show selected grammatical parameters"):
    st.write(st.session_state.relevant_parameters)
if st.session_state.alterlingua_contribution and st.sidebar.checkbox("Show isolated CQ pseudo-gloss contribution"):
    st.write(st.session_state.alterlingua_contribution)
if st.session_state.documents_contribution and st.sidebar.checkbox("Show isolated documents contribution"):
    st.write(st.session_state.documents_contribution)
if st.session_state.selected_pairs and st.sidebar.checkbox("Show selected sentence pairs"):
    st.write(st.session_state.selected_pairs)


if (st.session_state.alterlingua_contribution
    or st.session_state.documents_contribution
    or st.session_state.selected_pairs):

# ============= AGGREGATION ============================

    if st.session_state.run_aggregation:
        st.session_state.run_aggregation = False
        if st.session_state.is_cq and st.session_state.use_cq:
            tmp_p_blob = json.dumps([p for p in st.session_state.cq_knowledge["grammar_priors"]
                                     if p["Parameter"] in st.session_state.relevant_parameters], ensure_ascii=False)
            if tmp_p_blob == "":
                tmp_p_blob = "No relevant grammatical parameter."
            selected_params_blob = tmp_p_blob
            alterlingua_explanation = st.session_state.alterlingua_contribution["explanation"]
            alterlingua_examples = json.dumps(st.session_state.alterlingua_contribution["examples"], ensure_ascii=False)
        else:
            selected_params_blob = "No relevant grammatical parameter."
            alterlingua_explanation = "No description from sentence analysis."
            alterlingua_examples = "No available examples from sentence analysis."

        if st.session_state.is_doc and st.session_state.use_doc:
            doc_contribution = st.session_state.documents_contribution["text"]
        else:
            doc_contribution = "No available contribution from documents."

        if st.session_state.is_pairs and st.session_state.use_pairs:
            sps = []
            try:
                for spf in st.session_state.selected_pairs:
                    if spf in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                           "sentence_pairs", "augmented_pairs")):
                        with open(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                               "sentence_pairs", "augmented_pairs", spf), "r", encoding='utf-8') as f:
                            sp = json.load(f)
                            sapd = {
                                st.session_state.indi: sp["target"],
                                "source": sp["source"],
                                "grammatical_description": sp["description"],
                                "concept-words_connections": sp.get("key_translation_concepts", "no connections"),
                                "gloss": sp.get("gloss", "no gloss")
                            }
                        sps.append(sapd)
                    else:
                        print("Augmented pair file {} not found in ".format(spf, os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                           "sentence_pairs", "augmented_pairs"))))
                sentence_pairs_blob = json.dumps(sps, ensure_ascii=False)
            except:
                st.warning("Issue with sentence pair: {}".format(st.session_state.selected_pairs))
                sentence_pairs_blob = "No available sentence pairs."
        else:
            sentence_pairs_blob = "No available sentence pairs."

        with st.spinner("Aggregating sources..."):
            if st.session_state.document_format == "Grammar lesson":
                first_aggregation = gga.create_lesson_sync(
                    indi_language=st.session_state.indi,
                    source_language=st.session_state.readers_language,
                    readers_type=st.session_state.readers_type,
                    grammatical_params=selected_params_blob,
                    alterlingua_explanation=alterlingua_explanation,
                    alterlingua_examples=alterlingua_examples,
                    doc_contribution=doc_contribution,
                    sentence_pairs=sentence_pairs_blob
                )
                if st.session_state.polished_output:
                    with st.spinner("Post-processing lesson..."):
                        st.session_state.output_dict = gga.review_lesson_sync(
                            lesson=first_aggregation,
                            source_language=st.session_state.readers_language,
                            readers_type=st.session_state.readers_type
                            )
                else:
                    st.session_state.output_dict = first_aggregation

            else:
                st.session_state.output_dict = gga.create_sketch_sync(
                    indi_language=st.session_state.indi,
                    source_language=st.session_state.readers_language,
                    readers_type=st.session_state.readers_type,
                    grammatical_params=selected_params_blob,
                    alterlingua_explanation=alterlingua_explanation,
                    alterlingua_examples=alterlingua_examples,
                    doc_contribution=doc_contribution,
                    sentence_pairs=sentence_pairs_blob
                )

            # adding sources
            tmp_sources = {}
            if st.session_state.is_cq and st.session_state.use_cq:
                tmp_sources["cqs"] = st.session_state.cq_files
            if st.session_state.is_doc and st.session_state.use_doc:
                tmp_sources["documents"] = st.session_state.documents_contribution["sources"]
            if st.session_state.is_pairs and st.session_state.use_pairs:
                pair_file_list = []
                for pair in st.session_state.info_dict["pairs"]:
                    pair_file_list.append(f'{pair["name"]} ({pair["author"]})')
                tmp_sources["pairs"] = pair_file_list
            st.session_state.output_dict["sources"] = tmp_sources

            # adding identifiers, date etc.
            from datetime import datetime
            now = datetime.now()
            st.session_state.output_dict["date"] = now.strftime("%A, %-d %B %Y at %H:%M")
            with open("version.json", "r") as f:
                v = json.load(f)
                version = v.get("version", "no version")
            st.session_state.output_dict["version"] = version

        st.success("Done! Output available.")

        # TRACE BUILDING AND STORING FOR ANALYSIS
        print("Building trace")
        trace = {"date": now.strftime("%A, %-d %B %Y at %H:%M"),
                 "language": st.session_state.indi,
                 "output_type": st.session_state.document_format,
                 "prompt": query,
                 "use_cq": st.session_state.use_cq,
                 "use_documents": st.session_state.use_doc,
                 "use_pairs": st.session_state.use_pairs}
        with open("version.json", "r") as f:
            v = json.load(f)
            version = v.get("version", "no version")
        trace["version"] = version
        if st.session_state.relevant_parameters:
            trace["parameters"] = st.session_state.relevant_parameters
        else:
            trace["parameters"] = {}
        if st.session_state.alterlingua_contribution:
            trace["pseudo-gloss"] = st.session_state.alterlingua_contribution
        else:
            trace["pseudo-gloss"] = {}
        if st.session_state.documents_contribution:
            trace["documents"] = st.session_state.documents_contribution
        else:
            trace["documents"] = ""
        if st.session_state.selected_pairs:
            trace["pairs"] = st.session_state.selected_pairs
        else:
            trace["pairs"] = []
        trace["output_dict"] = st.session_state.output_dict
        trace["user"] = username

        tfn = "trace_"
        tfn += st.session_state.indi + "_"
        tfn += u.clean_sentence(query, filename=True, filename_length=30)
        tfn += f"_({st.session_state.readers_language})_"
        tfn += str(now)
        tfn += ".json"

        traces_dir = os.path.join(BASE_LD_PATH, "traces")
        os.makedirs(traces_dir, exist_ok=True)
        with open(os.path.join(BASE_LD_PATH, "traces", tfn), "w") as tf:
            json.dump(trace, tf)
        print("Trace saved")

# =========== DISPLAY, STORAGE, CONVERSION =========================================

if st.session_state.output_dict:
    if st.session_state.document_format == "Grammar sketch":
        st.markdown(f"""Remember: This raw output, available here or stored by other users, is a 
                            raw output from DIG4EL: It most probably contains inaccuracies and errors. 
                            It is meant to be edited and used by an expert of the 
                            {st.session_state.indi} language. 
                            """)
        now = datetime.now()
        fn = "dig4el_aggregated_output_sketch_"
        fn += st.session_state.indi + "_"
        fn += u.clean_sentence(query, filename=True, filename_length=50)
        fn += f"_({st.session_state.readers_language})_"
        fn += now.strftime("_%-d_%B_%Y_at_%H_%M")
        fn += ".json"
        colsk1, colsk2 = st.columns(2)
        colsk1.download_button(label="Download JSON output",
                                 data=json.dumps(st.session_state.output_dict, ensure_ascii=False),
                                 file_name=fn)
        st.divider()
        # Store/Download outputs
        if st.button("Store output (making it visible to all users)"):
            now = datetime.now()
            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn), "w", encoding='utf-8') as f:
                json.dump(st.session_state.output_dict, f, ensure_ascii=False)

            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
                info = json.load(f)
                qk = f"sketch_{query} ({st.session_state.readers_language}) "
                qk += now.strftime(" %-d %B %Y at %H:%M")
            info["outputs"][qk] = fn

            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "w", encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False)

            st.success("Output stored and available")

        # Display
        with st.expander("Output"):
            display_sketch_output(st.session_state.output_dict)
        # Feedback
        if role in ["user", "admin"]:
            feedback_form()


    elif st.session_state.document_format == "Grammar lesson":
        now = datetime.now()
        st.markdown(f"""Remember: This raw output, available here or stored by other users, is a 
                    raw output from DIG4EL: **It most probably contains inaccuracies and errors**. 
                    It is meant to be edited and used by an expert of the 
                    {st.session_state.indi} language. 
                    """)
        st.subheader("Store and/or download the output")
        fn = "dig4el_unverified_lesson_"
        fn += st.session_state.indi + "_"
        fn += u.clean_sentence(query, filename=True, filename_length=50)
        fn += f"_({st.session_state.readers_language})_"
        fn += now.strftime("_%-d_%B_%Y_at_%H_%M")
        fn += ".json"

        docx = None
        try:
            docx = ogu.generate_lesson_docx_from_aggregated_output(st.session_state.output_dict,
                                                                   st.session_state.indi,
                                                                   st.session_state.readers_language)
        except:
            st.write("Generation of docx failed")

        # Store/Download outputs
        if st.button("Store output (making it visible to all users)"):

            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn), "w", encoding='utf-8') as f:
                json.dump(st.session_state.output_dict, f, ensure_ascii=False)

            if docx:
                with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn[:-5] + ".docx"), "wb") as f:
                    f.write(docx.getvalue())
            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
                info = json.load(f)
                qk = f"lesson_{query}_({st.session_state.readers_language})"
            info["outputs"][qk] = fn

            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "w", encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False)

            st.success("Output stored and available")

        st.download_button(label="Download JSON output",
                             data=json.dumps(st.session_state.output_dict, ensure_ascii=False),
                             file_name=fn)
        if docx:
            st.download_button(label="Download DOCX output",
                                 data=docx,
                                 file_name=fn[:-5]+".docx",
                                 mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                 key="final_docx")

        display_lesson_output(st.session_state.output_dict)
        if role in ["user", "admin"]:
            feedback_form()

        if role == "admin":
            if st.checkbox("Show JSON"):
                st.write(st.session_state.output_dict)







