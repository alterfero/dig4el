import json
import os.path

from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np
import pickle
import torch
from libs import stats
from libs import utils

"""
Implementing Retrieval-Augmented Generation (RAG) to add relevant pairs of sentences from a parallel corpus
to a user LLM prompt.
Functions below allow to:
- generate an embedding for each sentence pair. 
- index these embeddings 
- save and load indexes. 
- use user prompt embedding to select the N most relevant sentences to add to the prompt. 

Uses SentenceTransformers
Sentence Transformers (a.k.a. SBERT) is the go-to Python module for accessing, using, 
and training state-of-the-art embedding and reranker models. 
It can be used to compute embeddings using Sentence Transformer models (quickstart) 
or to calculate similarity scores using Cross-Encoder (a.k.a. reranker) models (quickstart). 
This unlocks a wide range of applications, including semantic search, semantic textual similarity, 
and paraphrase mining.
https://www.sbert.net/
"""

# def sentence_pair_dict_to_sentence_pair_txt(sentence_pair_dict: dict) -> str:

BASE_LD_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./ld"),
    "storage"
)

def compute_embeddings_and_FAISS_index(
        sentences: list[str],
        metadata: list[dict] = None,
        model_name: str = 'all-MiniLM-L6-v2',
        normalize: bool = True
):
    """
    Create FAISS index and metadata mapping for sentence embeddings.

    Args:
        sentences (list[str]): Sentences or document strings to embed.
        metadata (list[dict], optional): Optional metadata for each sentence.
        model_name (str): SentenceTransformer model name.
        normalize (bool): Normalize embeddings for cosine similarity.

    Returns:
        index (faiss.Index): FAISS index built from sentence embeddings.
        id_to_meta (dict[int, dict]): Mapping from index id to metadata.
    """
    assert isinstance(sentences, list) and all(
        isinstance(s, str) for s in sentences), "sentences must be a list of strings"

    model = SentenceTransformer(model_name)
    embeddings = model.encode(sentences, convert_to_numpy=True, batch_size=64, show_progress_bar=True)

    if normalize:
        faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim) if normalize else faiss.IndexFlatL2(dim)
    index.add(embeddings)

    id_to_meta = {i: {'sentence': sentences[i]} | (metadata[i] if metadata else {}) for i in range(len(sentences))}

    return embeddings, index, id_to_meta

def vectorize_vaps(indi_language):
    vaps_path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vector_ready_pairs")
    vec_path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vectors")
    vapsf = [f for f in os.listdir(vaps_path) if f[-4:] == ".txt"]
    print("vectorizing {} vaps".format(len(vapsf)))
    if len(vapsf) == 0:
        return True
    else:
        vaps = []
        id_to_meta = []
        for vapf in vapsf:
            with open(os.path.join(vaps_path, vapf), "r", encoding='utf-8') as f:
                content = f.read()
                vaps.append(content)
                id_to_meta.append({
                    "filename": vapf
                })

        embeddings, index, id_to_meta = compute_embeddings_and_FAISS_index(vaps, id_to_meta)

        save_index_id_to_meta_and_metadata(index, id_to_meta, indi_language)

        return True

def save_index_id_to_meta_and_metadata(index, id_to_meta, indi_language):
    path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vectors")
    os.makedirs(path, exist_ok=True)
    index_path = os.path.join(path, "index.faiss")
    id_to_meta_path = os.path.join(path, "id_to_meta.json")
    faiss.write_index(index, index_path)
    with open(id_to_meta_path, 'w', encoding='utf-8') as f:
        utils.save_json_normalized(id_to_meta, f)

def load_index_and_id_to_meta(indi_language):
    path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vectors")
    index_path = os.path.join(path, "index.faiss")
    id_to_meta_path = os.path.join(path, "id_to_meta.json")
    if "index.faiss" in os.listdir(path):
        index = faiss.read_index(index_path)
    else:
        print("No index.faiss available, returning None")
        index = None
    if "id_to_meta.json" in os.listdir(path):
        with open(id_to_meta_path, 'r', encoding='utf-8') as f:
            id_to_meta = json.load(f)
    else:
        print("No id_to_meta.json available, returning None")
        id_to_meta = None
    return index, id_to_meta

def retrieve_similar(query: str, index, id_to_meta,
                     model_name='all-MiniLM-L6-v2', k=10, normalize=True,
                     min_score=0.5):
    k = min(len(id_to_meta.keys()), k)
    model = SentenceTransformer(model_name)
    q_vec = model.encode([query], convert_to_numpy=True)

    if normalize:
        faiss.normalize_L2(q_vec)

    dists, idxs = index.search(q_vec, k)

    scores, ids = dists[0], idxs[0]
    results = []
    for score, idx in zip(scores, ids):
        # if normalize:
        #     if score < min_score:
        #         continue
        # else:
        #     if score > min_score:  # lower L2 is better
        #         continue

        results.append(id_to_meta[str(int(idx))])
        print("id_to_meta: {}, score:{}".format(id_to_meta[str(int(idx))]["filename"], score))
        if len(results) >= k:
            break

    return results

def semantic_search(embeddings, query, model_name='all-MiniLM-L6-v2', top_k=10):
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query], convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings, top_k=top_k)
    return hits

def create_hard_kw_index(indi_language):
    aps_path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "augmented_pairs")
    vec_path = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vectors")
    apsf = [f for f in os.listdir(aps_path) if f[-5:] == ".json"]
    kwi = {}
    for apf in apsf:
        with open(os.path.join(aps_path, apf), "r", encoding='utf-8') as f:
            ap = json.load(f)
        kws = ap["description"].get("grammatical_keywords", [])
        kws += stats.custom_split(ap["description"].get("grammatical_description", ""))
        kws = list(set(kws))
        for kw in kws:
            if kw in kwi.keys():
                if apf not in kwi[kw]:
                    kwi[kw].append(apf)
            else:
                kwi[kw] = [apf]
    with open(os.path.join(vec_path, "hard_index.json"), "w", encoding='utf-8') as f:
        utils.save_json_normalized(kwi, f)
    return kwi

def hard_retrieve_from_query(query: str, indi_language: str) -> list[str]:
    kwif = os.path.join(BASE_LD_PATH, indi_language, "sentence_pairs", "vectors", "hard_index.json")
    results = []
    with open(kwif, "r", encoding='utf-8') as f:
        kwi = json.load(f)
    parsed_query = stats.custom_split(query)
    for w in parsed_query:
        ks = [k for k in kwi.keys() if w in k]
        if ks != []:
            results += [kwi[k] for k in ks][0]
    print("Hard retrieve from query {}: {}".format(query, results))
    print(results)
    results = list(set(results))
    return results

def cq_to_sentence_pairs(cq_transcription_dict: dict) -> list[dict]:
    out = []
    for entry in cq_transcription_dict["data"].keys():
        out.append(
            {
                "source": cq_transcription_dict["data"][entry]["cq"],
                "target": cq_transcription_dict["data"][entry]["translation"]
            }
        )
    return out

# with open("/Users/sebastienchristian/Desktop/d/01-These/Engine/v1/ld/Tahitian/cq/cq_translations/recording_cq_Going fishing_1716315461_Tahitian_Jacques Vernaudon_Mirose Paia_1748856964.json", "r", encoding='utf-8') as f:
#     spd = json.load(f)
# sp = cq_to_sentence_pairs(spd)
# with open("./going_fishing_sentence_pairs.json", "w", encoding='utf-8') as f:
#     json.dump(sp, f)

