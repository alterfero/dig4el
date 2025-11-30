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



import streamlit as st
import os
import json
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import tempfile
from libs import glottolog_utils as gu
from libs import file_manager_utils as fmu
from libs import utils as u
from libs import display_utils as du
from libs import knowledge_graph_utils as kgu
from libs import stats
from libs import output_generation_utils as ogu
from datetime import datetime
import pandas as pd
import plotly.express as px
from pyvis.network import Network


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

if "indi_path_check" not in st.session_state:
    st.session_state.indi_path_check = False
if "upload_language" not in st.session_state:
    st.session_state.upload_language = "Abkhaz-Adyge"
if "indi_glottocode" not in st.session_state:
    st.session_state["indi_glottocode"] = "abkh1242"
if "is_guest" not in st.session_state:
    st.session_state.is_guest = None
if "caretaker_of" not in st.session_state:
    st.session_state.caretaker_of = []
if "caretaker_trigger" not in st.session_state:
    st.session_state.caretaker_trigger = False
if "use" not in st.session_state:
    st.session_state.use = "consult"
if "new_cq_counter" not in st.session_state:
    st.session_state.new_cq_counter = 0
if "knowledge_graph" not in st.session_state:
    st.session_state.knowledge_graph = {}
if "cq_transcriptions" not in st.session_state:
    st.session_state.cq_transcriptions = []
if "active_language" not in st.session_state:
    st.session_state.active_language = None
if "delimiters" not in st.session_state:
    st.session_state.delimiters = None
if "selected_concept" not in st.session_state:
    st.session_state["selected_concept"] = ""
if "pdict" not in st.session_state:
    st.session_state["pdict"] = {}
if "pfilter" not in st.session_state:
    st.session_state["pfilter"] = {"intent": [], "enunciation": [], "predicate": {}, "ip": {}, "rp": []}
if "cdict" not in st.session_state:
    st.session_state["cdict"] = {}
if "concept_graph" not in st.session_state:
    with open("./data/concepts.json", "r", encoding='utf-8') as f:
        st.session_state["cg"] = json.load(f)

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

cfg = load_config(CFG_PATH)
authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"],
    auto_hash=True
)
# -------------------------------------------------------------------------------------------
st.image("./pics/conveqs_banner.png")
with st.sidebar:
    st.divider()
    st.page_link("pages/Conveqs_home.py", label="ConveQs Home", icon=":material/home:")
    st.divider()

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
        location="main",                 # "main" | "sidebar" | "unrendered"
        max_concurrent_users=20,         # soft cap; useful for small apps
        max_login_attempts=5,            # lockout window is managed internally
        fields={                         # optional label overrides
            "Form name": "Sign in",
            "Username": "email",
            "Password": "Password",
            "Login": "Sign in",
        },
        captcha=False,                    # simple built-in captcha
        single_session=True,             # block multiple sessions per user
        clear_on_submit=True,
        key="login_form_v1",             # avoid WidgetID collisions
    )

auth_status = st.session_state.get("authentication_status", None)
name        = st.session_state.get("name", None)
username    = st.session_state.get("username", None)

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
    st.info("Please log in or click on the 'Use without loging in' button")


# =========================== LOGIC AND UI =============================================

tab1, tab2, tab3 = st.tabs(["Browse CQ files", "Upload CQ file", "Explore CQs"])

# ========== EXPLORE CQs =============================
with tab1:
    st.subheader("Explore available Conversational Questionnaires")
    cq_catalog = u.catalog_all_available_cqs()
    n_language = len(set([lu["language"] for lu in cq_catalog]))
    st.markdown("{} CQs available, across {} languages.".format(len(cq_catalog), n_language))
    cq_catalog_df = pd.DataFrame(cq_catalog).sort_values(by="title")
    selected_rows = st.dataframe(cq_catalog_df, hide_index=True, column_order=["title", "language", "pivot", "index"],
                                 selection_mode="multi-row", on_select="rerun")
    selected_cqs_indexes_in_displayed_df = selected_rows["selection"]["rows"]
    selected_cqs_indexes_in_catalog = [cq_catalog_df.iloc[i]["index"] - 1 for i in selected_cqs_indexes_in_displayed_df]
    # st.write("selected_cqs_indexes_in_catalog  {}".format(selected_cqs_indexes_in_catalog))
    # for i, item in enumerate(cq_catalog):
    #     st.write("{}: {}".format(i, cq_catalog[i]))

    with st.expander("Display a single CQ"):
        if selected_cqs_indexes_in_catalog != []:
            # retrieving cq_catalog index in the df:
            catalog_entry = cq_catalog[selected_cqs_indexes_in_catalog[0]]
            with open(os.path.join(BASE_LD_PATH, catalog_entry["language"], "cq", "cq_translations", catalog_entry["filename"])) as fcqd:
                cqd = json.load(fcqd)
            du.display_cq(cqd, st.session_state.delimiters, catalog_entry["title"])
        else:
            st.write("Select a CQ in the table")

    with st.expander("Compare the same CQ in multiple languages"):
        # list available cq titles by creating the set of titles in the df
        cq_titles = list(set(cq_catalog_df["title"].tolist()))
        selected_cq_title = st.selectbox("Choose a CQ", cq_titles)
        filtered_df = cq_catalog_df[cq_catalog_df["title"] == selected_cq_title]
        available_languages = filtered_df["language"].tolist()
        selected_languages = st.multiselect("Select languages to compare", available_languages,
                                            default=available_languages[:2])
        if selected_languages != []:
            cqs_content = []
            for lang in selected_languages:
                lang_entry = filtered_df[filtered_df["language"] == lang].iloc[0]
                with open(os.path.join(BASE_LD_PATH, lang_entry["language"], "cq", "cq_translations",
                                       lang_entry["filename"])) as fcl:
                    cqs_content.append(json.load(fcl))
            du.display_same_cq_multiple_languages(cqs_content, selected_cq_title)

    with st.expander("Explore CQs within a language by words and parameters"):
        st.markdown("Select all the CQs you want to use for exploration and press the submit button")
        if st.button("Submit", key="explore_consolidation_button"):
            st.session_state["cq_transcriptions"] = []
            if selected_cqs_indexes_in_catalog != []:
                for cqi in selected_cqs_indexes_in_catalog:
                    cq_catalog_item = cq_catalog[cqi]
                    cq_filename = cq_catalog_item["filename"]
                    with open(os.path.join(BASE_LD_PATH, cq_catalog_item["language"], "cq", "cq_translations", cq_filename), "r") as cqf:
                        content = json.load(cqf)
                        st.session_state.active_language = content["target language"]
                        st.session_state.delimiters = content["delimiters"]
                        st.session_state["cq_transcriptions"].append(content)
            with st.spinner("Building knowledge graph..."):
                st.session_state["knowledge_graph"], unique_words, unique_words_frequency, total_target_word_count = kgu.consolidate_cq_transcriptions(
                    st.session_state["cq_transcriptions"],
                    st.session_state.active_language,
                    st.session_state.delimiters)

        if st.session_state["knowledge_graph"] != {}:
            st.session_state["cdict"] = kgu.build_concept_dict(st.session_state["knowledge_graph"])
            def index_parameters(cdict):
                param_index = {}
                for concept, details_list in cdict.items():
                    for oc in details_list:
                        for param_cat in oc["particularization"].keys():
                            if param_cat not in param_index.keys():
                                param_index[param_cat] = {}
                            for param in oc["particularization"][param_cat].keys():
                                if param not in param_index[param_cat]:
                                    param_index[param_cat][param] = []
                                if oc["particularization"][param_cat][param] not in param_index[param_cat][param]:
                                    param_index[param_cat][param].append(oc["particularization"][param_cat][param])
                return param_index


            st.session_state["pdict"] = index_parameters(st.session_state["cdict"])

            # OPTIONAL STATISTICS AND GRAPHS
            if st.toggle("Show statistics on target words"):
                word_dict = stats.build_blind_word_stats_from_knowledge_graph(st.session_state["knowledge_graph"],
                                                                              st.session_state["delimiters"])
                # UI controls for visualization parameters
                st.sidebar.header("Visualization Parameters")
                min_edge_weight = st.sidebar.slider("Minimum Edge Weight", 0.0, 1.0, 0.1, 0.05)
                min_node_size = 20
                max_node_size = 150
                show_labels = True
                physics_enabled = True

                # Color scheme
                node_color = "#4C78A8"
                edge_color = "#EEEEEE"
                background_color = "#FFFFFF"


                # Create a pyvis network
                def create_network(word_dict, min_edge_weight, min_node_size, max_node_size,
                                   show_labels, physics_enabled, node_color, edge_color, background_color):

                    # Create a network with basic options
                    net = Network(height="600px", width="100%", bgcolor=background_color,
                                  font_color="#000000", directed=True)

                    # Find max frequency for node scaling
                    all_words = set()
                    max_freq = 1  # default to avoid division by zero

                    for word_info in word_dict.values():
                        all_words.add(word_info['word'])
                        max_freq = max(max_freq, word_info['frequency'])
                        for following in word_info['following'].keys():
                            if following:  # Skip empty string
                                all_words.add(following)

                    # Add all nodes first
                    for word in all_words:
                        # Get word info if available, otherwise use default values
                        if word in word_dict:
                            freq = word_dict[word]['frequency']
                        else:
                            # This is a word that appears as a neighbor but not as a main entry
                            freq = 1  # Default frequency

                        # Scale node size based on frequency
                        size = min_node_size + ((max_node_size - min_node_size) * (freq / max_freq))

                        # Add node to network
                        tooltip = f"Word: {word}, Count: {freq}"
                        if word in word_dict:
                            preceding_words = ", ".join([f"{w}" for w in word_dict[word]['preceding'].keys() if w])
                            following_words = ", ".join([f"{w}" for w in word_dict[word]['following'].keys() if w])
                            if following_words:
                                tooltip += f"""
                                ---
                                Preceding words:
                                {preceding_words}
                                ---
                                Following words: 
                                {following_words}"""

                        net.add_node(word, label=word, size=size, title=tooltip)

                    # Add edges
                    for word, word_info in word_dict.items():
                        # Add edges for following words
                        for following, count in word_info['following'].items():
                            if following and following in all_words:  # Skip empty string and ensure target exists
                                probability = word_info['following_prob'].get(following, 0)

                                # Only add edges above the minimum weight
                                if probability >= min_edge_weight:
                                    # Width based on probability
                                    width = 1 + (9 * probability)  # Scale from 1 to 10

                                    # Add edge with custom attributes
                                    edge_label = f"{probability:.2f}" if show_labels else ""
                                    tooltip = f"Probability: {probability:.2f}"
                                    net.add_edge(word, following, value=width, title=tooltip, label=edge_label,
                                                 width=width)

                    # Set basic options as string
                    options = """
                    var options = {
                      "nodes": {
                        "borderWidth": 2,
                        "borderWidthSelected": 8,
                        "color": {
                          "highlight": {
                            "border": "#FF0000",
                            "background": "#FF9999"
                          },
                          "hover": {
                            "border": "#FF6600",
                            "background": "#FFCC99"
                          }
                        },
                        "font": {
                          "size": 20
                        },
                        "shape": "dot"
                      },
                      "edges": {
                        "arrows": {
                          "to": {
                            "enabled": true
                          }
                        },
                        "color": {
                          "inherit": false,
                          "highlight": "#FF0000",
                          "hover": "#FF6600"
                        },
                        "smooth": {
                          "type": "continuous",
                          "forceDirection": "none"
                        }
                      },
                      "interaction": {
                        "hover": true,
                        "hoverConnectedEdges": true,
                        "selectable": true,
                        "selectConnectedEdges": true,
                        "navigationButtons": true,
                        "tooltipDelay": 100
                      },
                      "physics": {
                        "enabled": %s,
                        "solver": "forceAtlas2Based",
                        "forceAtlas2Based": {
                          "gravitationalConstant": -300,
                          "centralGravity": 0.005,
                          "springLength": 100,
                          "springConstant": 0.08,
                          "damping": 0.9
                        },
                        "maxVelocity": 50,
                        "minVelocity": 0.1,
                        "timestep": 0.3,
                        "stabilization": {
                          "enabled": true,
                          "iterations": 1000,
                          "updateInterval": 25
                        }
                      },
                      "layout": {
                        "improvedLayout": false
                      }
                    }
                    """ % str(physics_enabled).lower()

                    # Apply options
                    net.set_options(options)

                    # Generate the HTML
                    html = net.generate_html()

                    return html


                # Create and display the network
                try:
                    # Create a temporary directory and file
                    temp_dir = tempfile.mkdtemp()
                    path = Path(temp_dir) / "word_network.html"

                    # Generate HTML
                    html = create_network(
                        word_dict,
                        min_edge_weight,
                        min_node_size,
                        max_node_size,
                        show_labels,
                        physics_enabled,
                        node_color,
                        edge_color,
                        background_color
                    )

                    # Write HTML to file
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(html)

                    # Display using streamlit components
                    st.components.v1.html(open(path, 'r', encoding='utf-8').read(), height=600)

                except Exception as e:
                    st.error(f"Error creating visualization: {e}")
                    st.error(f"Error details: {str(e)}")

                # Add comprehensive data exploration section
                st.header("Data Explorer")

                # Show basic statistics
                st.subheader("Basic Network Statistics")
                col1, col2, col3 = st.columns(3)
                total_words = len(word_dict)
                # Get all unique words (including those only appearing as followers)
                all_unique_words = set()
                for word, info in word_dict.items():
                    all_unique_words.add(word)
                    for follower in info['following'].keys():
                        if follower:  # Skip empty strings
                            all_unique_words.add(follower)

                total_connections = sum(len(info['following']) for info in word_dict.values())
                avg_connections = round(total_connections / total_words, 2) if total_words > 0 else 0

                with col1:
                    st.metric("Total Words in Dictionary", total_words)
                with col3:
                    st.metric("Total Connections", total_connections)

                # Advanced network metrics
                st.subheader("Advanced Network Metrics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Avg Connections Per Word", avg_connections)

                    # Calculate network density
                    max_possible_connections = total_words * (len(all_unique_words) - 1)
                    network_density = round((total_connections / max_possible_connections),
                                            4) if max_possible_connections > 0 else 0
                    st.metric("Network Density", network_density,
                              help="Ratio of actual connections to all possible connections. Higher values indicate a more interconnected network.")

                with col2:
                    # Calculate words with no followers and words with no precedents
                    isolated_words = sum(
                        1 for info in word_dict.values() if not any(f for f in info['following'].keys() if f))
                    st.metric("Words With No Followers", isolated_words)

                    # Calculate words that appear only as followers
                    follower_only = len(all_unique_words) - total_words
                    st.metric("Words Appearing Only As Followers", follower_only)

                # Most frequent words analysis
                st.subheader("Most Frequent Words")
                top_n_words = st.slider("Number of top words to display", 5, 50, 10)

                # Calculate word frequencies including words that are both in the dictionary and just followers
                word_frequencies = {}
                for word, info in word_dict.items():
                    word_frequencies[word] = info['frequency']

                # Create DataFrame and sort
                freq_df = pd.DataFrame([{"Word": word, "Count": freq} for word, freq in word_frequencies.items()])
                freq_df = freq_df.sort_values("Count", ascending=False).reset_index(drop=True)

                # Display top N frequent words
                if not freq_df.empty:
                    st.write(f"Top {top_n_words} Most Frequent Words:")
                    st.dataframe(freq_df.head(top_n_words))

                    # Create a bar chart for visualization
                    st.bar_chart(freq_df.head(top_n_words).set_index("Word"))
                else:
                    st.write("No frequency data available")

                # Hub analysis
                st.subheader("Hub Word Analysis")
                st.write("Hub words are central to the network, with many connections to other words.")

                # Calculate hub metrics
                hub_data = []
                for word, info in word_dict.items():
                    # Count outgoing connections (following)
                    out_degree = len([f for f in info['following'].keys() if f])

                    # Count incoming connections (preceding from other words)
                    in_degree = 0
                    for other_word, other_info in word_dict.items():
                        if word in other_info['following']:
                            in_degree += 1

                    # Calculate hub score (combining in and out degree)
                    hub_score = in_degree + out_degree

                    hub_data.append({
                        "Word": word,
                        "Out Degree": out_degree,
                        "In Degree": in_degree,
                        "Total Connections": hub_score,
                        "Count": info['frequency']
                    })

                # Create DataFrame and calculate different hub metrics
                hub_df = pd.DataFrame(hub_data)

                # Display different hub rankings
                hub_metric = st.selectbox(
                    "Select hub metric",
                    ["Total Connections", "Out Degree", "In Degree", "Count x Connections"]
                )

                if hub_metric == "Count x Connections":
                    # Create weighted metric that combines frequency and connections
                    hub_df["Count x Connections"] = hub_df["Count"] * hub_df["Total Connections"]
                    hub_df_sorted = hub_df.sort_values("Count x Connections", ascending=False).reset_index(drop=True)
                else:
                    hub_df_sorted = hub_df.sort_values(hub_metric, ascending=False).reset_index(drop=True)

                # Display top N hub words
                if not hub_df.empty:
                    st.write(f"Top {top_n_words} Hub Words by {hub_metric}:")
                    st.dataframe(hub_df_sorted.head(top_n_words))

                    # Create a bar chart for visualization
                    st.bar_chart(hub_df_sorted.head(top_n_words).set_index("Word")[hub_metric])
                else:
                    st.write("No hub data available")

                # Display the raw data in expandable section
                with st.expander("View Raw Data"):
                    # Convert to DataFrame for better display
                    rows = []
                    for word, info in word_dict.items():
                        following_str = ", ".join([f"{w}({p:.2f})" for w, p in info['following_prob'].items() if w])
                        preceding_str = ", ".join([f"{w}({p:.2f})" for w, p in info['preceding_prob'].items() if w])
                        rows.append({
                            "Word": word,
                            "Count": info['frequency'],
                            "Following Words (Probability)": following_str,
                            "Preceding Words (Probability)": preceding_str
                        })

                    if rows:
                        df = pd.DataFrame(rows)
                        st.dataframe(df)
                    else:
                        st.write("No data available")

            # EXPLORE BY CONCEPT -------------------
            with st.expander("Explore by concept"):
                user_concept = st.selectbox("Select a concept", list(st.session_state["cdict"].keys()), index=0)
                if st.button("Explore concept {}".format(user_concept)):
                    st.session_state["selected_concept"] = user_concept
                if st.session_state["selected_concept"] != "":
                    st.write(
                        "{} occurrences of **{}**. Click on the left of any row to get more details on an entry.".format(
                            len(st.session_state["cdict"][st.session_state["selected_concept"]]),
                            st.session_state["selected_concept"]))

                    # flatten cdict[selected] to display in a df
                    flat_cdict_oc = []
                    # st.write(st.session_state["cdict"][selected_concept])
                    for oc in st.session_state["cdict"][st.session_state["selected_concept"]]:
                        tmp = {}
                        tmp["pivot_sentence"] = oc["pivot_sentence"]
                        tmp["target_sentence"] = oc["target_sentence"]
                        tmp["target_words"] = oc["target_words"]
                        for param_cat, params in oc["particularization"].items():
                            for p, v in params.items():
                                tmp[f"{param_cat}_{p}"] = v
                        flat_cdict_oc.append(tmp)

                    oc_df = pd.DataFrame(flat_cdict_oc)

                    selected = st.dataframe(oc_df, selection_mode="single-row", on_select="rerun", key="oc_df")

                    # propose download in docx format
                    entry_list = [oc["kg_entry"] for oc in
                                  st.session_state["cdict"][st.session_state["selected_concept"]]]
                    docx_file = ogu.generate_docx_from_kg_index_list(st.session_state["knowledge_graph"],
                                                                     st.session_state["delimiters"],
                                                                     entry_list)
                    st.download_button(
                        label="📥 Download DOCX",
                        data=docx_file,
                        file_name=f'corpus filtered by concept {st.session_state["selected_concept"]}.docx',
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                    if selected["selection"]["rows"] != []:
                        selected_cdict_entry = st.session_state["cdict"][st.session_state["selected_concept"]][
                            (selected["selection"]["rows"][0])]
                        kg_entry = selected_cdict_entry["kg_entry"]
                        # st.write(selected_cdict_entry)
                        # Supergloss
                        st.markdown(f'**{selected_cdict_entry["target_sentence"]}**')
                        st.markdown(f'*{selected_cdict_entry["pivot_sentence"]}*')
                        supergloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kg_entry,
                                                              st.session_state["delimiters"])
                        gloss_selection = st.dataframe(supergloss, use_container_width=True,
                                                       selection_mode="single-column", on_select="rerun",
                                                       key="supergloss_df")
                        st.markdown(f'**Comments**: {selected_cdict_entry["comment"]}')
                        # show sentences with the selected word if any
                        if gloss_selection["selection"]["columns"] != []:
                            tw = gloss_selection["selection"]["columns"][0].split("_")[0].split("(")[0]
                            kg_entries_with_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                               tw,
                                                                               st.session_state["delimiters"])
                            # stats
                            wstats = {}
                            for e in kg_entries_with_word:
                                c = [c for c in
                                     st.session_state["knowledge_graph"][e]["recording_data"]["concept_words"].keys() if
                                     tw in st.session_state["knowledge_graph"][e]["recording_data"]["concept_words"][
                                         c].split("...")]
                                if c == []:
                                    c = "undefined"
                                else:
                                    c = c[0]
                                if c in wstats.keys():
                                    wstats[c] += 1
                                else:
                                    wstats[c] = 1
                            wstats_df = pd.DataFrame(list(wstats.items()), columns=["Concept", "Number of occurrences"])
                            wstats_df = wstats_df.sort_values("Number of occurrences", ascending=False)

                            st.subheader(
                                "'**{}**' is, or is part of, the expression of the following concepts:".format(tw))
                            # Create the clickable bar chart
                            fig = px.bar(
                                wstats_df,
                                x='Concept',
                                y='Number of occurrences',
                            )
                            # Enable clicking
                            fig.update_layout(
                                xaxis_title="Concepts",
                                yaxis_title="Count",
                                # Rotate x-axis labels if there are many words
                                xaxis=dict(tickangle=45)
                            )
                            # Display the chart and store click data in session state
                            sc = st.plotly_chart(
                                fig,
                                use_container_width=True,
                                key='bar_chart',
                                theme="streamlit",
                                on_select="rerun"
                            )
                            if sc["selection"]["points"]:
                                s_concept = sc["selection"]["points"][0]["label"]
                            else:
                                s_concept = ""
                            if s_concept != "" \
                                    and s_concept != "undefined" \
                                    and s_concept != st.session_state["selected_concept"] \
                                    and s_concept in list(st.session_state["cdict"].keys()):
                                if st.button("Jump to concept {}".format(s_concept)):
                                    st.session_state["selected_concept"] = s_concept
                                    st.rerun()

                            if s_concept != "" and s_concept != "undefined":
                                st.write("#### Sentences with *{}* contributing to the expression of **{}**".format(tw,
                                                                                                                    s_concept))
                            else:
                                st.write("#### Sentences with *{}*".format(
                                    tw, s_concept))
                            gloss_counter = 0
                            for kge in kg_entries_with_word:
                                kgc = st.session_state["knowledge_graph"][kge]
                                if s_concept != "" and s_concept != "undefined":
                                    if s_concept in kgc["recording_data"]["concept_words"].keys() and tw in \
                                            kgc["recording_data"]["concept_words"][s_concept].split("..."):
                                        gloss_counter += 1
                                        gloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kge,
                                                                         st.session_state["delimiters"])
                                        st.markdown(
                                            f'**{st.session_state["knowledge_graph"][kge]["recording_data"]["translation"]}**')
                                        st.write(st.session_state["knowledge_graph"][kge]["sentence_data"]["text"])
                                        st.dataframe(gloss, key="subgloss" + str(gloss_counter),
                                                     use_container_width=True)
                                        st.write(st.session_state["knowledge_graph"][kge]["recording_data"]["comment"])
                                else:
                                    gloss_counter += 1
                                    gloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kge,
                                                                     st.session_state["delimiters"])
                                    st.write(st.session_state["knowledge_graph"][kge]["sentence_data"]["text"])
                                    st.dataframe(gloss, key="subgloss" + str(gloss_counter), use_container_width=True)

                        # Showing sentences using the same target word(s)
                        st.write("---")
                        if selected_cdict_entry["target_words"] != "":
                            entries_with_target_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                                   selected_cdict_entry["target_words"],
                                                                                   st.session_state["delimiters"])
                            current_entries = []
                            for item in st.session_state["cdict"][st.session_state["selected_concept"]]:
                                current_entries.append(item["kg_entry"])
                            current_entries = list(set(current_entries))

            # EXPLORE BY PARAMETER
            with st.expander("Explore by parameter"):
                with st.popover("info"):
                    st.markdown("""
                    You can filter using **Intent**, **Internal Particularization** and **Relational Particularization**.
                    - Multiple choices within a selection field are unions (**OR**): If you select both "ASK" and "ORDER" in Intent, any entry with an "ASK" **OR** "ORDER" intent will be selected. 
                    - Selections across selection fields are intersections (**AND**): If you select "ASK" in Intent and "NEGATIVE" polarity in Internal Particularization, only entries with both "ASK" Intent **AND** "NEGATIVE" polarity will be selected.

                    This behavior allows selecting entries with any given range of grammatical parameters across those proposed. 

                    **If you don't see any output**, it probably means that there are no entries satisfying the filter you entered.
                    """)
                kcount = 0
                # FILTER INPUT
                colq, cola, colw, cole = st.columns(4)
                # intent
                s_intent = colq.multiselect("Filter by Intent", ["All"] + st.session_state["pdict"]["intent"]["intent"])
                if s_intent == ["All"] or s_intent == []:
                    is_intent_filter = False
                    s_intent = []
                else:
                    is_intent_filter = True
                st.session_state["pfilter"]["intent"] = s_intent
                # type of predicate
                s_pred = cola.multiselect("Filter by type of Predicate",
                                          ["All"] + st.session_state["pdict"]["predicate"]["predicate"])
                if s_pred == ["All"] or s_pred == []:
                    is_pred_filter = False
                    s_pred = []
                else:
                    is_pred_filter = True
                st.session_state["pfilter"]["predicate"] = s_pred
                # ip
                s_internal = colw.multiselect("Filter by Internal Particularization", ["All"] + list(
                    st.session_state["pdict"]["internal_particularization"].keys()))
                if s_internal == ["All"] or s_internal == []:
                    is_ip_filter = False
                    s_internal = []
                else:
                    is_ip_filter = True
                if is_ip_filter:
                    for p in s_internal:
                        kcount += 1
                        pp = colw.multiselect(f"Values of {p}",
                                              ["All"] + st.session_state["pdict"]["internal_particularization"][p],
                                              key="pp" + str(kcount))
                        if pp == ["All"]:
                            pp = []
                        st.session_state["pfilter"]["ip"][p] = pp
                # rp
                s_relational = cole.multiselect("Filter by Relational Particularization", ["All"] + list(
                    st.session_state["pdict"]["relational_particularization"].keys()))
                if s_relational == ["All"] or s_relational == []:
                    s_relational = []
                    is_rp_filter = False
                else:
                    is_rp_filter = True
                st.session_state["pfilter"]["rp"] = s_relational

                # FILTER USAGE
                selected_oc = []
                si_count = 0
                sp_count = 0
                sip_count = 0
                srp_count = 0
                oc_count = 0
                for concept in st.session_state["cdict"].keys():
                    for oc in st.session_state["cdict"][concept]:
                        oc_count += 1
                        si = False
                        sp = False
                        sip = False
                        srp = False
                        # intent
                        if is_intent_filter:
                            if oc["particularization"]["intent"]["intent"] in st.session_state["pfilter"]["intent"]:
                                si = True
                                si_count += 1
                        else:
                            si = True
                            si_count += 1
                        # predicate
                        if is_pred_filter:
                            if oc["particularization"]["predicate"]["predicate"] in st.session_state["pfilter"][
                                "predicate"]:
                                sp = True
                                sp_count += 1
                        else:
                            sp = True
                            sp_count += 1
                        # internal particularization
                        if is_ip_filter:
                            oc_ip_params = list(oc["particularization"]["internal_particularization"].keys())
                            subsip = True
                            if oc_ip_params == []:
                                subsip = False
                            for pfilter_ip_param in st.session_state["pfilter"]["ip"].keys():
                                # print("pfilter_ip_param: {}".format(pfilter_ip_param))
                                # print("oc_ip_params: {}".format(oc_ip_params))
                                if pfilter_ip_param in oc_ip_params:
                                    # print("MATCH: pfilter_ip_param in oc_ip_params")
                                    # print(oc["particularization"]["internal_particularization"][pfilter_ip_param])
                                    # print("in?")
                                    # print(st.session_state["pfilter"]["ip"][pfilter_ip_param])
                                    if oc["particularization"]["internal_particularization"][pfilter_ip_param] in \
                                            st.session_state["pfilter"]["ip"][pfilter_ip_param]:
                                        continue
                                    else:
                                        subsip = False
                                else:
                                    subsip = False
                            sip = subsip
                            if sip:
                                sip_count += 1
                        else:
                            sip = True
                            sip_count += 1
                        # relational particularization
                        if is_rp_filter:
                            oc_rp_params = oc["particularization"]["relational_particularization"].keys()
                            for oc_rp_param in oc_rp_params:
                                if oc_rp_param in st.session_state["pfilter"]["rp"]:
                                    srp = True
                                    srp_count += 1
                        else:
                            srp = True
                            srp_count += 1
                        if si and sp and sip and srp:
                            selected_oc.append(oc)

                # Display results
                # keep unique pivot sentences
                displayed_oc = []
                psl = []
                for oc in selected_oc:
                    if oc["pivot_sentence"] not in psl:
                        psl.append(oc["pivot_sentence"])
                        displayed_oc.append(oc)
                st.write("{} entries selected".format(len(displayed_oc)))

                ocp_df = pd.DataFrame(displayed_oc, columns=["pivot_sentence", "target_sentence"])
                ocp_selected = st.dataframe(ocp_df, selection_mode="single-row", on_select="rerun", key="ocp_df",
                                            use_container_width=True)

                # propose docx format
                entry_list_p = [ocp["kg_entry"] for ocp in displayed_oc]
                docx_file_p = ogu.generate_docx_from_kg_index_list(st.session_state["knowledge_graph"],
                                                                   st.session_state["delimiters"],
                                                                   entry_list_p)
                filter_string = ""
                if st.session_state["pfilter"]["intent"] != []:
                    filter_string += "_".join(st.session_state["pfilter"]["intent"])
                if st.session_state["pfilter"]["enunciation"] != []:
                    filter_string += "+" + "_".join(st.session_state["pfilter"]["enunciation"])
                if st.session_state["pfilter"]["predicate"] != []:
                    filter_string += "+" + "_".join(st.session_state["pfilter"]["predicate"])
                if st.session_state["pfilter"]["ip"] != {}:
                    filter_string += "+" + "_".join(
                        [k + ":" + "+".join(v) for k, v in st.session_state["pfilter"]["ip"].items()])
                if st.session_state["pfilter"]["rp"] != {}:
                    filter_string += "+" + "_".join(st.session_state["pfilter"]["rp"])
                st.download_button(
                    label="📥 Download DOCX",
                    data=docx_file_p,
                    file_name=f"corpus_filtered_by_parameters_{filter_string}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

                if ocp_selected["selection"]["rows"] != []:
                    selected_cdictp_entry = displayed_oc[(ocp_selected["selection"]["rows"][0])]
                    kgp_entry = selected_cdictp_entry["kg_entry"]

                    # Gloss of selected sentence
                    st.write("---")
                    st.subheader("Information on selected sentence")
                    st.markdown(f'**{selected_cdictp_entry["target_sentence"]}**')
                    st.markdown(f'*{selected_cdictp_entry["pivot_sentence"]}*')
                    pgloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], kgp_entry,
                                                      st.session_state["delimiters"])
                    pgloss_selection = st.dataframe(pgloss, selection_mode="single-column", on_select="rerun",
                                                    key="pgloss_df")
                    st.write(selected_cdictp_entry["comment"])

                    # show sentences with the selected word if any
                    if pgloss_selection["selection"]["columns"] != []:
                        ptw = pgloss_selection["selection"]["columns"][0].split("_")[0].split("(")[0]
                        pkg_entries_with_word = kgu.get_sentences_with_word(st.session_state["knowledge_graph"],
                                                                            ptw,
                                                                            st.session_state["delimiters"])

                        # stats
                        pwstats = {}
                        for e in pkg_entries_with_word:
                            c = [c for c in
                                 st.session_state["knowledge_graph"][e]["recording_data"]["concept_words"].keys() if
                                 ptw in st.session_state["knowledge_graph"][e]["recording_data"]["concept_words"][
                                     c].split(
                                     "...")]
                            if c == []:
                                c = "undefined"
                            else:
                                c = c[0]
                            if c in pwstats.keys():
                                pwstats[c] += 1
                            else:
                                pwstats[c] = 1
                        pwstats_df = pd.DataFrame(list(pwstats.items()), columns=["Concept", "Number of occurrences"])
                        pwstats_df = pwstats_df.sort_values("Number of occurrences", ascending=False)

                        st.subheader(
                            "'**{}**' is, or is part of, the expression of the following concepts:".format(ptw))
                        # Create the clickable bar chart
                        fig = px.bar(
                            pwstats_df,
                            x='Concept',
                            y='Number of occurrences',
                        )
                        # Enable clicking
                        fig.update_layout(
                            xaxis_title="Concepts",
                            yaxis_title="Count",
                            # Rotate x-axis labels if there are many words
                            xaxis=dict(tickangle=45)
                        )
                        # Display the chart and store click data in session state
                        psc = st.plotly_chart(
                            fig,
                            use_container_width=True,
                            key='pbar_chart',
                            theme="streamlit",
                            on_select="rerun"
                        )
                        if psc["selection"]["points"]:
                            ps_concept = psc["selection"]["points"][0]["label"]
                        else:
                            ps_concept = ""
                        if ps_concept != "" \
                                and ps_concept != "undefined" \
                                and ps_concept != st.session_state["selected_concept"] \
                                and ps_concept in list(st.session_state["cdict"].keys()):
                            if st.button("Jump to concept {}".format(ps_concept)):
                                st.session_state["selected_concept"] = ps_concept
                                st.rerun()

                        if ps_concept != "" and ps_concept != "undefined":
                            st.write("#### Sentences with *{}* contributing to the expression of **{}**".format(
                                ptw, ps_concept))
                        else:
                            st.write("#### Sentences with *{}*".format(
                                ptw, ps_concept))
                        pgloss_counter = 0
                        for pkge in pkg_entries_with_word:
                            pkgc = st.session_state["knowledge_graph"][pkge]
                            if ps_concept != "" and ps_concept != "undefined":
                                if ps_concept in pkgc["recording_data"]["concept_words"].keys() and ptw in \
                                        pkgc["recording_data"]["concept_words"][ps_concept].split("..."):
                                    pgloss_counter += 1
                                    pgloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], pkge,
                                                                      st.session_state["delimiters"])
                                    st.markdown(
                                        f'**{st.session_state["knowledge_graph"][pkge]["recording_data"]["translation"]}**')
                                    st.write(st.session_state["knowledge_graph"][pkge]["sentence_data"]["text"])
                                    st.dataframe(pgloss, key="subgloss" + str(pgloss_counter), use_container_width=True)
                                    st.write(st.session_state["knowledge_graph"][pkge]["recording_data"]["comment"])
                            else:
                                pgloss_counter += 1
                                pgloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], pkge,
                                                                  st.session_state["delimiters"])
                                st.write(st.session_state["knowledge_graph"][pkge]["sentence_data"]["text"])
                                st.dataframe(pgloss, key="subgloss" + str(pgloss_counter), use_container_width=True)

                        # st.subheader("Sentences with '*{}*':".format(ptw))
                        # for pkge in pkg_entries_with_word:
                        #     ppgloss = kgu.build_super_gloss_df(st.session_state["knowledge_graph"], pkge, st.session_state["delimiters"])
                        #     st.markdown(f'**{st.session_state["knowledge_graph"][pkge]["recording_data"]["translation"]}**')
                        #     st.write(st.session_state["knowledge_graph"][pkge]["sentence_data"]["text"])
                        #     st.dataframe(ppgloss)
                        #     st.write(st.session_state["knowledge_graph"][pkge]["recording_data"]["comment"])
                        #     st.markdown("---")

# ========== CONSULT FILES ==========================
with tab2:
    with st.popover("Information"):
        st.markdown("""Click on any file in the table to display what you can do with it.
                   You can Edit and delete your own files, and download files from other users if they allow it.
                   To explore all available CQs, go to the Explore CQ tab. 

                   When a CQ file is identified as a CQ that can be used and displayed, it is automatically added 
                   to the CQ database.""")
    with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
        conveqs_index = json.load(f)
    conveqs_index_df = pd.DataFrame(conveqs_index)
    selected = st.dataframe(conveqs_index_df.style.hide(axis="index"), column_order=["language", "name", "author",
                                                                                     "format", "uploaded by",
                                                                                     "is_downloadable"],
                            hide_index=True, selection_mode="single-cell", on_select="rerun")
    if selected["selection"]["cells"] != []:
        selected_row = selected["selection"]["cells"][0][0]
        selected_item = conveqs_index[selected_row]
        st.markdown("You selected **{}** by {}, uploaded by {} on {}".format(selected_item["name"],
                                                                             selected_item["author"],
                                                                             selected_item["uploaded by"],
                                                                             selected_item["date"]))
        if username == selected_item["uploaded by"]:
            st.markdown("This is **your file**, you can **download** or **delete** it")
        col1, col2 = st.columns(2)
        if selected_item["is_downloadable"] and role != "guest":
            with open(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]), "rb") as f:
                data = f.read()
            col1.download_button("You can download this file", data, file_name=selected_item["filename"])
        else:
            col1.markdown("*This file can only be downloaded by registered users, contact us to become one!*")
        if selected_item["uploaded by"] == username or role == "admin":
            if col2.button("Delete this file"):
                del conveqs_index[selected_row]
                with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w") as f:
                    json.dump(conveqs_index, f)
                try:
                    os.remove(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]))
                except FileNotFoundError:
                    print("{} does not exist".format(selected_item["filename"]))
                st.rerun()
            if selected_item.get("format", "other") == "DIG4EL JSON" and username == selected_item["uploaded by"]:
                with st.expander("You can preview and edit your CQ file here"):
                    with open(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]), "r") as f:
                        preview_cq = json.load(f)
                    edited_cq = du.display_and_edit_cq(preview_cq, selected_item["filename"])
                    if edited_cq is not None:
                        with open(os.path.join(CONVEQS_BASE_PATH, selected_item["filename"]), "w") as fw:
                            json.dump(edited_cq, fw)
                        st.success("Edited file saved")

# ========== UPLOAD FILES ============================
with tab3:
    if role == "guest":
        st.markdown("*Guests cannot upload or manage Conversational Questionnaires.*")
        st.markdown("*If you have Conversational Questionnaires to upload, contact us to become a registered user!*")

    else:
        # SELECT LANGUAGE
        colq, colw = st.columns(2)
        llist = gu.GLOTTO_LANGUAGE_LIST.keys()
        selected_language = colq.selectbox("What language are you working on?", llist)

        st.write("Active language: {}".format(st.session_state.upload_language))

        if st.button("Select {}".format(selected_language)):
            st.session_state.upload_language = selected_language
            st.session_state.indi_glottocode = gu.GLOTTO_LANGUAGE_LIST.get(st.session_state.upload_language,
                                                                           "glottocode not found")
            fmu.create_ld(BASE_LD_PATH, st.session_state.upload_language)
            if st.session_state.upload_language in cfg["credentials"]["usernames"].get(username, {}).get("caretaker",
                                                                                                         []):
                role = "caretaker"
                if not st.session_state.caretaker_trigger:
                    st.session_state.caretaker_trigger = True
                    print("CARETAKER RERUN")
                    st.rerun()
            st.rerun()
        if role in ["admin", "caretaker"]:

            # Upload cq file

            with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json")) as ci:
                conveqs_index = json.load(ci)
            existing_filenames = [fn["filename"] for fn in conveqs_index]
            # FILE UPLOAD FORM
            with st.form(key="file_upload_form", clear_on_submit=True, enter_to_submit=False,
                         border=True, width="stretch", height="content"):
                sub_ready = False
                replace_ok = True
                new_cq = st.file_uploader(
                    "Add a new CQ translation to the repository",
                    accept_multiple_files=False,
                    key="new_cq" + str(st.session_state.new_cq_counter)
                )
                info_entered = False
                name = st.text_input("Name this document (The name that will be displayed)")
                author = st.text_input("Author/owner of the corpus")
                visibility = st.selectbox("Visibility", ["Everyone", "Members only"], index=0)
                data_format = st.selectbox("Format", ["Excel template", "FleX XML", "DIG4EL JSON", "other"])
                is_downloadable = st.checkbox("Can be downloaded by registered users", value=True)

                submitted = st.form_submit_button("Submit", disabled=not replace_ok)

                if submitted:
                    with open(os.path.join(CONVEQS_BASE_PATH, new_cq.name), "wb") as f:
                        f.write(new_cq.read())
                    st.success(f"Saved `{new_cq.name}` on the server.")

                    now = datetime.now()
                    readable_date_time = now.strftime("%A, %d %B %Y at %H:%M:%S")
                    conveqs_index.append(
                        {
                            "filename": new_cq.name,
                            "format": data_format,
                            "visibility": visibility,
                            "is_downloadable": is_downloadable,
                            "name": name,
                            "language": st.session_state.upload_language,
                            "author": author,
                            "uploaded by": username,
                            "date": readable_date_time
                        }
                    )
                    if new_cq.name in existing_filenames:
                        existing_filename_index = existing_filenames.index(new_cq.name)
                        del conveqs_index[existing_filename_index]
                        print("Deleted item to replace at index {}".format(existing_filename_index))
                    with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "w",
                              encoding='utf-8') as f:
                        u.save_json_normalized(conveqs_index, f)
                    st.success("{} successfully indexed.".format(new_cq.name))

                    # CQ VALIDATION
                    if data_format == "DIG4EL JSON":
                        is_valid_cq = True
                        try:
                            with open(os.path.join(CONVEQS_BASE_PATH, new_cq.name), "r") as fr:
                                test_cq = json.load(fr)

                            for key in ["target language", "delimiters", "pivot_language", "cq_uid", "data"]:
                                if key not in test_cq.keys():
                                    is_valid_cq = False
                                    st.warning("{} is not a valid DIG4EL JSON file.".format(selected_item["filename"]))
                        except:
                            st.warning("An exception occurred while opening {} for validation".format(
                                selected_item["filename"]))
                            st.warning("This does not seem to be a valid JSON file.")
                            is_valid_cq = False
                        if is_valid_cq:
                            if st.session_state.upload_language in os.listdir(os.path.join(BASE_LD_PATH)):
                                with open(os.path.join(BASE_LD_PATH,
                                                       st.session_state.upload_language,
                                                       "cq",
                                                       "cq_translations"), "w") as fw:
                                    json.dump(test_cq, fw)
                            else:
                                st.warning("Valid DIG4EL CQ but invalid data path to store the CQ")

                    st.rerun()
        if role == "admin":
            with open(os.path.join(CONVEQS_BASE_PATH, "conveqs_index.json"), "r") as f:
                st.write(json.load(f))



