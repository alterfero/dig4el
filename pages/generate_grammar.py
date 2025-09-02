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
import streamlit as st
import json
from libs import utils as u
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import grammar_generation_agents as gga
from libs import grammar_generation_utils as ggu
from libs import output_generation_utils as ogu
from libs import retrieval_augmented_generation_utils as ragu
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
    st.session_state.run_aggregation = False
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

# ----- HELPERS -----------------------------------------------------------------------------------
def display_output(output_dict):
    o = output_dict
    st.title(o["title"])
    st.write(o["introduction"])
    st.divider()
    for section in o["sections"]:
        st.subheader(section["focus"])
        st.write(section["description"]["description"])
        st.markdown(f"**{section['example']['target_sentence']}**")
        st.markdown(f"*{section['example']['source_sentence']}*")
        st.write(section["example"]["description"])
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
    if cfg["credentials"]["usernames"].get(username, {}).get("email", "") in st.session_state.info_dict.get("caretaker", []):
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

# languages with existing data
l_with_data = [l for l in os.listdir(os.path.join(BASE_LD_PATH)) if os.path.isdir(os.path.join(BASE_LD_PATH, l))]
if role == "guest":
    l_with_data = ["Tahitian"]
    colq.markdown(
        "**Note**: *As a guest, you can perform generation on a restricted collection of language. Contact us to access more languages!*")

selected_language = colq.selectbox("What language are we generating learning content for?",
                                   l_with_data, index=l_with_data.index(st.session_state.indi))
if colq.button("Select {}".format(selected_language)):
    st.session_state.indi = selected_language
    st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi,
                                                                   "glottocode not found")
    fmu.create_ld(BASE_LD_PATH, st.session_state.indi)
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
        st.session_state.info_dict = json.load(f)
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
                display_output(json.load(jsonf))


# GATHERING MATERIAL

# cq
if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_knowledge")):
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_knowledge", "cq_knowledge.json"), "r", encoding='utf-8') as f:
        st.session_state.cq_knowledge = json.load(f)
    st.session_state.cq_files = [fn
                                for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_translations"))
                                if fn[-5:] ==".json"]
    st.session_state.is_cq = True
else:
    st.session_state.cq_knowledge = False

# documents
st.session_state.vs_name = st.session_state.info_dict["documents"]["oa_vector_store_name"]

if st.session_state.info_dict["documents"]["oa_vector_store_id"] != "":
    st.session_state.is_doc = True

# pairs
if "index.faiss" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                          "sentence_pairs", "vectors")):
    st.session_state.pairs_files = [fn
                                    for fn in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "pairs"))
                                    if fn[-5:] == ".json"]
    st.session_state.is_pairs = True

st.sidebar.write("✅ CQ Ready" if st.session_state.is_cq else "No CQ")
if st.session_state.is_cq:
    st.session_state.use_cq = st.sidebar.toggle("Use CQ", value=st.session_state.use_cq)
st.sidebar.write("✅ Docs Ready" if st.session_state.is_doc else "No documents")
if st.session_state.is_doc:
    st.session_state.use_doc = st.sidebar.toggle("Use documents", value=st.session_state.use_doc)
st.sidebar.write("✅ Pairs Ready" if st.session_state.is_pairs else "No pairs")
if st.session_state.is_pairs:
    st.session_state.use_pairs = st.sidebar.toggle("Use Pairs", value=st.session_state.use_pairs)

if ((st.session_state.is_cq and st.session_state.use_cq) or (st.session_state.is_doc and st.session_state.use_doc)
    or (st.session_state.is_pairs and st.session_state.use_pairs)):
    st.subheader("Generate a new grammatical description")
    query = st.text_input("Query")
    if query is not None and query != st.session_state.query:
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
        with st.spinner("Generating contribution from CQ alterlingua analysis"):
            st.session_state.alterlingua_contribution = gga.contribute_from_alterlingua_sync(st.session_state.query,
                                                                                             alterlingua_sentences)
    # document agent
    if st.session_state.is_doc and st.session_state.use_doc:
        vsids = [st.session_state.info_dict["documents"]["oa_vector_store_id"]]
        with st.spinner("Generating contribution from documents"):
            full_response = gga.file_search_request_sync(st.session_state.indi,
                                                           vsids,
                                                           query)
            raw_response = full_response.output[1].content
            st.session_state.documents_contribution = {
                "text": raw_response[0].text,
                "sources": list(set([a.filename for a in raw_response[0].annotations]))
            }

    # sentence pairs selection
    if st.session_state.is_pairs and st.session_state.use_pairs:
        with st.spinner("Retrieving a helpful selection of prepared pairs"):
            # retrieve N sentences using embeddings
            index_path = os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "vectors", "index.faiss")
            index, id_to_meta = ragu.load_index_and_id_to_meta(st.session_state.indi)
            vec_retrieved = ragu.retrieve_similar(query, index, id_to_meta, k=10, min_score=0.3)
            vecf_retrieved = [i["filename"][:-4]+".json" for i in vec_retrieved]
            # retrieve sentences from keywords
            kw_retrieved = ragu.hard_retrieve_from_query(query, st.session_state.indi)
            # aggregate
            st.session_state.selected_pairs = list(set(vecf_retrieved + kw_retrieved))

    st.session_state.run_sources = False

if st.session_state.relevant_parameters and st.sidebar.checkbox("Show selected grammatical parameters"):
    st.write(st.session_state.relevant_parameters)
if st.session_state.alterlingua_contribution and st.sidebar.checkbox("Show isolated alterlingua contribution"):
    st.write(st.session_state.alterlingua_contribution)
if st.session_state.documents_contribution and st.sidebar.checkbox("Show isolated documents contribution"):
    st.write(st.session_state.documents_contribution)
if st.session_state.selected_pairs and st.sidebar.checkbox("Show selected sentence pairs"):
    st.write(st.session_state.selected_pairs)

if (st.session_state.alterlingua_contribution
    or st.session_state.documents_contribution
    or st.session_state.selected_pairs):
    st.write("You can now aggregate all sources into a grammatical description.")
    st.divider()
    st.header("Aggregation")
    st.session_state.readers_language = st.selectbox("What is the language of readers?",
                                    ["Bislama", "English", "French", "Japanese", "Swedish"])
    readers_type = st.selectbox("The grammar is generated for...",
                                ["Teenage beginners", "Adult beginners", "Linguists"])
    document_format = st.selectbox("Format", ["Grammar lesson"])
    if st.button("Aggregate all sources into a lesson"):
        st.session_state.run_aggregation = True

    if st.session_state.run_aggregation:

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
        else:
            sentence_pairs_blob = "No available sentence pairs."

        with st.spinner("Aggregating sources..."):
            st.session_state.output_dict = gga.create_lesson_sync(
                indi_language=st.session_state.indi,
                source_language=st.session_state.readers_language,
                readers_type=readers_type,
                grammatical_params=selected_params_blob,
                alterlingua_explanation=alterlingua_explanation,
                alterlingua_examples=alterlingua_examples,
                doc_contribution=doc_contribution,
                sentence_pairs=sentence_pairs_blob
            )

            # adding sources
            st.session_state.output_dict["sources"] = {
                "cqs": st.session_state.cq_files,
                "documents": st.session_state.documents_contribution["sources"],
                "pairs": st.session_state.pairs_files
            }

        st.session_state.run_aggregation = False
        st.success("Done! Output available.")

if st.session_state.output_dict:
    st.markdown(f"""Remember: This raw output, available here or stored by other users, is a 
                raw output from DIG4EL: It most probably contains inaccuracies and errors. 
                It is meant to be edited and used by an expert of the 
                {st.session_state.indi} language. 
                """)
    st.subheader("Store and/or download the output")
    if st.sidebar.checkbox("Show JSON output"):
        st.write(st.session_state.output_dict)
    fn = "dig4el_aggregated_output_"
    fn += st.session_state.indi + "_"
    fn += u.clean_sentence(query, filename=True, filename_length=50)
    fn += f"_({st.session_state.readers_language})"
    fn += ".json"

    docx = None
    try:
        docx = ogu.generate_lesson_docx_from_aggregated_output(st.session_state.output_dict,
                                                               st.session_state.indi,
                                                               st.session_state.readers_language)
    except:
        st.write("Generation of docx failed")

    # Save outputs
    if st.button("Store output (and share it with others)"):


        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn), "w", encoding='utf-8') as f:
            json.dump(st.session_state.output_dict, f, ensure_ascii=False)

        if docx:
            with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn[:-5]+".docx"), "wb") as f:
                f.write(docx.getvalue())
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r", encoding='utf-8') as f:
            info = json.load(f)
        info["outputs"][query] = fn

        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "w", encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False)

        st.success("Output stored and available")

    # Download outputs
    colz, colx = st.columns(2)
    colz.download_button(label="Download JSON output",
                         data=json.dumps(st.session_state.output_dict, ensure_ascii=False),
                         file_name=fn)
    if docx:
        colx.download_button(label="Download DOCX output",
                             data=docx,
                             file_name=fn[:-5]+".docx",
                             mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             key="final_docx")

    st.divider()
    st.subheader("Output")
    st.divider()
    display_output(st.session_state.output_dict)







