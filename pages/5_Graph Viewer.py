import networkx as nx
import pandas as pd
from libs import graphs_utils
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

features_kson = graphs_utils.load_json("features.json")
features_ontology_json_ok = graphs_utils.verify_ontology_json(features_kson)
concepts_kson = graphs_utils.load_json("concepts.json")
concepts_ontology_json_ok = graphs_utils.verify_ontology_json(graphs_utils.load_json("concepts.json"))
roots = graphs_utils.get_roots(concepts_kson)
leaves = graphs_utils.get_all_leaves(concepts_kson)

show_concepts = True
show_features = False

if features_ontology_json_ok and concepts_ontology_json_ok:
    g = nx.DiGraph()
    # ---- GRAPH CREATION
    # ---- feature graph creation logic based on the JSON file
    if show_features:
        changed = True
        counter = 0
        # feature graph creation logic based on the JSON file
        while changed and counter < 100:
            changed = False
            for feature in features_kson.keys():
                #print("feature {}".format(feature))
                if (feature, "feature") not in g.nodes():
                    g.add_node((feature, "feature"))
                    #print("added node {}".format(feature))
                    changed = True
                if features_kson[feature]["ontological parent"] != "self" and features_kson[feature]["ontological parent"] not in g.nodes():
                    g.add_node((features_kson[feature]["ontological parent"], "feature"))
                    #print("added node {}".format(features_kson[feature]["ontological parent"]))
                    changed = True
                    if ((features_kson[feature]["ontological parent"], "feature"), (feature, "feature")) not in g.edges():
                        g.add_edge((features_kson[feature]["ontological parent"], "feature"), (feature, "feature"), object={"type": features_kson[feature]["type"]})
                        #print("added edge {} -> {}".format(features_kson[feature]["ontological parent"], feature))
                        changed = True
            counter += 1
    # concept graph creation logic based on the JSON file
    if show_concepts:
        changed = True
        counter = 0
        while changed and counter < 100:
            changed = False
            for concept in concepts_kson.keys():
                #print("concept {}".format(concept))
                if (concept, "concept") not in g.nodes():
                    g.add_node((concept, "concept"))
                    #print("added node {}".format(concept))
                    changed = True
                if concepts_kson[concept]["ontological parent"] != "self" and concepts_kson[concept]["ontological parent"] not in g.nodes():
                    g.add_node((concepts_kson[concept]["ontological parent"], "concept"))
                    #print("added node {}".format(concepts_kson[concept]["ontological parent"]))
                    changed = True
                    if ((concepts_kson[concept]["ontological parent"], "concept"), (concept, "concept")) not in g.edges():
                        g.add_edge((concepts_kson[concept]["ontological parent"], "concept"), (concept, "concept"))
                        #print("added edge {} -> {}".format(concepts_kson[concept]["ontological parent"], concept))
                        changed = True
            counter += 1
    # ---- VISUALIZATION: networkx graph to a-graph
    nodes = []
    edges = []
    for networkx_node in g.nodes():
        #print("adding node {}".format(networkx_node[0]))
        if networkx_node[0] in roots:
            size = 20
            color = "blue"
        else:
            size = 15
            if networkx_node[1] == "feature":
                if networkx_node[0] in leaves:
                    color = "green"
                else:
                    color = "lightblue"
            elif networkx_node[1] == "intent":
                color = "orange"
            elif networkx_node[1] == "mood":
                color = "lightgreen"
            elif networkx_node[1] == "concept":
                if networkx_node[0] in leaves:
                    color = "pink"
                else:
                    color = "brown"
        nodes.append(Node(id=networkx_node[0],
                          label=networkx_node[0],
                          size=size,
                          color=color,
                          title=networkx_node[0],
                          symbolType="circle"))
    for networkx_edge in g.edges():
        edge_color = "darkgrey"
        edges.append(Edge(source=networkx_edge[0][0],
                          target=networkx_edge[1][0],
                          color=edge_color,
                          strokeWidth=15,
                          type="STRAIGHT"))
    config = Config(width=1500,
                    height=1500,
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

else:
    st.write("ERROR")
    st.write("features_ontology_json_ok: {}".format(features_ontology_json_ok))
    st.write("concepts_ontology_json_ok: {}".format(concepts_ontology_json_ok))
