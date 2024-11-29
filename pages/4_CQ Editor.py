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
import json
from libs import graphs_utils
from libs import utils
import time
import copy
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "uid" not in st.session_state:
    st.session_state["uid"] = str(int(time.time()))
if "cq" not in st.session_state:
    st.session_state["cq"] = {
        "uid": st.session_state["uid"],
        "title": "xx",
        "context": "xx",
        "speakers": {
            "A": {
                "name": "xx",
                "gender": "indef",
                "age": "adult"
            },
            "B": {
                "name": "xx",
                "gender": "indef",
                "age": "adult"
            }
        },
        "dialog": {}
    }
if "loaded_existing" not in st.session_state:
    st.session_state["loaded_existing"] = False
if "counter" not in st.session_state:
    st.session_state["counter"] = 1
if "current node" not in st.session_state:
    st.session_state["current node"] = "GRAMMAR"
if "starting_item" not in st.session_state:
    st.session_state["starting_item"] = "GRAMMAR"
if "current_concept_node" not in st.session_state:
    st.session_state["current_concept_node"] = "GRAMMAR"
if "path_in_progress" not in st.session_state:
    st.session_state["path_in_progress"] = False
if "is_terminal_feature" not in st.session_state:
    st.session_state["is_terminal_feature"] = False
if "concept_set" not in st.session_state:
    st.session_state["concept_set"] = []
if "req_json" not in st.session_state:
    st.session_state["req_json"] = {}

def get_last_dialog_position():
    last_position = st.session_state["counter"]
    while str(last_position + 1) in st.session_state["cq"]["dialog"].keys():
        last_position += 1
    return last_position

def reset_current_dialog():
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["speaker"] = "A"
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["text"] = ""
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["intent"] = []
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["predicate"] = []
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["concept"] = []
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = {}
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["trimmed_graph"] = {}
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["legacy index"] = ""
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["idiomaticity"] = 1
    print("reset_current_dialog executed")


concepts_kson = json.load(open("./data/concepts.json"))
intent_list = graphs_utils.get_leaves_from_node(concepts_kson, "INTENT")
predicate_list = graphs_utils.get_leaves_from_node(concepts_kson, "PREDICATE")

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

if not st.session_state["loaded_existing"]:
    st.write("You can start a new questionnaire, or load an existing one")
if not st.session_state["loaded_existing"]:
    with st.expander("Load CQ"):
        existing_cq = st.file_uploader("Load an existing questionnaire", type="json")
        if existing_cq is not None:
            st.session_state["cq"] = json.load(existing_cq)
            st.session_state["uid"] = st.session_state["cq"]["uid"]
            st.session_state["loaded_existing"] = True

if st.session_state["loaded_existing"]:
    default_title = st.session_state["cq"]["title"]
    default_context = st.session_state["cq"]["context"]
    default_a_name = st.session_state["cq"]["speakers"]["A"]["name"]
    default_a_gender = st.session_state["cq"]["speakers"]["A"]["gender"]
    default_b_name = st.session_state["cq"]["speakers"]["B"]["name"]
    default_b_gender = st.session_state["cq"]["speakers"]["B"]["gender"]
else:
    default_title = ""
    default_context = ""
    default_a_name = "A"
    default_a_gender = "indef"
    default_b_name = "B"
    default_b_gender = "indef"

with st.expander("Header"):
    st.subheader("Title")
    title = st.text_input("Enter a title for this dialog.", value=default_title)
    st.subheader("Context")
    context = st.text_input("Enter a sentence describing the context of the dialog.", value=default_context)
    st.subheader("Speaker A")
    a_name = st.text_input("Speaker A Name", value=default_a_name)
    a_gender = st.selectbox("Gender",["male", "female", "indef"], index=["male", "female", "indef"].index(default_a_gender), key="a_gender")
    st.subheader("Speaker B")
    b_name = st.text_input("Speaker B Name", value=default_b_name)
    b_gender = st.selectbox("Gender",["male", "female", "indef"], index=["male", "female", "indef"].index(default_b_gender), key="b_gender")
    if st.button("Submit header"):
        st.session_state["cq"]["title"] = title
        st.session_state["cq"]["context"] = context
        st.session_state["cq"]["speakers"]["A"]["name"] = a_name
        st.session_state["cq"]["speakers"]["B"]["name"] = b_name
        st.session_state["cq"]["speakers"]["A"]["gender"] = a_gender
        st.session_state["cq"]["speakers"]["B"]["gender"] = b_gender
        st.success("Header submitted")

st.subheader("Dialog - Sentence #{}/{}".format(str(st.session_state.counter), str(get_last_dialog_position())))
colz, colx = st.columns(2)
with colz.container():
    cola, cols, cold, cole = st.columns(4)
    if cola.button("Previous"):
        if st.session_state["counter"] > 1:
            st.session_state["counter"] = st.session_state["counter"] - 1
            st.rerun()
    if cols.button("Next"):
            st.session_state["counter"] = st.session_state["counter"] + 1
            st.rerun()
    if cold.button("Insert"):
    # insert a new empty sentence, push all the following one step ahead
        last_position = get_last_dialog_position()
        # shift everything
        for i in range(0, last_position - st.session_state["counter"]):
            st.session_state["cq"]["dialog"][str(last_position - i + 1)] = copy.deepcopy(st.session_state["cq"]["dialog"][str(last_position - i)])
        # move counter to next and rerun
        st.session_state["counter"] = st.session_state["counter"] + 1
        # reset this position
        reset_current_dialog()
        st.rerun()
    if cole.button("Delete"):
        last_position = get_last_dialog_position()
        # shift dialogs
        for i in range(st.session_state["counter"], last_position - 1):
            st.session_state["cq"]["dialog"][str(i)] = copy.deepcopy(st.session_state["cq"]["dialog"][str(i+1)])
        # erase last
        del(st.session_state["cq"]["dialog"][str(last_position)])
        st.rerun()


# there's an entry on that counter mark
if str(st.session_state["counter"]) in st.session_state["cq"]["dialog"].keys():
    #print("Existing sentence in this dialog, retrieving content")
    #print("getting defaults from {}".format(st.session_state["cq"]["dialog"][str(st.session_state["counter"])]))
    current_counter = str(st.session_state["counter"])
    st.session_state["req_json"] = st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"]
    default_s = st.session_state["cq"]["dialog"][current_counter]["speaker"]
    if default_s == "":
        default_s = "A"
    default_t = st.session_state["cq"]["dialog"][current_counter]["text"]
    default_i = st.session_state["cq"]["dialog"][current_counter]["intent"]
    if default_i == []:
        default_i = None
    default_p = st.session_state["cq"]["dialog"][current_counter]["predicate"]
    if default_p ==[]:
        default_p = None
    if "legacy index" in st.session_state["cq"]["dialog"][current_counter]:
        default_legacy_index = st.session_state["cq"]["dialog"][current_counter]["legacy index"]
    else:
        st.session_state["cq"]["dialog"][current_counter]["legacy index"] = ""
        default_legacy_index = ""
    if "idiomaticity" in st.session_state["cq"]["dialog"][current_counter]:
        default_idiomaticity = st.session_state["cq"]["dialog"][current_counter]["idiomaticity"]
    else:
        default_idiomaticity = 1
    default_c = st.session_state["cq"]["dialog"][current_counter]["concept"]
    if default_c == []:
        default_c = None
    default_g = st.session_state["cq"]["dialog"][current_counter]["graph"]
    if default_g == {}:
        default_g = None

#print("New sentence in this dialog, setting defaults")
else:
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])] = {
        "speaker": "",
        "text": "",
        "intent": "",
        "legacy index": "",
        "idiomaticity": 1,
        "predicate": "",
        "concept": [],
        "graph": {},
        "trimmed_graph": {}
    }
    default_legacy_index = ""
    default_s = "A"
    default_t = ""
    default_i = None
    default_p = None
    default_idiomaticity = 1
    default_f = None
    default_c = None
    default_g = {}
    default_tg = {}

colz.write(default_t)
with colz.expander("sentence descriptors", expanded=False):
    colf, colg = st.columns(2)
    lsi = colf.text_input("legacy sentence index", default_legacy_index)
    s = colf.selectbox("Speaker", ["A", "B"], index=["A", "B"].index(default_s))
    s_name = st.session_state["cq"]["speakers"][s]["name"]
    t = st.text_input(s_name + " says", value=default_t)

    idio = st.slider("idiomaticity evaluation (1 = should not be idiomatic, 5 = is most probably idiomatic)", 1, 5, value=default_idiomaticity)

    try:
        i = colg.multiselect("Intents", intent_list, default=default_i)
    except:
        i = colg.multiselect("Intents", intent_list)
        #colz.write("Original intents not found in intents.json, please select from the list")

    try:
        p = colg.multiselect("Predicate", predicate_list, default=default_p)
    except:
        p = colg.multiselect("Predicate", predicate_list)
        colg.write("Original predicates not found, please select from the list")

try:
    c = colz.multiselect("Concepts", list(concepts_kson.keys()), default=default_c)
except:
    c = colz.multiselect("Concepts", list(concepts_kson.keys()))
    #colz.write("Original concepts not found in concepts.json, please select from the list")

# if some concepts have been chosen, create concept graph with requirements or load if existing, otherwise clean st.session_state["req_json"]
if c == []:
    #print("CONCEPT MULTISELECT EMPTY")
    st.session_state["req_json"] = {}
else:
    if c != st.session_state["concept_set"]:
        st.session_state["concept_set"] = c

if colz.button("Initialize particularization graph with {}".format(c)):
    st.session_state["req_json"] = graphs_utils.create_requirement_graph(c, concepts_kson)
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]

if st.session_state["req_json"] != {}:
    # focus on nodes with empty requires, end of requirement chain
    # [expression for item in iterable if condition]
    req_leaves = [r for r in st.session_state["req_json"].keys() if st.session_state["req_json"][r]["requires"] == []]

    # The user will be asked to fill in the values for the leaves of the requirement graph.
    # If the requirement leaf is a terminal feature in the grammar graph (i.e. it has children that are all leaves)
    # the user will be asked to choose a value from the children of the feature node.
    # If the requirement leaf is a non terminal feature in the grammar graph (i.e. it has children that are not all leaves)
    # the user will be asked to navigate the grammar graph to a terminal node with leaves being values, and choose a value.

    if not st.session_state["path_in_progress"]:
        tmp_req = colz.selectbox("Pick a requirement", req_leaves)
        if colz.button("set starting item to {}".format(tmp_req)):
            st.session_state["starting_item"] = tmp_req
            st.session_state["current_concept_node"] = st.session_state["req_json"][st.session_state["starting_item"]]["path"][-1]
            st.session_state["path_in_progress"] = True
            st.rerun()

    if st.session_state["path_in_progress"]:
        colz.subheader("Input in progress")
        if colz.button("cancel"):
            st.session_state["path_in_progress"] = False
            st.rerun()
        colz.write("Input for {} in progress".format(st.session_state["starting_item"]))
        #colz.write("Current node: {}".format(st.session_state["current_concept_node"]))

        #is the current node a terminal feature?
        current_node_leaves = sorted(graphs_utils.get_leaves_from_node(concepts_kson, st.session_state["current_concept_node"]), key=str.lower)
        current_node_children = sorted(graphs_utils.get_children(concepts_kson, st.session_state["current_concept_node"]), key=str.lower)
        if current_node_leaves == current_node_children or current_node_children == [] or st.session_state["current_concept_node"]=="ABSOLUTE REFERENCE":
            st.session_state["is_terminal_feature"] = True
            #print("{} is a TERMINAL FEATURE".format(st.session_state["current_concept_node"]))
        else:
            st.session_state["is_terminal_feature"] = False
            #print("{} is NOT A TERMINAL FEATURE".format(st.session_state["current_concept_node"]))

        #if the current node is a terminal feature, ask the user to choose a value if there are values to choose from.
        if st.session_state["is_terminal_feature"]:
            #print("terminal feature")
            if st.session_state["current_concept_node"] == "ABSOLUTE REFERENCE":
                #print("absolute reference")
                # If the requirement is an absolute reference, the user will be asked to choose a value from the set of concepts in the questionnaire.
                req_value = colz.selectbox("Choose value", st.session_state["concept_set"] + ["None"])
                if colz.button("Set to {}?".format(req_value)):
                    if req_value == "None":
                        st.session_state["req_json"][st.session_state["starting_item"]]["value"] = st.session_state["current_concept_node"]
                        #print("Set {} to {}".format(st.session_state["starting_item"], st.session_state["current_concept_node"]))
                        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]
                        st.session_state["path_in_progress"] = False
                        st.rerun()
                    else:
                        st.session_state["req_json"][st.session_state["starting_item"]]["value"] = req_value
                        #print("Set {} to {}".format(st.session_state["starting_item"], req_value))
                        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]
                        st.session_state["path_in_progress"] = False
                        st.rerun()
            else:
                #print("terminal feature that is not an absolute reference")
                if current_node_children != []:
                    req_value = colz.selectbox("Choose value", current_node_children)
                else:
                    req_value = st.session_state["current_concept_node"]
                if colz.button("set to {}?".format(req_value)):
                    st.session_state["req_json"][st.session_state["starting_item"]]["value"] = req_value
                    #print("Set {} to {}".format(st.session_state["starting_item"], req_value))
                    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]
                    st.session_state["path_in_progress"] = False
                    st.rerun()

        #if the current node is not a terminal feature, ask the user to navigate the grammar graph to a terminal node with leaves being values, and choose a value.
        else:
            #colz.write("The current grammar node is not a terminal feature, navigate to a terminal feature to choose a value")
            # currently not allowing direct inputs of deictic. They have to be conceps introduced in the sentence.
            if current_node_children == ["ABSOLUTE REFERENCE", "DEICTIC"]:
                st.session_state["current_concept_node"] = "ABSOLUTE REFERENCE"
                st.rerun()
            else:
                next_node = colz.selectbox("navigate to", current_node_children)
                if colz.button("go to {}".format(next_node)):
                    st.session_state["current_concept_node"] = next_node
                    st.rerun()

with colz.container():
    colu, coli, colo = st.columns(3)
    if colu.button("Validate sentence"):
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["legacy index"] = lsi
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["speaker"] = s
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["text"] = t
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["idiomaticity"] = idio
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["intent"] = i
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["predicate"] = p
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["concept"] = c
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]
        if st.session_state["req_json"] != {}:
            trimmed_graph = graphs_utils.arrange_requirement_graph_for_display(st.session_state["req_json"])
            st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["trimmed_graph"] = trimmed_graph
        else:
            st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["trimmed_graph"] = {}
        colu.success("validated sentence #{}".format(st.session_state["counter"]))
        #print(st.session_state["cq"]["dialog"][str(st.session_state["counter"])])
        st.rerun()

    coli.download_button(label="download your Conversational Questionnaire", data=json.dumps(st.session_state["cq"], indent=4),
                       file_name="cq_" + st.session_state["cq"]["title"] + "_" + st.session_state["uid"] + ".json")

    if colo.button("Reset sentence"):
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["legacy index"] = ""
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["idiomaticity"] = 1
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["speaker"] = "A"
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["text"] = ""
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["intent"] = []
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["predicate"] = []
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["concept"] = []
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = {}
        st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["trimmed_graph"] = {}
        st.rerun()

#visualization of requirement graph
if st.session_state["req_json"] != {}:

    displayed_graph = graphs_utils.arrange_requirement_graph_for_display(st.session_state["req_json"])

    nodes = []
    edges = []

    # list all values (to remove edges between "sentence" and any node that is a value)
    values = []
    for item in displayed_graph.keys():
        if displayed_graph[item]["value"] != "":
            values.append(displayed_graph[item]["value"])
    #print("VALUES:", values)

    # The graph drawing logic is as follows:
    # 1) Beyond the concept nodes entered by the user, only dependency nodes that received input from the user are drawn.
    # 2) When a concept node has a path leading to another node, it disconnects from the "sentence" node.

    # ---- nodes
    for item in displayed_graph.keys():
        #print("ITEM TO DISPLAY:", displayed_graph[item])
        if not graphs_utils.is_agraph_node(item, nodes):
            if item == "sentence":
                size = 20
                color = "pink"
            elif displayed_graph[item]["is_required_by"] == ['sentence']:
                size = 30
                color = "red"
            else:
                size = 15
                color = "blue"
            nodes.append(Node(id=item,
                              label=item,
                              size=size,
                              color=color,
                              title=item,
                              symbolType="circle"))
            if displayed_graph[item]["value"] != "":
                if not graphs_utils.is_agraph_node(displayed_graph[item]["value"], nodes):
                    nodes.append(Node(id=displayed_graph[item]["value"],
                                      label=displayed_graph[item]["value"],
                                      size=8,
                                      color="green",
                                      title=displayed_graph[item]["value"],
                                      symbolType="square"))
    # ---- edges
    for item in displayed_graph.keys():
        for req in displayed_graph[item]["is_required_by"]:
            if item not in values and req != ["sentence"]:
                if not graphs_utils.is_agraph_edge(item, req, edges):
                    edges.append(Edge(source=item,
                                      target=req,
                                      physics=True,
                                      smooth=True,
                                      type="DYNAMIC",
                                      color="grey"))

        if displayed_graph[item]["value"] != "":
            if not graphs_utils.is_agraph_node(displayed_graph[item]["value"], nodes):
                nodes.append(Node(id=displayed_graph[item]["value"],
                                  label=displayed_graph[item]["value"],
                                  size=8,
                                  color="green",
                                  title=displayed_graph[item]["value"],
                                  symbolType="square"))
            if not graphs_utils.is_agraph_edge(item, displayed_graph[item]["value"], edges):
                edges.append(Edge(source=displayed_graph[item]["value"],
                                  target=item,
                                  dashes=True,
                                  physics=True,
                                  smooth=True,
                                  type="DYNAMIC",
                                  color="green"))
    # add intent to displayed graph
    nodes.append(Node(id="-".join(i),
                      label="-".join(i),
                      size=20,
                      color="yellow",
                      title=i,
                      symbolType="circle"))
    edges.append(Edge(source="-".join(i),
                    target="sentence",
                    physics=True,
                    smooth=True,
                    type="DYNAMIC",
                    color="grey"))
    # add predicate to displayed graph if it's not empty
    if p != []:
        nodes.append(Node(id="-".join(p),
                          label="-".join(p),
                          size=20,
                          color="orange",
                          title=p,
                          symbolType="circle"))
        edges.append(Edge(source="-".join(p),
                        target="sentence",
                        physics=True,
                        smooth=True,
                        type="DYNAMIC",
                        color="grey"))

    # ---- graph
    config = Config(width=800,
                        height=800,
                        directed=True,
                        physics=True,
                        hierarchical=False,
                        nodeHighlightBehavior=True,
                        highlightColor="#F7A7A6",  # or "blue"
                        collapsible=True,
                        automaticRearrangeAfterDropNode=False,
                        node={'labelProperty': 'label'},
                        link={'labelProperty': 'label', 'renderLabel': True}
                        # **kwargs e.g. node_size=1000 or node_color="blue"
                        )

    with colx.container():
        return_value = agraph(nodes=nodes,
                              edges=edges,
                              config=config)


# st.subheader("Current questionnaire")
# st.write(st.session_state["cq"])
# st.write("req_json")
# st.write(st.session_state["req_json"])
# st.write("concepts")
# st.write(st.session_state["concept_set"])
    
    


