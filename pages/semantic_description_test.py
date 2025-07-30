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
from libs import semantic_description_agents as sda
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
if "enunciation" not in st.session_state:
    st.session_state.enunciation = None
if "done" not in st.session_state:
    st.session_state.done = False


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

sentence = st.text_input("Sentence")

if st.session_state.done:
    if st.button("Reset"):
        st.session_state.result = None
        st.session_state.enunciation = None
        st.session_state.done = False

if not st.session_state.done:

    if st.button("Describe sentence"):
        with st.spinner("Generating sentence description..."):
            st.session_state.result = sda.describe_sentence_sync(sentence)
        st.session_state.done = True

if st.session_state.result:

    st.markdown(f"**{sentence}**")
    html = sdu.plot_semantic_graph_pyvis(st.session_state.result)
    components.html(html, height=600, width=1000)
    st.write("**Enunciation**: ".format(st.session_state.result.get("enunciation", "no enunciation info")))
    st.markdown("**Semantic Description: *{}*".format(st.session_state.result.get("grammatical_description", "no description")))
    st.markdown( "**Keywords: *{}*".format(st.session_state.result.get("grammatical_keywords", "no keywords")))
    st.markdown("**Agent comments**: *{}*".format(st.session_state.result.get("comments", "no comments")))
    st.write(st.session_state.result)
