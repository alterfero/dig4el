import deepl
import json
import pickle

def create_eng_corpus_from_kg_file():
    corpus = []
    with open("../data/knowledge/current_kg.json", "r", encoding='utf-8') as f:
        kg = json.load(f)
    for index, data in kg.items():
        corpus.append(data["sentence_data"]["text"])

    with open("../data/embeddings/corpus_single_eng.json", "w", encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=4)

    return corpus

def create_target_corpus_from_kg_file():
    corpus = []
    with open("../data/knowledge/current_kg.json", encoding='utf-8') as f:
        kg = json.load(f)
    for index, data in kg.items():
        corpus.append(data["recording_data"]["translation"])

    with open("../data/embeddings/corpus_single_target.json", "w", encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=4)

    return corpus



auth_key = "5433546d-d4ba-4f42-863b-c8b1b00123e6:fx"
translator = deepl.Translator(auth_key)
target_lang_list = ["BG", "CS", "DA", "DE", "EL", "ES", "ET", "FI", "FR", "HU", "ID", "IT", "JA", "KO", "LT", "LV", "NB", "NL", "PL", "PT-PT", "RO", "RU", "SK", "SL", "SV", "TR", "UK", "ZH"]

with open("../data/embeddings/corpus_single_eng.json", "r", encoding='utf-8') as f:
    corpus_english = json.load(f)
corpus = {}

n_char = 0
corpus["EN"] = corpus_english["english"]
print("{} sentences to translate".format(len(corpus_english["english"])))
for target_language in target_lang_list:
    print("Target language {}".format(target_language))
    corpus[target_language] = []
    sentence_count = 0
    for entry in corpus_english["english"]:
        sentence_count += 1
        n_char += len(entry)
        translation = translator.translate_text(entry, source_lang="EN", target_lang=target_language)
        corpus[target_language].append(translation.text)
        print("{}: {} ==> {}".format(sentence_count, entry, translation.text))
    print("translation done for {}".format(target_language))
    print("{} sentences translated, {} character translated.".format(len(corpus[target_language]), n_char))

    with open(f"../data/embeddings/corpus_adding_{target_language}.json", "w", encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=4)
    print(f"../data/embeddings/corpus_adding_{target_language}.json file saved")

with open("../data/embeddings/corpus_deepl.json", "w", encoding='utf-8') as f:
    json.dump(corpus, f, ensure_ascii=False, indent=4)


