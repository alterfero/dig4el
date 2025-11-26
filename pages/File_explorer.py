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
from libs import glottolog_utils as gu
from libs import auth_utils as au
import streamlit as st
import zipfile
import tempfile
import yaml
from pathlib import Path
from libs import auth_utils as au
import streamlit_authenticator as stauth
import shutil



st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "has_access" not in st.session_state:
    st.session_state.has_access = False
if "authdata" not in st.session_state:
    st.session_state.authdata = None
if "vss" not in st.session_state:
    st.session_state.vss = []

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

# --------- HELPERS

def erase_all_files_in_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")


def delete_directory(directory_path):
    if os.path.exists(directory_path):
        try:
            shutil.rmtree(directory_path)
            print(f"Deleted directory: {directory_path}")
        except Exception as e:
            print(f"Failed to delete directory {directory_path}: {e}")
    else:
        print(f"The directory '{directory_path}' does not exist.")


def list_folders(directory_path):
    if not os.path.exists(directory_path):
        print(f"The directory '{directory_path}' does not exist.")
        return []

    return [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]


def zip_folder_download(folder_path: str | os.PathLike, archive_name: str | None = None) -> None:
    """
    Zip an entire folder (recursively) to a temp file and present a download button.

    Parameters
    ----------
    folder_path : str | Path
        Directory to zip (all files/subfolders included).
    archive_name : str | None
        Name of the downloaded file (defaults to "<foldername>.zip").
    """
    root = Path(folder_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        st.error(f"Folder not found or not a directory: {root}")
        return

    if archive_name is None:
        archive_name = f"{root.name}.zip"

    # Build zip in a temporary file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    p = Path(dirpath) / fn
                    arcname = p.relative_to(root)
                    # If a file disappears mid-walk, skip it
                    try:
                        zf.write(p, arcname)
                    except OSError:
                        pass

        # Read bytes for the button, then clean up the temp file
        data = tmp_path.read_bytes()
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    st.download_button(
        label=f"Download {archive_name}",
        data=data,
        file_name=archive_name,
        mime="application/zip",
    )



# --------- LOGIC ------------------------------------------------
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

    with st.expander("File explorer"):
        if st.checkbox("Zip and download"):
            zip_folder_download(BASE_LD_PATH, archive_name="dig4el.zip")
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

        st.subheader("Bulk actions")
        available_languages = list_folders(BASE_LD_PATH)
        selected_language = st.selectbox("Select a language", available_languages)
        st.write("You have selected {}".format(selected_language))
        if st.button("Reset {} pairs".format(selected_language)):
            with open(os.path.join(BASE_LD_PATH, selected_language, "info.json"), "r") as f:
                id = json.load(f)
            id["pairs"] = []
            with open(os.path.join(BASE_LD_PATH, selected_language, "info.json"), "w") as g:
                json.dump(id, g)
            erase_all_files_in_folder(os.path.join(BASE_LD_PATH, selected_language, "sentence_pairs", "pairs"))
            erase_all_files_in_folder(
                os.path.join(BASE_LD_PATH, selected_language, "sentence_pairs", "augmented_pairs"))
            erase_all_files_in_folder(
                os.path.join(BASE_LD_PATH, selected_language, "sentence_pairs", "vector_ready_pairs"))
            erase_all_files_in_folder(os.path.join(BASE_LD_PATH, selected_language, "sentence_pairs", "vectors"))
            erase_all_files_in_folder(
                os.path.join(BASE_LD_PATH, selected_language, "sentence_pairs", "vectors", "description_vectors"))
        if st.button("Reset {} outputs".format(selected_language)):
            erase_all_files_in_folder(os.path.join(BASE_LD_PATH, selected_language, "outputs"))
            with open(os.path.join(BASE_LD_PATH, selected_language, "info.json"), "r") as f:
                info_tmp = json.load(f)
            info_tmp["outputs"] = {}
            with open(os.path.join(BASE_LD_PATH, selected_language, "info.json"), "w") as f:
                json.dump(info_tmp, f)
            st.success("outputs deleted")
        if st.button("Reset {} vector store(s)".format(selected_language)):
            with st.spinner("Listing vector stores..."):
                st.session_state.vss = vsu.list_vector_stores_sync()
            to_erase = [vs for vs in st.session_state.vss if vs.name == selected_language + "_documents"]
            st.write("{} vector stores to delete".format(len(to_erase)))
            with st.spinner("Deleting {} {} vector stores".format(len(to_erase), selected_language)):
                for vs in to_erase:
                    with st.spinner("Deleting {}".format(vs.id)):
                        vsu.delete_vector_store_sync(vs.id)
                st.success("vector stores deleted")
                st.rerun()

        st.divider()
        if st.checkbox("Delete {} data".format(selected_language)):
            if st.button("Delete {} data".format(selected_language)):
                delete_directory(os.path.join(BASE_LD_PATH, selected_language))
                st.success("{} deleted".format(selected_language))
                st.rerun()
        if st.checkbox("Delete languages with no data"):
            llist = [l for l in os.listdir(os.path.join(BASE_LD_PATH))
                     if (os.path.isdir(os.path.join(BASE_LD_PATH, l)) and l in list(gu.GLOTTO_LANGUAGE_LIST.keys()))]
            empty_l_list = []
            for lang in llist:
                cqsb = True
                pairsb = True
                docsb = True
                if "cq_knowledge.json" not in os.listdir(os.path.join(BASE_LD_PATH, lang, "cq", "cq_knowledge")):
                    cqsb = False
                pdf_files = [file for file in os.listdir(os.path.join(BASE_LD_PATH, lang, "descriptions", "sources"))
                             if file.endswith('.pdf')]
                if pdf_files == []:
                    docsb = False
                pairs_files = [file for file in os.listdir(os.path.join(BASE_LD_PATH, lang, "sentence_pairs", "pairs"))
                               if file.endswith('.json')]
                if pairs_files == []:
                    pairsb = False
                if not cqsb and not pairsb and not docsb:
                    empty_l_list.append(lang)
            if st.button("Erase {}?".format(", ".join(empty_l_list))):
                for l_to_delete in empty_l_list:
                    delete_directory(os.path.join(BASE_LD_PATH, l_to_delete))
                st.rerun()

    # ---------------------------- VS

    with st.expander("Open AI stores management"):
        i = 0

        if st.button("List vector stores"):
            st.session_state.vss = vsu.list_vector_stores_sync()
        st.write(st.session_state.vss)

        selected_vsid = st.text_input("list files in VS by vsid", value="")
        if selected_vsid != "" and st.button("List files used by this vector store"):
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

        if st.button("Erase all vector stores"):
            to_erase = vsu.list_vector_stores_sync()
            st.write(len(to_erase))
            c = len(to_erase)
            with st.spinner("Deleting {} vector stores".format(len(to_erase))):
                for vs in to_erase:
                    with st.spinner("Deleting {}, {} to go".format(vs.id, c)):
                        vsu.delete_vector_store_sync(vs.id)
                        c = c - 1
            st.success("All vector stores deleted")
            st.rerun()


    with st.expander("User management"):
        colu1, colu2 = st.columns(2)
        if colu1.button("Load auth data"):
            with open(os.path.join(BASE_LD_PATH, "auth_config.yaml"), "r") as uf:
                st.session_state.authdata = yaml.safe_load(uf)
        if colu2.button("Save modified auth data"):
            with open(os.path.join(BASE_LD_PATH, "auth_config.yaml"), "w") as ufo:
                yaml.safe_dump(st.session_state.authdata, ufo)
        if st.session_state.authdata:
            if st.checkbox("Display auth data"):
                st.write(st.session_state.authdata)
            users = st.session_state.authdata["credentials"]["usernames"]
            selected_user = st.selectbox("Select a user", users)
            st.write("username: {}".format(selected_user))
            st.write("role: {}".format(st.session_state.authdata["credentials"]["usernames"][selected_user]["role"]))
            st.write("caretaker of: {}".format(st.session_state.authdata["credentials"]["usernames"][selected_user]["caretaker"]))

            selang = st.multiselect("Make caretaker of ", gu.GLOTTO_LANGUAGE_LIST.keys())
            if st.button("Make {} caretaker of {}".format(selected_user, selang)):
                st.session_state.authdata["credentials"]["usernames"][selected_user]["caretaker"] += selang
                st.rerun()

            if st.button("Reset caretaker list for {}".format(selected_user)):
                st.session_state.authdata["credentials"]["usernames"][selected_user]["caretaker"] = []
                st.rerun()

            if st.button("Delete {}".format(selected_user)):
                del st.session_state.authdata["credentials"]["usernames"][selected_user]
                st.rerun()

            st.write("New user")
            new_username = st.text_input("email")
            new_name = st.text_input("name")
            new_caretaker_of = st.multiselect("Caretaker of ", gu.GLOTTO_LANGUAGE_LIST.keys())
            if st.button("Create user"):
                new_entry = {}
                new_entry["name"] = new_name
                new_entry["email"] = new_username
                new_entry["password"] = au.make_hash("TemporaryPassw0rd!")
                new_entry["role"] = "user"
                new_entry["caretaker"] = new_caretaker_of
                new_entry["failed_login_attempts"] = 0
                st.session_state.authdata["credentials"]["usernames"][new_username] = new_entry
                st.rerun()

    with st.expander("Grammar seeds"):
        with open("./grammar_seeds/grammar_seeds.json", "r") as f:
            seeds = json.load(f)
        selected_seed = st.selectbox("Select a topic to edit its seed", seeds.keys())
        if selected_seed:
            new_seed = st.text_area("Seed", value=seeds[selected_seed]["guidance"])
            if st.button("Save new seed"):
                seeds[selected_seed]["guidance"] = new_seed
                st.markdown("**New seed** *{}*... submitted".format(seeds[selected_seed]["guidance"][:50]))
                with open("./grammar_seeds/grammar_seeds.json", "w") as fu:
                    seeds = json.dump(seeds, fu)
                st.success("Edited seed saved")
                st.rerun()
        st.markdown("**Or create a new seed**")
        new_topic = st.text_input("Topic")
        new_topic_seed = st.text_area("New seed")
        if st.button("Save new topic and seed"):
            seeds[new_topic] = {
                "guidance": new_topic_seed
            }
            with open("./grammar_seeds/grammar_seeds.json", "w") as fu:
                seeds = json.dump(seeds, fu)
            st.success("New seed saved")
            st.rerun()










