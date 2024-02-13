

class PronounFinder:
    """PronounFinder class creates intelligent agents that find pronouns in a given text."""
    def __init__(self, language):
        """Initialize a PronounFinder object."""
        self.language = language
        self.pronoun_list = ["PP1SG", "PP2SG", "PP1EXCDU", "PP1INCDU", "PP2DU","PP3DU", "PP1EXCPL", "PP1INCPL", "PP2PL", "PP3PL"]
        # in addition to the person, pronouns can vary based on semantic role, gender and social status
        # the PronounFinder object holds a person/gender/social/semantic role table to record probable targets and their probabilities
        self.guess_dict = {
            "PP1SG": {"agent": {"guess": "not enough data", "p": 0},
                      "patient": {"guess": "not enough data", "p": 0}},
            "PP2SG": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP1EXCDU": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP1INCDU": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP2DU": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP3DU": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP1EXCPL": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP1INCPL": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP2PL": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}},
            "PP3PL": {"agent": {"guess": "not enough data", "p": 0},
                        "patient": {"guess": "not enough data", "p": 0}}
        }
        self.is_dual = False
        self.is_social = False
        self.is_gendered = False

