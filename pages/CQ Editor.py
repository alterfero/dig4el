import streamlit as st
import json
from libs import graphs_utils
from libs import utils
import time
from streamlit_agraph import agraph, Node, Edge, Config

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
                "gender": "xx",
                "age": "adult"
            },
            "B": {
                "name": "xx",
                "gender": "xx",
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

st.title("Conversational Questionnaire Editor")

concepts_kson = json.load(open("./data/concepts.json"))
intents_kson = json.load(open("./data/intents.json"))

st.write("You can start a new questionnaire right away, or load an existing one")
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
    default_a_name = ""
    default_a_gender = "indef"
    default_b_name = ""
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
    b_name = st.text_input("Speaker B Name")
    b_gender = st.selectbox("Gender",["male", "female", "indef"], index=["male", "female", "indef"].index(default_b_gender), key="b_gender")
    colj, colk = st.columns(2)
    if colj.button("Submit header"):
        st.session_state["cq"]["title"] = title
        st.session_state["cq"]["context"] = context
        st.session_state["cq"]["speakers"]["A"]["name"] = a_name
        st.session_state["cq"]["speakers"]["B"]["name"] = b_name
        st.session_state["cq"]["speakers"]["A"]["gender"] = a_gender
        st.session_state["cq"]["speakers"]["B"]["gender"] = b_gender
        colk.success("Header submitted")

st.subheader("Dialog")
colq, colw = st.columns(2)
if colq.button("Previous"):
    if st.session_state["counter"] > 1:
        st.session_state["counter"] = st.session_state["counter"] - 1
        st.rerun()
if colw.button("Next"):
        st.session_state["counter"] = st.session_state["counter"] + 1
        st.rerun()

colq.subheader("Sentence #"+str(st.session_state.counter))
if colw.button("Reset this sentence"):
    del(st.session_state["cq"]["dialog"][str(st.session_state["counter"])])
    st.rerun()

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
    if default_i == "":
        default_i = None
    default_c = st.session_state["cq"]["dialog"][current_counter]["concept"]
    if default_c == []:
        default_c = None
    default_g = st.session_state["cq"]["dialog"][current_counter]["graph"]
    if default_g == {}:
        default_g = None

else:
    print("New sentence in this dialog, setting defaults")
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])] = {
        "speaker": "",
        "text": "",
        "intent": "",
        "concept": [],
        "graph": {},
    }
    default_s = "A"
    default_t = ""
    default_i = None
    default_f = None
    default_c = None
    default_g = {}

s = st.selectbox("Speaker", ["A", "B"], index=["A", "B"].index(default_s))
s_name = st.session_state["cq"]["speakers"][s]["name"]
t = st.text_input(s_name + " says", value=default_t)

try:
    i = st.multiselect("Intents", list(intents_kson.keys()), default=default_i)
except:
    i = st.multiselect("Intents", list(intents_kson.keys()))
    st.write("Original intents not found in intents.json, please select from the list")
try:
    c = st.multiselect("Concepts", list(concepts_kson.keys()), default=default_c)
except:
    c = st.multiselect("Concepts", list(concepts_kson.keys()))
    st.write("Original concepts not found in concepts.json, please select from the list")

# if some concepts have been chosen, create concept graph with requirements or load if existing, otherwise clean st.session_state["req_json"]
if c == []:
    st.session_state["req_json"] = {}
else:
    if c != st.session_state["concept_set"]:
        st.session_state["concept_set"] = c

    if st.session_state["req_json"] != {}:
        print("Using current requirement graph for this sentence.")
    else:
        print("No existing requirement graph: Computing requirement graph for this sentence")
        st.session_state["req_json"] = graphs_utils.create_requirement_graph(c, concepts_kson)
    # focus on nodes with empty requires, end of requirement chain
    # [expression for item in iterable if condition]
    req_leaves = [r for r in st.session_state["req_json"].keys() if st.session_state["req_json"][r]["requires"] == []]

    # The use will be asked to fill in the values for the leaves of the requirement graph.
    # If the requirement leaf is a terminal feature in the grammar graph (i.e. it has children that are all leaves)
    # the user will be asked to choose a value from the children of the feature node.
    # If the requirement leaf is a non terminal feature in the grammar graph (i.e. it has children that are not all leaves)
    # the user will be asked to navigate the grammar graph to a terminal node with leaves being values, and choose a value.

    # st.write("Input is needed for the following requirements:")
    # for req in req_leaves:
    #     req_string = ""
    #     for req in st.session_state["req_json"][req]["path"]:
    #         req_string += "--> " + req
    #     st.write(req_string)

    if not st.session_state["path_in_progress"]:
        tmp_req = st.selectbox("Pick a requirement", req_leaves)
        if st.button("set starting item to {}".format(tmp_req)):
            st.session_state["starting_item"] = tmp_req
            st.session_state["current_concept_node"] = st.session_state["req_json"][st.session_state["starting_item"]]["path"][-1]
            st.session_state["path_in_progress"] = True
            st.rerun()

    if st.session_state["path_in_progress"]:
        st.subheader("Input in progress")
        if st.button("cancel"):
            st.session_state["path_in_progress"] = False
            st.rerun()
        st.write("Input for {} in progress".format(st.session_state["starting_item"]))
        st.write("Current node: {}".format(st.session_state["current_concept_node"]))

        #is the current node a terminal feature?
        current_node_leaves = graphs_utils.get_leaves_from_node(concepts_kson, st.session_state["current_concept_node"])
        current_node_children = graphs_utils.get_children(concepts_kson, st.session_state["current_concept_node"])
        if current_node_leaves == current_node_children or current_node_children == [] or st.session_state["current_concept_node"]=="ABSOLUTE REFERENCE":
            st.session_state["is_terminal_feature"] = True
            print("{} is a TERMINAL FEATURE".format(st.session_state["current_concept_node"]))
        else:
            st.session_state["is_terminal_feature"] = False
            print("{} is NOT A TERMINAL FEATURE".format(st.session_state["current_concept_node"]))

        #if the current node is a terminal feature, ask the user to choose a value if there are values to choose from.
        if st.session_state["is_terminal_feature"]:
            print("terminal feature")
            if st.session_state["current_concept_node"] == "ABSOLUTE REFERENCE":
                print("absolute reference")
                # If the requirement is an absolute reference, the user will be asked to choose a value from the set of concepts in the questionnaire.
                req_value = st.selectbox("Choose value", st.session_state["concept_set"] + ["None"])
                if st.button("Set to {}?".format(req_value)):
                    if req_value == "None":
                        st.session_state["req_json"][st.session_state["starting_item"]]["value"] = st.session_state["current_concept_node"]
                        st.write("Set {} to {}".format(st.session_state["starting_item"], st.session_state["current_concept_node"]))
                        st.session_state["path_in_progress"] = False
                        st.rerun()
                    else:
                        st.session_state["req_json"][st.session_state["starting_item"]]["value"] = req_value
                        st.write("Set {} to {}".format(st.session_state["starting_item"], req_value))
                        st.session_state["path_in_progress"] = False
                        st.rerun()
            else:
                print("terminal feature that is not not an absolute reference")
                if current_node_children != []:
                    req_value = st.selectbox("Choose value", current_node_children)
                else:
                    req_value = st.session_state["current_concept_node"]
                if st.button("set to {}?".format(req_value)):
                    st.session_state["req_json"][st.session_state["starting_item"]]["value"] = req_value
                    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]
                    st.success("Set {} to {}".format(st.session_state["starting_item"], req_value))
                    st.session_state["path_in_progress"] = False
                    st.rerun()

        #if the current node is not a terminal feature, ask the user to navigate the grammar graph to a terminal node with leaves being values, and choose a value.
        else:
            st.write("The current grammar node is not a terminal feature, navigate to a terminal feature to choose a value")
            next_node = st.selectbox("navigate to", current_node_children)
            if st.button("go to {}".format(next_node)):
                st.session_state["current_concept_node"] = next_node
                st.rerun()

colq, colw = st.columns(2)
if colq.button("Validate sentence"):
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["speaker"] = s
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["text"] = t
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["intent"] = i
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["concept"] = c
    st.session_state["cq"]["dialog"][str(st.session_state["counter"])]["graph"] = st.session_state["req_json"]
    colq.success("validated sentence #{}".format(st.session_state["counter"]))
    #print(st.session_state["cq"]["dialog"][str(st.session_state["counter"])])
    st.rerun()
if colw.button("Save questionnaire"):
    cq_file_name = "cq_"+ st.session_state["cq"]["title"] + "_" + st.session_state["uid"] + ".json"
    json.dump(st.session_state["cq"], open("./questionnaires/"+cq_file_name, "w"))
    colw.success("Saved questionnaire as {}".format(cq_file_name))

#visualization of requirement graph
if st.session_state["req_json"] != {}:
    st.subheader("Requirement graph")
    nodes = []
    edges = []

    for item in st.session_state["req_json"].keys():
        if not graphs_utils.is_agraph_node(item, nodes):
            if item=="sentence":
                size=20
                color="pink"
            else:
                size=15
                color="blue"
            nodes.append(Node(id=item,
                              label=item,
                              size=size,
                              color=color,
                              title=item,
                              symbolType="circle"))
        for req in st.session_state["req_json"][item]["requires"]:
            if not graphs_utils.is_agraph_node(req, nodes):
                nodes.append(Node(id=req,
                                  label=req,
                                  size=15,
                                  color="blue",
                                  title=req,
                                  symbolType="circle"))
            if not graphs_utils.is_agraph_edge(item, req, edges):
                edges.append(Edge(source=item,
                                  target=req,
                                  physics=True,
                                  smooth=True,
                                  type="DYNAMIC",
                                  color="grey"))
        if st.session_state["req_json"][item]["value"] != "":
            if not graphs_utils.is_agraph_node(st.session_state["req_json"][item]["value"], nodes):
                nodes.append(Node(id=st.session_state["req_json"][item]["value"],
                                  label=st.session_state["req_json"][item]["value"],
                                  size=8,
                                  color="green",
                                  title=st.session_state["req_json"][item]["value"],
                                  symbolType="square"))
            if not graphs_utils.is_agraph_edge(item, st.session_state["req_json"][item]["value"], edges):
                edges.append(Edge(source=item,
                                  target=st.session_state["req_json"][item]["value"],
                                  dashes=True,
                                  physics=True,
                                  smooth=True,
                                  type="DYNAMIC",
                                  color="green"))
    # ---- graph
    config = Config(width=800,
                        height=600,
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
    return_value = agraph(nodes=nodes,
                          edges=edges,
                          config=config)


#st.subheader("Current questionnaire")
#st.write(st.session_state["cq"])
st.write(st.session_state["req_json"])
st.write(st.session_state["cq"]["dialog"][str(st.session_state["counter"])])
    
    


