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

    st.write("**Base Features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

    st.write("**Advanced features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.page_link("pages/WALS_Explore.py", label="WALS Data", icon=":material/database:")

st.page_link("pages/Conditional_proba_exploration.py", label="Conditional Probabilies", icon=":material/casino:")

st.page_link("pages/General_agent_gawo_example.py", label="General Agent Gawo Example",
             icon=":material/travel_explore:")

st.page_link("pages/Testing_general_agents.py", label="Testing General Agents",
             icon=":material/quiz:")