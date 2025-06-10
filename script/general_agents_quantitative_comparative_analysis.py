from __future__ import annotations
import csv
import json
import os
import pandas as pd
import re
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from libs import general_agents
from libs import wals_utils as wu
from libs.utils import generate_hash_from_list
from scipy.stats import gaussian_kde
from matplotlib.patches import Patch

"""
1) Load test results by language ("../test_result_analysis/summaries/per_language_accuracy.csv")
2) For each language, generate naive results based on what is expected for this language family:
    - Determine the family of this language.
    - Compute the expected value of each of the nobs parameter for that language.
    - Create a baseline_truth_table showing for which parameter these results are right or wrong.
    - Compute the accuracy of the baseline_truth_table. 
    - Compare this baseline_accuracy with the test results accuracy
"""

# experimental_lids = ["abk", "ace", "adi", "ame", "arg", "obo", "aeg", "anj", "may", "bto", "bud", "baw", "bkr",
#                 "bul", "ccm", "nko", "cct", "chv", "tin", "cle", "cpl", "chr", "coo", "cso", "wel", "dsh",
#                 "ger", "din", "ndy", "est", "eng", "bsq", "fij", "fin", "fre", "fua", "fut", "krb", "gae",
#                 "gmw", "orh", "hai", "hau", "htc", "arm", "arw", "iaa", "iba", "ind", "jpn", "jng", "kmj",
#                 "abu", "khs", "kch", "kmh", "klm", "awt", "kwo", "knr", "kos", "tla", "kis", "ksg", "krr",
#                 "lug", "lmp", "lmn", "lon", "mlu", "mad", "mxo", "mxc", "mxp", "min", "tab", "mmn", "mau",
#                 "mng", "mao", "brm", "kho", "nav", "ngz", "nht", "nun", "otm", "tsh", "pal", "poh", "qim",
#                 "rot", "sdw", "san", "ngm", "spa", "sul", "mup", "svs", "swe",
#                 "twe", "tml", "ttn", "tgk", "tha", "len", "tsi", "tur", "tzu", "ung", "wal", "wol", "wlf",
#                 "sio", "cnt", "yur"]

experimental_lids = ["abk", "ace", "adi"]

nobs = {
      "Order of Object, Oblique, and Verb": 84,
      "Order of Adposition and Noun Phrase": 85,
      "Order of Adverbial Subordinator and Clause": 94,
      "Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase": 95,
      "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
      "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
      "Order of Genitive and Noun": 86,
      "Order of Degree Word and Adjective": 91
    }

out_list = []


# load test result
test_file_path = "../test_result_analysis/summaries/per_language_accuracy.csv"
with open(test_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    test_data = [row for row in reader]

def create_naive_vs_dig4el_accuracy_list(tested_language):
    language_name = tested_language["language_name"]
    print(language_name)
    language_test_mean_accuracy = tested_language["mean"]
    print("test accuracy: {}".format(language_test_mean_accuracy))
    language_id = wu.language_pk_id_by_name[language_name]["id"]
    language_pk = wu.language_pk_id_by_name[language_name]["pk"]
    language_family = wu.language_info_by_id[language_id].get("family", "no family")

    # use a general agent to compute priors based on the language family, the naive baseline
    if language_family != "no family":
        ga = general_agents.GeneralAgent("baseline", parameter_names=[p for p in nobs.keys()],
                                         language_stat_filter={"family": [language_family]},
                                         verbose=False)
    else:
        ga = general_agents.GeneralAgent("baseline", parameter_names=[p for p in nobs.keys()],
                                         verbose=False)
    naive_baseline_beliefs = ga.get_beliefs()
    print("naive_baseline_beliefs: {}".format(naive_baseline_beliefs))
    # compute accuracy of naive beliefs across test parameters
    naive_accuracy = 0.0
    naive_win_count = 0.0
    for lpn in ga.language_parameters.keys():
        print(lpn)
        # naive depk pick
        naive_depk = max(naive_baseline_beliefs[lpn], key=naive_baseline_beliefs[lpn].get)
        print("naive: {}".format(naive_depk))
        # true value
        language_data = wu.get_wals_language_data_by_id_or_name(language_id)
        ppk = int(wu.parameter_pk_by_name[lpn])
        true_depk = language_data[ppk]["domainelement_pk"]
        print("true: {}".format(true_depk))
        # accuracy
        if str(true_depk) == str(naive_depk):
            naive_win_count += 1.0
    naive_accuracy = naive_win_count/len(nobs)
    print("accuracy: {}".format(naive_accuracy))

    out_list.append(
        {
            "language": language_name,
            "dig4el mean accuracy": language_test_mean_accuracy,
            "naive accuracy": naive_accuracy
        }
    )

if __name__ == "__main__":
    from multiprocessing import Pool, cpu_count
    num_processes = min(cpu_count() - 1, len(experimental_lids))
    with Pool(num_processes) as pool:
        pool.map(create_naive_vs_dig4el_accuracy_list, experimental_lids)

    with open("../test_result_analysis/summaries/comparative_results_baseline_vs_dig4el.json", "w") as f:
        json.dump(out_list, f)
    print("saved results")









