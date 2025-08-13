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

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.subheader("Explore DIG4EL processes")

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")


st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

st.page_link("pages/Transcriptions_explorer.py", label="Explore transcriptions", icon=":material/search:")

st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

st.page_link("pages/WALS_Explore.py", label="WALS Data", icon=":material/database:")

st.page_link("pages/Grambank_Explore.py", label="Grambank Data", icon=":material/database:")

st.page_link("pages/wgb_cp.py", label="Grambank <-> WALS Conditional Probabilities", icon=":material/casino:")

st.page_link("pages/Conditional_proba_exploration.py", label="Conditional Probabilies", icon=":material/casino:")

st.page_link("pages/General_agent_gawo_example.py", label="General Agent Gawo Example",
             icon=":material/travel_explore:")

st.page_link("pages/Testing_general_agents.py", label="Testing General Agents",
             icon=":material/quiz:")

st.page_link("pages/experimental_menu.py", label="Experimental features",
             icon=":material/experiment:")