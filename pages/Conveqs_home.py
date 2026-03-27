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
import time
from io import BytesIO

import pandas
import streamlit as st
import os
import json
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import tempfile
from libs import utils as u
from datetime import datetime
import pandas as pd
from streamlit_folium import st_folium
import folium
from libs import conveqs_utils as cu
from folium import DivIcon
from collections import defaultdict
import math

# TODO: Save alert / Autosave
# TODO: Explain the difference between the original file and the local file.

st.set_page_config(
    page_title="ConveQs",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage")

if "upload_language" not in st.session_state:
    if "indi_language" in st.session_state:
        st.session_state.upload_language = st.session_state.indi_language
    else:
        st.session_state.upload_language = "Abkhaz-Adyge"
if "indi_glottocode" not in st.session_state:
    st.session_state["indi_glottocode"] = "abkh1242"
if "is_guest" not in st.session_state:
    st.session_state.is_guest = None

if "use" not in st.session_state:
    st.session_state.use = "consult"
if "new_cq_counter" not in st.session_state:
    st.session_state.new_cq_counter = 0

if "uid_dict" not in st.session_state:
    with open("./uid_dict.json", "r") as uid:
        st.session_state.uid_dict = json.load(uid)
if "ccq" not in st.session_state:
    with open("./conveqs/canonical_cqs.json", "r") as f:
        st.session_state.ccq = json.load(f)
if "languages" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, "languages.json"), "r") as lf:
        st.session_state.languages = json.load(lf)
if "llist" not in st.session_state:
    with open(os.path.join(BASE_LD_PATH, "languages.json"), "r") as llf:
        gll = json.load(llf)
        st.session_state.llist = sorted(gll.keys())
if "picked_location" not in st.session_state:
    st.session_state.picked_location = {"lat": 0, "lng": 200}
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 2
if "delete_file" not in st.session_state:
    st.session_state.delete_file = False
if "compare_disp_df" not in st.session_state:
    st.session_state.compare_disp_df = None
if "compare_column_order" not in st.session_state:
    st.session_state.compare_column_order = None
if "compare_export_name" not in st.session_state:
    st.session_state.compare_export_name = "cq_comparison"

CONVEQS_BASE_PATH = os.path.join(BASE_LD_PATH, "conveqs")

# ------ AUTH SETUP --------------------------------------------------------------------------------
CFG_PATH = Path(
    os.getenv("AUTH_CONFIG_PATH") or
    os.path.join(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"), "storage", "auth_config.yaml")
)
# Cookie secret (override YAML)
COOKIE_KEY = os.getenv("AUTH_COOKIE_KEY", None)


# ---------- Load config ----------
def load_config(path: Path) -> dict:
    if not path.exists():
        print("load auth config failed, no config file")
        st.stop()  # fail fast; create it before running
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if COOKIE_KEY:
        cfg.setdefault("cookie", {})["key"] = COOKIE_KEY
    return cfg


# --- helper: atomic YAML write ---
def save_config_atomic(data: dict, path: Path):
    d = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=d, encoding="utf-8") as tmp:
        yaml.safe_dump(data, tmp, sort_keys=False, allow_unicode=True)
        tmp_path = tmp.name
    os.replace(tmp_path, path)  # atomic on POSIX


def dataframe_to_excel_bytes(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Comparison")
    output.seek(0)
    return output.getvalue()


cfg = load_config(CFG_PATH)
authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"],
    auto_hash=True
)
# -------------------------------------------------------------------------------------------

with st.sidebar:
    st.image("./pics/conveqs_banner.png")
    # st.divider()
    # st.page_link("pages/Conveqs_home.py", label="ConveQs Home", icon=":material/home:")
    # st.divider()

# AUTH UI AND FLOW -----------------------------------------------------------------------
if st.session_state["username"] is None:
    if st.button("Use without logging in"):
        st.session_state.is_guest = True
# ---------- Guest path: skip rendering the login widget entirely ----------
if st.session_state.is_guest:
    st.session_state["authentication_status"] = True
    st.session_state["username"] = "guest"
    st.session_state["name"] = "Guest"
else:
    authenticator.login(
        location="main",  # "main" | "sidebar" | "unrendered"
        max_concurrent_users=20,  # soft cap; useful for small apps
        max_login_attempts=5,  # lockout window is managed internally
        fields={  # optional label overrides
            "Form name": "Sign in",
            "Username": "email",
            "Password": "Password",
            "Login": "Sign in",
        },
        captcha=False,  # simple built-in captcha
        single_session=True,  # block multiple sessions per user
        clear_on_submit=True,
        key="login_form_v1",  # avoid WidgetID collisions
    )

auth_status = st.session_state.get("authentication_status", None)
name = st.session_state.get("name", None)
username = st.session_state.get("username", None)

if auth_status:
    role = cfg["credentials"]["usernames"].get(username, {}).get("role", "guest")
    if st.session_state.upload_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker", []):
        role = "caretaker"
    title = ""
    if role in ["admin", "caretaker"]:
        title = role
    st.sidebar.success(f"Hello, {title} {name or username}")
    if st.session_state.is_guest:
        if st.sidebar.button("Logout", key="guest_logout"):
            for x in ("is_guest", "authentication_status", "username", "name"):
                st.session_state.pop(x, None)
            st.rerun()
    else:
        if st.sidebar.checkbox("Change password"):
            with st.sidebar:
                st.markdown("""Passwords must 
                - Be between 8 and 20 characters long, 
                - Contain at least one digit,
                - Contain at least one uppercase letter,
                - Contain at least one special character (@$!%*?&)""")
            authenticator.reset_password(username, location="sidebar")
            save_config_atomic(cfg, CFG_PATH)  # <-- persist the updated hash
            st.success("Password updated.")
        authenticator.logout(button_name="Logout", location="sidebar", key="auth_logout")

elif auth_status is False:
    role = None
    st.error("Invalid credentials")
    st.write("Try again. If you have forgotten your password, contact sebastien.christian@upf.pf")
    st.stop()

else:
    role = None
    st.info("Please log in or click on the 'Use without logging in' button")


# ========================== HELPERS ===================================================

def normalize_lng(lng: float) -> float:
    """
    Normalize longitude to [-180, 180).
    Examples:
        210.5859375 -> -149.4140625
        -190 -> 170
        360 -> 0
    """
    return ((lng + 180) % 360) - 180

def mean_lat_lng(coords):
    """
    coords: list of (lat, lng)
    Returns:
        mean latitude
        circular mean longitude
    """
    mean_lat = sum(lat for lat, lng in coords) / len(coords)

    x = sum(math.cos(math.radians(normalize_lng(lng))) for lat, lng in coords)
    y = sum(math.sin(math.radians(normalize_lng(lng))) for lat, lng in coords)

    mean_lng = math.degrees(math.atan2(y, x))
    mean_lng = normalize_lng(mean_lng)

    return mean_lat, mean_lng

def representative_point(cq_list):
    """
    Return the real CQ location closest to the centroid.
    """
    coords = [
        (
            float(cq["collection_location"]["lat"]),
            normalize_lng(float(cq["collection_location"]["lng"]))
        )
        for cq in cq_list
    ]

    centroid_lat, centroid_lng = mean_lat_lng(coords)

    def sqdist(a, b):
        lat1, lng1 = a
        lat2, lng2 = b
        return (lat1 - lat2) ** 2 + (lng1 - lng2) ** 2

    return min(coords, key=lambda p: sqdist(p, (centroid_lat, centroid_lng)))

def show_cq_map(cqs):
    # Keep only CQs with valid coordinates and a language
    valid_cqs = [
        cq for cq in cqs
        if cq.get("collection_location")
           and cq["collection_location"].get("lat") is not None
           and cq["collection_location"].get("lng") is not None
           and cq.get("language")
    ]
    if role == "admin" and valid_cqs and st.checkbox("Show displayed coordinates"):
        for cq in valid_cqs:
            lat = cq["collection_location"]["lat"]
            lng = cq["collection_location"]["lng"]
            st.write(
                "MARKER INPUT",
                cq.get("filename"),
                type(lat), repr(lat),
                type(lng), repr(lng),
            )

    if not valid_cqs:
        st.info("No CQ with both a valid collection_location and a language.")
        return

    # Session state
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = None

    if "selected_cq_in_language" not in st.session_state:
        st.session_state.selected_cq_in_language = 0

    # Group CQs by language
    grouped_cqs = defaultdict(list)
    for cq in valid_cqs:
        grouped_cqs[cq["language"]].append(cq)

    # Build language groups with representative marker locations
    language_groups = []
    for language, cq_list in grouped_cqs.items():
        clean_cqs = []
        for cq in cq_list:
            loc = cq.get("collection_location", {})
            if loc.get("lat") is None or loc.get("lng") is None:
                continue

            cq_copy = dict(cq)
            cq_copy["collection_location"] = {
                "lat": float(loc["lat"]),
                "lng": normalize_lng(float(loc["lng"]))
            }
            clean_cqs.append(cq_copy)

        if not clean_cqs:
            continue

        marker_lat, marker_lng = representative_point(clean_cqs)

        language_groups.append({
            "language": language,
            "center": (marker_lat, marker_lng),
            "cqs": clean_cqs,
        })

    # Sort for stable display / stable indexing
    language_groups.sort(key=lambda g: g["language"].lower())

    m = folium.Map(location=[0, -150], zoom_start=3)
    if language_groups:
        bounds = [group["center"] for group in language_groups]
        m.fit_bounds(bounds, padding=(30, 30))

    # Add one marker per language
    for i, group in enumerate(language_groups):
        lat, lng = group["center"]
        language = group["language"]
        cq_list = group["cqs"]
        count = len(cq_list)

        if count == 1:
            hover_text = f"{language} — 1 CQ"
        else:
            hover_text = f"{language} — {count} CQs"

        # Internal id via tooltip hack
        tooltip = f"{i}|{hover_text}"

        html = f"""
        <div style="position: relative; width: 32px; height: 42px;">
            <div style="
                position: absolute;
                left: 50%;
                top: 100%;
                transform: translate(-50%, -100%);
                font-size: 20px;
                line-height: 20px;
            ">⭕</div>
            <div style="
                position: absolute;
                right: -4px;
                top: 16px;
                min-width: 18px;
                height: 18px;
                padding: 0 4px;
                border-radius: 9px;
                background: #b22222;
                color: white;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
                line-height: 18px;
                border: 1px solid white;
            ">{count}</div>
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            tooltip=tooltip,
            icon=DivIcon(html=html),
        ).add_to(m)

    map_data = st_folium(
        m,
        height=500,
        use_container_width=True,
        returned_objects=["last_object_clicked_tooltip"],
        key="cq_map_by_language",
    )

    clicked_tooltip = map_data.get("last_object_clicked_tooltip")
    if clicked_tooltip:
        try:
            group_idx = int(clicked_tooltip.split("|", 1)[0])
            clicked_language = language_groups[group_idx]["language"]

            if st.session_state.selected_language != clicked_language:
                st.session_state.selected_language = clicked_language
                st.session_state.selected_cq_in_language = 0

        except (ValueError, IndexError):
            st.warning(f"Could not parse clicked tooltip: {clicked_tooltip}")

    selected_language = st.session_state.selected_language
    if selected_language is None:
        st.info("Click a language marker to view available CQs.")
        return

    cq_list = grouped_cqs[selected_language]

    st.markdown(f"### {selected_language}")

    if len(cq_list) > 1:
        labels = [
            cq.get("title", "Untitled CQ")
            for cq in cq_list
        ]

        st.session_state.selected_cq_in_language = st.selectbox(
            "Select a CQ",
            options=range(len(cq_list)),
            index=st.session_state.selected_cq_in_language,
            format_func=lambda i: labels[i],
            key="cq_selector_for_language",
        )

    selected_cq = cq_list[st.session_state.selected_cq_in_language]

    title = selected_cq.get("title", "Untitled CQ")
    language = selected_cq.get("language", "Unknown language")

    st.subheader(f"{title} in {language}")

    filepath = os.path.join(
        CONVEQS_BASE_PATH,
        "transposed_files",
        selected_cq["filename"],
    )

    try:
        with open(filepath, "r", encoding="utf-8") as ccf:
            data = json.load(ccf)["data"]
        if data["1"]["lingua franca"] == "":
            df_col = ["index", "cq", "translation"]
        else:
            df_col = ["index", "cq", "lingua franca", "translation"]
        data_df = pd.DataFrame(data).T
        st.dataframe(data_df, use_container_width=True, hide_index=True, column_order=df_col)

    except FileNotFoundError:
        st.error(f"File not found: {selected_cq['filename']}")
    except KeyError:
        st.error(f"Missing 'data' key in file: {selected_cq['filename']}")


# =========================== LOGIC AND UI =============================================
with st.sidebar:
    st.markdown(
        "You can automate the transposition to the ConveQs common format by using the Excel templates!")
    with open("./conveqs/conveqs_cq_templates.zip", "rb") as file:
        file_data = file.read()
    st.download_button(label="Download CQ templates",
                       data=file_data,
                       mime="application/zip",
                       icon="📁",
                       file_name="conveqs_cq_template.zip")

cole1, cole2 = st.columns(2)
with cole1:
    with st.popover("What are Conversational Questionnaires?"):
        st.markdown("#### An introduction to Conversational Questionnaires")
        st.markdown(
            "Conversational Questionnaires (CQ) are a linguistic data collection method. The method consists in eliciting speech not at the level of words or of isolated sentences, but in the form of a chunk of dialogue. Ahead of fieldwork, a number of scripted conversations are written in the area’s lingua franca, each anchored in a plausible real-world situation – whether universal or culture-specific. Native speakers are then asked to come up with the most naturalistic utterances that would occur in each context, resulting in a plausible conversation in the target language. Experience shows that conversational questionnaires provide a number of advantages in linguistic fieldwork, compared to traditional elicitation methods. The anchoring in real-life situations lightens the cognitive burden on consultants, making the fieldwork experience easier for all. The method enables efficient coverage of various linguistic structures at once, from phonetic to pragmatic dimensions, from morphosyntax to phraseology. The tight-knit structure of each dialogue makes it an effective tool for cross-linguistic comparison, whether areal, historical or typological. Conversational questionnaires help the linguist make quick progress in language proficiency, which in turn facilitates further stages of data collection. Finally, these stories can serve as learning resources for language teaching and revitalization.")
        st.markdown(
            "Reference: François, Alexandre. 2019. A proposal for conversa­tional ques­tionnaires. In Lahaussois, Aimée & Vuillermet, Marine (eds.), Methodological Tools for Linguistic Description and Typology, Language Documentation & Conservation Special Publication No. 16. Honolulu: University of Hawai'i Press.")
        st.markdown("https://scholarspace.manoa.hawaii.edu/items/ef98c1c0-bee6-4ac9-9ea0-0543594ce3b3")
with cole2:
    with st.popover("What is ConveQs?"):
        st.markdown("#### ConveQs")
        st.markdown("""
        ConveQs, the system you are accessing through this website, is designed for the storage, consultation, and sharing of Conversational Questionnaires (CQs).
        - As a registered user you can upload files containing CQs in any format, for your languages of expertise.These files are archived and you can at any time download and delete them. 
        - The files are then processed to be transposed to the ConveQs Common Format. 
        - Once transposed, all ConveQs users, registered or not, can consult and compare CQ translations in all available languages.
        """)
        st.markdown("""
        All documents on this platform follow a [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) licence.
        The software itself is [open source](https://github.com/alterfero/dig4el), under a [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.en.html).
        """)
        st.markdown("""ConveQs and DIG4EL are research efforts supported by the [CNRS](https://www.cnrs.fr/en) as part 
        of the [Heliceo](https://www.cnrs.fr/en/ri2-project/heliceo) project.""")

st.markdown("""
<style>
/* TAB BAR CONTAINER */
div[data-testid="stTabs"] {
  background: #f3f4f6;
  padding: 0.35rem 0.5rem;
  border-radius: 10px;
}

/* TAB LIST */
div[data-testid="stTabs"] [role="tablist"] {
  gap: 0.35rem;
}

/* INDIVIDUAL TABS */
div[data-testid="stTabs"] button[role="tab"] {
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  border: 1px solid transparent;
  color: #6b7280;
  font-weight: 500;
}

/* HOVER */
div[data-testid="stTabs"] button[role="tab"]:hover {
  background: #e5e7eb;
  color: #111827;
}

/* ACTIVE TAB */
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: #111827;
  color: white;
  border-color: #111827;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍Explore", "⬆️Upload", "📂My files"])

# ========== MY FILES ==========================
with tab3:
    st.markdown("""#### My files""")
    if role == "guest":
        st.markdown("Guest users cannot upload files. Contact us to become a registered user !")
    else:
        with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
            conveqs_index = json.load(f)
        user_files = [item for item in conveqs_index if item["username"] == username]
        if user_files == []:
            st.markdown("*You have'nt uploaded any file yet.*")
        else:
            conveqs_index_df = pd.DataFrame(user_files)

            selected = st.dataframe(conveqs_index_df.style.hide(axis="index"),
                                    column_order=["language", "original_filename", "date"],
                                    hide_index=True, selection_mode="single-cell", on_select="rerun")

            if selected["selection"]["cells"] != []:
                selected_row = selected["selection"]["cells"][0][0]
                selected_item = user_files[selected_row]
                st.markdown("Uploaded on {}".format(
                    selected_item["date"]))
                col1, col2, col3 = st.columns([1, 1, 5])

                with open(os.path.join(CONVEQS_BASE_PATH, "original_files", selected_item["actual_filename"]),
                          "rb") as f:
                    data = f.read()
                col1.download_button("Download", data, file_name=selected_item["original_filename"])

                if col2.button("Delete"):
                    st.session_state.delete_file = True
                if st.session_state.delete_file:
                    st.markdown(
                        "Deleting your file will also delete any version of your content transposed to the ConveQs common format")
                    if st.button("Confirm deletion"):
                        # delete transposed
                        transposed = selected_item["transposed_as"]
                        for tfn in transposed:
                            try:
                                os.remove(os.path.join(CONVEQS_BASE_PATH, "transposed_files", tfn))
                            except FileNotFoundError:
                                print("Can't find {} to delete".format(tfn))
                        # delete original file
                        try:
                            os.remove(
                                os.path.join(CONVEQS_BASE_PATH, "original_files", selected_item["actual_filename"]))
                        except FileNotFoundError:
                            print("{} does not exist".format(selected_item["filename"]))
                        # delete index entry
                        del conveqs_index[selected_row]
                        with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w") as ci:
                            u.save_json_normalized(conveqs_index, ci, indent=4)
                        st.session_state.delete_file = False
                        st.rerun()

# ========== UPLOAD FILES ============================
with (tab2):
    st.markdown("### Upload CQ translations in any format.")
    if role == "guest":
        st.markdown("*Guests cannot upload or manage Conversational Questionnaires.*")
        st.markdown("*If you have Conversational Questionnaires to upload, contact us to become a registered user!*")
    else:
        co1, co2 = st.columns(2, gap="large", border=True)
        co1.markdown("""You can upload CQ translations **in any format**. 
        As the uploader of the files, you will be able to download and delete them at any time in the future. 
        The files you upload require to be transposed in a format allowing 
        the CQs to be consulted and compared: Allow some time for your files to be transposed
        or use the Excel templates for an automated transposition. 
        """)
        with co2:
            st.markdown(
                "You can utomate the transposition to the ConveQs common format by using the Excel templates below.")
            with open("./conveqs/conveqs_cq_templates.zip", "rb") as file:
                file_data = file.read()
            st.download_button(label="Download CQ templates",
                               data=file_data,
                               mime="application/zip",
                               icon="📁",
                               file_name="conveqs_cq_template.zip")
        # SELECT LANGUAGE
        colq, colw = st.columns(2)

        coli1, coli2 = st.columns(2)
        selected_language_from_list = coli1.selectbox("Select the language you are working on in the list below",
                                                      st.session_state.llist)
        free_language_input = coli2.text_input("If not in the list, enter the language name here and press Enter.")
        if free_language_input != "":
            if free_language_input.capitalize() in st.session_state.llist:
                st.warning("This language is already in the list! It is now selected.")
                selected_language = free_language_input.capitalize()
            else:
                selected_language = free_language_input.capitalize()
                if st.button("Create new language {}?".format(free_language_input)):
                    selected_language = free_language_input.capitalize()
                    os.makedirs(os.path.join(CONVEQS_BASE_PATH, "original_files"), exist_ok=True)
                    st.success("Adding {} to the list of languages.".format(free_language_input))
                    st.markdown("Note that a pseudo-glottocode is added: {}".format(free_language_input.lower() + "+"))
                    with open(os.path.join(BASE_LD_PATH, "languages.json"), "r") as fg:
                        language_list_json = json.load(fg)
                    language_list_json[free_language_input.capitalize()] = free_language_input + "+"
                    st.session_state.languages = language_list_json
                    st.session_state.llist = list(language_list_json.keys())
                    with open(os.path.join(BASE_LD_PATH, "languages.json"), "w") as fgg:
                        json.dump(language_list_json, fgg, indent=4)
        else:
            selected_language = selected_language_from_list

        if selected_language != st.session_state.upload_language:
            st.session_state.upload_language = selected_language
            st.session_state.indi_glottocode = st.session_state.languages.get(st.session_state.upload_language,
                                                                              "glottocode not found")

        if role in ["admin", "user"]:

            with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json")) as ci:
                conveqs_index = json.load(ci)

            # FILE UPLOAD FORM

            sub_ready = False
            valid = False
            new_cq = st.file_uploader(
                "Add a new CQ translation file in {} to the repository".format(st.session_state.upload_language),
                accept_multiple_files=False,
                key="new_cq" + str(st.session_state.new_cq_counter)
            )
            name = st.text_input("Which CQ(s) does your document contain?")
            collection_date = st.date_input("Collection date (last day if multiple)")

            collection_location = st.text_input(
                "Collection location: Enter the name of the location in the text box and click on the map.")
            # collection_coordinates with map =================================================================
            m = folium.Map(
                location=[
                    st.session_state.picked_location["lat"],
                    st.session_state.picked_location["lng"],
                ],
                zoom_start=st.session_state.map_zoom,
            )

            if st.session_state.picked_location["lng"] != 200:
                folium.Marker(
                    [
                        st.session_state.picked_location["lat"],
                        st.session_state.picked_location["lng"],
                    ],
                    tooltip="Current selection",
                ).add_to(m)

            map_data = st_folium(m, height=450,
                                 width="100%")

            # Capture click
            if map_data and map_data.get("last_clicked"):
                st.session_state.picked_location = {
                    "lat": map_data["last_clicked"]["lat"],
                    "lng": normalize_lng(map_data["last_clicked"]["lng"]),
                }
                st.session_state.map_zoom = map_data["zoom"]
                st.rerun()
            # =================================================================
            st.write("picked location: {}".format(st.session_state.picked_location))
            informant = st.text_input("Collected from (speaker(s) full name(s))")
            field_worker = st.text_input("Collected by (language documenter's full name)")
            visibility = "Everyone"
            consent_received = st.checkbox(
                "**I have recorded the consent of the {} speaker(s)**".format(st.session_state.upload_language))

            st.markdown("""
                                        Reminder: Uploading a document engages your responsibility. 
                                        Any portion of this document can be made available for display and download to any visitor of the ConveQs and DIG4EL websites
                                        with a [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) licence. 
                                        Make sure you have the proper rights to allow it.
                                        """)

            if st.button("Confirm and upload"):
                if not new_cq:
                    st.warning("Upload a file before submitting!")
                else:
                    if consent_received:
                        file_record_name = ":".join(str(time.time()).split(".")) + "_" + new_cq.name
                        with open(os.path.join(CONVEQS_BASE_PATH, "original_files", file_record_name), "wb") as f:
                            f.write(new_cq.read())
                        st.success(f"Your file `{new_cq.name}` has been uploade to the server.")

                        # AUTO TRANSPOSITION TEST IF XLS
                        if ".xls" in new_cq.name:
                            transposed, message = cu.conveqs_cq_translation_from_transcription_xlsx(new_cq)
                            if transposed is not None:
                                addict = {
                                    "name": name,
                                    "language": st.session_state.upload_language,
                                    "collection_date": collection_date.strftime("%Y-%m-%d"),
                                    "collection_location": st.session_state.picked_location,
                                    "speaker": informant,
                                    "language documenter": field_worker,
                                    "consent": consent_received,
                                    "uploaded by": username
                                }
                                mergedict = transposed | addict

                                fn = "?title:" + transposed["title"][
                                                 :4] + "?language:" + st.session_state.upload_language + "?uid:" + \
                                     transposed["recording_uid"] + ".json"

                                with open(os.path.join(CONVEQS_BASE_PATH, "transposed_files", fn), "w") as tf:
                                    u.save_json_normalized(mergedict, tf)

                                st.success(
                                    "Your file has been successfully transposed to the ConveQs common format and is available for consultation and comparison.")
                        else:
                            transposed = None

                        # Adding/editing to conveqs_index
                        now = datetime.now()
                        readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")
                        recorded_location = {
                            "lat": st.session_state.picked_location["lat"],
                            "lng": normalize_lng(st.session_state.picked_location["lng"])
                        }
                        conveqs_index.append(
                            {
                                "username": username,
                                "original_filename": new_cq.name,
                                "actual_filename": file_record_name,
                                "id": username + "_" + str(time.time()),
                                "name": name,
                                "language": st.session_state.upload_language,
                                "collection_date": collection_date.strftime("%Y-%m-%d"),
                                "collection_location": recorded_location,
                                "speaker": informant,
                                "language documenter": field_worker,
                                "consent": consent_received,
                                "uploaded by": username,
                                "date": readable_date_time,
                                "transposed_as": [] if transposed is None else [fn]
                            }
                        )
                        with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w",
                                  encoding='utf-8') as f:
                            u.save_json_normalized(conveqs_index, f, indent=4)

                        st.markdown(
                            "To upload another file, just click on the button below, change the document, edit fields and press submit again.")
                        st.markdown(
                            "Note that uploading the same file creates separate copies. You can manage your files in the *My Files* tab")
                        if st.button("Close this upload session"):
                            st.rerun()

                    else:
                        st.markdown("You must receive and record the consent of the speaker(s) to upload a document.")
        if role == "admin":
            with st.expander("ADMIN: Check index"):
                with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
                    st.write(json.load(f))

# ========== EXPLORE CQs =============================
os.makedirs(os.path.join(CONVEQS_BASE_PATH, "original_files"), exist_ok=True)
os.makedirs(os.path.join(CONVEQS_BASE_PATH, "transposed_files"), exist_ok=True)

with tab1:
    st.markdown("""
                #### Consult and compare CQ translations
                """)
    transposed_cq_catalog = cu.catalog_transposed_conveqs_cqs()
    if transposed_cq_catalog == []:
        st.markdown("*No CQ transposed to the ConveQs common file format yet.*")
    else:
        show_cq_map(transposed_cq_catalog)

    st.divider()

    st.markdown("#### Compare CQs")
    selected_title = st.selectbox("Select a CQ", st.session_state.ccq.keys())
    available_languages = list(set([c["language"] for c in transposed_cq_catalog if c["title"] == selected_title]))
    st.markdown("{} languages available for this CQ".format(len(available_languages)))
    selected_languages = st.multiselect("Select the languages to compare", available_languages)
    if st.button("Compare"):
        c_to_display = [c for c in transposed_cq_catalog
                     if c["title"] == selected_title and c["language"] in selected_languages]
        display_dict = {}
        for item in c_to_display:
            with open(os.path.join(CONVEQS_BASE_PATH, "transposed_files", item["filename"]), "r") as f:
                tfd = json.load(f)
            display_dict[item["language"]] = [tfd["data"][k]["translation"] for k in tfd["data"].keys()]
            display_dict["English"] = [tfd["data"][k]["cq"] for k in tfd["data"].keys()]
            display_dict["Index"] = [tfd["data"][k]["index"] for k in tfd["data"].keys()]
        st.session_state.compare_disp_df = pd.DataFrame(display_dict)
        st.session_state.compare_column_order = ["Index", "English"] + selected_languages
        st.session_state.compare_export_name = selected_title.replace(" ", "_").replace("/", "_").replace(".", "_")

    if st.session_state.compare_disp_df is not None:
        disp_df = st.session_state.compare_disp_df
        column_order = st.session_state.compare_column_order
        st.dataframe(disp_df, hide_index=True, column_order=column_order)
        st.download_button(
            "Download as Excel",
            data=dataframe_to_excel_bytes(disp_df[column_order]),
            file_name=f"{st.session_state.compare_export_name}_comparison.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click="ignore",
        )

