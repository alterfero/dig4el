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
    properson_props = {
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
    parameters = ["intent", "polarity", "semantic_role"]

    def __init__(self, properson):
        self.properson = properson
        self.parameters = ["intent", "polarity", "semantic_role"]
        self.data_list = None
        self.data_df = None

    def populate_data_list(self, knowledge_graph):
        self.data_list = cqo.properson_observer(self.properson, knowledge_graph)
        self.data_df = pd.DataFrame(self.data_list)

