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

# Openai DOCUMENTATION
# https://platform.openai.com/docs/api-reference/vector-stores
# https://platform.openai.com/docs/guides/tools-file-search

import streamlit as st
from libs import openai_file_search_utils as fsu
import openai
import os
import json

api_key = os.getenv("OPEN_AI_KEY")
openai.api_key = api_key

if "tl" not in st.session_state:
    st.session_state["tl"] = "Mwotlap"
if "full_response" not in st.session_state:
    st.session_state["full_response"] = None
if "response_text" not in st.session_state:
    st.session_state["response_text"] = ""
if "response_sources" not in st.session_state:
    st.session_state["response_sources"] = []

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.markdown("---")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Transcriptions_explorer.py", label="Explore transcriptions", icon=":material/search:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

tl_vs_dict = {
    "Mwotlap": "Mwotlap",
    "Iaai": "iaai"
}

st.title("Isolated Component Beta-test: Information retrieval using existing papers.")

st.session_state["tl"] = st.selectbox("Choose the target language",["Mwotlap", "Iaai"])


pivot_language = st.selectbox("Choose the output language",["English", "French", "Bislama"])

prompt = "You are a grammar description assistant retrieving grammar lesson content from existing documents."
prompt += "The lessson topic is: "
prompt += "In " + st.session_state["tl"] + ", " + st.text_input("Ask a question about the target language")
prompt += "Use as much available examples as possible retrieved from the document to explain it."
prompt += "Provide your answer in the " + pivot_language + " language."

if st.button("Submit"):
    st.session_state["full_response"] = fsu.file_search_request(tl_vs_dict[st.session_state["tl"]], prompt)
    try:
        raw_response = st.session_state["full_response"].output[1].content
        st.session_state["response_text"] = raw_response[0].text
        st.session_state["response_sources"] = raw_response[0].annotations
    except AttributeError:
        st.write("Issue retrieving content: ")
        st.write(full_response)

if st.session_state["response_text"] != "":
    st.write(st.session_state["response_text"])
    st.write(st.session_state["response_text"])
    st.subheader("Sources: ")
    filenames = [source.filename for source in st.session_state["response_sources"]]
    filenames = list(set(filenames))
    for f in filenames:
        st.write(f)

    if st.checkbox("show full response"):
        st.write(st.session_state["full_response"])