import xml.etree.ElementTree as ET

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
            "Sentence (URN)": sentence_urn,
            "Words": words_data
        })

    return data

