import xml.etree.ElementTree as ET
import json
from libs import utils


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