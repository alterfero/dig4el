import json
import os
import streamlit as st

base_dir = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")

if "path" not in st.session_state:
    st.session_state.path = [base_dir, "storage"]
if "content" not in st.session_state:
    st.session_state.content = None


st.write("CWD: {}".format(os.getcwd()))
st.write("Volume mount: {}".format(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")))

st.write("Current path: {}".format(st.session_state.path))

for item in os.listdir(os.path.join(*st.session_state.path)):
    if st.button(item, key=item):
        if item.endswith(".json"):
            with open(os.path.join(*st.session_state.path, item), "r") as f:
                st.session_state.content = json.load(f)
            st.rerun()
        else:
            st.session_state.path.append(item)
            st.rerun()

if st.session_state.content:
    st.write(st.session_state.content)

if st.button("reset"):
    st.session_state.path = [base_dir, "storage"]
    st.rerun()
