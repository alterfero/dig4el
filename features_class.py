
class Grammatical_feature():
    def __init__(self, name):
        self.name = name

class EntityDeixis(Grammatical_feature):
    def __init__(self, name):
        super().__init__(name)
        self.name = "Entity Deixis"
        self.description = "Points to or refers to entities, based on the context."
        self.example = "I, you, you two, us but not you, this, that, etc."

class PersonalPronoun(EntityDeixis):
    def __init__(self, name, person, semantic_role):
        super().__init__(name, description)
        self.name = "Personal Pronoun"
        self.description = "Pronouns that refer to entities, based on the context."
        self.example = "I, you, you two, us but not you, etc."
        self.options = ["PP1SG", "PP2SG", "PP3SG", "PP1EXCDU", "PP1INCDU", "PP2DU", "PP3DU", "PP1EXCPL", "PP1INCPL", "PP2PL", "PP3PL"]
        self.person = person
        if self.person not in self.options:
            raise ValueError("person must be one of " + str(self.options))
        self.semantic_role = semantic_role

class SemanticRole():
    def __init__(self, name, role):
        self.name = name
        self.description = "Agent, patient, experiencer, etc."
        self.role_options = ["SemRoleAgent", "SemRolePatient", "SemRoleSole"]
        self.role = role
        if self.role not in self.role_options:
            raise ValueError("role must be one of " + str(self.role_options))

class SpeechAct():
    def __init__(self, name, act):
        self.name = name
        self.description = "Speech Act perfomed by the utterance."
        self.example = "Statement, question, command, etc."
        self.act_options = ["SpeechActStatement", "SpeechActQuestion", "SpeechActCommand"]
        self.act = act
        if self.act not in self.act_options:
            raise ValueError("act must be one of " + str(self.act_options))

class Concept():
    def __init__(self, name, aspect):
        self.name = name
        self.description = "Concepts, based on the context."
        self.example = "Dog, walking, numbers."
        self.aspect = aspect

class Aspect():
    def __init__(self, aspect):
        self.name = name
        self.description = "Aspect of the concept."
        self.example = "Progressive, perfective, etc."
        self.aspect_options = ["NA","AspectProgressive", "AspectPerfective", "AspectImperfective", "AspectHabitual", "AspectIterative", "AspectInceptive", "AspectCessative", "AspectInchoative", "AspectTerminative", "AspectDurative", "AspectPunctual", "AspectMomentane", "AspectRepetitive", "AspectSemelfactive", "AspectFrequentative", "AspectContinuative", "AspectProximative", "AspectRetrospective"]
        self.aspect = aspect
        if self.aspect not in self.aspect_options:
            raise ValueError("aspect must be one of " + str(self.aspect_options))