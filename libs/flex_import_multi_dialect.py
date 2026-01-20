#!/usr/bin/env python3
"""
Parse FLEx Interlinear XML and export per-dialect JSON files.

Usage:
  python flex_xml_to_dialect_json.py input.xml out_dir

Output:
  out_dir/Zerqet.json
  out_dir/SomeOtherDialect.json
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


PUNCT_NO_SPACE_BEFORE = {".", ",", ";", ":", "?", "!", ")", "]", "}", "…"}
PUNCT_NO_SPACE_AFTER = {"(", "[", "{"}


def strip_ns(tag: str) -> str:
    """Remove XML namespace from a tag if present."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def findall_local(root: ET.Element, path: str) -> List[ET.Element]:
    """
    Minimal helper for namespace-agnostic search using local names.
    path like: "interlinear-text/item" or "paragraphs/paragraph"
    """
    parts = path.strip("/").split("/")
    nodes = [root]
    for part in parts:
        nxt = []
        for n in nodes:
            for c in list(n):
                if strip_ns(c.tag) == part:
                    nxt.append(c)
        nodes = nxt
    return nodes


def iter_desc_local(root: ET.Element, local_name: str):
    """Iterate descendants matching local tag name."""
    for el in root.iter():
        if strip_ns(el.tag) == local_name:
            yield el


def safe_text(el: Optional[ET.Element]) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def slugify(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)
    return s or "dialect"


def dialect_from_title(title_text: str) -> str:
    """
    "Zerqet (Bunjel) Story ..." -> "Zerqet"
    Fallback: first token.
    """
    t = title_text.strip()
    if not t:
        return "Unknown"
    if " (" in t:
        return t.split(" (", 1)[0].strip()
    # If no parenthesis, take first chunk up to first space
    return t.split(None, 1)[0].strip()


def is_punct_token(tok: str) -> bool:
    return tok in PUNCT_NO_SPACE_BEFORE or tok in PUNCT_NO_SPACE_AFTER or re.fullmatch(r"[.,;:!?…]+", tok or "") is not None


def join_tokens_with_punct(tokens: List[str]) -> str:
    """
    Join tokens into a sentence with basic punctuation spacing rules.
    """
    out = []
    for tok in tokens:
        if not tok:
            continue
        if not out:
            out.append(tok)
            continue

        prev = out[-1]

        if tok in PUNCT_NO_SPACE_BEFORE or (is_punct_token(tok) and tok not in PUNCT_NO_SPACE_AFTER):
            out[-1] = prev + tok
        elif prev in PUNCT_NO_SPACE_AFTER:
            out[-1] = prev + tok
        else:
            out.append(" " + tok)

    return "".join(out).strip()


def get_item_text(word_el: ET.Element, item_type: str, lang: Optional[str] = None) -> Optional[str]:
    """
    Return the text for <item type="..."> in a given element.
    If lang is None, accept any lang.
    """
    for item in findall_local(word_el, "item"):
        if item.get("type") != item_type:
            continue
        if lang is not None and item.get("lang") != lang:
            continue
        txt = safe_text(item)
        if txt:
            return txt
    return None


@dataclass
class ParseConfig:
    source_lang: str = "en"      # mainstream language (free translation + word gloss labels)
    target_lang: Optional[str] = None  # inferred if None


def infer_target_lang(interlinear: ET.Element, source_lang: str = "en") -> Optional[str]:
    """
    Infer target language code by looking for a non-source title.
    Example: <item type="title" lang="sjs-Latn">...</item>
    """
    for item in findall_local(interlinear, "item"):
        if item.get("type") == "title":
            lang = item.get("lang")
            if lang and lang != source_lang:
                return lang
    return None


def extract_dialect(interlinear: ET.Element, source_lang: str = "en") -> str:
    """
    Take the first non-source title as dialect-bearing string.
    """
    for item in findall_local(interlinear, "item"):
        if item.get("type") == "title" and item.get("lang") != source_lang:
            return dialect_from_title(safe_text(item))
    return "Unknown"


def extract_paragraph_entries(interlinear: ET.Element, cfg: ParseConfig) -> List[dict]:
    """
    Extract one JSON entry per <paragraph>.
    """
    target_lang = cfg.target_lang or infer_target_lang(interlinear, cfg.source_lang)
    if not target_lang:
        # fallback: will accept any non-source token lang at word level
        target_lang = None

    entries: List[dict] = []

    paragraphs = []
    for paragraphs_el in findall_local(interlinear, "paragraphs"):
        paragraphs.extend(findall_local(paragraphs_el, "paragraph"))

    for par in paragraphs:
        # Find the "phrase container" in your sample: <phrases> ... </phrases>
        # FLEx sometimes uses <phrase> elements; your sample uses a nested <word><words>...
        phrases_els = findall_local(par, "phrases")
        if not phrases_els:
            continue

        # Get the paragraph-level free translation (often item type="gls" lang="en" near segnum)
        source_sentence = ""
        # look for item type gls lang en within paragraph
        for item in iter_desc_local(par, "item"):
            if item.get("type") == "gls" and item.get("lang") == cfg.source_lang:
                # take the last one; in FLEx the free translation is usually the final gls
                candidate = safe_text(item)
                if candidate:
                    source_sentence = candidate

        # Collect all word elements that represent tokens: usually under <words><word> ... </word></words>
        word_token_els: List[ET.Element] = []
        for words_container in iter_desc_local(par, "words"):
            for w in findall_local(words_container, "word"):
                word_token_els.append(w)

        if not word_token_els:
            continue

        target_tokens: List[str] = []
        connections: Dict[str, List[str]] = defaultdict(list)

        for w in word_token_els:
            # token text: prefer txt in target_lang; else punct; else any txt not in source lang
            tok = None
            if target_lang is not None:
                tok = get_item_text(w, "txt", target_lang)
                if tok is None:
                    tok = get_item_text(w, "punct", target_lang)
            else:
                # no known target lang: try any txt not in source_lang
                tok = None
                for item in findall_local(w, "item"):
                    itype = item.get("type")
                    ilang = item.get("lang")
                    if itype == "txt" and ilang != cfg.source_lang:
                        tok = safe_text(item)
                        break
                if tok is None:
                    # punctuation can still be used
                    for item in findall_local(w, "item"):
                        itype = item.get("type")
                        if itype == "punct":
                            tok = safe_text(item)
                            break

            if tok:
                target_tokens.append(tok)

            # word-level gloss label in source_lang (semantic/grammatical label in your description)
            gloss = get_item_text(w, "gls", cfg.source_lang)

            # Only connect gloss to non-punctuation target tokens
            if gloss and tok and not is_punct_token(tok):
                connections[gloss].append(tok)

        target_sentence = join_tokens_with_punct(target_tokens).strip()

        # Skip empty records
        if not source_sentence and not target_sentence:
            continue

        entries.append(
            {
                "source": source_sentence,
                "target": target_sentence,
                "word connections": dict(connections),
            }
        )

    return entries


def parse_file(xml_path: str) -> Dict[str, List[dict]]:
    """
    Returns: dialect -> list of entries
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    by_dialect: Dict[str, List[dict]] = defaultdict(list)

    # There may be multiple <interlinear-text> sections
    for interlinear in iter_desc_local(root, "interlinear-text"):
        dialect = extract_dialect(interlinear, source_lang="en")
        cfg = ParseConfig(source_lang="en", target_lang=infer_target_lang(interlinear, "en"))
        entries = extract_paragraph_entries(interlinear, cfg)
        if entries:
            by_dialect[dialect].extend(entries)

    return dict(by_dialect)


def write_outputs(by_dialect: Dict[str, List[dict]], out_dir: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    written = []

    for dialect, entries in by_dialect.items():
        fname = f"{slugify(dialect)}.json"
        out_path = os.path.join(out_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
            f.write("\n")
        written.append(out_path)

    return written


def parse_flex_xml_to_dialect_json(
    xml_path: str,
    *,
    source_lang: str = "en",
) -> Dict[str, List[dict]]:
    """
    Parse a FLEx interlinear XML file and return per-dialect JSON-ready data.

    Parameters
    ----------
    xml_path : str
        Path to the FLEx XML file.
    source_lang : str, default="en"
        Language code used for free translations and gloss labels.

    Returns
    -------
    Dict[str, List[dict]]
        Mapping:
            dialect_name -> list of entries

        Each entry has the shape:
        {
            "source": str,
            "target": str,
            "word connections": Dict[str, List[str]]
        }

    Notes
    -----
    - Dialects are inferred from non-source <item type="title"> elements.
    - One entry is produced per paragraph.
    - No files are written; the caller owns serialization.
    """
    by_dialect: Dict[str, List[dict]] = {}

    tree = ET.parse(xml_path)
    root = tree.getroot()

    for interlinear in iter_desc_local(root, "interlinear-text"):
        dialect = extract_dialect(interlinear, source_lang=source_lang)

        cfg = ParseConfig(
            source_lang=source_lang,
            target_lang=infer_target_lang(interlinear, source_lang),
        )

        entries = extract_paragraph_entries(interlinear, cfg)
        if not entries:
            continue

        if dialect not in by_dialect:
            by_dialect[dialect] = []

        by_dialect[dialect].extend(entries)

    return by_dialect

# fp = "/Users/sebastienchristian/Desktop/d/01-These/language_lib/Jenia/senhaja berber/Flex Texts export 16 Jan with Dialects.xml"
# output = parse_flex_xml_to_dialect_json(fp)
# for dialect in output.keys():
#     with open(f"/Users/sebastienchristian/Desktop/d/01-These/language_lib/Jenia/senhaja berber/sentence_pairs_{dialect}.json",
#               "w") as f:
#         json.dump(output[dialect], f, indent=4)
