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
import os
import copy
import random
from libs import wals_utils as wu, grambank_utils as gu
import math

class ConstructionAgent:
    """
    A concstruction agent focuses on a semantic-to-syntaxic process, as determining how a reference to a known object is made,
    how aspect or negation are expressed. The CA starts from a collection of concepts, that are assembled as being part of the
    same semantic group, and searches the mechanisms of expression of these concepts.
    The model of the process is
    - Ontological impact
    - Internal particularization options
    - Relational particularization options
    - Graphemical neighboring effects
    """

    def __init__(self, concepts, wals_parameter_names, grambank_parameter_names):
        self.concepts = concepts
        self.wals_parameter_names = wals_parameter_names
        self.grambank_parameter_names = grambank_parameter_names

