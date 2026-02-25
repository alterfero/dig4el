import xml.etree.ElementTree as ET
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# =============== FLEX XML to DIG4EL =============

_PUNCT_RE = re.compile(r"^[\.\,\;\:\!\?\…]+$")

def flex_xml_gloss_to_dig4el(
    xml_input: Union[str, Path],
    source_lang: str = "en",
    target_lang: Optional[str] = None,
    include_pos_in_keys: bool = False,
    join_multiples: str = " ",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convert a Flex Interlinear XML export (sentence gloss export) to DIG4EL JSON format.

    Returns: (data_list, meta)
      - data_list: list of dicts: {"source", "target", "word connections"}
      - meta: helpful metadata (detected title(s), detected language codes, guid)

    Notes / assumptions (matching your sample):
      - Each sentence lives under paragraph/phrases/word.
      - That outer <word> contains:
          - a <words> child listing <word> tokens with <item type="txt|punct"> and <item type="gls"> (word gloss)
          - and an outer <item type="gls" lang="en"> that is the free translation of the whole segment.
      - Punctuation tokens are excluded from word connections by default.
    """
    # Load XML
    if isinstance(xml_input, Path) or (isinstance(xml_input, str) and Path(xml_input).exists()):
        xml_text = Path(xml_input).read_text(encoding="utf-8")
    else:
        xml_text = str(xml_input)

    root = ET.fromstring(xml_text)

    interlinear = root.find(".//interlinear-text")
    guid = interlinear.get("guid") if interlinear is not None else None

    # Titles (often two: en + target)
    titles = []
    for it in root.findall(".//interlinear-text/item[@type='title']"):
        titles.append({"lang": it.get("lang"), "text": (it.text or "").strip()})

    # Detect target language from first token txt item if not provided
    detected_target_lang = None
    if target_lang is None:
        first_txt = root.find(".//words/word/item[@type='txt']")
        if first_txt is not None:
            detected_target_lang = first_txt.get("lang")
            target_lang = detected_target_lang  # use it

    # Collect all "sentences"
    out: List[Dict[str, Any]] = []

    # In your sample, each sentence is a <word> under <phrases>, which itself contains <words> tokens
    for sent_node in root.findall(".//paragraphs/paragraph/phrases/word"):
        # segment number if present
        segnum_item = sent_node.find("./item[@type='segnum']")
        segnum = (segnum_item.text or "").strip() if segnum_item is not None else None

        # sentence-level free translation in source_lang
        free_tr_item = None
        for it in sent_node.findall("./item[@type='gls']"):
            if (it.get("lang") or "").strip() == source_lang:
                free_tr_item = it
                break
        source_sentence = (free_tr_item.text or "").strip() if free_tr_item is not None else ""

        # Build target sentence from token txt/punct items
        token_words = []
        connections: Dict[str, str] = {}
        conn_acc: Dict[str, List[str]] = defaultdict(list)

        for w in sent_node.findall("./words/word"):
            txt_item = w.find("./item[@type='txt']")
            punct_item = w.find("./item[@type='punct']")
            gls_item = w.find(f"./item[@type='gls'][@lang='{source_lang}']") or w.find("./item[@type='gls']")
            pos_item = w.find(f"./item[@type='pos'][@lang='{source_lang}']") or w.find("./item[@type='pos']")

            if punct_item is not None and (punct_item.text or "").strip():
                tok = (punct_item.text or "").strip()
                token_words.append(tok)
                continue

            if txt_item is None or not (txt_item.text or "").strip():
                # token without txt; skip
                continue

            target_tok = (txt_item.text or "").strip()
            token_words.append(target_tok)

            # mapping key: from gloss (or fallback to english free gloss)
            gloss = (gls_item.text or "").strip() if gls_item is not None else ""
            if not gloss:
                # if no gloss, you can still map target->target or skip; we skip
                continue

            key = gloss
            if include_pos_in_keys and pos_item is not None and (pos_item.text or "").strip():
                key = f"{gloss}<{(pos_item.text or '').strip()}>"

            # accumulate (many target tokens may share same gloss)
            conn_acc[key].append(target_tok)

        # Normalize spacing/punctuation in target sentence
        target_sentence = _join_tokens_like_text(token_words)

        # finalize connections: join multiple target tokens for same key
        for k, toks in conn_acc.items():
            # Deduplicate but preserve order
            seen = set()
            uniq = [t for t in toks if not (t in seen or seen.add(t))]
            connections[k] = join_multiples.join(uniq)

        out.append(
            {
                "source": source_sentence,
                "target": target_sentence,
                "word connections": connections,
                **({"segnum": segnum} if segnum else {}),
            }
        )

    meta = {
        "guid": guid,
        "titles": titles,
        "source_lang": source_lang,
        "target_lang": target_lang,
        **({"detected_target_lang": detected_target_lang} if detected_target_lang else {}),
        "count": len(out),
    }

    return out, meta


def _join_tokens_like_text(tokens: List[str]) -> str:
    """
    Join tokens into a human-looking sentence:
    - no space before punctuation tokens like , . ; : ! ? …
    - space elsewhere
    """
    out = []
    for tok in tokens:
        if not tok:
            continue
        if out and (_is_punct(tok) or tok in [",", ".", ";", ":", "!", "?", "…"]):
            out[-1] = out[-1] + tok
        else:
            out.append(tok)
    return " ".join(out).strip()


def _is_punct(tok: str) -> bool:
    return bool(_PUNCT_RE.match(tok))

# =================================================

def pangloss_xml_to_sentence_pairs_json(pangloss_xml_filepath):

    with open(pangloss_xml_filepath, "rb") as f:
        xml_data = f.read()

    # Parse XML
    root = ET.fromstring(xml_data)

    # Extract sentences
    data = []
    for sentence in root.findall('.//S'):
        try:
            source = sentence.find('.//TRANSL').text
            target = sentence.find('.//FORM').text.strip()
            word_connections = {}

            for word in sentence.findall('.//W'):
                target_word = word.find('.//FORM').text.strip()
                source_word = word.find('.//TRANSL').text.strip()
                word_connections[source_word] = [target_word]

            data.append({
                'source': source,
                'target': target,
                'word connections': word_connections
            })
        except:
            print("issue with sentence {}".format(sentence))

    return data





# =============


TAG_RE = re.compile(r'^[A-Z0-9.\-]+$')

def _is_taglike(s: str) -> bool:
    """Heuristic: checks if a string looks like a grammatical tag."""
    s = s.strip()
    return bool(TAG_RE.match(s)) and len(s) <= 10

def transform_gloss_json(input_path: str, output_path: str) -> None:
    """
    Read a JSON file containing glossed sentences, transform it into
    {"source", "target", "word connections"} format, and save to output_path.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    transformed = []

    for item in data:
        source = item.get("source", "")
        target = item.get("target", "")
        gloss_list = item.get("gloss", [])
        word_connections = defaultdict(list)

        for word_entry in gloss_list:
            word_form = (word_entry.get("Word") or "").strip()
            if not word_form:
                continue

            morphemes = word_entry.get("Morphemes", []) or []
            glosses = [m.get("Gloss", "").strip() for m in morphemes if m.get("Gloss")]
            if not glosses and word_entry.get("Gloss"):
                glosses = [word_entry["Gloss"].strip()]

            # fallback for punctuation
            if not glosses and word_form in {"?", "!", ",", ";", ":", ".", "…", "—", "–"}:
                glosses = [word_form]

            if not glosses:
                continue

            glosses = list(dict.fromkeys(glosses))  # remove duplicates

            # If multiple short grammatical tags, join them as composite
            if len(glosses) > 1 and all(_is_taglike(g) for g in glosses):
                composite = ">".join(glosses)
                word_connections[composite].append(word_form)
            else:
                for g in glosses:
                    word_connections[g].append(word_form)

        transformed.append({
            "source": source,
            "target": target,
            "word connections": dict(word_connections)
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transformed, f, ensure_ascii=False, indent=2)

    print(f"✅ Transformation complete. Output written to: {output_path}")

