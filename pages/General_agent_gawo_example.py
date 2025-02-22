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
import pandas as pd
from libs import utils as u, wals_utils as wu, general_agents
import json
import altair as alt

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "ga_created" not in st.session_state:
    st.session_state["ga_created"] = False
if "current_ga" not in st.session_state:
    st.session_state["current_ga"] = None

with st.sidebar:
    st.subheader("DIG4EL")
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

st.title("General Agent Gawo example")

if st.session_state["current_ga"] is None:
    gawo = general_agents.GeneralAgent("gawo",
                                       parameter_names=["Order of Subject, Object and Verb",
                                                    "Order of Genitive and Noun",
                                                    "Order of Demonstrative and Noun",
                                                    "Order of Adjective and Noun",
                                                    "Order of Numeral and Noun",
                                                    "Order of Relative Clause and Noun",
                                                    "Order of Negative Morpheme and Verb",
                                                    "Order of Adposition and Noun Phrase",
                                                    "Order of Adverbial Subordinator and Clause"],
                                       language_stat_filter={})
    # language_stat_filter={"family":["Austronesian"]}
    st.session_state["current_ga"] = gawo
else:
    gawo = st.session_state["current_ga"]

colq, colw, cole, colr = st.columns(4)
if colq.button("Inject observation on SVO from marquesan"):
    observations = {'387': 0, '386': 0, '388': 0, '385': 8, '383': 2, '384': 0, '389': 0}
    gawo.add_observations("Order of Subject, Object and Verb", observations)
    gawo.language_parameters["Order of Subject, Object and Verb"].update_beliefs_from_observations()
if colw.button("Run messaging cycle"):
    gawo.run_belief_update_cycle()
if cole.button("Reset"):
    st.session_state["current_ga"] = None
    st.rerun()

param_number = len(gawo.language_parameters)
param_working_list = gawo.language_parameters
col1, col2, col3 = st.columns(3)
p = 0
for param_name, param in gawo.language_parameters.items():
    p += 1
    if p == 4:
        p = 1
    beliefs = param.beliefs
    display_dict = {}
    for de_pk, proba in beliefs.items():
        display_dict[wu.domain_element_by_pk[str(de_pk)]["name"]] = proba
    df = pd.DataFrame(list(display_dict.items()), columns=['values', 'p'])
    c = (
        alt.Chart(df)
        .mark_arc(innerRadius=30, outerRadius=80)
        .encode(theta='p', color="values:N")
    )
    if p == 1:
        col1.write("{}, locked: {}".format(param_name, param.locked))
        col1.altair_chart(c)
    if p == 2:
        col2.write("{}, locked: {}".format(param_name, param.locked))
        col2.altair_chart(c)
    if p == 3:
        col3.write("{}, locked: {}".format(param_name, param.locked))
        col3.altair_chart(c)

