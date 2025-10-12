import xml.etree.ElementTree as ET
import json
from libs import utils


def pangloss_xml_to_sentence_pairs_json(pangloss_xml_filepath):

    test_xml_data = xml_data = '''<?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE TEXT SYSTEM "https://cocoon.huma-num.fr/schemas/Archive.dtd">
    <TEXT xml:lang="iai" id="crdo-IAI_OBOLO">
        <HEADER>
            <TITLE xml:lang="fr">L'écho dans le rocher Oboloo à Lekiny</TITLE>
            <TITLE xml:lang="en">The echo in the Oboloo Rock at Lekiny</TITLE>
            <SOUNDFILE href="Nouvelle_Caledonie/Iaai/OBOLO.mp3"/>
        </HEADER>
        <S id="OBOLOs1">
            <AUDIO start="0.0800" end="3.9200"/>
            <FORM kindOf="phono">Bongon wakap hnyi kic \"Oboloo\" ien kic. </FORM>
            <TRANSL xml:lang="fr">Histoire de l'écho dans le rocher \"Oboloo\".</TRANSL>
            <W>
                <FORM kindOf="phono">Bongon</FORM>
                <TRANSL xml:lang="fr">histoire</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">wakap</FORM>
                <TRANSL xml:lang="fr">écho</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">hnyi</FORM>
                <TRANSL xml:lang="fr">dans</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">kic</FORM>
                <TRANSL xml:lang="fr">rocher</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">Oboloo</FORM>
                <TRANSL xml:lang="fr">Oboloo</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">ien</FORM>
                <TRANSL xml:lang="fr">nom+à lui</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">kic</FORM>
                <TRANSL xml:lang="fr">rocher</TRANSL>
            </W>
        </S>
        <S id="OBOLOs2">
            <AUDIO start="3.9200" end="6.9000"/>
            <FORM kindOf="phono">E hu ûxacaköu anyin wahingat adreem. </FORM>
            <TRANSL xml:lang="fr">Autrefois, les vieux s'étant réunis,</TRANSL>
            <W>
                <FORM kindOf="phono">E</FORM>
                <TRANSL xml:lang="fr">il</TRANSL>
            </W>
            <W>
                <FORM kindOf="phono">hu</FORM>
                <TRANSL xml:lang="fr">y a</TRANSL>
            </W>
        </S>
    </TEXT>'''
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

    # Output JSON
    with open("/Users/sebastienchristian/Desktop/ngen_pangloss_NG_Guinea_fowl.json", "w", encoding='utf-8') as f:
        utils.save_json_normalized(data, f)

pangloss_xml_to_sentence_pairs_json("/Users/sebastienchristian/Desktop/d/01-These/language_lib/ngen/NG_Guinea_fowl.xml")