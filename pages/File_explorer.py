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
import zipfile
import tempfile
import yaml
from pathlib import Path
from libs import auth_utils as au
import streamlit_authenticator as stauth

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "has_access" not in st.session_state:
    st.session_state.has_access = False

# -------- AUTH ------------------------------------------------------------------------
CFG_PATH = Path(
    os.getenv("AUTH_CONFIG_PATH") or
    os.path.join(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage", "auth_config.yaml")
)
# Cookie secret (override YAML)
COOKIE_KEY = os.getenv("AUTH_COOKIE_KEY", None)

cfg = au.load_config(CFG_PATH)

authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"],
    auto_hash=True)

auth_status = st.session_state.get("authentication_status", None)
name        = st.session_state.get("name", None)
username    = st.session_state.get("username", None)

if auth_status:
    role = cfg["credentials"]["usernames"].get(username, {}).get("role", "guest")
    if role != "admin":
        st.error("You don't have access to this page")
        st.page_link("home.py", label="Back to home page")
        st.stop()
    else:
        st.session_state.has_access = True
else:
    st.error("You don't have access to this page")
    st.page_link("home.py", label="Back to home page")
    st.stop()

# -------- END AUTH ------------------------------------------------------------------------
if st.session_state.has_access:

    with st.sidebar:
        st.image("./pics/dig4el_logo_sidebar.png")
        st.divider()
        st.page_link("home.py", label="Home", icon=":material/home:")
        st.sidebar.page_link("pages/generate_grammar.py", label="Generate Grammar", icon=":material/bolt:")
        st.divider()

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
    if st.button("Download All Files"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, "w") as zipf:
                for fname in files:
                    fpath = os.path.join(current_path, fname)
                    zipf.write(fpath, arcname=fname)  # Add file to the ZIP archive
            tmp_zip.seek(0)
            with open(tmp_zip.name, "rb") as zip_bytes:
                st.download_button(
                    label="Download All Files as ZIP",
                    data=zip_bytes,
                    file_name="all_files.zip",
                    mime="application/zip"
                )
    dtrigger = False
    if st.text_input("erase all files?") == "erase all files":
        dtrigger = True
    if dtrigger:
        for i, fname in enumerate(files):
            fpath = os.path.join(current_path, fname)
            with st.spinner("{}/{} deleting {}".format(i, len(files), fpath)):
                os.remove(fpath)
        dtrigger = False
        st.rerun()
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
                    with open(fpath, "r", encoding='utf-8') as jf:
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

