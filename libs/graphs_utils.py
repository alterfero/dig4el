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

import networkx as nx
import json
from libs import utils
from streamlit_agraph import agraph, Node, Edge, Config

def load_json(json_filename):
    with open("./data/"+json_filename) as knowledge_file:
        kf = knowledge_file.read()
        kkf = kf.replace("'", '"')
        knowledge_json = json.loads(kkf)
    return knowledge_json


def verify_ontology_json(ontology_json):
    is_ok = True
    for key in ontology_json.keys():
        if ontology_json[key]["ontological parent"] not in ontology_json.keys() and ontology_json[key]["ontological parent"] != "self":
            print("ERROR: {} has a parent that is not in the ontology".format(key))
            is_ok = False
    return is_ok

def get_roots(ontology_json):
    roots = []
    for key in ontology_json.keys():
        if ontology_json[key]["ontological parent"] == "self":
            roots.append(key)
    return roots

def get_children(ontology_json, parent):
    children = []
    for key in ontology_json.keys():
        if ontology_json[key]["ontological parent"] == parent:
            children.append(key)
    return children

def get_all_leaves(ontology_json):
    leaves = []
    for key in ontology_json.keys():
        if get_children(ontology_json, key) == []:
            leaves.append(key)
    return leaves

def get_leaves_from_node(ontology_json, node):
    # get all the leaves issued from a node
    leaves = []
    children = get_children(ontology_json, node)
    if children == []:
        leaves.append(node)
    else:
        for child in children:
            leaves = leaves + get_leaves_from_node(ontology_json, child)
    return leaves

def inherit_required_features(ontology_json, feature):
    required_features = []
    if ontology_json[feature]["ontological parent"] != "self":
        required_features = required_features + inherit_required_features(ontology_json, ontology_json[feature]["ontological parent"])
    required_features = required_features + ontology_json[feature]["requires"]
    return list(set(required_features))

def get_genealogy(concept_graph, node):
    current_node = node
    parents = []
    while concept_graph[current_node]["ontological parent"] != "self" and concept_graph[current_node]["ontological parent"] != "sentence":
        parents.append(concept_graph[current_node]["ontological parent"])
        current_node = concept_graph[current_node]["ontological parent"]
    return parents

def create_features_graph():
    g = nx.DiGraph()
    features_kson = load_json("../data/features.json")
    features_ontology_json_ok = verify_ontology_json(features_kson)
    if features_ontology_json_ok:
        changed = True
        counter = 0
        # feature graph creation logic based on the JSON file
        while changed and counter < 100:
            changed = False
            for feature in features_kson.keys():
                # print("feature {}".format(feature))
                if (feature, "feature") not in g.nodes():
                    g.add_node((feature, "feature"))
                    # print("added node {}".format(feature))
                    changed = True
                if features_kson[feature]["ontological parent"] != "self" and features_kson[feature][
                    "ontological parent"] not in g.nodes():
                    g.add_node((features_kson[feature]["ontological parent"], "feature"))
                    # print("added node {}".format(features_kson[feature]["ontological parent"]))
                    changed = True
                    if (
                    (features_kson[feature]["ontological parent"], "feature"), (feature, "feature")) not in g.edges():
                        g.add_edge((features_kson[feature]["ontological parent"], "feature"), (feature, "feature"),
                                   object={"type": features_kson[feature]["type"]})
                        # print("added edge {} -> {}".format(features_kson[feature]["ontological parent"], feature))
                        changed = True
            counter += 1
    else:
        print("ERROR: ontology JSON is not valid")
    return g


def create_concepts_graph():
    g = nx.DiGraph()
    concepts_kson = load_json("../data/concepts.json")
    concepts_ontology_json_ok = verify_ontology_json(concepts_kson)
    if concepts_ontology_json_ok:
        changed = True
        counter = 0
        while changed and counter < 100:
            changed = False
            for concept in concepts_kson.keys():
                # print("concept {}".format(concept))
                if (concept, "concept") not in g.nodes():
                    g.add_node((concept, "concept"))
                    # print("added node {}".format(concept))
                    changed = True
                if concepts_kson[concept]["ontological parent"] != "self" and concepts_kson[concept][
                    "ontological parent"] not in g.nodes():
                    g.add_node((concepts_kson[concept]["ontological parent"], "concept"))
                    # print("added node {}".format(concepts_kson[concept]["ontological parent"]))
                    changed = True
                    if (
                    (concepts_kson[concept]["ontological parent"], "concept"), (concept, "concept")) not in g.edges():
                        g.add_edge((concepts_kson[concept]["ontological parent"], "concept"), (concept, "concept"))
                        # print("added edge {} -> {}".format(concepts_kson[concept]["ontological parent"], concept))
                        changed = True
            counter += 1
    else:
        print("ERROR: ontology JSON is not valid")
    return g


def get_recordings_graph(recordings):
    """create a graph from a list of recordings, with nodes as words and edges as concepts and features
    connected to these words"""
    g = create_features_graph()
    # create a graph from the recordings
    for recording in recordings:
        words_list = list(set(utils.tokenize(utils.clean_sentence(recording["recording"]))))
        for word in words_list:
            if (word, "word") not in g.nodes():
                g.add_node((word, "word"))
            if "features" in recording["cq"].keys():
                for feature in recording["cq"]["features"]:
                    if (feature,"feature") not in g.nodes():
                        g.add_node((feature, "feature"))
                    if ((feature, "feature"), (word, "word")) not in g.edges():
                        g.add_edge((feature, "feature"), (word, "word"))
            else:
                print("WARNING: recording {} has no feature".format(recording["recording"]))
    return g

def create_requirement_graph(concept_list, concept_kson):
    # takes a list of concepts and creates a json representing a graph of all the concepts and features required
    g = {"sentence": {"is_required_by": ["self"], "requires": concept_list, "path": ["sentence"], "value": ""}}
    # for each concept in concept_list, recursively explore the required features and add them to the graph with the proper linkage
    for concept in concept_list:
        #print("concept: ", concept)
        g[concept] = {"is_required_by": ["sentence"], "requires": [], "path":["sentence", concept], "value": ""}
        require1 = inherit_required_features(concept_kson, concept)
        for req1 in require1:
            #print("req1: ", req1)
            req1_name = concept + " " + req1
            g[concept]["requires"].append(req1_name)
            g[req1_name] = {"is_required_by": [concept], "requires": [], "path":["sentence", concept, req1], "value": ""}
            if concept_kson[req1]["requires"] != []:
                require2 = concept_kson[req1]["requires"]
                for req2 in require2:
                    req2_name = req1_name + " " + req2
                    g[req1_name]["requires"].append(req2_name)
                    g[req2_name] = {"is_required_by": [req1_name], "requires": [], "path":["sentence", concept, req1, req2], "value": ""}
                    if concept_kson[req2]["requires"] != []:
                        require3 = concept_kson[req2]["requires"]
                        for req3 in require3:
                            req3_name = req2_name + " " + req3
                            g[req2_name]["requires"].append(req3_name)
                            g[req3_name] = {"is_required_by": [req2_name], "requires": [], "path":["sentence", concept, req1, req2, req3], "value": ""}
                            if concept_kson[req3]["requires"] != []:
                                require4 = concept_kson[req3]["requires"]
                                for req4 in require4:
                                    req4_name = req3_name + " " + req4
                                    g[req3_name]["requires"].append(req4_name)
                                    g[req4_name] = {"is_required_by": [req3_name], "requires": [], "path":["sentence", concept, req1, req2, req3, req4], "value": ""}
                                    if concept_kson[req4]["requires"] != []:
                                        require5 = concept_kson[req4]["requires"]
                                        for req5 in require5:
                                            req5_name = req4_name + " " + req5
                                            g[req4_name]["requires"].append(req5_name)
                                            g[req5_name] = {"is_required_by": [req4_name], "requires": [], "path":["sentence", concept, req1, req2, req3, req4, req5], "value": ""}
    return g

def create_requirement_graph_recursive(concept_list, concept_json):
    def add_requirements(node, path, graph):
        # Create a unique node name based on the path
        node_name = f"{path} {node}".strip()
        if node_name in graph:
            return node_name

        # Initialize the node in the graph
        graph[node_name] = {"is_required_by": [path.strip()] if path else [], "requires": []}

        # Recursively add requirements
        for requirement in concept_json.get(node, {}).get("requires", []):
            requirement_name = add_requirements(requirement, node_name, graph)
            if requirement_name not in graph[node_name]["requires"]:
                graph[node_name]["requires"].append(requirement_name)

        return node_name

    graph = {}
    for concept in concept_list:
        add_requirements(concept, "", graph)

    return graph



def is_agraph_node(id, node_list):
    is_node = False
    for node in node_list:
        if node.id == id:
            is_node = True
    return is_node
def is_agraph_edge(source, target, edge_list):
    is_edge = False
    for edge in edge_list:
        if edge == Edge(source=source,
                              target=target,
                              physics=True,
                              smooth=True,
                              type="DYNAMIC",
                              color="grey"):
            is_edge = True
    return is_edge

def arrange_requirement_graph_for_display(requirement_graph):
    arranged_graph = {}
    # add the concepts directly connected to the sentence node
    for node in requirement_graph:
        if "sentence" in requirement_graph[node]["is_required_by"]:
            arranged_graph[node] = {"is_required_by": requirement_graph[node]["is_required_by"], "requires": requirement_graph[node]["requires"],
                                    "path": ["sentence", node], "value": requirement_graph[node]["value"]}
    # test all the graph branches starting at the sentence node, keep those where the leaf has a non-empty value or is required by the sentence or self nodes
    paths_to_leaves = list_paths_to_leaves(requirement_graph, "sentence")
    #print("PATHS TO LEAVES: ", paths_to_leaves)
    for path in paths_to_leaves:
        leaf = path[-1]
        if requirement_graph[leaf]["value"] != "" or "sentence" in requirement_graph[leaf]["is_required_by"] or "self" in requirement_graph[leaf]["is_required_by"]:
            #print("SELECTED PATH: ", path)
            # add the path to the arranged_graph
            current_node = "sentence"
            for node in path:
                if node not in arranged_graph:
                    arranged_graph[node] = {"is_required_by": requirement_graph[node]["is_required_by"], "path": [], "value": requirement_graph[node]["value"]}
                arranged_graph[node]["path"].append(current_node)
                current_node = node

        #bypass nodes with a label ending in "REFERENCE TO CONCEPT" and remove them for visual clarity
        #print("REFERENCE TO CONCEPT NODE BYPASS")
        for node in arranged_graph.keys():
            kill_list = []
            if node.endswith("REFERENCE TO CONCEPT"):
                #print("node ***{}*** is a REFERENCE TO CONCEPT".format(node))
                #bypass: pass its reference value to its parents
                parents = arranged_graph[node]["is_required_by"]
                for parent in parents:
                    arranged_graph[parent]["value"] = arranged_graph[node]["value"]
                #and get on the kill list
                kill_list.append(node)
        for k in kill_list:
            #print("KILL LIST: ", kill_list)
            try:
                del arranged_graph[k]
            except KeyError:
                print("node {} not found in arranged_graph".format(k))
                pass
    return arranged_graph


def list_paths_to_leaves(graph, start_node, end_node='sentence'):
    #using DFS "Depth-First Search" to list all the paths from the start_node to leaves
    #a leaf is a node that has no children or that is connected to the "sentence" node.
    def dfs(current_node, path):
        if current_node not in graph or not graph[current_node].get("requires"):
            paths.append(path)
            return

        for child in graph[current_node]["requires"]:
            dfs(child, path + [child])

    paths = []
    dfs(start_node, [start_node])
    return paths


def list_sentences_with_value_v(v):
    l = []
