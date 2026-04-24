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
import shutil
import tempfile
import zipfile
from datetime import datetime
from email.utils import parseaddr
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml

from libs import auth_utils as au
from libs import glottolog_utils as gu
from libs import openai_vector_store_utils as vsu


st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)


CFG_PATH = Path(
    os.getenv("AUTH_CONFIG_PATH")
    or os.path.join(
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
        "storage",
        "auth_config.yaml",
    )
).resolve()

ROOT_PATH = Path(
    os.path.join(
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
        "storage",
    )
).resolve()

GRAMMAR_SEEDS_PATH = Path("./grammar_seeds/grammar_seeds.json").resolve()
TEMP_PASSWORD = "TemporaryPassw0rd!"
LANGUAGE_OPTIONS = sorted(gu.GLOTTO_LANGUAGE_LIST.keys())
PAIR_RESET_TARGETS = [
    Path("sentence_pairs/pairs"),
    Path("sentence_pairs/augmented_pairs"),
    Path("sentence_pairs/vector_ready_pairs"),
    Path("sentence_pairs/vectors"),
    Path("sentence_pairs/vectors/description_vectors"),
]


def init_session_state() -> None:
    defaults = {
        "has_access": False,
        "authdata": None,
        "auth_dirty": False,
        "vss": [],
        "admin_flash": None,
        "empty_language_scan": None,
        "vector_store_listing": None,
        "manual_vector_store_id": "",
        "prepared_archive_path": None,
        "prepared_archive_name": None,
        "prepared_archive_label": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_flash(message: str, kind: str = "success") -> None:
    st.session_state.admin_flash = {"message": message, "kind": kind}


def render_flash() -> None:
    flash = st.session_state.pop("admin_flash", None)
    if not flash:
        return
    level = flash.get("kind", "info")
    message = flash.get("message", "")
    renderer = getattr(st, level, st.info)
    renderer(message)


def ensure_path_within_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(ROOT_PATH)
    except ValueError as exc:
        raise ValueError("Path escapes the managed storage root.") from exc
    return resolved


def current_path() -> Path:
    raw_path = Path(st.session_state.get("current_path", ROOT_PATH))
    try:
        resolved = ensure_path_within_root(raw_path)
    except ValueError:
        resolved = ROOT_PATH

    if not resolved.exists() or not resolved.is_dir():
        resolved = ROOT_PATH

    st.session_state.current_path = str(resolved)
    return resolved


def relative_label(path: Path) -> str:
    if path == ROOT_PATH:
        return "."
    return path.relative_to(ROOT_PATH).as_posix()


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{int(size)} B"


def format_timestamp(timestamp: float | int | None) -> str:
    if not timestamp:
        return "Unknown"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=path.parent,
            encoding="utf-8",
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            delete=False,
            dir=path.parent,
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, indent=2, ensure_ascii=False),
    )


def atomic_write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=path.parent,
            encoding="utf-8",
        ) as tmp:
            yaml.safe_dump(payload, tmp, sort_keys=False, allow_unicode=True)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def archive_cache_dir() -> Path:
    preferred_dir = ROOT_PATH.parent / "_prepared_archives"
    try:
        preferred_dir.mkdir(parents=True, exist_ok=True)
        return preferred_dir.resolve()
    except OSError:
        fallback_dir = Path(tempfile.gettempdir()) / "dig4el_prepared_archives"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir.resolve()


def clear_prepared_archive() -> None:
    archive_path = st.session_state.get("prepared_archive_path")
    if archive_path:
        try:
            Path(archive_path).unlink(missing_ok=True)
        except OSError:
            pass
    st.session_state.prepared_archive_path = None
    st.session_state.prepared_archive_name = None
    st.session_state.prepared_archive_label = None


def remember_prepared_archive(archive_path: Path, file_name: str, label: str) -> None:
    clear_prepared_archive()
    st.session_state.prepared_archive_path = str(archive_path)
    st.session_state.prepared_archive_name = file_name
    st.session_state.prepared_archive_label = label


def build_zip_from_directory(directory: Path) -> Path:
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".zip",
            prefix="storage_backup_",
            dir=archive_cache_dir(),
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)

        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(directory.rglob("*")):
                if file_path.is_symlink() or not file_path.is_file():
                    continue
                archive.write(file_path, arcname=file_path.relative_to(directory))

        return tmp_path
    except Exception:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def build_zip_from_files(files: list[Path]) -> Path:
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".zip",
            prefix="folder_backup_",
            dir=archive_cache_dir(),
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)

        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in files:
                if file_path.is_symlink() or not file_path.is_file():
                    continue
                archive.write(file_path, arcname=file_path.name)

        return tmp_path
    except Exception:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def render_prepared_archive_download() -> None:
    archive_path_raw = st.session_state.get("prepared_archive_path")
    archive_name = st.session_state.get("prepared_archive_name")
    archive_label = st.session_state.get("prepared_archive_label")

    if not archive_path_raw or not archive_name or not archive_label:
        return

    archive_path = Path(archive_path_raw)
    if not archive_path.exists():
        clear_prepared_archive()
        st.warning("The prepared ZIP is no longer available. Please prepare it again.")
        return

    st.caption(
        f"Prepared archive: `{archive_name}` ({format_size(archive_path.stat().st_size)})"
    )
    with archive_path.open("rb") as archive_file:
        st.download_button(
            archive_label,
            data=archive_file,
            file_name=archive_name,
            mime="application/zip",
            use_container_width=True,
            on_click="ignore",
            key="prepared_archive_download",
        )


def delete_files_only(folder: Path) -> dict[str, Any]:
    result = {"deleted": 0, "missing": False, "errors": []}
    if not folder.exists():
        result["missing"] = True
        return result

    for child in folder.iterdir():
        if child.is_symlink() or not child.is_file():
            continue
        try:
            child.unlink()
            result["deleted"] += 1
        except Exception as exc:
            result["errors"].append(f"{child.name}: {exc}")
    return result


def delete_directory_safe(directory: Path) -> None:
    resolved = ensure_path_within_root(directory)
    if resolved == ROOT_PATH:
        raise ValueError("Refusing to delete the storage root.")
    if not resolved.exists():
        raise FileNotFoundError(f"Directory not found: {resolved}")
    shutil.rmtree(resolved)


def load_json_file(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def load_pretty_json(path: Path) -> str:
    raw_text = path.read_text(encoding="utf-8")
    try:
        return json.dumps(json.loads(raw_text), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return raw_text


def collect_directories(directory: Path) -> list[Path]:
    return sorted(
        [
            child
            for child in directory.iterdir()
            if child.is_dir() and not child.is_symlink()
        ],
        key=lambda child: child.name.lower(),
    )


def collect_files(directory: Path) -> list[Path]:
    return sorted(
        [
            child
            for child in directory.iterdir()
            if child.is_file() and not child.is_symlink()
        ],
        key=lambda child: child.name.lower(),
    )


def count_direct_files(directory: Path, suffix: str | None = None) -> int:
    if not directory.exists():
        return 0
    count = 0
    for child in directory.iterdir():
        if child.is_symlink() or not child.is_file():
            continue
        if suffix is None or child.name.endswith(suffix):
            count += 1
    return count


def summarize_delete_results(results: dict[str, dict[str, Any]]) -> str:
    deleted_total = sum(item["deleted"] for item in results.values())
    missing_total = sum(1 for item in results.values() if item["missing"])
    error_total = sum(len(item["errors"]) for item in results.values())

    parts = [f"Deleted {deleted_total} files"]
    if missing_total:
        parts.append(f"{missing_total} target folders were already missing")
    if error_total:
        parts.append(f"{error_total} deletions failed")
    return ". ".join(parts) + "."


def load_authdata_from_disk() -> dict[str, Any]:
    with open(CFG_PATH, "r", encoding="utf-8") as file_handle:
        return yaml.safe_load(file_handle) or {}


def ensure_authdata_loaded(force: bool = False) -> None:
    if force or st.session_state.authdata is None:
        st.session_state.authdata = load_authdata_from_disk()
        st.session_state.auth_dirty = False


def user_records() -> dict[str, dict[str, Any]]:
    authdata = st.session_state.authdata or {}
    credentials = authdata.setdefault("credentials", {})
    return credentials.setdefault("usernames", {})


def normalize_caretakers(values: list[str]) -> list[str]:
    selected = set(values)
    return [language for language in LANGUAGE_OPTIONS if language in selected]


def is_valid_email(value: str) -> bool:
    address = parseaddr(value)[1]
    return bool(address and "@" in address and "." in address.split("@")[-1])


def reset_language_pairs(language: str) -> str:
    language_root = ROOT_PATH / language
    info_path = language_root / "info.json"

    info = load_json_file(info_path)
    info["pairs"] = []
    atomic_write_json(info_path, info)

    cleared = {
        target.as_posix(): delete_files_only(language_root / target)
        for target in PAIR_RESET_TARGETS
    }
    return summarize_delete_results(cleared)


def reset_language_outputs(language: str) -> str:
    language_root = ROOT_PATH / language
    info_path = language_root / "info.json"

    info = load_json_file(info_path)
    info["outputs"] = {}
    atomic_write_json(info_path, info)

    cleared = {"outputs": delete_files_only(language_root / "outputs")}
    return summarize_delete_results(cleared)


def scan_empty_languages() -> list[dict[str, Any]]:
    results = []
    for language_dir in collect_directories(ROOT_PATH):
        language = language_dir.name
        if language not in gu.GLOTTO_LANGUAGE_LIST:
            continue

        has_cq_knowledge = (language_dir / "cq" / "cq_knowledge" / "cq_knowledge.json").exists()
        has_documents = any((language_dir / "descriptions" / "sources").glob("*.pdf")) if (language_dir / "descriptions" / "sources").exists() else False
        has_pairs = any((language_dir / "sentence_pairs" / "pairs").glob("*.json")) if (language_dir / "sentence_pairs" / "pairs").exists() else False

        if not has_cq_knowledge and not has_documents and not has_pairs:
            results.append(
                {
                    "Language": language,
                    "CQ knowledge": "No",
                    "Pairs": "No",
                    "Documents": "No",
                }
            )

    return results


def summarize_language_workspace(language: str) -> dict[str, Any]:
    language_root = ROOT_PATH / language
    info_path = language_root / "info.json"
    info = {}
    if info_path.exists():
        try:
            info = load_json_file(info_path)
        except Exception:
            info = {}

    vector_store_count = None
    if st.session_state.vss:
        vector_store_count = len(
            [
                vector_store
                for vector_store in st.session_state.vss
                if getattr(vector_store, "name", "") == f"{language}_documents"
            ]
        )

    return {
        "pairs_in_info": len(info.get("pairs", [])) if isinstance(info.get("pairs"), list) else 0,
        "pair_files": count_direct_files(language_root / "sentence_pairs" / "pairs", ".json"),
        "output_files": count_direct_files(language_root / "outputs"),
        "document_sources": count_direct_files(language_root / "descriptions" / "sources", ".pdf"),
        "cq_knowledge": (language_root / "cq" / "cq_knowledge" / "cq_knowledge.json").exists(),
        "vector_store_count": vector_store_count,
        "info_exists": info_path.exists(),
    }


def model_to_dict(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if isinstance(item, dict):
        return item
    if hasattr(item, "__dict__"):
        return dict(item.__dict__)
    return {"value": str(item)}


def vector_store_rows(vector_stores: list[Any]) -> pd.DataFrame:
    rows = []
    for vector_store in vector_stores:
        file_counts = getattr(vector_store, "file_counts", None)
        rows.append(
            {
                "Name": getattr(vector_store, "name", "") or "(no name)",
                "ID": getattr(vector_store, "id", ""),
                "Files": getattr(file_counts, "total", 0) if file_counts else 0,
                "Status": getattr(vector_store, "status", "unknown"),
                "Created": format_timestamp(getattr(vector_store, "created_at", None)),
            }
        )
    return pd.DataFrame(rows)


def vector_store_label(vector_store: Any) -> str:
    file_counts = getattr(vector_store, "file_counts", None)
    total_files = getattr(file_counts, "total", 0) if file_counts else 0
    name = getattr(vector_store, "name", "") or "(no name)"
    return f"{name} [{vector_store.id}] • {total_files} files"


init_session_state()

cfg = au.load_config(CFG_PATH)
authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"],
    auto_hash=True,
)

auth_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

if auth_status:
    role = cfg["credentials"]["usernames"].get(username, {}).get("role", "guest")
    if role != "admin":
        st.error("You don't have access to this page.")
        st.page_link("home.py", label="Back to home page")
        st.stop()
    st.session_state.has_access = True
else:
    st.error("You don't have access to this page.")
    st.page_link("home.py", label="Back to home page")
    st.stop()

if not ROOT_PATH.exists():
    st.error(f"Storage root not found: {ROOT_PATH}")
    st.stop()

if "current_path" not in st.session_state:
    st.session_state.current_path = str(ROOT_PATH)


with st.sidebar:
    st.image("./pics/dig4el_logo_sidebar.png")
    st.divider()
    st.page_link("home.py", label="Home", icon=":material/home:")
    st.page_link("pages/generate_grammar.py", label="Generate Grammar", icon=":material/bolt:")
    st.divider()
    st.caption(f"Signed in as `{username}`")


st.title("Admin Storage Console")
st.caption(
    "Critical admin tools with stronger confirmation gates, atomic writes, and clearer feedback."
)
st.info(
    "Destructive actions now require explicit confirmation phrases. Most edits stay local until you press a save button."
)
render_flash()

ADMIN_SECTIONS = [
    "Storage Explorer",
    "Language Maintenance",
    "OpenAI Vector Stores",
    "User Management",
    "Grammar Seeds",
]
selected_admin_section = st.radio(
    "Admin section",
    options=ADMIN_SECTIONS,
    key="admin_section",
    horizontal=True,
    label_visibility="collapsed",
)

current_directory = current_path()
directories = collect_directories(current_directory)
files = collect_files(current_directory)
filter_term = st.text_input(
    "Filter items in the current folder",
    key="storage_filter",
    placeholder="Type part of a file or folder name",
).strip().lower()

if filter_term:
    filtered_directories = [item for item in directories if filter_term in item.name.lower()]
    filtered_files = [item for item in files if filter_term in item.name.lower()]
else:
    filtered_directories = directories
    filtered_files = files


if selected_admin_section == "Storage Explorer":
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Folders", len(directories))
    metric_col2.metric("Files", len(files))
    metric_col3.metric(
        "Direct file size",
        format_size(sum(file_path.stat().st_size for file_path in files)),
    )

    st.caption(f"Current directory: `{relative_label(current_directory)}`")

    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 4])
    if nav_col1.button("Go to root", disabled=current_directory == ROOT_PATH, use_container_width=True):
        st.session_state.current_path = str(ROOT_PATH)
        st.rerun()
    if nav_col2.button("Parent directory", disabled=current_directory == ROOT_PATH, use_container_width=True):
        st.session_state.current_path = str(current_directory.parent)
        st.rerun()
    nav_col3.caption(f"Storage root: `{ROOT_PATH}`")

    zip_col1, zip_col2 = st.columns(2)
    if zip_col1.button("Prepare ZIP of files in this folder", use_container_width=True):
        if not files:
            st.warning("There are no files in the current folder to package.")
        else:
            try:
                with st.spinner("Preparing archive..."):
                    archive_path = build_zip_from_files(files)
                archive_name = f"{current_directory.name or 'storage'}_files.zip"
                remember_prepared_archive(
                    archive_path,
                    archive_name,
                    "Download current-folder ZIP",
                )
                st.success(
                    f"Archive ready ({format_size(archive_path.stat().st_size)}). "
                    "Use the download button below."
                )
            except Exception as exc:
                st.error(f"Could not prepare the current-folder ZIP: {exc}")
    if zip_col2.button("Prepare full storage backup ZIP", use_container_width=True):
        try:
            with st.spinner("Preparing recursive storage archive..."):
                archive_path = build_zip_from_directory(ROOT_PATH)
            remember_prepared_archive(
                archive_path,
                "dig4el_storage_backup.zip",
                "Download storage backup ZIP",
            )
            st.success(
                f"Archive ready ({format_size(archive_path.stat().st_size)}). "
                "Use the download button below."
            )
        except Exception as exc:
            st.error(f"Could not prepare the storage backup ZIP: {exc}")

    render_prepared_archive_download()

    with st.form("upload_file_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload a file to this folder")
        overwrite_upload = st.checkbox("Overwrite if a file with the same name already exists")
        upload_submitted = st.form_submit_button("Upload file", type="primary")

    if upload_submitted:
        if uploaded_file is None:
            st.warning("Choose a file before uploading.")
        else:
            safe_name = Path(uploaded_file.name).name
            destination = current_directory / safe_name
            if uploaded_file.name != safe_name:
                st.error("Folder paths in upload names are not allowed. Please upload a single file.")
            elif destination.exists() and not overwrite_upload:
                st.warning(f"`{safe_name}` already exists here. Enable overwrite to replace it.")
            else:
                atomic_write_bytes(destination, uploaded_file.getvalue())
                set_flash(f"Uploaded `{safe_name}` to `{relative_label(current_directory)}`.")
                st.rerun()

    st.subheader("Folders")
    if filtered_directories:
        folder_columns = st.columns(3)
        for index, folder_path in enumerate(filtered_directories):
            with folder_columns[index % 3]:
                if st.button(
                    f"Open {folder_path.name}",
                    key=f"dir_{relative_label(folder_path)}",
                    use_container_width=True,
                ):
                    st.session_state.current_path = str(folder_path)
                    st.rerun()
    else:
        st.info("No folders match the current filter.")

    st.subheader("Files")
    if filtered_files:
        for file_path in filtered_files:
            stat = file_path.stat()
            expander_label = (
                f"{file_path.name} • {format_size(stat.st_size)} • modified {format_timestamp(stat.st_mtime)}"
            )
            file_key = relative_label(file_path).replace("/", "__")
            with st.expander(expander_label, expanded=False):
                st.caption(f"Path: `{relative_label(file_path)}`")

                action_col1, action_col2 = st.columns([1, 2])
                action_col1.download_button(
                    "Download",
                    data=file_path.read_bytes(),
                    file_name=file_path.name,
                    mime="application/octet-stream",
                    key=f"download_{file_key}",
                    use_container_width=True,
                )

                delete_phrase = f"DELETE {file_path.name}"
                typed_delete_phrase = action_col2.text_input(
                    f"Type `{delete_phrase}` to enable deletion",
                    key=f"delete_file_phrase_{file_key}",
                    placeholder=delete_phrase,
                )
                if action_col2.button(
                    "Delete file",
                    key=f"delete_file_button_{file_key}",
                    disabled=typed_delete_phrase != delete_phrase,
                    use_container_width=True,
                ):
                    file_path.unlink()
                    st.session_state.pop(f"json_editor_{file_key}", None)
                    set_flash(f"Deleted `{file_path.name}` from `{relative_label(current_directory)}`.")
                    st.rerun()

                if file_path.suffix.lower() == ".json":
                    editor_key = f"json_editor_{file_key}"
                    if editor_key not in st.session_state:
                        st.session_state[editor_key] = load_pretty_json(file_path)

                    st.caption("JSON is validated before the file is overwritten.")
                    st.text_area(
                        "JSON content",
                        key=editor_key,
                        height=320,
                    )

                    json_col1, json_col2, json_col3 = st.columns(3)
                    if json_col1.button("Reload from disk", key=f"reload_{file_key}", use_container_width=True):
                        st.session_state[editor_key] = load_pretty_json(file_path)
                        set_flash(f"Reloaded `{file_path.name}` from disk.", kind="info")
                        st.rerun()
                    if json_col2.button("Validate JSON", key=f"validate_{file_key}", use_container_width=True):
                        try:
                            json.loads(st.session_state[editor_key])
                        except json.JSONDecodeError as exc:
                            st.error(f"Invalid JSON: {exc}")
                        else:
                            st.success("JSON is valid.")
                    if json_col3.button(
                        "Save JSON",
                        key=f"save_{file_key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            parsed = json.loads(st.session_state[editor_key])
                        except json.JSONDecodeError as exc:
                            st.error(f"Invalid JSON. The file was not changed: {exc}")
                        else:
                            atomic_write_json(file_path, parsed)
                            st.session_state[editor_key] = json.dumps(
                                parsed,
                                indent=2,
                                ensure_ascii=False,
                            )
                            set_flash(f"Saved `{file_path.name}`.")
                            st.rerun()
    else:
        st.info("No files match the current filter.")

    st.subheader("Current-folder actions")
    st.caption("These actions affect only direct files in the current folder. Subfolders are preserved.")
    if files:
        file_preview = ", ".join(file_path.name for file_path in files[:8])
        if len(files) > 8:
            file_preview += ", ..."
        st.caption(f"Files targeted: {file_preview}")

    folder_delete_phrase = f"DELETE FILES IN {relative_label(current_directory)}"
    typed_folder_delete_phrase = st.text_input(
        f"Type `{folder_delete_phrase}` to delete every direct file in this folder",
        key=f"delete_folder_phrase_{relative_label(current_directory)}",
        placeholder=folder_delete_phrase,
    )
    if st.button(
        "Delete all direct files in current folder",
        disabled=typed_folder_delete_phrase != folder_delete_phrase,
        use_container_width=True,
    ):
        result = delete_files_only(current_directory)
        if result["errors"]:
            set_flash(
                f"Deleted {result['deleted']} files, but {len(result['errors'])} deletions failed.",
                kind="warning",
            )
        else:
            set_flash(
                f"Deleted {result['deleted']} direct files from `{relative_label(current_directory)}`."
            )
        st.rerun()


if selected_admin_section == "Language Maintenance":
    available_languages = [directory.name for directory in collect_directories(ROOT_PATH)]
    if not available_languages:
        st.info("No language workspaces were found under the storage root.")
    else:
        selected_language = st.selectbox(
            "Select a language workspace",
            options=available_languages,
            key="language_maintenance_selection",
        )
        summary = summarize_language_workspace(selected_language)

        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        summary_col1.metric("Pairs in info.json", summary["pairs_in_info"])
        summary_col2.metric("Pair files", summary["pair_files"])
        summary_col3.metric("Output files", summary["output_files"])
        if summary["vector_store_count"] is None:
            summary_col4.metric("Cached vector stores", "Not loaded")
        else:
            summary_col4.metric("Cached vector stores", summary["vector_store_count"])

        st.caption(f"Workspace path: `{relative_label(ROOT_PATH / selected_language)}`")
        if not summary["info_exists"]:
            st.warning("`info.json` is missing for this language. Reset actions that depend on it will fail.")
        if not summary["cq_knowledge"]:
            st.info("No `cq_knowledge.json` detected for this language.")

        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            reset_pairs_phrase = f"RESET {selected_language} PAIRS"
            with st.form(f"reset_pairs_form_{selected_language}"):
                st.caption("Clears pair-related folders and resets `info.json -> pairs`.")
                typed_phrase = st.text_input(
                    f"Type `{reset_pairs_phrase}`",
                    placeholder=reset_pairs_phrase,
                )
                submitted = st.form_submit_button(
                    "Reset pairs",
                    disabled=typed_phrase != reset_pairs_phrase,
                    use_container_width=True,
                )
            if submitted:
                try:
                    message = reset_language_pairs(selected_language)
                except Exception as exc:
                    st.error(f"Pairs reset failed: {exc}")
                else:
                    set_flash(f"Reset pairs for `{selected_language}`. {message}")
                    st.rerun()

        with action_col2:
            reset_outputs_phrase = f"RESET {selected_language} OUTPUTS"
            with st.form(f"reset_outputs_form_{selected_language}"):
                st.caption("Clears direct files in `outputs` and resets `info.json -> outputs`.")
                typed_phrase = st.text_input(
                    f"Type `{reset_outputs_phrase}`",
                    placeholder=reset_outputs_phrase,
                )
                submitted = st.form_submit_button(
                    "Reset outputs",
                    disabled=typed_phrase != reset_outputs_phrase,
                    use_container_width=True,
                )
            if submitted:
                try:
                    message = reset_language_outputs(selected_language)
                except Exception as exc:
                    st.error(f"Output reset failed: {exc}")
                else:
                    set_flash(f"Reset outputs for `{selected_language}`. {message}")
                    st.rerun()

        with action_col3:
            reset_vs_phrase = f"DELETE {selected_language} VECTOR STORES"
            with st.form(f"reset_vector_stores_form_{selected_language}"):
                st.caption("Deletes every OpenAI vector store named `<language>_documents`.")
                typed_phrase = st.text_input(
                    f"Type `{reset_vs_phrase}`",
                    placeholder=reset_vs_phrase,
                )
                submitted = st.form_submit_button(
                    "Delete matching vector stores",
                    disabled=typed_phrase != reset_vs_phrase,
                    use_container_width=True,
                )
            if submitted:
                try:
                    with st.spinner("Listing vector stores..."):
                        vector_stores = vsu.list_vector_stores_sync()
                    matching_stores = [
                        vector_store
                        for vector_store in vector_stores
                        if getattr(vector_store, "name", "") == f"{selected_language}_documents"
                    ]
                    with st.spinner(f"Deleting {len(matching_stores)} vector stores..."):
                        for vector_store in matching_stores:
                            vsu.delete_vector_store_sync(vector_store.id)
                    st.session_state.vss = []
                except Exception as exc:
                    st.error(f"Vector-store reset failed: {exc}")
                else:
                    set_flash(
                        f"Deleted {len(matching_stores)} vector stores for `{selected_language}`."
                    )
                    st.rerun()

        st.divider()
        delete_language_phrase = f"DELETE {selected_language}"
        with st.form(f"delete_language_form_{selected_language}"):
            st.warning("This removes the entire language workspace directory recursively.")
            typed_phrase = st.text_input(
                f"Type `{delete_language_phrase}`",
                placeholder=delete_language_phrase,
            )
            delete_submitted = st.form_submit_button(
                f"Delete {selected_language} workspace",
                disabled=typed_phrase != delete_language_phrase,
                use_container_width=True,
            )
        if delete_submitted:
            try:
                delete_directory_safe(ROOT_PATH / selected_language)
            except Exception as exc:
                st.error(f"Language deletion failed: {exc}")
            else:
                if current_directory == ROOT_PATH / selected_language:
                    st.session_state.current_path = str(ROOT_PATH)
                set_flash(f"Deleted the `{selected_language}` workspace.")
                st.rerun()

        st.divider()
        scan_col1, scan_col2 = st.columns([1, 2])
        if scan_col1.button("Scan for languages with no data", use_container_width=True):
            with st.spinner("Scanning language workspaces..."):
                st.session_state.empty_language_scan = scan_empty_languages()

        empty_language_scan = st.session_state.empty_language_scan
        if empty_language_scan is not None:
            if empty_language_scan:
                scan_col2.success(
                    f"Found {len(empty_language_scan)} language workspaces with no CQ knowledge, pair files, or document PDFs."
                )
                st.dataframe(
                    pd.DataFrame(empty_language_scan),
                    use_container_width=True,
                    hide_index=True,
                )
                delete_empty_phrase = f"DELETE {len(empty_language_scan)} EMPTY LANGUAGES"
                typed_phrase = st.text_input(
                    f"Type `{delete_empty_phrase}` to remove all listed workspaces",
                    key="delete_empty_languages_phrase",
                    placeholder=delete_empty_phrase,
                )
                if st.button(
                    "Delete all scanned empty-language workspaces",
                    disabled=typed_phrase != delete_empty_phrase,
                    use_container_width=True,
                ):
                    deleted_languages = []
                    errors = []
                    for row in empty_language_scan:
                        language = row["Language"]
                        try:
                            delete_directory_safe(ROOT_PATH / language)
                            deleted_languages.append(language)
                        except Exception as exc:
                            errors.append(f"{language}: {exc}")

                    st.session_state.empty_language_scan = None
                    if errors:
                        set_flash(
                            f"Deleted {len(deleted_languages)} languages, but {len(errors)} deletions failed.",
                            kind="warning",
                        )
                    else:
                        set_flash(f"Deleted {len(deleted_languages)} empty language workspaces.")
                    st.rerun()
            else:
                scan_col2.info("No empty language workspaces were found in the last scan.")


if selected_admin_section == "OpenAI Vector Stores":
    load_col1, load_col2 = st.columns([1, 3])
    if load_col1.button("Refresh vector stores", use_container_width=True):
        try:
            with st.spinner("Loading vector stores..."):
                st.session_state.vss = vsu.list_vector_stores_sync()
        except Exception as exc:
            st.error(f"Could not load vector stores: {exc}")
        else:
            st.success(f"Loaded {len(st.session_state.vss)} vector stores.")

    vector_stores = st.session_state.vss
    load_col2.caption(
        "Load the latest vector-store list before deleting by name or inspecting cached counts elsewhere on the page."
    )

    if vector_stores:
        st.dataframe(
            vector_store_rows(vector_stores),
            use_container_width=True,
            hide_index=True,
        )

        selected_vector_store = st.selectbox(
            "Inspect a loaded vector store",
            options=vector_stores,
            format_func=vector_store_label,
            key="selected_vector_store",
        )
        selected_vector_store_id = getattr(selected_vector_store, "id", "")
        manual_vector_store_id = st.text_input(
            "Optional vector store ID override",
            key="manual_vector_store_id",
            placeholder=selected_vector_store_id,
        ).strip()
        effective_vector_store_id = manual_vector_store_id or selected_vector_store_id
        st.caption(f"Using vector store ID: `{effective_vector_store_id}`")

        if st.button("List files in this vector store", use_container_width=True):
            if not effective_vector_store_id:
                st.warning("Provide a vector store ID first.")
            else:
                try:
                    with st.spinner("Listing files in vector store..."):
                        st.session_state.vector_store_listing = {
                            "id": effective_vector_store_id,
                            "items": [
                                model_to_dict(item)
                                for item in vsu.list_files_in_vector_store_sync(effective_vector_store_id)
                            ],
                        }
                except Exception as exc:
                    st.error(f"Could not list files for `{effective_vector_store_id}`: {exc}")

        if st.session_state.vector_store_listing is not None:
            st.caption(
                f"Latest file listing for vector store `{st.session_state.vector_store_listing['id']}`"
            )
            st.json(st.session_state.vector_store_listing["items"])

        delete_vsid_phrase = f"DELETE {effective_vector_store_id}" if effective_vector_store_id else "DELETE <VSID>"
        typed_vsid_phrase = st.text_input(
            f"Type `{delete_vsid_phrase}` to delete this vector store",
            key="delete_vsid_phrase",
            placeholder=delete_vsid_phrase,
        )
        if st.button(
            "Delete vector store by ID",
            disabled=(not effective_vector_store_id) or typed_vsid_phrase != delete_vsid_phrase,
            use_container_width=True,
        ):
            try:
                vsu.delete_vector_store_sync(effective_vector_store_id)
                st.session_state.vss = [
                    vector_store
                    for vector_store in vector_stores
                    if getattr(vector_store, "id", "") != effective_vector_store_id
                ]
                st.session_state.vector_store_listing = None
            except Exception as exc:
                st.error(f"Could not delete `{effective_vector_store_id}`: {exc}")
            else:
                set_flash(f"Deleted vector store `{effective_vector_store_id}`.")
                st.rerun()

        distinct_names = sorted(
            {
                getattr(vector_store, "name", "") or "(no name)"
                for vector_store in vector_stores
            }
        )
        selected_name = st.selectbox(
            "Delete every loaded vector store with this name",
            options=distinct_names,
            key="delete_vector_store_name",
        )
        exempt_vsid = st.text_input(
            "Optional vector store ID to keep",
            key="keep_vector_store_id",
            placeholder="Paste an ID to exempt it from name-based deletion",
        ).strip()
        matching_by_name = [
            vector_store
            for vector_store in vector_stores
            if (getattr(vector_store, "name", "") or "(no name)") == selected_name
            and getattr(vector_store, "id", "") != exempt_vsid
        ]
        delete_name_phrase = f"DELETE {len(matching_by_name)} STORES NAMED {selected_name}"
        typed_delete_name_phrase = st.text_input(
            f"Type `{delete_name_phrase}` to confirm",
            key="delete_by_name_phrase",
            placeholder=delete_name_phrase,
        )
        if st.button(
            "Delete vector stores by name",
            disabled=typed_delete_name_phrase != delete_name_phrase,
            use_container_width=True,
        ):
            try:
                with st.spinner(f"Deleting {len(matching_by_name)} vector stores..."):
                    for vector_store in matching_by_name:
                        vsu.delete_vector_store_sync(vector_store.id)
                st.session_state.vss = [
                    vector_store
                    for vector_store in vector_stores
                    if vector_store not in matching_by_name
                ]
            except Exception as exc:
                st.error(f"Could not delete vector stores named `{selected_name}`: {exc}")
            else:
                set_flash(
                    f"Deleted {len(matching_by_name)} vector stores named `{selected_name}`."
                )
                st.rerun()

        delete_all_phrase = "DELETE ALL VECTOR STORES"
        typed_delete_all_phrase = st.text_input(
            f"Type `{delete_all_phrase}` to delete every loaded vector store",
            key="delete_all_vector_stores_phrase",
            placeholder=delete_all_phrase,
        )
        if st.button(
            "Delete all loaded vector stores",
            disabled=typed_delete_all_phrase != delete_all_phrase,
            use_container_width=True,
        ):
            try:
                with st.spinner(f"Deleting {len(vector_stores)} vector stores..."):
                    for vector_store in vector_stores:
                        vsu.delete_vector_store_sync(vector_store.id)
                st.session_state.vss = []
                st.session_state.vector_store_listing = None
            except Exception as exc:
                st.error(f"Could not delete all vector stores: {exc}")
            else:
                set_flash("Deleted all loaded vector stores.")
                st.rerun()

        delete_empty_phrase = "DELETE EMPTY VECTOR STORES"
        typed_delete_empty_phrase = st.text_input(
            f"Type `{delete_empty_phrase}` to remove every empty vector store",
            key="delete_empty_vector_stores_phrase",
            placeholder=delete_empty_phrase,
        )
        if st.button(
            "Delete empty vector stores",
            disabled=typed_delete_empty_phrase != delete_empty_phrase,
            use_container_width=True,
        ):
            try:
                with st.spinner("Deleting empty vector stores..."):
                    st.session_state.vss = vsu.delete_empty_vector_stores_sync()
                st.session_state.vector_store_listing = None
            except Exception as exc:
                st.error(f"Could not delete empty vector stores: {exc}")
            else:
                set_flash("Deleted empty vector stores and refreshed the cache.")
                st.rerun()
    else:
        st.info("Load vector stores to inspect them or perform cache-aware bulk actions.")


if selected_admin_section == "User Management":
    try:
        ensure_authdata_loaded()
    except Exception as exc:
        st.error(f"Could not load auth data: {exc}")
    else:
        auth_status_col1, auth_status_col2 = st.columns([1, 2])
        if st.session_state.auth_dirty:
            auth_status_col1.warning("Unsaved changes")
        else:
            auth_status_col1.success("Saved state")

        discard_unsaved = auth_status_col2.checkbox(
            "Allow reloading from disk and discarding unsaved user-management changes",
            key="discard_auth_changes",
            disabled=not st.session_state.auth_dirty,
        )

        auth_action_col1, auth_action_col2 = st.columns(2)
        if auth_action_col1.button("Save auth changes", disabled=not st.session_state.auth_dirty, use_container_width=True):
            try:
                atomic_write_yaml(CFG_PATH, st.session_state.authdata)
                st.session_state.auth_dirty = False
            except Exception as exc:
                st.error(f"Could not save auth data: {exc}")
            else:
                set_flash(f"Saved auth data to `{CFG_PATH}`.")
                st.rerun()

        if auth_action_col2.button(
            "Reload auth data from disk",
            disabled=st.session_state.auth_dirty and not discard_unsaved,
            use_container_width=True,
        ):
            try:
                ensure_authdata_loaded(force=True)
            except Exception as exc:
                st.error(f"Could not reload auth data: {exc}")
            else:
                set_flash("Reloaded auth data from disk.", kind="info")
                st.rerun()

        users = user_records()
        user_count = len(users)
        st.metric("Users", user_count)

        if not users:
            st.info("No users found in the auth configuration.")
        else:
            existing_tab, create_tab = st.tabs(["Existing users", "Create user"])

            with existing_tab:
                selected_user = st.selectbox(
                    "Select a user",
                    options=sorted(users.keys()),
                    key="selected_user",
                )
                selected_user_data = users[selected_user]

                detail_col1, detail_col2, detail_col3 = st.columns(3)
                detail_col1.write(f"**Role**: {selected_user_data.get('role', 'user')}")
                detail_col2.write(f"**Email**: {selected_user_data.get('email', selected_user)}")
                detail_col3.write(
                    f"**Failed logins**: {selected_user_data.get('failed_login_attempts', 0)}"
                )
                st.write(
                    f"**Caretaker of**: {', '.join(selected_user_data.get('caretaker', [])) or 'No languages assigned'}"
                )

                with st.form(f"caretaker_add_form_{selected_user}"):
                    languages_to_add = st.multiselect(
                        "Add caretaker assignments",
                        LANGUAGE_OPTIONS,
                        key=f"caretaker_add_{selected_user}",
                    )
                    add_caretaker_submitted = st.form_submit_button(
                        "Add selected languages",
                        use_container_width=True,
                    )
                if add_caretaker_submitted:
                    if not languages_to_add:
                        st.warning("Select at least one language to add.")
                    else:
                        current_caretakers = selected_user_data.get("caretaker", [])
                        selected_user_data["caretaker"] = normalize_caretakers(
                            current_caretakers + languages_to_add
                        )
                        st.session_state.auth_dirty = True
                        set_flash(f"Updated caretaker assignments for `{selected_user}`.")
                        st.rerun()

                clear_caretaker_phrase = f"CLEAR CARETAKER {selected_user}"
                with st.form(f"clear_caretaker_form_{selected_user}"):
                    typed_phrase = st.text_input(
                        f"Type `{clear_caretaker_phrase}` to remove all caretaker assignments",
                        placeholder=clear_caretaker_phrase,
                    )
                    clear_caretaker_submitted = st.form_submit_button(
                        "Clear caretaker assignments",
                        disabled=typed_phrase != clear_caretaker_phrase,
                        use_container_width=True,
                    )
                if clear_caretaker_submitted:
                    selected_user_data["caretaker"] = []
                    st.session_state.auth_dirty = True
                    set_flash(f"Cleared caretaker assignments for `{selected_user}`.")
                    st.rerun()

                reset_password_phrase = f"RESET PASSWORD {selected_user}"
                with st.form(f"reset_password_form_{selected_user}"):
                    st.caption(f"Resets the password to `{TEMP_PASSWORD}`.")
                    typed_phrase = st.text_input(
                        f"Type `{reset_password_phrase}`",
                        placeholder=reset_password_phrase,
                    )
                    reset_password_submitted = st.form_submit_button(
                        "Reset password",
                        disabled=typed_phrase != reset_password_phrase,
                        use_container_width=True,
                    )
                if reset_password_submitted:
                    selected_user_data["password"] = au.make_hash(TEMP_PASSWORD)
                    st.session_state.auth_dirty = True
                    set_flash(
                        f"Reset the password for `{selected_user}` to the temporary value `{TEMP_PASSWORD}`.",
                        kind="warning",
                    )
                    st.rerun()

                delete_user_phrase = f"DELETE USER {selected_user}"
                with st.form(f"delete_user_form_{selected_user}"):
                    if selected_user == username:
                        st.warning("You are about to delete the currently signed-in admin account.")
                    typed_phrase = st.text_input(
                        f"Type `{delete_user_phrase}` to delete this account",
                        placeholder=delete_user_phrase,
                    )
                    delete_user_submitted = st.form_submit_button(
                        "Delete user",
                        disabled=typed_phrase != delete_user_phrase,
                        use_container_width=True,
                    )
                if delete_user_submitted:
                    admin_users = [
                        user_name
                        for user_name, data in users.items()
                        if data.get("role", "user") == "admin"
                    ]
                    if selected_user_data.get("role", "user") == "admin" and len(admin_users) <= 1:
                        st.error("Refusing to delete the last admin account.")
                    else:
                        del users[selected_user]
                        st.session_state.auth_dirty = True
                        set_flash(f"Deleted user `{selected_user}`.")
                        st.rerun()

            with create_tab:
                with st.form("create_user_form"):
                    st.caption(
                        f"New users are created with role `user` and temporary password `{TEMP_PASSWORD}`."
                    )
                    new_username = st.text_input("Email / username")
                    new_name = st.text_input("Display name")
                    new_caretakers = st.multiselect(
                        "Caretaker assignments",
                        LANGUAGE_OPTIONS,
                    )
                    create_user_submitted = st.form_submit_button(
                        "Create user",
                        type="primary",
                        use_container_width=True,
                    )
                if create_user_submitted:
                    normalized_username = new_username.strip().lower()
                    normalized_name = new_name.strip()
                    if not normalized_username:
                        st.error("Email / username is required.")
                    elif not is_valid_email(normalized_username):
                        st.error("Enter a valid email address for the new user.")
                    elif normalized_username in users:
                        st.error("A user with that email already exists.")
                    elif not normalized_name:
                        st.error("Display name is required.")
                    else:
                        users[normalized_username] = {
                            "name": normalized_name,
                            "email": normalized_username,
                            "password": au.make_hash(TEMP_PASSWORD),
                            "role": "user",
                            "caretaker": normalize_caretakers(new_caretakers),
                            "failed_login_attempts": 0,
                        }
                        st.session_state.auth_dirty = True
                        set_flash(f"Created user `{normalized_username}`.")
                        st.rerun()


if selected_admin_section == "Grammar Seeds":
    try:
        grammar_seeds = load_json_file(GRAMMAR_SEEDS_PATH)
    except Exception as exc:
        st.error(f"Could not load grammar seeds: {exc}")
    else:
        st.metric("Seed topics", len(grammar_seeds))
        if grammar_seeds:
            selected_seed = st.selectbox(
                "Select a topic to edit",
                options=sorted(grammar_seeds.keys()),
                key="selected_grammar_seed",
            )

            with st.form(f"edit_seed_form_{selected_seed}"):
                edited_seed = st.text_area(
                    "Seed guidance",
                    value=grammar_seeds[selected_seed].get("guidance", ""),
                    height=280,
                )
                save_seed_submitted = st.form_submit_button(
                    "Save edited seed",
                    type="primary",
                    use_container_width=True,
                )
            if save_seed_submitted:
                if not edited_seed.strip():
                    st.error("Seed guidance cannot be empty.")
                else:
                    grammar_seeds[selected_seed]["guidance"] = edited_seed
                    atomic_write_json(GRAMMAR_SEEDS_PATH, grammar_seeds)
                    set_flash(f"Saved grammar seed `{selected_seed}`.")
                    st.rerun()
        else:
            st.info("No grammar seed topics exist yet. Use the form below to create the first one.")

        st.divider()
        with st.form("create_seed_form"):
            new_topic = st.text_input("New topic")
            new_topic_seed = st.text_area("New seed guidance", height=220)
            overwrite_existing_topic = st.checkbox("Overwrite if the topic already exists")
            create_seed_submitted = st.form_submit_button(
                "Create topic",
                use_container_width=True,
            )
        if create_seed_submitted:
            normalized_topic = new_topic.strip()
            if not normalized_topic:
                st.error("Topic is required.")
            elif not new_topic_seed.strip():
                st.error("Seed guidance cannot be empty.")
            elif normalized_topic in grammar_seeds and not overwrite_existing_topic:
                st.warning("That topic already exists. Enable overwrite to replace it.")
            else:
                grammar_seeds[normalized_topic] = {"guidance": new_topic_seed}
                atomic_write_json(GRAMMAR_SEEDS_PATH, grammar_seeds)
                set_flash(f"Saved grammar seed topic `{normalized_topic}`.")
                st.rerun()
