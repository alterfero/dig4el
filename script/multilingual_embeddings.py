import torch
import numpy as np
import pandas as pd
from transformers import BertModel, BertTokenizerFast, XLMRobertaModel, XLMRobertaTokenizerFast
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import os
from tqdm import tqdm


class MultilingualEmbedder:
    """
    Class to create and analyze word embeddings from a small corpus across multiple languages
    """

    def __init__(self, model_name='xlm-roberta-base', target_language='unknown'):
        """
        Initialize the embedder with a multilingual model

        Args:
            model_name: Pre-trained model to use (xlm-roberta-base supports 100 languages)
        """
        # XLM-RoBERTa is preferred for lower-resource languages
        if 'xlm-roberta' in model_name:
            self.tokenizer = XLMRobertaTokenizerFast.from_pretrained(model_name)
            self.model = XLMRobertaModel.from_pretrained(model_name)
        else:
            self.tokenizer = BertTokenizerFast.from_pretrained(model_name)
            self.model = BertModel.from_pretrained(model_name)

        self.model.eval()
        self.embeddings = {}

    def extract_embeddings(self, corpus_dict, batch_size=32, layers=[-1, -2, -3, -4]):
        """
        Extract embeddings for each token in each language's corpus

        Args:
            corpus_dict: Dictionary mapping language codes to lists of texts
            batch_size: Batch size for processing
            layers: Which model layers to use for embeddings

        Returns:
            Dictionary mapping languages to their token embeddings
        """
        results = {}

        for lang, texts in tqdm(corpus_dict.items(), desc="Processing languages"):
            lang_embeddings = {}

            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]

                # Tokenize with attention to word boundaries
                encodings = self.tokenizer(batch_texts,
                                           padding=True,
                                           truncation=True,
                                           return_tensors="pt",
                                           return_offsets_mapping=True,
                                           return_special_tokens_mask=True)

                input_ids = encodings["input_ids"]
                attention_mask = encodings["attention_mask"]
                special_tokens_mask = encodings["special_tokens_mask"]

                # Track original word-to-token mapping
                word_to_tokens = {}
                offset_mapping = encodings.offset_mapping

                # Map each word position to its token indices
                for sent_idx, (offsets, specials) in enumerate(zip(offset_mapping, special_tokens_mask)):
                    word_idx = -1
                    current_tokens = []

                    for token_idx, (offset, is_special) in enumerate(zip(offsets, specials)):
                        # Skip special tokens ([CLS], [SEP], etc.)
                        if is_special.item() == 1:
                            continue

                        # New word starts
                        if offset[0].item() == 0 and word_idx >= 0:
                            # Save previous word's tokens
                            if current_tokens:
                                key = (sent_idx, word_idx)
                                word_to_tokens[key] = current_tokens
                                current_tokens = []
                            word_idx += 1
                        elif offset[0].item() == 0:
                            word_idx += 1

                        current_tokens.append(token_idx)

                    # Save the last word's tokens
                    if current_tokens:
                        key = (sent_idx, word_idx)
                        word_to_tokens[key] = current_tokens

                # Get embeddings from model
                with torch.no_grad():
                    outputs = self.model(input_ids=input_ids,
                                         attention_mask=attention_mask,
                                         output_hidden_states=True)

                    # Get hidden states from specified layers
                    hidden_states = [outputs.hidden_states[layer] for layer in layers]

                    # Stack and average across requested layers
                    stacked_hidden_states = torch.stack(hidden_states)
                    avg_hidden_states = torch.mean(stacked_hidden_states, dim=0)

                    # Extract word-level embeddings by averaging constituent tokens
                    for key, token_indices in word_to_tokens.items():
                        sent_idx, word_idx = key
                        token_embeds = avg_hidden_states[sent_idx, token_indices, :]
                        word_embed = torch.mean(token_embeds, dim=0).cpu().numpy()

                        # Store with unique identifier
                        word_text = batch_texts[sent_idx].split()[word_idx] if word_idx < len(
                            batch_texts[sent_idx].split()) else "UNK"
                        embed_key = f"{word_text}_{sent_idx}_{word_idx}"
                        lang_embeddings[embed_key] = word_embed

            results[lang] = lang_embeddings

        self.embeddings = results
        return results

    def analyze_cross_lingual_similarity(self, parallel_words=None):
        """
        Analyze similarity between parallel words across languages

        Args:
            parallel_words: Optional list of tuples with (word, lang) pairs that have the same meaning.
                           If None, will analyze based on position in parallel texts.

        Returns:
            DataFrame with pairwise similarities
        """
        if not self.embeddings:
            raise ValueError("Extract embeddings first!")

        similarities = []

        if parallel_words:
            # Find embeddings for specified parallel words
            word_embeds = {}
            for word, lang in parallel_words:
                # Find the word in the language embeddings
                for key, embed in self.embeddings[lang].items():
                    if key.startswith(f"{word}_"):
                        word_embeds[(word, lang)] = embed
                        break

            # Calculate cosine similarities
            for (word1, lang1), embed1 in word_embeds.items():
                for (word2, lang2), embed2 in word_embeds.items():
                    if (word1, lang1) != (word2, lang2):
                        # Cosine similarity
                        sim = np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))
                        similarities.append({
                            'word1': word1,
                            'lang1': lang1,
                            'word2': word2,
                            'lang2': lang2,
                            'similarity': sim
                        })
        else:
            # Analyze words at the same position in parallel texts
            # This assumes texts are aligned and in the same order across languages
            unknown_lang = "unknown"  # Adjust based on your actual unknown language code
            known_langs = [lang for lang in self.embeddings.keys() if lang != unknown_lang]

            # For each word in unknown language
            for unk_word_key, unk_embed in self.embeddings[unknown_lang].items():
                # Extract position information from the key
                try:
                    unk_word, sent_idx, word_idx = unk_word_key.split('_')
                    sent_idx, word_idx = int(sent_idx), int(word_idx)

                    # Compare with words at same position in known languages
                    for known_lang in known_langs:
                        for known_word_key, known_embed in self.embeddings[known_lang].items():
                            if f"_{sent_idx}_{word_idx}" in known_word_key:
                                known_word = known_word_key.split('_')[0]

                                # Calculate similarity
                                sim = np.dot(unk_embed, known_embed) / (
                                            np.linalg.norm(unk_embed) * np.linalg.norm(known_embed))

                                similarities.append({
                                    'word1': unk_word,
                                    'lang1': unknown_lang,
                                    'word2': known_word,
                                    'lang2': known_lang,
                                    'position': f"sent_{sent_idx}_word_{word_idx}",
                                    'similarity': sim
                                })
                except ValueError:
                    # Skip entries that don't match the expected format
                    continue

        return pd.DataFrame(similarities)

    def find_closest_unknown_words(self, top_n=10):
        """
        Find closest known language words for each unknown language word

        Args:
            top_n: Number of top matches to return for each word

        Returns:
            DataFrame with unknown words and their closest matches in known languages
        """
        if not self.embeddings:
            raise ValueError("Extract embeddings first!")

        unknown_lang = "unknown"  # Adjust based on your actual unknown language code
        if unknown_lang not in self.embeddings:
            raise ValueError(f"No embeddings found for {unknown_lang}")

        known_langs = [lang for lang in self.embeddings.keys() if lang != unknown_lang]

        results = []

        # For each word in the unknown language
        for unk_word_key, unk_embed in self.embeddings[unknown_lang].items():
            unk_word = unk_word_key.split('_')[0]

            # Compare with all words in known languages
            word_similarities = []

            for known_lang in known_langs:
                for known_word_key, known_embed in self.embeddings[known_lang].items():
                    known_word = known_word_key.split('_')[0]

                    # Calculate similarity
                    sim = np.dot(unk_embed, known_embed) / (np.linalg.norm(unk_embed) * np.linalg.norm(known_embed))

                    word_similarities.append({
                        'unknown_word': unk_word,
                        'known_word': known_word,
                        'known_lang': known_lang,
                        'similarity': sim
                    })

            # Get top N matches
            top_matches = sorted(word_similarities, key=lambda x: x['similarity'], reverse=True)[:top_n]
            results.extend(top_matches)

        return pd.DataFrame(results)

    def visualize_embeddings(self, words_of_interest=None, languages=None, method='tsne'):
        """
        Visualize embeddings using dimensionality reduction

        Args:
            words_of_interest: List of words to visualize (if None, use all)
            languages: List of languages to include (if None, use all)
            method: 'pca' or 'tsne'
        """
        if not self.embeddings:
            raise ValueError("Extract embeddings first!")

        # Filter embeddings
        filtered_embeds = []
        labels = []

        langs_to_use = languages or list(self.embeddings.keys())

        for lang in langs_to_use:
            for word_key, embed in self.embeddings[lang].items():
                word = word_key.split('_')[0]
                if words_of_interest is None or word in words_of_interest:
                    filtered_embeds.append(embed)
                    labels.append(f"{word} ({lang})")

        # Convert to numpy array
        embeddings_array = np.array(filtered_embeds)

        # Apply dimensionality reduction
        if method == 'pca':
            reducer = PCA(n_components=2)
        else:
            reducer = TSNE(n_components=2, perplexity=min(30, len(embeddings_array) - 1))

        reduced_embeds = reducer.fit_transform(embeddings_array)

        # Plot
        plt.figure(figsize=(12, 10))
        for i, (x, y) in enumerate(reduced_embeds):
            plt.scatter(x, y, marker='o')
            plt.annotate(labels[i], (x, y), fontsize=9)

        plt.title(f"Word Embeddings Visualization ({method.upper()})")
        plt.tight_layout()
        plt.savefig(f"../data/embeddings/multilingual_embeddings_{method}.png", dpi=300)
        plt.show()

    def save_embeddings(self, output_dir="../data/embeddings/embeddings"):
        """Save embeddings to disk"""
        os.makedirs(output_dir, exist_ok=True)

        for lang, embeds in self.embeddings.items():
            lang_dir = os.path.join(output_dir, lang)
            os.makedirs(lang_dir, exist_ok=True)

            # Save as numpy files
            for word_key, embed in embeds.items():
                filename = f"{word_key.replace('/', '_')}.npy"
                np.save(os.path.join(lang_dir, filename), embed)

        print(f"Saved embeddings to {output_dir}")


# Example usage for N languages, including an "unknown" language
def main():
    # Load your corpus from JSON file
    import json

    with open("../data/embeddings/multilingual_corpus.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)

    # Extract languages from your corpus
    languages = [lname.lower() for lname in list(corpus.keys())]
    print(f"Processing {len(languages)} languages: {', '.join(languages)}")

    # Initialize embedder with XLM-RoBERTa (supports 100 languages)
    embedder = MultilingualEmbedder(model_name='xlm-roberta-base')

    # Extract embeddings
    print("Extracting embeddings...")
    embeddings = embedder.extract_embeddings(corpus)
    print(f"Available languages in embeddings: {list(embedder.embeddings.keys())}")

    # Automatically analyze unknown language words
    print("\nFinding closest known words for each unknown word...")
    closest_words = embedder.find_closest_unknown_words(top_n=5)
    print("\nTop matches for unknown words:")

    # Group by unknown word to show top matches for each
    for unknown_word, group in closest_words.groupby('unknown_word'):
        print(f"\nUnknown word: '{unknown_word}'")
        for _, row in group.sort_values('similarity', ascending=False).head(5).iterrows():
            print(f"  • {row['known_word']} ({row['known_lang']}): similarity {row['similarity']:.4f}")

    # Analyze words at the same positions in parallel texts
    print("\nAnalyzing parallel text positions...")
    position_similarities = embedder.analyze_cross_lingual_similarity()

    # Show average similarity by language
    lang_similarities = position_similarities.groupby('lang2')['similarity'].mean().sort_values(ascending=False)
    print("\nAverage similarity between unknown language and known languages:")
    for lang, sim in lang_similarities.items():
        print(f"  • {lang}: {sim:.4f}")

    # Visualize embeddings
    print("\nGenerating visualization...")
    # Get available languages first
    available_langs = list(embedder.embeddings.keys())
    print(f"Available languages: {available_langs}")

    # Use only available languages for visualization
    vis_langs = [lang for lang in ["en", "fr", "es", "unknown"] if lang in available_langs]
    if vis_langs:
        embedder.visualize_embeddings(languages=vis_langs)
    else:
        print("No requested languages available in embeddings.")

    # Save embeddings
    print("\nSaving embeddings...")
    embedder.save_embeddings()


if __name__ == "__main__":
    main()