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

constructions = {
"PP1SG": {
	"morpheme": ["absent", "free", "bound"],
	"compacity": ["compact", "multiple"],
	"varies_with_intent": ["ASSERT", "ORDER", "ASK"]
	"varies_with_context": ["speaker_gender", "speaker_age", "politeness"],
	"varies_with_internal_particularization": [],
	"varies_with_relational_particularization": ["agent", "patient", "oblique"]
	}
}

class Construction:
    def __init__(self):
        self.process = ["context_impact",
                        "intent_impact",
                        "internal_particularization",
                        "relational_particularization",
                        "combinations"]
        self.concept = "PP1SG"
        self.available_concept_specs = {
    "morpheme": ["absent", "free", "bound"],
    "compacity": ["compact", "multiple"],
    "varies_with_intent": ["ASSERT", "ORDER", "ASK"],
    "varies_with_context": ["speaker_gender", "speaker_age", "politeness"],
    "varies_with_internal_particularization": [],
    "varies_with_relational_particularization": ["AGENT", "PATIENT", "OBLIQUE", "POSSESSOR", "POSSESSEE"]
    }


class GrammarIndividual:
    def __init__(self, rules):
        self.rules = rules if rules else {}
        self.fitness = None  # Will be assigned during evaluation


    def serialize(self, superconcept_graph, genes):
        return None
