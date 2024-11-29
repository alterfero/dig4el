from libs import construction_agent as ca
from libs import knowledge_graph_utils as kgu, cq_observers as cqo
import json
from libs import construction_agent as ca, stats
import matplotlib.pyplot as plt
import pandas as pd

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

c = ca.Properson_Construction("PP3SG")
c.populate_data_list(kg)
with open ("/Users/sebastienchristian/Desktop/ca_data.json", "w") as f:
    json.dump(c.data_list, f, indent=4)

# Display raw observer data
print("Observer data list")
for item in c.data_list:
    print(item)

# USING BINARY VALUE INFLUENCE
df = c.data_df
# List of parameters to encode
parameters = ['speaker_gender', 'listener_gender', 'ref_gender', 'number', 'intent', 'polarity', 'semantic_role']

# USING (IN)CONSISTENCY OR TARGET WORDS ACROSS VALUES

def parameter_consistency(cdf, parameter):
    # Group by the target word and get unique values of the parameter
    grouped = cdf.groupby('target_words')[parameter].nunique()
    # If any target word has multiple values of the parameter, it is consistent across values
    consistent_words = grouped[grouped > 1]
    return len(consistent_words) > 0, consistent_words

results = {}

for param in parameters:
    consistency, details = parameter_consistency(df, param)
    results[param] = {
        "consistent_words": consistency,
        "details": details.to_dict()  # Words that appear across multiple values
    }

influential_params = [param for param in results.keys() if results[param]["consistent_words"] is False]
# Display results
print()
print("The expression of the concept {} varies with {}. ".format(c.properson, ", ".join(influential_params)))
print()
#
# for param, result in results.items():
#     print(f"Parameter: {param}")
#     print(f"  Words Consistent Across Multiple Values: {result['consistent_words']}")
#     if result['consistent_words']:
#         print(f"  Details: {result['details']}")
#     print()

# USING INFORMATION THEORY

# # Assess parameter influence using Mutual Information
# mi_scores = stats.assess_parameter_influence_mi(c.data_df, c.parameters)
#
# # Assess parameter influence using Standardized Residuals
# residuals_dict = stats.assess_parameter_influence_residuals(c.data_df, c.parameters)
