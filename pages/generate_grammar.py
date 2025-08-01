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
from libs import grammar_generation_agents as gga
from libs import grammar_generation_utils as ggu
from libs import output_generation_utils as ogu
from libs import retrieval_augmented_generation_utils as ragu

BASE_LD_PATH = "./ld/"

if "indi" not in st.session_state:
    try:
        st.session_state.indi = st.session_state.indi_language
    except AttributeError:
        st.session_state.indi = "Abkhaz-Adyge"
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
if "is_doc" not in st.session_state:
    st.session_state.is_doc = False
if "use_doc" not in st.session_state:
    st.session_state.use_doc = True
if "is_pairs" not in st.session_state:
    st.session_state.is_pairs = False
if "use_pairs" not in st.session_state:
    st.session_state.use_pairs = True
if "info_dict" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r") as f:
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

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/dashboard.py", label="Source dashboard", icon=":material/search:")
    st.divider()

colq, colw = st.columns(2)
if st.session_state.indi == "Abkhaz-Adyge":
    selected_language = colq.selectbox("What language are we generating learning content for?",
                                       gu.GLOTTO_LANGUAGE_LIST)
    if colq.button("Select {}".format(selected_language)):
        st.session_state.indi = selected_language
        st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi,
                                                                       "glottocode not found")
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r") as f:
            st.session_state.info_dict = json.load(f)
else:
    colq.markdown(f"Working on **{st.session_state.indi}**")
    colq.markdown("*glottocode* {}".format(st.session_state.indi_glottocode))

# PROPOSING EXISTING DOCUMENTS
with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r") as f:
    info = json.load(f)
if info["outputs"] != {}:
    st.subheader("Access stored outputs from previous queries")
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

# GATHERING MATERIAL

# cq
if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_knowledge")):
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "cq", "cq_knowledge", "cq_knowledge.json"), "r") as f:
        st.session_state.cq_knowledge = json.load(f)
    st.session_state.is_cq = True
else:
    st.session_state.cq_knowledge = False

# documents
st.session_state.vs_name = st.session_state.info_dict["documents"]["oa_vector_store_name"]
if st.session_state.vs_name != "":
    st.session_state.is_doc = True

# pairs
if "index.pkl" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                          "sentence_pairs", "vectors")):
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
        vs_names = [st.session_state.info_dict["documents"]["oa_vector_store_name"]]
        with st.spinner("Generating contribution from documents"):
            full_response = gga.file_search_request_sync(st.session_state.indi,
                                                           vs_names,
                                                           query)
            raw_response = full_response.output[1].content
            st.session_state.documents_contribution = {
                "text": raw_response[0].text,
                "sources": raw_response[0].annotations
            }

    # sentence pairs selection
    if st.session_state.is_pairs and st.session_state.use_pairs:
        with st.spinner("Retrieving a helpful selection of augmented pairs"):
            # retrieve N sentences using embeddings
            index_path = os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "vectors", "index.pkl")
            with open(index_path, "rb") as f:
                index = pickle.load(f)
            id_to_meta_path = os.path.join(BASE_LD_PATH, st.session_state.indi, "sentence_pairs", "vectors", "id_to_meta.json")
            with open(id_to_meta_path, "r") as f:
                id_to_meta = json.load(f)
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
                                     if p["Parameter"] in st.session_state.relevant_parameters])
            if tmp_p_blob == "":
                tmp_p_blob = "No relevant grammatical parameter."
            selected_params_blob = tmp_p_blob
            alterlingua_explanation = st.session_state.alterlingua_contribution["explanation"]
            alterlingua_examples = json.dumps(st.session_state.alterlingua_contribution["examples"])
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
                with open(os.path.join(BASE_LD_PATH, st.session_state.indi,
                                       "sentence_pairs", "augmented_pairs", spf), "r") as f:
                    sp = json.load(f)
                sps.append(
                    {
                        st.session_state.indi: sp["target"],
                        "source": sp["source"],
                        "grammatical_description": sp["description"]["grammatical_description"],
                        "enunciation": sp["description"]["enunciation"],
                        "concept-words_connections": sp.get("connections", "no connections")
                    }
                )
            sentence_pairs_blob = json.dumps(sps)
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

        st.session_state.run_aggregation = False
        st.success("Done! Output available.")

if st.session_state.output_dict:
    st.subheader("Store and/or download the output below")
    if st.sidebar.checkbox("Show JSON output"):
        st.write(st.session_state.output_dict)
    fn = "dig4el_aggregated_output_"
    fn += st.session_state.indi + "_"
    fn += u.clean_sentence(query, filename=True, filename_length=50)
    fn += ".json"
    docx = ogu.generate_lesson_docx_from_aggregated_output(st.session_state.output_dict,
                                                           st.session_state.indi,
                                                           st.session_state.readers_language)

    # Save outputs
    if st.button("Store output (and share it with others)"):
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn), "w") as f:
            json.dump(st.session_state.output_dict, f)
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "outputs", fn[:-5]+".docx"), "wb") as f:
            f.write(docx.getvalue())
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "r") as f:
            info = json.load(f)
        info["outputs"][query] = fn
        with open(os.path.join(BASE_LD_PATH, st.session_state.indi, "info.json"), "w") as f:
            info = json.dump(info, f)
        st.success("Output stored and available")

    # Download outputs
    colz, colx = st.columns(2)
    colz.download_button(label="Download JSON output",
                         data=json.dumps(st.session_state.output_dict),
                         file_name=fn)
    colx.download_button(label="Download DOCX output",
                         data=docx,
                         file_name=fn[:-5]+".docx",
                         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                         key="final_docx")


