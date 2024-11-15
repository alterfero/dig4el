from libs import construction_agent as ca
from libs import knowledge_graph_utils as kgu, cq_observers as cqo
import json
from libs import construction_agent as ca, stats

transcription_file_list = [
    "/Users/sebastienchristian/Desktop/CQ_transcriptions/French/recording_cq_A family album_1716852912_french_Seb_Seb_1719423282.json",
    "/Users/sebastienchristian/Desktop/CQ_transcriptions/French/recording_cq_At the doctor_1715973404_french_Sebastien_Sebastien_1719362850.json",
    "/Users/sebastienchristian/Desktop/CQ_transcriptions/French/recording_cq_Going fishing_1716315461_French_Sebastien_Sebastien_1730401618.json",
    "/Users/sebastienchristian/Desktop/CQ_transcriptions/French/recording_cq_Preparing for the New Year_1716403492_french_Sebastien_Sebastien_1719358814.json",
    "/Users/sebastienchristian/Desktop/CQ_transcriptions/French/recording_cq_where is my notebook_1716497507_french_Sebastien_Sebastien_1719357570.json"
]
transcription_list = []
for filename in transcription_file_list:
    with open(filename, "r") as f:
        transcription_list.append(json.load(f))

kg, unique_words, unique_words_frequency, total_target_word_count = \
    kgu.consolidate_cq_transcriptions(
        transcription_list,
        "French",
        delimiters=transcription_list[0]["delimiters"]
    )

c = ca.Properson_Construction("PP1SG")
c.populate_data_list(kg)
with open ("/Users/sebastienchristian/Desktop/ca_data.json", "w") as f:
    json.dump(c.data_list, f, indent=4)

# Assess parameter influence using Mutual Information
mi_scores = stats.assess_parameter_influence_mi(c.data_df, c.parameters)

# Assess parameter influence using Standardized Residuals
residuals_dict = stats.assess_parameter_influence_residuals(c.data_df, c.parameters)
