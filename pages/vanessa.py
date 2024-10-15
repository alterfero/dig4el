import streamlit as st



infospot = st.empty()

name = infospot.text_input("Enter your name:")
if name:
    infospot.write(f"Hello, {name}!")
if st.button("Reset"):
    infospot.write("")


