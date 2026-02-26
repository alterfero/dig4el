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

import xml.etree.ElementTree as ET


def _get_direct_child_text(parent, tag, *, lang=None):
    """
    Return the text of the first direct child <tag> of parent.
    If lang is provided, match xml:lang exactly.
    """
    for child in list(parent):
        if child.tag != tag:
            continue
        if lang is not None:
            if child.get("{http://www.w3.org/XML/1998/namespace}lang") != lang:
                continue
        if child.text and child.text.strip():
            return child.text.strip()
    return None


def _reconstruct_target_from_words(sentence, form_kind_preference=("phono", "orth", None)):
    """
    Build target sentence by concatenating W/FORM tokens.
    Tries kindOf preferences in order; falls back to first FORM if none match.
    """
    tokens = []
    for w in sentence.findall("./W"):
        form_el = None

        # Try preferred kindOf values first
        for kind in form_kind_preference:
            if kind is None:
                continue
            for cand in w.findall("./FORM"):
                if cand.get("kindOf") == kind and cand.text and cand.text.strip():
                    form_el = cand
                    break
            if form_el is not None:
                break

        # Fallback: any FORM
        if form_el is None:
            for cand in w.findall("./FORM"):
                if cand.text and cand.text.strip():
                    form_el = cand
                    break

        if form_el is not None:
            tokens.append(form_el.text.strip())

    # Simple join; Pangloss tokens often already include hyphens etc.
    return " ".join(tokens).strip() if tokens else None


def pangloss_xml_to_sentence_pairs_json(pangloss_xml_filepath, *, pivot_lang="fr", target_form_kind=("phono", "orth")):
    with open(pangloss_xml_filepath, "rb") as f:
        xml_data = f.read()

    root = ET.fromstring(xml_data)

    data = []
    for s in root.findall(".//S"):
        try:
            # 1) SOURCE: sentence-level translation (direct child of S), prefer pivot_lang
            source = _get_direct_child_text(s, "TRANSL", lang=pivot_lang) \
                     or _get_direct_child_text(s, "TRANSL")  # fallback any lang

            # 2) TARGET: sentence-level FORM if present, else reconstruct from W tokens
            target = _get_direct_child_text(s, "FORM")  # some Pangloss exports put it here
            if not target:
                target = _reconstruct_target_from_words(s, form_kind_preference=(*target_form_kind, None))

            # 3) WORD CONNECTIONS: token-level mapping from W/TRANSL -> W/FORM
            word_connections = {}
            for w in s.findall("./W"):
                # pick word-level translation in pivot_lang if possible
                w_transl = _get_direct_child_text(w, "TRANSL", lang=pivot_lang) or _get_direct_child_text(w, "TRANSL")
                if not w_transl:
                    continue

                # pick word-level form with preferred kindOf
                w_form = None
                for kind in (*target_form_kind, None):
                    if kind is None:
                        # any FORM
                        w_form = _get_direct_child_text(w, "FORM")
                        if w_form:
                            break
                    else:
                        for cand in w.findall("./FORM"):
                            if cand.get("kindOf") == kind and cand.text and cand.text.strip():
                                w_form = cand.text.strip()
                                break
                        if w_form:
                            break

                if not w_form:
                    continue

                # handle repeated source tokens by accumulating
                word_connections.setdefault(w_transl, []).append(w_form)

            # Skip unusable sentences cleanly
            if not source and not target:
                continue

            data.append({
                "source": source or "",
                "target": target or "",
                "word connections": word_connections
            })

        except Exception as e:
            sid = s.get("id", "<?>")
            print(f"issue with sentence id={sid}: {e}")

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

