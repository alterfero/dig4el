import json
from libs import evolutionary_utils as eu

with open("../data/knowledge/current_kg.json", "r") as f:
    kg = json.load(f)

training_data = eu.build_training_data(kg)

print(training_data[0])
