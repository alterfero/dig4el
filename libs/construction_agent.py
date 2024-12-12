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

from libs import cq_observers as cqo
import pandas as pd

class Properson_Construction_Agent():
    def __init__(self):
        self.data_list = None
        self.data_df = None
        self.signatures_by_target_word = {}
        self.language_characteristics = {
            "is_bound_morphemes": None
        }
        self.discovery_graph = {
            "root": {
                "parameters": {
                    "uses_dual": {
                        "value": None,
                        "method": (cqo.observer_free_pp_dual, False)
                    },
                    "uses_exclusive": {
                        "value": None,
                        "method": (cqo.observer_free_pp_inclusive_exclusive, False)
                    },
                },
                "edges_to": {
                    "PP1SG": {"requires": []},
                    "PP2SG": {"requires": []},
                    "PP2INCDU": {"requires": ["uses_exclusive", "uses_dual"]},
                    "PP2EXCDU": {"requires": ["uses_exclusive", "uses_dual"]},
                    "PP2DU": {"requires": ["uses_dual"]},
                    "PP3SG": {"requires": []},
                    "PP3DU": {"requires": ["uses_dual"]}
                }

            },
            "PP1SG_internal_particularization": {
                "parameters": {
                "uses_gender": {
                        "value": None,
                        "method": (cqo.observer_free_pp1_gender, False)
                    }
                },
                "edges_to": {}
            },
            "PP2SG": {
                "parameters": {
                    "uses_gender": {
                        "value": None,
                        "method": (cqo.observer_free_pp2_gender, False)
                    }
                },
                "edges_to": {}
            },
            "PP2INCDU": {
                "parameters": {},
                "edges_to": {}
            }
        }






