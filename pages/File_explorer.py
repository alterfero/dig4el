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

import json
import os
from libs import openai_vector_store_utils as vsu
import streamlit as st

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("---")
    st.page_link("home.py", label="Home", icon=":material/home:")

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
    "storage",
)

ROOT_PATH = os.path.join(BASE_LD_PATH)

if "current_path" not in st.session_state:
    st.session_state.current_path = ROOT_PATH

current_path = st.session_state.current_path

st.title("Local Data Explorer")
st.write(f"Current directory: {os.path.relpath(current_path, ROOT_PATH)}")

uploaded = st.file_uploader("Upload a file", key="uploader")
if uploaded is not None:
    dest = os.path.join(current_path, uploaded.name)
    with open(dest, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"Uploaded {uploaded.name}")
    st.rerun()

if current_path != ROOT_PATH:
    if st.button("⬆️ Parent directory"):
        st.session_state.current_path = os.path.dirname(current_path)
        st.rerun()

dirs = [
    d for d in sorted(os.listdir(current_path))
    if os.path.isdir(os.path.join(current_path, d))
]
files = [
    f for f in sorted(os.listdir(current_path))
    if os.path.isfile(os.path.join(current_path, f))
]

st.subheader("Directories")
for d in dirs:
    if st.button(f"📁 {d}", key=f"dir_{d}"):
        st.session_state.current_path = os.path.join(current_path, d)
        st.rerun()

st.subheader("Files")
for fname in files:
    fpath = os.path.join(current_path, fname)
    with st.expander(fname):
        with open(fpath, "rb") as file_bytes:
            st.download_button(
                "Download", file_bytes, file_name=fname, key=f"dl_{fname}"
            )
        if st.button("Delete", key=f"del_{fname}"):
            os.remove(fpath)
            st.rerun()
        if fname.endswith(".json"):
            try:
                with open(fpath, "r") as jf:
                    st.json(json.load(jf))
            except Exception as e:
                st.warning(f"Could not read JSON: {e}")

st.divider()
st.subheader("Open AI stores")
i = 0
if "vss" not in st.session_state:
    st.session_state.vss = []
if st.button("List vector stores"):
    st.session_state.vss = vsu.list_vector_stores_sync()
st.write(st.session_state.vss)

selected_vsid = st.text_input("list files in VS by vsid", value="")
if selected_vsid is not "" and st.button("LIst files used by this vector store"):
    st.write(vsu.list_files_in_vector_store_sync(selected_vsid))

to_delete_vsid = st.text_input("Delete VS with vsid...", value="")
if st.button("Delete {}".format(to_delete_vsid)):
    vsu.delete_vector_store_sync(to_delete_vsid)
    st.write("Done")
to_delete_name = st.text_input("Delete all VS with name...", value="")
but = st.text_input("But VSDI", "")
to_erase = [vs for vs in st.session_state.vss if (vs.name == to_delete_name and vs.id != but)]
if st.button("Delete {} VS with name {} but {}".format(len(to_erase), to_delete_name, but)):
    with st.spinner("Deleting {} {} vector stores but {}".format(len(to_erase), to_delete_name, but)):
        for vs in to_erase:
            with st.spinner("Deleting {}".format(vs.id)):
                vsu.delete_vector_store_sync(vs.id)
    st.success("vector stores deleted")
    st.rerun()

