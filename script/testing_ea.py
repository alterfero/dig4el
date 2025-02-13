import json
from libs import evolutionary_utils as eu
from libs import grammar as g

with open("../data/knowledge/current_kg.json", "r") as f:
    kg = json.load(f)

training_data, concepts = eu.build_training_data(kg)
print("training_data[0]: {}".format(training_data[0]))
# print(concepts[:10])

gi = g.GrammarIndividual(["PP1SG", "picture", "seeing"], training_data)
gi.initialize()
expression = gi.serialize_sentence(gi.training_data[0])

print(expression)





