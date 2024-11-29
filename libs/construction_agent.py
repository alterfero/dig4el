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
from scipy.stats import chi2_contingency
from libs import wals_utils as wu, grambank_utils as gu, cq_observers as cqo
import pandas as pd
from libs import stats

class Properson_Construction():
    def __init__(self, properson):
        self.properson = properson
        self.properson_props = {
            "PP1SG": {"number": "singular", "ref": ["speaker"]},
            "PP1INCDU": {"number": "dual", "ref": ["speaker", "listener"]},
            "PP1EXCDU": {"number": "dual", "ref": ["speaker", "other"]},
            "PP1INCTR": {"number": "trial", "ref": ["speaker", "listener", "other"]},
            "PP1EXCTR": {"number": "trial", "ref": ["speaker", "other", "other"]},
            "PP1INCPC": {"number": "paucal", "ref": ["speaker", "listener(s)", "other(s)"]},
            "PP1EXCPC": {"number": "paucal", "ref": ["speaker", "other(s)"]},
            "PP1INCPL": {"number": "plural", "ref": ["speaker", "listener(s)", "other(s)"]},
            "PP1EXCPL": {"number": "plural", "ref": ["speaker", "other(s)"]},

            "PP2SG": {"number": "singular", "ref": ["listener"]},
            "PP2DU": {"number": "dual", "ref": ["listener", "listener"]},
            "PP2TR": {"number": "trial", "ref": ["listener", "listener", "listener"]},
            "PP2PC": {"number": "paucal", "ref": ["listener(s)"]},
            "PP2PL": {"number": "plural", "ref": ["listener(s)"]},

            "PP3SG": {"number": "singular", "ref": ["other"]},
            "PP3DU": {"number": "dual", "ref": ["other", "other"]},
            "PP3TR": {"number": "trial", "ref": ["other", "other", "other"]},
            "PP3PC": {"number": "paucal", "ref": ["other(s)"]},

            "PP3PL": {"number": "plural", "ref": ["other(s)"]},
        }
        self.parameters = {"speaker_gender": ["male", "female"],
                           "listener_gender": ["male", "female"],
                           "ref_gender": ["male", "female", "other", "multiple"],
                           "number": ["singular", "dual", "trial", "paucal", "plural"],
                           "intent": ["ASSERT", "ASK", "ORDER"],
                           "polarity": ["POSITIVE", "NEGATIVE"],
                           "semantic_role": ["agent", "patient", "oblique"]}
        self.data_list = None
        self.data_df = None
        self.signatures_by_target_word = {}
        self.boolean_properties = {
            "is_expressed": None,
            "is_free_morpheme": None,
            "is_speaker_gender_sensitive": None,
            "is_listener_gender_sensitive": None,
            "is_ref_gender_sensitive": None,
            "is_number_sensitive": None,
            "is_intent_sensitive": None,
            "is_polarity_sensitive": None,
            "is_semantic_role_sensitive": None
            }

    def populate_data_list(self, knowledge_graph):
        self.data_list = cqo.properson_observer(self.properson, knowledge_graph)
        self.data_df = pd.DataFrame(self.data_list)
        self.data_df.fillna('None', inplace=True)

    def populate_standard_signature_by_target_word(self):
        for entry in self.data_list:
            tmp = {}
            for parameter in self.parameters.keys():
                tmp[parameter] = entry[parameter] if entry[parameter] in self.parameters[parameter] else None

            if entry["target_words"] in self.signatures_by_target_word.keys():
                self.signatures_by_target_word[entry["target_words"]].append(tmp)
            else:
                self.signatures_by_target_word[entry["target_words"]] = [tmp]



