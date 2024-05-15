import streamlit as st
import json

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Inferential Engine")
st.selectbox("Language",["Mwotlap", "Tahitian"])
st.selectbox("Focus",["Qualifier", "Agent", "Patient", "Tense", "Aspect"])
st.selectbox("Algorithm", ["Evolutionary Bayesian", "Pure Bayesian"])
st.write("In **Mwotlap**, the most probable projection function for **qualifiers** is")
st.subheader("Juxtaposition")
st.write("The qualifier follows the entity it qualifies")
st.write("as in **nēbē lon**, expanse of water + running (river)")