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
