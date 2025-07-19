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

import streamlit as st
import json
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_LD_PATH = "./ld/"

if "has_bayesian" not in st.session_state:
    st.session_state.has_bayesian = False
if "has_docs" not in st.session_state:
    st.session_state.has_docs = False
if "has_pairs" not in st.session_state:
    st.session_state.has_pairs = False
if "has_monolingual" not in st.session_state:
    st.session_state.has_monolingual = False
if "info_doc" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "descriptions", "info.json")) as f:
        st.session_state.info_doc = json.load(f)

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home2.py", label="Home", icon=":material/home:")

st.header("Dashboard")
st.write("Combine your language data and generate descriptions and grammar lessons")

colq, colw = st.columns(2)
st.session_state.indi_language = colq.selectbox("What language are we working on?", gu.GLOTTO_LANGUAGE_LIST)
st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.indi_language, "glottocode not found")
st.markdown("*glottocode {}*".format(st.session_state.indi_glottocode))
st.session_state.l1_language = colw.selectbox("What is the language of the readers?", ["English", "Bislama", "French", "German", "Tahitian"])

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
    st.page_link("pages/infer_from_knowledge_and_cqs.py", label="Generate CQ Knowledge from existing CQs", icon=":material/contract_edit:")

    if st.session_state.indi_language in os.listdir(BASE_LD_PATH):
        if "cq" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language)):
            if "cq_knowledge" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language, "cq")):
                if "cq_knowledge.json" in os.listdir(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                                                  "cq",
                                                                  "cq_knowledge")):

                    st.markdown("**There is an existing CQ Knowledge, click below to use it**")
                    if st.button("Use existing CQ Knowledge in {}".format(st.session_state.indi_language)):
                        with open(os.path.join(BASE_LD_PATH, st.session_state.indi_language,
                                               "cq",
                                               "cq_knowledge",
                                               "cq_knowledge.json"), "r") as f:
                            st.session_state.bayesian_data = json.load(f)
                        st.session_state.has_bayesian = True

    cq_knowledge_file = st.file_uploader("Upload a CQ Knowledge JSON file")
    if cq_knowledge_file is not None:
        with open(cq_knowledge_file, "r") as f:
            st.session_state.bayesian_data = json.load(f)
        st.session_state.has_bayesian = True

    if st.session_state.has_bayesian:
        st.success("✅ CQ knowledge ready")
with tab2:
    st.write("""
            The Document Knowledge is created by indexing the content of the documents you are providing.
            These documents will be uploaded to be indexed, and their indexing stored on a remote server. 
            Use only documents that are public, or that you have the right to use. Rename your documents to make 
            their title and author(s) explicit in the document name. Avoid using spaces or punctuation in the name. 
            For example: author_noam_chomsky_title_the_architecture_of_language.pdf
             """
             )
    available_documents = os.listdir(os.path.join(BASE_LD_PATH,
                                                  st.session_state.indi_language,
                                                  "descriptions",
                                                  "sources"))
    available_documents = [d for d in available_documents if d[-3:] in ["txt", "ocx", "pdf"]]
    vectorized_documents = st.session_state.info_doc["documents_currently_vectorized"]
    st.write("{} available documents".format(len(available_documents)))
    st.write(available_documents)
    st.write("{} documents present in the current index".format(len(vectorized_documents)))
    st.write(vectorized_documents)



with tab3:
    st.write("**Sentence Pairs**")
with tab4:
    tab4.write("**Monolingual Text**")

st.divider()




