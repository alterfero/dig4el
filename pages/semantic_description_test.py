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
from libs import semantic_description_utils as sdu
import pkg_resources
import streamlit.components.v1 as components
from pyvis.network import Network
import asyncio

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "result" not in st.session_state:
    st.session_state.result = None
if "existential" not in st.session_state:
    st.session_state.existential = None


st.subheader("Test semantic descriptions")

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

try:
    # If there’s already a running loop on this thread, do nothing.
    asyncio.get_running_loop()
except RuntimeError:
    # No loop set ⇒ create one and register it as the thread’s default.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


def plot_semantic_graph_pyvis(data,
                              height="600px",
                              width="100%",
                              coordination_color="#DD22AA",
                              concept_color="#AED6F1",
                              predicate_color="#A9DFBF",
                              top_node_color="#E74C3C"):

    # ensure PyVis can find its Jinja templates
    template_dir = pkg_resources.resource_filename("pyvis", "templates")

    net = Network(height=height,
                  width=width,
                  directed=True,
                  notebook=False,
                  )
    net.barnes_hut()

    # index concepts, predicates & coordinations by ID
    predicates = {p["pid"]: p for p in data.get("predicates", [])}

    # add all predicate nodes, then their edges
    for pid, p in predicates.items():
        head = p.get("head", pid)
        type = p.get("ptype", pid).get("type", pid)
        if type == "existential":
            type = ""
        if type in ["equative", "possessive"]:
            head = ""
        if head != "" and type != "":
            head += ", "

        net.add_node(
            n_id=pid,
            label=f"{head}{type}",
            title=(
                f"Aspect: {p.get('feats').get('aspect')} · "
                f"Mood: {p.get('feats').get('mood')} · "
                f"Tense: {p.get('feats').get('tense')} · "
                f"Reality: {p.get('feats').get('reality')}"
            ),
            shape="box",
            color=predicate_color,
            size=30
        )
    for pid, p in predicates.items():
        for arg in p.get("args", []):
            role = arg.get("role", "")
            target = arg.get("target_pid", None)
            net.add_edge(
                source=pid,
                to=target,
                label=role,
                title=role,
                arrows="to",
                physics=True
            )

    # highlight the top node if specified
    top_id = data.get("top", {})
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


sentence = st.text_input("Sentence")
if st.button("Output Sentence Structure"):
    st.session_state.existential = None
    st.session_state.result = None
    st.write("Extracting individual existential predicates")
    st.session_state.existential = sdu.extract_existential_predicates(sentence)

if st.session_state.existential:
    st.write(st.session_state.existential)

if st.session_state.existential:
    st.write("Computing higher order predicates")
    st.session_state.result = sdu.describe_sentence(sentence, st.session_state.existential)

if st.session_state.result:
    st.write(sentence)
    html = plot_semantic_graph_pyvis(st.session_state.result)
    components.html(html, height=600, width=1000)
    st.markdown("**Agent comments**: *{}*".format(st.session_state.result.get("comments", "no comments")))
    st.write(st.session_state.result)
