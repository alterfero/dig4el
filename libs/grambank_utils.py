# Copyright (C) 2024 Sebastien CHRISTIAN, University of French Polynesia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import json
import csv
import pandas as pd
import numpy as np
from libs import utils as u

# GLOBAL VARIABLES
try:
    with open("../external_data/grambank_derived/grambank_pname_by_pid.json", "r") as f:
        grambank_pname_by_pid = json.load(f)
    with open("../external_data/grambank_derived/grambank_pid_by_pname.json", "r") as f:
        grambank_pid_by_pname = json.load(f)
    with open("../external_data/grambank_derived/grambank_param_value_dict.json", "r") as f:
        grambank_param_value_dict = json.load(f)
    with open("../external_data/grambank_derived/grambank_language_by_lid.json", "r") as f:
        grambank_language_by_lid = json.load(f)
    with open("../external_data/grambank_derived/grambank_pvalues_by_language.json", "r") as f:
        grambank_pvalues_by_language = json.load(f)
    with open("../external_data/grambank_derived/parameter_id_by_value_id.json", "r") as f:
        parameter_id_by_value_id = json.load(f)
    with open("../external_data/grambank_derived/grambank_vname_by_vid.json", "r") as f:
        grambank_vname_by_vid = json.load(f)
    with open("../external_data/grambank_derived/grambank_language_id_by_vid.json", "r") as f:
        grambank_language_id_by_vid = json.load(f)

    cpt = pd.read_json("../external_data/grambank_derived/grambank_vid_conditional_probability.json")
except FileNotFoundError:
    with open("./external_data/grambank_derived/grambank_pname_by_pid.json", "r") as f:
        grambank_pname_by_pid = json.load(f)
    with open("./external_data/grambank_derived/grambank_pid_by_pname.json", "r") as f:
        grambank_pid_by_pname = json.load(f)
    with open("./external_data/grambank_derived/grambank_param_value_dict.json", "r") as f:
        grambank_param_value_dict = json.load(f)
    with open("./external_data/grambank_derived/grambank_language_by_lid.json", "r") as f:
        grambank_language_by_lid = json.load(f)
    with open("./external_data/grambank_derived/grambank_pvalues_by_language.json", "r") as f:
        grambank_pvalues_by_language = json.load(f)
    with open("./external_data/grambank_derived/parameter_id_by_value_id.json", "r") as f:
        parameter_id_by_value_id = json.load(f)
    with open("./external_data/grambank_derived/grambank_vname_by_vid.json", "r") as f:
        grambank_vname_by_vid = json.load(f)
    with open("./external_data/grambank_derived/grambank_language_id_by_vid.json", "r") as f:
        grambank_language_id_by_vid = json.load(f)
    cpt = pd.read_json("./external_data/grambank_derived/grambank_vid_conditional_probability.json")

def build_vname_by_vid():
    grambank_vname_by_vid = {}
    for pid in grambank_param_value_dict.keys():
        for vid, valueinfo in grambank_param_value_dict[pid]["pvalues"].items():
            grambank_vname_by_vid[vid] = valueinfo["vname"]
    with open("../external_data/grambank_derived/grambank_vname_by_vid.json", "w") as f:
        json.dump(grambank_vname_by_vid, f, indent=4)


def get_grambank_language_data_by_id_or_name(language_id, language_name=None):

    language_id_found = False
    if language_id is None and language_name is not None:
        # check if lname is in grambank
        selected_language_id, language_id_found = next(((lid, True) for lid in grambank_language_by_lid if grambank_language_by_lid[lid]["name"] == language_name), (None, False))
    elif language_id is not None and language_name is None:
        language_id_found = language_id in grambank_language_by_lid
        selected_language_id = language_id
    if language_id_found:
        result_dict = {}
        pvalues = grambank_pvalues_by_language[selected_language_id]
        for pvalue in pvalues:
            result_dict[pvalue[:5]] = {
                "parameter": grambank_pname_by_pid[pvalue[:5]],
                "value": pvalue,
                "vid": pvalue,
            }
        return result_dict
    else:
        print("language id {} not found".format(language_id))
        return {}


def compute_grambank_cp_matrix_from_general_data(pid1, pid2):
    """ creates the conditional probability matrix P(pid1 | pid2) and returns it as  df"""

    if pid1 in grambank_param_value_dict and pid2 in grambank_param_value_dict:

        pid1_list = list(grambank_param_value_dict[pid1]["pvalues"].keys())
        pid2_list = list(grambank_param_value_dict[pid2]["pvalues"].keys())

        # P1 GIVEN P2 DF
        # keep only p1 on rows
        filtered_cpt_p1 = cpt.loc[pid1_list]
        # keep only p2 on columns
        filtered_cpt_p1_given_p2 = filtered_cpt_p1[pid2_list]
        # normalization: all the columns of each row (primary event) should sum up to 1
        filtered_cpt_p2_given_p1_normalized = filtered_cpt_p1_given_p2.apply(u.normalize_column, axis=0)

        return filtered_cpt_p2_given_p1_normalized
    else:
        # not grambank pids
        return None


def compute_grambank_param_distribution(pid, lids_list=["ALL"]):
    if lids_list == ["ALL"]:
        available_lids = list(grambank_language_by_lid.keys())
    else:
        available_lids = lids_list
    vids = list(grambank_param_value_dict[pid]["pvalues"].keys())
    param_distribution = {key: 0 for key in vids}
    for lid, pvalues in grambank_pvalues_by_language.items():
        if lid in available_lids:
            for pvalue in pvalues:
                if pvalue in param_distribution.keys():
                    param_distribution[pvalue] += 1
    total_count = sum(param_distribution.values())
    for vid in param_distribution.keys():
        param_distribution[vid] = param_distribution[vid]/total_count
    return param_distribution

        
def compute_grambank_conditional_de_proba(vid_a, vid_b, filtered_language_lid=[]):
    """
    compute the conditional probability p(vid_a | vid_b)
    """
    total_language_count = len(filtered_language_lid)
    total_observation_count = 0
    a_count = 0
    b_count = 0
    a_and_b_count = 0
    for language_id in filtered_language_lid:
        total_observation_count += 1
        a = False
        b = False
        if vid_a in grambank_pvalues_by_language[language_id]:
            a = True
            a_count += 1
        if vid_b in grambank_pvalues_by_language[language_id]:
            b = True
            b_count += 1
        if a and b:
            a_and_b_count += 1
    # P(A|B) = P(A inter B)/P(B)
    joint_probability =  a_and_b_count / total_observation_count
    marginal_probability_b = b_count / total_observation_count
    if b_count != 0:
        p_a_given_b = a_and_b_count / b_count
    else:
        p_a_given_b = None

    return {"a": vid_a, "b": vid_b, "p_a_given_b": p_a_given_b, "a_count":a_count, "b_count":b_count, "a_and_b_count": a_and_b_count,
            "marginal_proba_b": marginal_probability_b, "joint_probability": joint_probability}


def build_grambank_conditional_probability_table(language_filter={}):
    print("BUILDING D.E. CONDITIONAL PROBABILITY TABLE")
    """the conditional probability table shows the probability of having value b knowing value a,
    for all pairs of values, by measuring them across all languages where they both appear. 
     the filtered_params argument says if we use a filtered list of parameters
     the language_filter argument is a dict that restricts the languages the cpt is computed on
     by any of family, subfamily, genus and macroarea."""

    # use language filter param to list all language pks to use
    # TODO: Make possible language filtering for conditional probability computation
    # if language_filter != {}:
    #     filtered_language_lid = []
    #     if "family" in language_filter.keys():
    #         for fam in language_filter["family"]:
    #             if fam in language_pk_by_family.keys():
    #                 filtered_language_lid += (language_pk_by_family[fam])
    #             else:
    #                 print("{} not in language_pk_by_family".format(fam))
    #     if "subfamily" in language_filter.keys():
    #         for fam in language_filter["subfamily"]:
    #             if fam in language_pk_by_subfamily.keys():
    #                 filtered_language_lid += (language_pk_by_subfamily[fam])
    #             else:
    #                 print("{} not in language_pk_by_subfamily".format(fam))
    #     if "genus" in language_filter.keys():
    #         for fam in language_filter["genus"]:
    #             if fam in language_pk_by_genus.keys():
    #                 filtered_language_lid += (language_pk_by_genus[fam])
    #             else:
    #                 print("{} not in language_pk_by_genus".format(fam))
    #     if "macroarea" in language_filter:
    #         for fam in language_filter["macroarea"].keys():
    #             if fam in language_pk_by_macroarea.keys():
    #                 filtered_language_lid += (language_pk_by_macroarea[fam])
    #             else:
    #                 print("{} not in language_pk_by_macroarea".format(fam))
    #     filtered_language_lid = list(set(filtered_language_lid))
    # else:
    #     filtered_language_lid = list(language_by_pk.keys())

    filtered_language_lid = list(grambank_language_by_lid.keys())
    vid_list = list(parameter_id_by_value_id.keys())

    #full_proba_dict = {}

    # create df
    cpt = pd.DataFrame(index=vid_list, columns=vid_list)

    #populate df
    de_count = len(vid_list)
    c = 0
    for vid_a in vid_list:
        c += 1
        print("vid {}, {}% total completion".format(vid_a, 100 * c / de_count))
        for vid_b in vid_list:
            proba_dict = compute_grambank_conditional_de_proba(vid_a, vid_b, filtered_language_lid)
            p_a_given_b = proba_dict["p_a_given_b"]
            cpt.at[vid_a, vid_b] = p_a_given_b

    output_folder = "../external_data/grambank_derived/"
    output_filename = "grambank_vid_conditional_probability"
    if "family" in language_filter.keys():
        output_filename += "_family_" + "-".join(language_filter["family"])
    if "subfamily" in language_filter.keys():
        output_filename += "_subfamily_" + "-".join(language_filter["subfamily"])
    if "genus" in language_filter.keys():
        output_filename += "_genus_" + "-".join(language_filter["genus"])
    if "macroarea" in language_filter.keys():
        output_filename += "_macroarea" + "-".join(language_filter["macroarea"])
    output_filename += ".json"

    cpt.to_json(output_folder + output_filename)
    return cpt


def build_grambank_pvalues_by_language():
    grambank_pvalues_by_language = {}
    with open("../external_data/grambank-1.0.3/cldf/values.csv", "r") as f:
        dict_reader = csv.DictReader(f)
        values = [row for row in dict_reader]
    entry_count = len(values)
    for item in values:
        if item["Language_ID"] not in grambank_pvalues_by_language.keys() and item["Code_ID"] != "":
            grambank_pvalues_by_language[item["Language_ID"]] = [item["Code_ID"]]
        elif item["Language_ID"] in grambank_pvalues_by_language.keys() and item["Code_ID"] != "":
            grambank_pvalues_by_language[item["Language_ID"]].append(item["Code_ID"])
    print("grambank_pvalues_by_language built, {} data points.".format(entry_count))
    with open("../external_data/grambank_derived/grambank_pvalues_by_language.json", "w") as f:
        json.dump(grambank_pvalues_by_language, f, indent=4)


def build_grambank_language_id_by_vid():
    grambank_language_id_by_vid = {}
    with open("../external_data/grambank-1.0.3/cldf/values.csv", "r") as f:
        dict_reader = csv.DictReader(f)
        values = [row for row in dict_reader]
    entry_count = len(values)
    for item in values:
        if item["Code_ID"] != "" and item["Code_ID"] not in grambank_language_id_by_vid.keys() and item["Language_ID"] != "":
            grambank_language_id_by_vid[item["Code_ID"]] = [item["Language_ID"]]
        elif item["Code_ID"] != "" and item["Code_ID"] in grambank_language_id_by_vid.keys() and item["Language_ID"] != "":
            grambank_language_id_by_vid[item["Code_ID"]].append(item["Language_ID"])
    print("grambank_language_id_by_pvalue_id built, {} data points.".format(entry_count))
    with open("../external_data/grambank_derived/grambank_language_id_by_vid.json", "w") as f:
        json.dump(grambank_language_id_by_vid, f, indent=4)


def build_grambank_language_by_lid():
    language_by_lid = {}
    with open("../external_data/grambank-1.0.3/cldf/languages.csv", "r") as f:
        csv_reader = csv.DictReader(f)
        languages = [row for row in csv_reader]
    for item in languages:
        language_by_lid[item["Glottocode"]] = {
            "glottocode": item["Glottocode"],
            "id": item["ID"],
            "name": item["Name"],
            "family": item["Family_name"],
            "macroarea": item["Macroarea"]
        }
    with open("../external_data/grambank_derived/language_by_lid.json", "w") as f:
        json.dump(language_by_lid, f, indent=4)


def build_grambank_pname_by_pid():
    # grambank pname_by_pid and pid_by_name
    grambank_pname_by_pid = {}
    grambank_pid_by_pname = {}
    with open("../external_data/grambank-1.0.3/cldf/parameters.csv") as f:
        csv_reader = csv.DictReader(f)
        params = [row for row in csv_reader]
        for param in params:
            grambank_pname_by_pid[param["ID"]] = param["Name"]
            grambank_pid_by_pname[param["Name"]] = param["ID"]
    with open("../external_data/grambank_derived/grambank_pname_by_pid.json", "w") as f:
        json.dump(grambank_pname_by_pid, f, indent=4)
    with open("../external_data/grambank_derived/grambank_pid_by_pname.json", "w") as f:
        json.dump(grambank_pid_by_pname, f, indent=4)


def build_grambank_param_value_dict():
    # grambank_param_value_dict
    grambank_param_value_dict = {}
    with open("../external_data/grambank-1.0.3/cldf/codes.csv") as f:
        csv_reader = csv.DictReader(f)
        gram_codes = [row for row in csv_reader]
    for item in gram_codes:
        if item["Parameter_ID"] in grambank_param_value_dict.keys():
            grambank_param_value_dict[item["Parameter_ID"]]["pvalues"][item["ID"]] = {
                "vid": item["ID"],
                "vcode": item["Name"],
                "vname": item["Description"]
                }
        else:
            grambank_param_value_dict[item["Parameter_ID"]] = {
                "pid": item["Parameter_ID"],
                "pname": grambank_pname_by_pid[item["Parameter_ID"]],
                "pvalues":{
                    item["ID"]: {
                        "vid": item["ID"],
                        "vcode": item["Name"],
                        "vname": item["Description"]
                    }
                }
            }
    with open("../external_data/grambank_derived/grambank_param_value_dict.json", "w") as f:
        json.dump(grambank_param_value_dict, f, indent=4)
        
        
def build_pid_by_vid():
    pid_by_vid = {}
    with open("../external_data/grambank-1.0.3/cldf/codes.csv", "r") as f:
        dict_reader = csv.DictReader(f)
        items = [row for row in dict_reader]
    for item in items:
        pid_by_vid[item["ID"]] = item["Parameter_ID"]
    with open("../external_data/grambank_derived/parameter_id_by_value_id.json", "w") as f:
        json.dump(pid_by_vid, f, indent=4)


def build_vids_by_lid():
    vids_by_lid = {}
    with open("../external_data/grambank-1.0.3/cldf/values.csv", "r") as f:
        dict_reader = csv.DictReader(f)
        items = [row for row in dict_reader]
    for item in items:
        if item["Language_ID"] in vids_by_lid.keys():
            vids_by_lid[item["Language_ID"]].append(item["Code_ID"])
        else:
            vids_by_lid[item["Language_ID"]] = [item["Code_ID"]]
    with open("../external_data/grambank_derived/pvalue_ids_by_language_id.json", "w") as f:
        json.dump(vids_by_lid, f, indent=4)


def build_lid_by_family():
    lid_by_family = {}
    for lid, ldata in grambank_language_by_lid.items():
        if ldata["family"] not in lid_by_family.keys():
            lid_by_family[ldata["family"]] = [lid]
        else:
            lid_by_family[ldata["family"]].append(lid)
    with open("../external_data/grambank_derived/lid_by_family.json", "w") as f:
        json.dump(lid_by_family, f, indent=4)
