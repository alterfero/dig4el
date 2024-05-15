import json
import streamlit as st

word_corpus_file = "../adhoc/wordCorpus.json"
new_word_corpus_file = "../adhoc/new2WordCorpus.json"
expression_file = "../adhoc/expressionCorpus.json"
new_expression_file = "../adhoc/new2ExpressionCorpus.json"

#load corpuses
with open(word_corpus_file, "r") as file:
    word_corpus = json.load(file)
with open(expression_file, "r") as file:
    expression_corpus = json.load(file)

new_word_corpus = {}
for item in word_corpus:
    new_word_corpus[item] = {}
    if "audio"  in word_corpus[item]:
        new_word_corpus[item]["audio"] = word_corpus[item]["audio"]
    if "image"  in word_corpus[item]:
        new_word_corpus[item]["image"] = word_corpus[item]["image"]
    if "in_expression" in word_corpus[item]:
        new_word_corpus[item]["in_expression"] = word_corpus[item]["in_expression"]
    if "themes" in word_corpus[item]:
        new_word_corpus[item]["themes"] = word_corpus[item]["themes"]
    if "translations" in word_corpus[item]:
        new_word_corpus[item]["translations"] = word_corpus[item]["translations"]

#save new word corpus
with open(new_word_corpus_file, "w") as file:
    json.dump(new_word_corpus, file, indent=4)

new_expression_corpus = {}
for item in expression_corpus:
    new_expression_corpus[item] = {}
    if "audio" in expression_corpus[item]:
        new_expression_corpus[item]["audio"] = expression_corpus[item]["audio"]
    if "image" in expression_corpus[item]:
        new_expression_corpus[item]["image"] = expression_corpus[item]["image"]
    if "themes" in expression_corpus[item]:
        new_expression_corpus[item]["themes"] = expression_corpus[item]["themes"]
    if "components" in expression_corpus[item]:
        new_expression_corpus[item]["components"] = expression_corpus[item]["components"]
    if "translations" in expression_corpus[item]:
        new_expression_corpus[item]["translations"] = expression_corpus[item]["translations"]

#save new expression corpus
with open(new_expression_file, "w") as file:
    json.dump(new_expression_corpus, file, indent=4)