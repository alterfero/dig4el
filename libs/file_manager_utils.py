import os
import streamlit as st
import pandas as pd
import json
from libs import utils as u

doc_info = {
  "language": "",
  "documents": {
    "vectorized": [],
    "oa_vector_store_name": "",
    "oa_vector_store_id": ""
  },
  "pairs": [],
  "original_cqs": [],
  "outputs": {}
}
default_delimiters = [" ",
    ".",
    ",",
    ";",
    ":",
    "!",
    "?",
    "\u2026"]

def create_ld(BASE_LD_PATH, lname):
    if lname not in os.listdir(BASE_LD_PATH):
        os.mkdir(os.path.join(BASE_LD_PATH, lname))
    if "cq" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "cq"))
    if "cq_translations" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "cq")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "cq", "cq_translations"))
    if "cq_knowledge" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "cq")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "cq", "cq_knowledge"))
    if "descriptions" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "descriptions"))
    if "sources" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "descriptions")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "descriptions", "sources"))
    if "embeddings" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "descriptions")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "descriptions", "embeddings"))
    if "sentence_pairs" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs"))
    if "augmented_pairs" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs", "augmented_pairs"))
    if "pairs" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs", "pairs"))
    if "vector_ready_pairs" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs", "vector_ready_pairs"))
    if "vectors" not in os.listdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs")):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "sentence_pairs", "vectors"))
    if "monolingual" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "monolingual"))
    if "outputs" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "outputs"))
    if "info.json" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        with open(os.path.join(BASE_LD_PATH, lname, "info.json"), "w", encoding='utf-8') as f:
            u.save_json_normalized(doc_info, f)
    if "delimiters.json" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        with open(os.path.join(BASE_LD_PATH, lname, "delimiters.json"), "w", encoding='utf-8') as f:
            u.save_json_normalized(default_delimiters, f)
    if "batch_id_store.json" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        bids = {"batch_id": "no_id_set"}
        with open(os.path.join(BASE_LD_PATH, lname, "batch_id_store.json"), "w", encoding='utf-8') as f:
            u.save_json_normalized(bids, f)
    if "conveqs" not in os.listdir(os.path.join(BASE_LD_PATH, lname)):
        os.mkdir(os.path.join(BASE_LD_PATH, lname, "conveqs"))

def display_file_manager(folder_path: str, file_extensions: list[str] = None):
    """
    Displays a navigable file manager UI in a Streamlit app for files in `folder_path`,
    filtered by `file_extensions`. Users can navigate into subfolders, rename, or delete files.

    Parameters:
    - folder_path: Path to the root directory to manage.
    - file_extensions: List of file extensions to include (e.g., ['.txt', '.csv']).
                       If None, all files are shown.
    """
    # Validate base folder
    if not os.path.isdir(folder_path):
        st.error(f"Folder '{folder_path}' not found or is not a directory.")
        return

    base = os.path.abspath(folder_path)
    # Initialize session state for navigation
    if 'base_path' not in st.session_state or st.session_state.base_path != base:
        st.session_state.base_path = base
        st.session_state.current_path = base

    current = st.session_state.current_path

    # Breadcrumb navigation
    rel = os.path.relpath(current, base)
    parts = [] if rel == '.' else rel.split(os.sep)
    cols = st.columns(len(parts) + 1)

    # Root breadcrumb
    root_label = os.path.basename(base) or base
    if cols[0].button(root_label, key='crumb_0'):
        st.session_state.current_path = base
        st.rerun()

    # Sub-path breadcrumbs
    for idx, part in enumerate(parts):
        if cols[idx+1].button(part, key=f'crumb_{idx+1}'):
            new_path = os.path.join(base, *parts[:idx+1])
            st.session_state.current_path = new_path
            st.rerun()

    # Parent navigation
    if current != base:
        if st.button("🔙 Back"):
            st.session_state.current_path = os.path.dirname(current)
            st.rerun()

    # List directory entries
    try:
        entries = os.listdir(current)
    except PermissionError:
        st.error("Permission denied accessing this folder.")
        return

    # Show subfolders
    folders = [e for e in entries if os.path.isdir(os.path.join(current, e))]
    if folders:
        st.write("### Folders")
        for folder_name in sorted(folders):
            if st.button(f"📁 {folder_name}", key=f'enter_{folder_name}'):
                st.session_state.current_path = os.path.join(current, folder_name)
                st.rerun()

    # Prepare file extension filter
    if file_extensions:
        exts = tuple(e.lower() if e.startswith('.') else f'.{e.lower()}' for e in file_extensions)
    else:
        exts = None

    # List files
    files = []
    for entry in entries:
        full_path = os.path.join(current, entry)
        if os.path.isfile(full_path):
            if exts is None or entry.lower().endswith(exts):
                files.append(entry)
    files.sort()

    if not files:
        st.info("No files found with the given filter.")
        return

    # Display files in a table
    df = pd.DataFrame({'Filename': files})
    st.table(df)

    # File selection and actions
    selected = st.selectbox("Select file", files, key='selected_file')
    action = st.radio("Action", ["None", "Rename", "Delete"], key='file_action')

    # Rename logic
    if action == "Rename":
        new_name = st.text_input("New name", value=selected, key='rename_name')
        if st.button("Apply Rename", key='apply_rename'):
            if new_name and new_name != selected:
                src = os.path.join(current, selected)
                dst = os.path.join(current, new_name)
                if os.path.exists(dst):
                    st.error(f"Cannot rename: '{new_name}' already exists.")
                else:
                    try:
                        os.rename(src, dst)
                        st.success(f"Renamed '{selected}' to '{new_name}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error renaming file: {e}")
            else:
                st.warning("Enter a different name to rename.")

    # Delete logic with confirmation

    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False
    if action == "Delete":
        if not st.session_state.confirm_delete:
            if st.button("Delete", key='confirm_delete_prompt'):
                st.session_state.confirm_delete = True
                st.rerun()
        else:
            st.warning(f"Are you sure you want to delete '{selected}'?")
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("Yes, delete", key='delete_yes'):
                    try:
                        os.remove(os.path.join(current, selected))
                        st.success(f"Deleted '{selected}'.")
                        st.session_state.confirm_delete = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {e}")
            with col_cancel:
                if st.button("Cancel", key='delete_cancel'):
                    st.session_state.confirm_delete = False
                    st.rerun()
