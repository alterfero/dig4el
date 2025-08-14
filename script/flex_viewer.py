import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import json

if "sentence_pairs" not in st.session_state:
    st.session_state.sentence_pairs = None

def parse_flex_xml(xml_content):
    root = ET.fromstring(xml_content)

    data = []

    for phrase in root.findall(".//phrase"):
        sentence_urn = phrase.find("item[@type='txt'][@lang='urn']").text
        sentence_num = phrase.find("item[@type='segnum'][@lang='en']").text

        words_data = []
        for word in phrase.findall("words/word"):
            txt_elem = word.find("item[@type='txt'][@lang='urn']")
            punct_elem = word.find("item[@type='punct'][@lang='urn']")

            if punct_elem is not None:
                words_data.append({"Word": punct_elem.text, "Gloss": "", "Morphemes": []})
                continue

            word_text = txt_elem.text if txt_elem is not None else ""
            gloss_elem = word.find("item[@type='gls'][@lang='en']")
            word_gloss = gloss_elem.text if gloss_elem is not None else ""

            morphemes_data = []
            for morph in word.findall("morphemes/morph"):
                morph_text = morph.find("item[@type='txt'][@lang='urn']")
                morph_gloss = morph.find("item[@type='gls'][@lang='en']")

                morphemes_data.append({
                    "Morph": morph_text.text if morph_text is not None else "",
                    "Gloss": morph_gloss.text if morph_gloss is not None else ""
                })

            words_data.append({"Word": word_text, "Gloss": word_gloss, "Morphemes": morphemes_data})

        data.append({
            "Sentence Number": sentence_num,
            "Sentence": sentence_urn,
            "Words": words_data
        })

    return data

def _convert_to_sentence_pairs(data):
    pairs = []
    for item in data:
        pairs.append(
            {
                "source": "",
                "target": item["Sentence"],
                "gloss": item["Words"]
            }
        )
    return pairs

st.title("FLEX XML Visualizer")

uploaded_file = st.file_uploader("Upload XML file", type="xml")

if uploaded_file:
    xml_content = uploaded_file.read().decode("utf-8")
    parsed_data = parse_flex_xml(xml_content)
    st.session_state.sentence_pairs = _convert_to_sentence_pairs(parsed_data)
    if st.session_state.sentence_pairs:
        st.download_button("Download sentence pairs",
                           data=json.dumps(st.session_state.sentence_pairs, ensure_ascii=False),
                           file_name="sentence_pairs_from_flex.json",
                           mime="application/json"
                           )

    for sentence in parsed_data:
        st.subheader(f"Sentence {sentence['Sentence Number']}")
        st.write(sentence["Sentence"])

        for word in sentence["Words"]:
            st.markdown(f"**{word['Word']}** - *{word['Gloss']}*")

            if word['Morphemes']:
                morph_df = pd.DataFrame(word['Morphemes'])
                st.table(morph_df)


