import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu, agents
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

    st.write("**Base Features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

    st.write("**Advanced features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.title("General Agent Gawo example")

with st.popover("i"):
    st.markdown("This pages allows to replicate the 'Gawo' example. Gawo is a general agent focusing on "
                "word order in Marquesan. Each parameter is presented as a pie chart showing Gawo's beliefs about the value of "
                "each parameters. Initial beliefs are computed from WALS. The 'Inject observation' button shows the effect on beliefs of "
                "having observed 8 VSO ans 2 SVO in Conversational Questionnaires. Then each press on the  'Run messaging cycle button' "
                "triggers a Markov Random Field message exchange between all parameters, converging toward a consensus. Injecting, or not injecting observations "
                "lead to different consensus.")

if st.session_state["current_ga"] is None:
    gawo = agents.GeneralAgent("gawo",
                                   parameter_names=["Order of Subject, Object and Verb",
                                                    "Order of Genitive and Noun",
                                                    "Order of Demonstrative and Noun",
                                                    "Order of Adjective and Noun",
                                                    "Order of Numeral and Noun",
                                                    "Order of Relative Clause and Noun",
                                                    "Order of Negative Morpheme and Verb",
                                                    "Order of Adposition and Noun Phrase",
                                                    "SVNegO Order"],
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

