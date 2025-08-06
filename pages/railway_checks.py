

import os
import streamlit as st

base_dir = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")

if "path" not in st.session_state:
    st.session_state.path = [base_dir, "storage"]


st.write("CWD: {}".format(os.getcwd()))
st.write("Volume mount: {}".format(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")))

st.write("Current path: {}".format(st.session_state.path))

for item in os.listdir(os.path.join(*st.session_state.path)):
    if st.button(item, key=item):
        st.session_state.path.append(item)
        st.rerun()

if st.button("reset"):
    st.session_state.path = ["storage"]
    st.rerun()
