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
import json
from libs import graphs_utils as gu

with open("../data/concepts.json", "r") as f:
    concepts = json.load(f)

def build_training_data(kg):
    internal_particularization_list = ["DEFINITENESS", "POLARITY", "TENSE", "ASPECT"]
    relational_particularization_list = ["AGENT", "PATIENT", "OBLIQUE", "POSSESSOR", "POSSESSEE", "QUANTIFIER", "LOCATION INFORMATION", "TIME INFORMATION"]
    training_data = []
    def get_concept(concept_string):
        for entry in concepts:
            if concept_string in entry:
                return entry
    def build_training_graph(data, filter=None):
        training_graph = {
            "internal_particularization": [],
            "relational_particularization": []
        }
        kg_graph = data["sentence_data"]["graph"]
        for entry, content in kg_graph.items():
            if content["value"] != "":
                if entry.endswith("REFERENCE TO CONCEPT"):
                    s = [s for s in relational_particularization_list if s in entry]
                    if s != []:
                        c = get_concept(entry.split(' ', 1)[0])
                        relation = s[0]
                        training_graph["relational_particularization"].append(
                            {"concept": content["value"],
                             "genealogy": gu.get_genealogy(concepts, c),
                             "relation": relation,
                             "to": c})
                else:
                    s = [s for s in internal_particularization_list if s in entry]
                    if s != []:
                        c = get_concept(entry.split(' ', 1)[0])
                        particularization = s[0]
                        training_graph["internal_particularization"].append(
                            {"concept": c,
                             "genealogy": gu.get_genealogy(concepts, c),
                             "feature": particularization,
                             "value": content["value"]})
        return training_graph

    for index, data in kg.items():
        t = {}
        t["context"] = {
            "speaker_gender": data["speaker_gender"],
            "listener_gender": data["listener_gender"]
        }
        sd = data["sentence_data"]
        i = sd.get("intent", "None")
        if i != "None" and i != []:
            t["intent"] = i[0]
        else:
            t["intent"] = "None"
        p = sd.get("predicate", "None")
        if p != "None" and p != []:
            t["type_of_predicate"] = p[0]
        else:
            t["type_of_predicate"] = "None"

        t["concepts"] = sd["concept"]
        t["super_concept_graph"] = build_training_graph(data)
        t["concept_words"] = data["recording_data"]["concept_words"]
        training_data.append((t, data["recording_data"]["translation"]))

    return training_data
