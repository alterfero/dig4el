import json
from libs import utils
from libs import wals_utils as wu, grambank_utils as gu, grambank_wals_utils as gwu
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from multiprocessing import freeze_support
from libs import sentence_class_utils as scu
from libs import retrieval_augmented_generation_utils as ragu
import streamlit as st
import json

with open("/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/mwotlap_english_parallel_corpus_cleaned.json", "r", encoding='utf-8') as f:
    sentence_pairs = list(json.load(f))

# with open("/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/output.jsonl", "w", encoding='utf-8') as f:
#     for item in sentence_pairs:
#         f.write(json.dumps(item, ensure_ascii=False) + "\n")
#
# with open("/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/output.jsonl", "r", encoding='utf-8') as f:
#     items = [json.loads(line) for line in f]

# eng_sentences = [item["english"] for item in sentence_pairs]
# embeddings = ragu.build_embeddings(eng_sentences)
# ragu.save_embeddings(embeddings, path="/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/embeddings.pkl")

embeddings = ragu.load_embeddings("/Users/sebastienchristian/Desktop/d/01-These/language_lib/mwotlap/sentence pairs/embeddings.pkl")

scores, indices = ragu.query_similarity(embeddings, "Future tense")
print("Similarity")
for score, idx in zip(scores, indices):
        print(sentence_pairs[idx], f"(Score: {score:.4f})")

# Alternatively, we can also use util.semantic_search to perform cosine similarty + topk
print("Semantic Search")
hits = ragu.semantic_search(embeddings, "How to express negation")
hits = hits[0]      #Get the hits for the first query
for hit in hits:
    print(sentence_pairs[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))
