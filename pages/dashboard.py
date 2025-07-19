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
from libs import glottolog_utils as gu

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "has_bayesian" not in st.session_state:
    st.session_state.has_bayesian = False
if "has_docs" not in st.session_state:
    st.session_state.has_docs = False
if "has_pairs" not in st.session_state:
    st.session_state.has_pairs = False
if "has_monolingual" not in st.session_state:
    st.session_state.has_monolingual = False

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
st.sidebar.write("CQ Ready" if st.session_state.has_bayesian else "CQ: No Data")
st.sidebar.write("Docs Ready" if st.session_state.has_docs else "Docs: No Data")
st.sidebar.write("Pairs Ready" if st.session_state.has_pairs else "Pairs: No Data")
st.sidebar.write("Mono Ready" if st.session_state.has_monolingual else "Mono: No Data")
st.sidebar.divider()

st.markdown("#### Using the tabs below, add information about {}".format((st.session_state.indi_language)))

st.divider()
col1, col2, col3, col4 = st.tabs(["CQ Inferences", "Documents", "Sentence Pairs", "Monolingual text"])
with col1:
    st.markdown("""
    If you don't have created Conversational Questionnaires yet, you can do it with "Enter CQ Translations". 
    If you have CQ translations, you can go to "Generate CQ Knowledge". You will be directed back here once the CQ
    Knowledge is built. 
    """)
    st.page_link("pages/record_cq_transcriptions.py", label="Enter CQ translations", icon=":material/contract_edit:")
    st.page_link("pages/infer_from_knowledge_and_cqs.py", label="Generate CQ Knowledge", icon=":material/contract_edit:")
with col2:
    st.write("""
            The Document Knowledge is created by indexing the content of the documents you are providing.
            These documents will be uploaded to be indexed, and their indexing stored on a remote server. 
            Use only documents that are public, or that you have the right to use. Rename your documents to make 
            their title and author(s) explicit in the document name. Don't use spaces or punctuation in the name. 
            For example: author_noam_chomsky_title_the_architecture_of_language.pdf
            This will simplify their management!
             """
             )
with col3:
    st.write("**Sentence Pairs**")
with col4:
    col4.write("**Monolingual Text**")

st.divider()




