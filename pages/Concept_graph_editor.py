import json
import time

import streamlit as st
from libs import utils
from libs import graphs_utils
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "focus" not in st.session_state:
    st.session_state["focus"] = "CONCEPT"
if "concepts_kson" not in st.session_state:
    st.session_state["concepts_kson"] = graphs_utils.load_json("concepts.json")

print("PAGE RELOAD")
print("focus: {}".format(st.session_state["focus"]))

# if st.button("SAVE"):
#     json.dump(st.session_state["concepts_kson"], open("./data/concepts.json", "w"))

def on_focus_change():
    print("callback says: focus changed to {}".format(st.session_state["focus"]))
def is_agraph_node(id, node_list):
    is_node = False
    for node in node_list:
        if node.id == id:
            is_node = True
    return is_node

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

cola, colb, colc = st.columns(3)
cola.subheader("Explore")
concept_key_list = list(st.session_state["concepts_kson"].keys()) + ["self"]
if st.session_state["focus"] not in concept_key_list:
    concept_index = 0
else:
    concept_index = concept_key_list.index(st.session_state["focus"])
new_focus = cola.selectbox("Change Focus", concept_key_list, on_change=on_focus_change, index=concept_index)
if new_focus != st.session_state["focus"]:
    st.session_state["focus"] = new_focus
    st.rerun()

parent = st.session_state["concepts_kson"][st.session_state["focus"]]["ontological parent"]
if cola.button("Up to {}".format(parent), key="jump to {}".format(parent)):
    if st.session_state["focus"] != "CONCEPT":
        st.session_state["focus"] = parent
        st.rerun()

children = graphs_utils.get_children(st.session_state["concepts_kson"], st.session_state["focus"])
selected_child = cola.selectbox("Focus on children", children)
if cola.button("Down to {}".format(selected_child), key="jump to {} at {}".format(selected_child, str(int(time.time())))):
    st.session_state["focus"] = selected_child
    print("focus change")
    st.rerun()

# EDIT FOCUS
colb.subheader("Edit {}".format(st.session_state["focus"]))
new_description = colb.text_input("DESCRIPTION", st.session_state["concepts_kson"][st.session_state["focus"]]["description"])
new_name = colb.text_input("NEW NAME", value=st.session_state["focus"], key="change name")
#new_type = colb.selectbox("TYPE", ["concept", "feature"], index=["concept", "feature"].index(st.session_state["concepts_kson"][st.session_state["focus"]]["type"]), key="change type")
new_parent = colb.selectbox("ONTOLOGICAL PARENT", concept_key_list, index=concept_key_list.index(st.session_state["concepts_kson"][st.session_state["focus"]]["ontological parent"]),key="change parent")
try:
    new_properties = colb.multiselect("INTRINSIC GRAMMATICALIZABLE PROPERTIES", concept_key_list, default=st.session_state["concepts_kson"][st.session_state["focus"]]["gramprop"], key="change properties")
except:
    new_properties = colb.multiselect("INTRINSIC GRAMMATICALIZABLE PROPERTIES", concept_key_list, key="change properties")
    st.warning("ERROR: gramprop list is not valid")
try:
    new_requires = colb.multiselect("PARTICULARIZATION AND RELATIONAL EDGES", concept_key_list, default=st.session_state["concepts_kson"][st.session_state["focus"]]["requires"], key="change requires")
except:
    new_requires = colb.multiselect("PARTICULARIZATION AND RELATIONAL EDGES", concept_key_list, key="change requires")
    st.warning("ERROR: requires list is not valid")
if colb.button("SUBMIT", key="submit changes"):
    st.session_state["concepts_kson"][st.session_state["focus"]]["description"] = new_description
    st.session_state["concepts_kson"][st.session_state["focus"]]["type"] = "concept"
    st.session_state["concepts_kson"][st.session_state["focus"]]["ontological parent"] = new_parent
    st.session_state["concepts_kson"][st.session_state["focus"]]["gramprop"] = new_properties
    st.session_state["concepts_kson"][st.session_state["focus"]]["requires"] = new_requires

    if new_name != st.session_state["focus"]:
        st.session_state["concepts_kson"][new_name] = st.session_state["concepts_kson"][st.session_state["focus"]]
        del st.session_state["concepts_kson"][st.session_state["focus"]]
        # update all the references to the old name in concepts_kson
        for concept in st.session_state["concepts_kson"]:
            if st.session_state["concepts_kson"][concept]["ontological parent"] == st.session_state["focus"]:
                st.session_state["concepts_kson"][concept]["ontological parent"] = new_name
            if st.session_state["concepts_kson"][concept]["requires"] != []:
                for req in st.session_state["concepts_kson"][concept]["requires"]:
                    if req == st.session_state["focus"]:
                        st.session_state["concepts_kson"][concept]["requires"].remove(req)
                        st.session_state["concepts_kson"][concept]["requires"].append(new_name)
        st.session_state["focus"] = new_name

    st.rerun()
if colb.button("DELETE"):
    if graphs_utils.get_children(st.session_state["concepts_kson"], st.session_state["focus"]) == []:
        p = st.session_state["concepts_kson"][st.session_state["focus"]]["ontological parent"]
        del st.session_state["concepts_kson"][st.session_state["focus"]]
        st.session_state["focus"] = "INTELLECT"
        colb.success("deleted")
        st.rerun()
    else:
        st.warning("This node has children, erase children first.")

# CREATE NEW CONCEPT
colc.subheader("Create")
new_name = colc.text_input("NAME")
new_description = colc.text_input("DESCRIPTION", key="new description")
#new_type = colc.selectbox("TYPE", ["concept", "feature"], key="new type")
new_parent = colc.selectbox("ONTOLOGICAL PARENT", concept_key_list, key="new parent")
new_gramprop = colc.multiselect("INTRINSIC GRAMMATICALIZABLE PROPERTIES", concept_key_list, key="new properties")
new_requires = colc.multiselect("PARTICULARIZATION AND RELATIONAL EDGES", concept_key_list, key="new require")
if colc.button("SUBMIT", key="submit new concept"):
    st.session_state["concepts_kson"][new_name] = {"description": new_description, "type": "concept", "ontological parent": new_parent, "gramprop": new_gramprop, "requires": new_requires}
    st.session_state["focus"] = new_name
    st.rerun()

# ---- VISUALIZATION of focus node, parents and children with a-graph
nodes = []
edges = []
# ---- focus node
nodes.append(Node(id=st.session_state["focus"],
                          label=st.session_state["focus"],
                          size=15,
                          color="blue",
                          title=st.session_state["focus"],
                          symbolType="circle"))
# ---- parents
nodes.append(Node(id=parent,
                          label=parent,
                          size=15,
                          color="brown",
                          title=parent,
                          symbolType="circle"))
edges.append(Edge(source=parent,
                  physics=True,
                  target=st.session_state["focus"],
                  type="SMOOTH",
                  color="brown"))
# ---- children
for child in children:
    nodes.append(Node(id=child,
                              label=child,
                              size=10,
                              color="green",
                              title=child,
                              symbolType="circle"))
    edges.append(Edge(source=st.session_state["focus"],
                      target=child,
                      physics=True,
                      type="SMOOTH",
                      color="green"))
# ---- requires with three degrees of inheritance
requires_list = graphs_utils.inherit_required_features(st.session_state["concepts_kson"], st.session_state["focus"])
#print("Require 1: {} requires {}".format(st.session_state["focus"], requires_list))
for require in requires_list:
    if not is_agraph_node(require, nodes):
        nodes.append(Node(id=require,
                          label=require,
                          size=8,
                          color="grey",
                          title=require,
                          symbolType="square"))
    edges.append(Edge(source=require,
                      target=st.session_state["focus"],
                      dashes=True,
                      physics=True,
                      smooth=True,
                      type="DYNAMIC",
                      color="grey"))
    req2 = graphs_utils.inherit_required_features(st.session_state["concepts_kson"], require)
    #print("Require 2: {} requires {}".format(require, req2))
    for r2 in req2:
        if not graphs_utils.is_agraph_node(r2, nodes):
            nodes.append(Node(id=r2,
                                      label=r2,
                                      size=7,
                                      color="grey",
                                      title=r2,
                                      symbolType="square"))
        edges.append(Edge(source=r2,
                          target=require,
                          dashes=True,
                          physics=True,
                          smooth=True,
                          type="DYNAMIC",
                          color="grey"))
        req3 = graphs_utils.inherit_required_features(st.session_state["concepts_kson"], r2)
        #print("Require 3: {} requires {}".format(r2, req3))
        for r3 in req3:
            if not graphs_utils.is_agraph_node(r3, nodes):
                nodes.append(Node(id=r3,
                                          label=r3,
                                          size=6,
                                          color="grey",
                                          title=r3,
                                          symbolType="square"))
            edges.append(Edge(source=r3,
                              target=r2,
                              dashes=True,
                              physics=True,
                              smooth=True,
                              type="DYNAMIC",
                              color="grey"))

# ---- graph
config = Config(width=800,
                    height=600,
                    directed=True,
                    physics=True,
                    dashed=True,
                    hierarchical=False,
                    nodeHighlightBehavior=True,
                    highlightColor="#F7A7A6",  # or "blue"
                    collapsible=True,
                    automaticRearrangeAfterDropNode=False,
                    node={'labelProperty': 'label'},
                    link={'labelProperty': 'label', 'renderLabel': True}
                    # **kwargs e.g. node_size=1000 or node_color="blue"
                    )
return_value = agraph(nodes=nodes,
                      edges=edges,
                      config=config)