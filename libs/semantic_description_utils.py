from __future__ import annotations

import copy
import json
import os
from libs import semantic_description_agents as sda
from typing import List, Tuple
from collections import defaultdict
import pkg_resources
from libs import utils as u

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
    "storage"
)

def description_dict_to_kw(description_dict: dict) -> List[str]:

    quantifiability = [p["features"].get("quantifiability", None)
                       for p in description_dict["referents"]
                       if p["features"].get("quantifiability", None) is not None]
    quantity = [p["features"].get("quantity", None)
                for p in description_dict["referents"]
                if p["features"].get("quantity", None) is not None]

    definiteness = [p["features"].get("definiteness", None)
                    for p in description_dict["referents"]
                    if p["features"].get("definiteness", None) is not None]

    reality = [p["features"].get("reality", None)
               for p in description_dict["referents"] if
               p["features"].get("reality", None) is not None]

    polarity = [p["features"].get("quantity", None)
                for p in description_dict["referents"]
                if p["features"].get("quantity", None) is not None]

    time_aspect = [p["features"].get("time_aspect", None)
                   for p in description_dict["referents"]
                   if p["features"].get("time_aspect", None) is not None]

    time_position = [p["features"].get("time_position", None)
             for p in description_dict["referents"] if
             p["features"].get("time_position", None) is not None]

    movement = [p["features"].get("movement", None)
             for p in description_dict["referents"] if
             p["features"].get("movement", None) is not None]

    space_location = [p["features"].get("space_location", None)
             for p in description_dict["referents"] if
             p["features"].get("space_location", None) is not None]

    intent = [description_dict["enunciation"].get("intent", None)]

    mood = [description_dict["enunciation"].get("mood", None)]

    voice = [description_dict["enunciation"].get("voice", None)]

    emphasis = [description_dict["enunciation"].get("emphasis", None)]

    predicate_types = [p["ptype"].get("type", None)
                       for p in description_dict["predicates"]]

    predicate_args = [a["role"]
                      for p in description_dict["predicates"]
                      for a in p["args"]]

    kw = []
    for v in [quantifiability, quantity, definiteness, reality, polarity, time_aspect, time_position,
              movement, space_location, intent, mood, voice, emphasis, predicate_types, predicate_args]:
        kw += v

    return kw


def TEST_add_description_and_keywords_to_sentence_pair(sentence_pair: dict) -> None | dict:
    source_sentence = sentence_pair.get("source", "")
    if source_sentence == "":
        print("No source in {}".format(sentence_pair))
        return None
    else:

        augmented_pair = {
                "source": sentence_pair["source"],
                "target": sentence_pair["target"],
                "description_dict": "description_dict",
                "description_text": "description_text",
                "grammatical_keywords": "keywords"
            }
        return augmented_pair


def add_description_and_keywords_to_sentence_pair(sentence_pair: dict) -> None | Tuple[dict, str]:
    source_sentence = sentence_pair.get("source", "")
    if source_sentence == "":
        print("No source in {}".format(sentence_pair))
        return None
    else:
        description = sda.describe_sentence_sync(source_sentence)
        keywords = description.get("grammatical_keywords", [])
        keywords += description_dict_to_kw(description)
        keywords = list(set(keywords))
        description["grammatical_keywords"] = keywords
        augmented_pair = copy.deepcopy(sentence_pair)
        augmented_pair["description"] = description

        # filename
        filename = u.clean_sentence(source_sentence, filename=True)

        return augmented_pair, filename

def build_keyword_index(enriched_pairs: List) -> dict:
    """
    Build an inverted index from each keyword → set of sentence‐indices.
    enriched_pairs: list of dicts, each has a "keywords" key with a list of strings.
    Returns: index: dict[str, set[int]]
    """
    index = defaultdict(set)
    print("build_keyword_index")
    for i, pair in enumerate(enriched_pairs):
        for kw in pair["description"]["grammatical_keywords"]:
            index[kw].add(i)
    return index

def plot_semantic_graph_pyvis(data,
                              height="600px",
                              width="100%",
                              referent_color="#C680B6",
                              top_node_color="#729EA1",
                              predicate_color="#C2D5D6"):
    from pyvis.network import Network
    # ensure PyVis can find its Jinja templates
    template_dir = pkg_resources.resource_filename("pyvis", "templates")

    net = Network(height=height,
                  width=width,
                  directed=True,
                  notebook=False,
                  )
    net.barnes_hut()

    # add all referent nodes
    for r in data["referents"]:
        rid = r["rid"]
        designation = r.get("designation", rid)
        speaker_relation = r.get("speaker_relation", "not specified")
        type = r.get("type", rid)
        referent_status = r.get("referent_status", "status unspecified")
        indexicality = r.get("indexicality", "indexicality unspecified")
        feat_list = [f"{k}: {r['features'][k]}" for k in r["features"].keys()]
        features = "\n".join(feat_list)

        net.add_node(
            n_id=rid,
            label=f"Referent\n{designation}\n({type})",
            title=(
                f"ontological type: {type}\n"
                f"speaker relation: {speaker_relation}.\n"
                f"referent_status: {referent_status}.\n"
                f"indexicality: {indexicality}.\n"
                f"\n{features}"
            ),
            shape="ellipse",
            color=referent_color,
            size=30
        )

    # add predicate nodes
    for p in data["predicates"]:
        p_type = p["ptype"]["type"]
        net.add_node(
            n_id=p["pid"],
            label=f"{p_type}\npredicate",
            title=(
                f"{p['pid']}\ntype: {p_type}"
            ),
            shape="box",
            color=predicate_color,
            size=20
        )

    # add predicate-based edges

    for p in data["predicates"]:
        referent_kernel_id = p["kernel"]["rid"]
        if referent_kernel_id and referent_kernel_id != "":
            try:
                net.add_edge(
                    source=p["pid"],
                    to=referent_kernel_id,
                    value=2,
                    arrows=None,
                    physics=True
                )
            except AssertionError:
                print("!!!! Edge creation exception !!!")
                print("Predicate: {}".format(p))
        for arg in p["args"]:
            role = arg["role"]
            target = arg["target_pid"]
            try:
                net.add_edge(
                    source=p["pid"],
                    to=target,
                    value=1,
                    label=role,
                    title=role,
                    arrows="to",
                    physics=True
                )
            except AssertionError:
                print("!!!! Edge creation exception !!!")
                print("Predicate: {}".format(p))


    # highlight the top node if specified
    top_id = data.get("top", {})
    if top_id and net.get_node(top_id):
        net.get_node(top_id)["color"] = top_node_color
        net.get_node(top_id)["title"] += "  ← top node"
        net.get_node(top_id)["label"] = "TOP node\n" + net.get_node(top_id)["label"]

    # custom physics for stability
    net.set_options("""
    var options = {
      "nodes": {"font":{"size":16}},
      "edges": {"smooth":true},
      "physics": {
        "barnesHut": {"gravitationalConstant":-7000, "centralGravity":0.5},
        "minVelocity":0.5
      }
    }
    """)

    return net.generate_html()

def build_vector_ready_augmented_pair(augmented_pair: dict) -> str:
    out_str = ""
    out_str += augmented_pair["source"] + "."
    # out_str += " TARGET LANGUAGE: " + augmented_pair["target"] + "."
    # if augmented_pair.get("connections", None) not in [None, {}]:
    #     out_str += " CONCEPT - TARGET WORD(S) RELATIONS: "
    #     for concept, words in augmented_pair["connections"].items():
    #         if words != "":
    #             out_str += " " + concept + ": " + ", ".join(words) + "."
    out_str += augmented_pair["description"]["grammatical_description"] + "."
    out_str += ", ".join(augmented_pair["description"]["grammatical_keywords"]) + "."
    out_str = out_str.replace("..", ".")
    return out_str

def get_vector_ready_pairs(indi_language):
    input_path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "augmented_pairs")
    output_path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vector_ready_pairs")
    apfs = [f for f in os.listdir(input_path) if f[-5:] == ".json"]
    if apfs == []:
        print("no file to get vector-ready in the folder {}".format(input_path))
        return True
    else:
        for apf in apfs:
            with open(os.path.join(input_path, apf), "r", encoding='utf-8') as f:
                ap = json.load(f)

            vap = build_vector_ready_augmented_pair(ap)
            vapf = apf[:-5] + ".txt"

            with open(os.path.join(output_path, vapf), "w", encoding='utf-8') as f:
                f.write(vap)
        return True

