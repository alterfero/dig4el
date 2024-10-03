import openai
import streamlit as st

openai.api_key = st.secrets["openai_key"]
print(openai.models.list())
