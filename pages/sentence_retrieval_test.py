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
import asyncio

import pandas as pd
import streamlit as st
import json
from libs import semantic_description_utils as sdu
from libs import retrieval_augmented_generation_utils as ragu
import pkg_resources
import streamlit.components.v1 as components
from pyvis.network import Network
import time
import os

if "sentence_pairs" not in st.session_state:
    st.session_state.sentence_pairs = []
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "result" not in st.session_state:
    st.session_state.result = None
if "description_response" not in st.session_state:
    st.session_state.description_response = None
if "description_dict" not in st.session_state:
    st.session_state.description_dict = None
if "description_text" not in st.session_state:
    st.session_state.description_text = None
if "enriching_pairs" not in st.session_state:
    st.session_state.enriching_pairs = False
if "enriched_pairs" not in st.session_state:
    st.session_state.enriched_pairs = None
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "index" not in st.session_state:
    st.session_state.index = None
if "hard_query_result" not in st.session_state:
    st.session_state.hard_query_result = None
if "stime" not in st.session_state:
    st.session_state.stime = None

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)


try:
    # If there’s already a running loop on this thread, do nothing.
    asyncio.get_running_loop()
except RuntimeError:
    # No loop set ⇒ create one and register it as the thread’s default.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

TEMP_FILE = "./data/tmp_enriched_pairs_file.json"

def generate_and_save_embeddings_of_source_sentence_list(sentences, embedding_file_path="/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/embeddings.pkl"):
    embeddings = ragu.build_embeddings(sentences)
    ragu.save_embeddings(embeddings, path=embedding_file_path)
    return embeddings

def load_embeddings(embedding_file_path="/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/embeddings.pkl"):
    embeddings = ragu.load_embeddings(embedding_file_path)
    return embeddings

def get_similar_entries_with_torch_topk(sentence_pairs, embeddings, query):
    scores, indices = ragu.query_similarity(embeddings, "Future tense")
    print("Similarity")
    for score, idx in zip(scores, indices):
            print(sentence_pairs[idx], f"(Score: {score:.4f})")

def get_similar_entries_with_semantic_search(sentence_pairs, embeddings, query):
    hits = ragu.semantic_search(embeddings, "How to express negation")
    hits = hits[0]      #Get the hits for the first query
    for hit in hits:
        print(sentence_pairs[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))


def plot_semantic_graph_pyvis(data,
                              height="600px",
                              width="100%",
                              coordination_color="#DD22AA",
                              concept_color="#AED6F1",
                              predicate_color="#A9DFBF",
                              top_node_color="#E74C3C"):
    """
    Turn a semantic-graph JSON dict into a PyVis graph and return the HTML for Streamlit.

    Parameters
    ----------
    data : dict
      JSON with keys "concepts", "predicates", and optional "top_node".
    height, width : str
      CSS size for the visualization pane (e.g. "600px", "100%").
    concept_color : str
      Fill color for concept nodes.
    predicate_color : str
      Fill color for predicate nodes.
    top_node_color : str
      Override color for the top_node (if present).

    Returns
    -------
    html : str
      HTML snippet you can embed via st.components.v1.html(...)
    """
    # ensure PyVis can find its Jinja templates
    template_dir = pkg_resources.resource_filename("pyvis", "templates")

    net = Network(height=height,
                  width=width,
                  directed=True,
                  notebook=False,
                  )
    net.barnes_hut()

    # index concepts, predicates & coordinations by ID
    concepts = {c["id"]: c for c in data.get("concepts", [])}
    predicates = {p["id"]: p for p in data.get("predicates", [])}
    coordinations = {p["id"]: p for p in data.get("coordination", [])}

    # add all concept nodes
    for cid, c in concepts.items():
        net.add_node(
            n_id=cid,
            label=c.get("description", cid),
            title=(
                f"Type: {c.get('entity_type')} · "
                f"Definiteness: {c.get('definiteness')} · "
                f"Known: {c.get('known')}"
            ),
            shape="ellipse",
            color=concept_color,
            size=20
        )

    # add all predicate nodes, then their edges
    for pid, p in predicates.items():
        net.add_node(
            n_id=pid,
            label=p.get("kernel", pid),
            title=(
                f"Aspect: {p.get('aspect')} · "
                f"Mood: {p.get('mood')} · "
                f"Tense: {p.get('tense')} · "
                f"Reality: {p.get('reality')}"
            ),
            shape="box",
            color=predicate_color,
            size=30
        )
    for pid, p in predicates.items():
        for arg in p.get("arguments", []):
            role = arg.get("role", "")
            target = arg["node"]["id"]
            net.add_edge(
                source=pid,
                to=target,
                label=role,
                title=role,
                arrows="to",
                physics=True
            )

    # add all coordination nodes, then their edges
    for cid, c in coordinations.items():
        net.add_node(
            n_id=cid,
            label=c.get("type", cid),
            title=(
                f"Type: {c.get('type')} · "
            ),
            shape="ellipse",
            color=coordination_color,
            size=20
        )
    for cid, c in coordinations.items():
        for arg in c.get("arguments", []):
            role = arg.get("role", "")
            target = arg["node"]["id"]
            net.add_edge(
                source=cid,
                to=target,
                label=role,
                title=role,
                arrows="to",
                physics=True
            )

    # highlight the top node if specified
    top_id = data.get("top_node", {}).get("id")
    if top_id and net.get_node(top_id):
        net.get_node(top_id)["color"] = top_node_color
        net.get_node(top_id)["title"] += "  ← top node"

    # custom physics for stability
    net.set_options("""
    var options = {
      "nodes": {"font":{"size":14}},
      "edges": {"smooth":true},
      "physics": {
        "barnesHut": {"gravitationalConstant":-5000, "centralGravity":0.2},
        "minVelocity":0.5
      }
    }
    """)

    return net.generate_html()

# Global variables =============================
BASE_PATH = "/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence_pairs/"

# ========= interface ===========================

st.header("Sentence Pairs LLM & KW Retrieval Test")

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

source_sentence = st.text_input("Sentence description test")
if st.button("Describe"):
    st.session_state.description_dict = sdu.describe_sentence(source_sentence)

if st.session_state.description_dict is not None:
    html = plot_semantic_graph_pyvis(st.session_state.description_dict)
    components.html(html, height=600, width=1000)
    st.markdown("**Agent comments**: *{}*".format(st.session_state.description_dict.get("comments", "no comments")))
    st.markdown("**Description: *{}*".format(st.session_state.description_dict.get("grammatical_description", "no description")))
    st.markdown("**Keywords: *{}*".format(st.session_state.description_dict.get("grammatical_keywords", "no keywords")))

# Add descriptions to sentence pairs
st.subheader("Add description to sentence pairs and store enriched pairs json")
sentence_pairs_file = st.file_uploader("Upload a sentence pair file (must contain 'source' and 'target' keys)", type="json")
if sentence_pairs_file is not None:
    st.session_state.sentence_pairs = json.load(sentence_pairs_file)
if st.session_state.sentence_pairs is not None:
    if st.button("Create enriched pairs file (long process, LLM use)"):
        st.session_state.enriching_pairs = True
if st.session_state.enriching_pairs:
    st.write("Starting sentence pairs augmentation process on {} sentences".format(len(st.session_state.sentence_pairs)))
    info1 = st.empty()
    info2 = st.empty()
    info3 = st.empty()
    st.session_state.enriched_pairs = []
    for c, sentence_pair in enumerate(st.session_state.sentence_pairs):

        with info1:
            st.progress(c/len(st.session_state.sentence_pairs), "Sentence augmentation in progress...")
        info2.write("Processing sentence {}/{}".format(c + 1, len(st.session_state.sentence_pairs)))
        if st.session_state.stime:
            info2.write("Estimated {} minutes remaining".format(round(st.session_state.stime * (len(st.session_state.sentence_pairs) - c)/60)))
        info3.write("sentence {}: {}".format(c + 1, sentence_pair.get("source", "no source")))
        start_time = time.time()
        augmented_sentence = sdu.add_description_and_keywords_to_sentence_pair(sentence_pair)
        st.session_state.stime = round(time.time() - start_time)
        st.session_state.enriched_pairs.append(augmented_sentence)
        with open(TEMP_FILE, "w") as f:
            json.dump(st.session_state.enriched_pairs, f)
        if c == len(st.session_state.sentence_pairs) - 1:
            st.session_state.enriching_pairs = False
            st.rerun()

if not st.session_state.enriching_pairs and st.session_state.enriched_pairs is not None:
    st.download_button("Download and store the augmented sentence pairs file",
                       data=json.dumps(st.session_state.enriched_pairs),
                       file_name="augmented_sentence_pairs.json")
    if st.checkbox("Explore augmented sentences"):
        tdf = pd.DataFrame(st.session_state.enriched_pairs, columns=["source", "description_text", "grammatical_keywords"])
        st.dataframe(tdf)

# Computing embeddings
st.subheader("Generating embeddings from enriched pairs")
if st.session_state.enriched_pairs is None:
    enriched_pairs_file = st.file_uploader("Upload enriched pairs file", type="json")
    if enriched_pairs_file is not None:
        st.session_state.enriched_pairs = json.load(enriched_pairs_file)
if st.session_state.enriched_pairs is not None:
    if st.button("generate embeddings"):
        embedding_ready_sentences = [item["description_text"] for item in st.session_state.enriched_pairs]
        st.session_state.embeddings = ragu.build_embeddings(embedding_ready_sentences)
        ragu.save_embeddings(st.session_state.embeddings, path="./data/current_embeddings")

# Query embeddings
if st.session_state.embeddings is not None:
    query = st.text_input("Query")
    if st.button("Submit query"):
        st.session_state.result = ragu.semantic_search(st.session_state.embeddings, query)[0]
        for item in st.session_state.result:
            st.write("{} (score {})".format(st.session_state.enriched_pairs[item["corpus_id"]]["source"],
                                            item["score"]))

# Hard-indexing and querying
st.subheader("Hard-indexing and querying")
if st.session_state.enriched_pairs is None:
    st.session_state.enriched_pairs = st.file_uploader("Upload an augmented sentence pair file", type="json")
else:
    if st.session_state.index is None:
        st.session_state.index = sdu.build_keyword_index(st.session_state.enriched_pairs)

if st.session_state.enriched_pairs and st.session_state.index:
    if st.checkbox("see index"):
        st.write(st.session_state.index)
    selected_keywords = st.multiselect("Select keywords", st.session_state.index)
    selected_indexes = [index for kw in selected_keywords for index in st.session_state.index[kw]]
    selected_indexes = list(set(selected_indexes))
    if selected_indexes:
        st.markdown("{} sentences with these keywords".format(len(selected_indexes)))
    for i in selected_indexes:
        st.markdown(f"Sentence: **{st.session_state.enriched_pairs[i]['target']}**")
        st.write(f"Pivot: {st.session_state.enriched_pairs[i]['source']}")
        st.markdown("*Description: {}*".format(st.session_state.enriched_pairs[i]["description_text"]))
        st.write(", ".join(st.session_state.enriched_pairs[i]["grammatical_keywords"]))
        st.divider()




