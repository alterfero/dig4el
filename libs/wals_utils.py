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
from libs import utils as u
import pandas as pd
import math
import numpy as np
import pickle
from collections import defaultdict
from pathlib import Path
import libs.utils as u
from multiprocessing import Pool, cpu_count

# parameter.csv list parameters by pk and their names
#
# domainelement.csv lists all the existing values of these parameters, referencing parameter pk
#
# value.csv and valueset.csv tell what languages uses which value by referencing the value id, the language pk and the parameter pk
# They share the same pk.
#
# language.csv contains all the languages with their pk, id, name and location

# GLOBAL VARIABLES
try:
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json", encoding='utf-8') as f:
        parameter_pk_by_name = json.load(f)
    with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json", encoding='utf-8') as f:
        parameter_pk_by_name_filtered = json.load(f)
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
        language_by_pk = json.load(f)
    with open("./external_data/wals_derived/domain_elements_by_language.json", encoding='utf-8') as f:
        domain_elements_by_language = json.load(f)
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", encoding='utf-8') as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json", encoding='utf-8') as f:
        domain_element_by_pk = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_family.json", encoding='utf-8') as f:
        language_pk_by_family = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_subfamily.json", encoding='utf-8') as f:
        language_pk_by_subfamily = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_genus.json", encoding='utf-8') as f:
        language_pk_by_genus = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_macroarea.json", encoding='utf-8') as f:
        language_pk_by_macroarea = json.load(f)
    with open("./external_data/wals_derived/language_pk_id_by_name.json", encoding='utf-8') as f:
        language_pk_id_by_name = json.load(f)
    with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", encoding='utf-8') as f:
        value_by_domain_element_pk = json.load(f)
    with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", encoding='utf-8') as f:
        valueset_by_pk = json.load(f)
    with open("./external_data/wals_derived/n_param_by_language_id.json", encoding='utf-8') as f:
        n_param_by_language_id = json.load(f)
    with open("./external_data/wals_derived/language_info_by_id_lookup_table.json", encoding='utf-8') as f:
        language_info_by_id = json.load(f)
    with open("./external_data/wals_derived/param_pk_by_de_pk.json", encoding='utf-8') as f:
        param_pk_by_de_pk = json.load(f)
    with open("./external_data/wals_derived/params_pk_by_language_pk.json", encoding='utf-8') as f:
        params_pk_by_language_pk = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_id.json", encoding='utf-8') as f:
        language_pk_by_id = json.load(f)
    cpt = pd.read_json("./external_data/wals_derived/de_conditional_probability_df.json")
    cpt.index = cpt.index.astype(str)
    cpt.columns = cpt.columns.astype(str)
except FileNotFoundError:
    with open("../external_data/wals_derived/parameter_pk_by_name_lookup_table.json", encoding='utf-8') as f:
        parameter_pk_by_name = json.load(f)
    with open("../external_data/wals_derived/parameter_pk_by_name_filtered.json", encoding='utf-8') as f:
        parameter_pk_by_name_filtered = json.load(f)
    with open("../external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
        language_by_pk = json.load(f)
    with open("../external_data/wals_derived/domain_elements_by_language.json", encoding='utf-8') as f:
        domain_elements_by_language = json.load(f)
    with open("../external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", encoding='utf-8') as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    with open("../external_data/wals_derived/domain_element_by_pk_lookup_table.json", encoding='utf-8') as f:
        domain_element_by_pk = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_family.json", encoding='utf-8') as f:
        language_pk_by_family = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_subfamily.json", encoding='utf-8') as f:
        language_pk_by_subfamily = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_genus.json", encoding='utf-8') as f:
        language_pk_by_genus = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_macroarea.json", encoding='utf-8') as f:
        language_pk_by_macroarea = json.load(f)
    with open("../external_data/wals_derived/language_pk_id_by_name.json", encoding='utf-8') as f:
        language_pk_id_by_name = json.load(f)
    with open("../external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", encoding='utf-8') as f:
        value_by_domain_element_pk = json.load(f)
    with open("../external_data/wals_derived/valueset_by_pk_lookup_table.json", encoding='utf-8') as f:
        valueset_by_pk = json.load(f)
    with open("../external_data/wals_derived/language_info_by_id_lookup_table.json", encoding='utf-8') as f:
        language_info_by_id = json.load(f)
    with open("../external_data/wals_derived/param_pk_by_de_pk.json", encoding='utf-8') as f:
        param_pk_by_de_pk = json.load(f)
    with open("../external_data/wals_derived/params_pk_by_language_pk.json", encoding='utf-8') as f:
        params_pk_by_language_pk = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_id.json", encoding='utf-8') as f:
        language_pk_by_id = json.load(f)
    cpt = pd.read_json("../external_data/wals_derived/de_conditional_probability_df.json")
    cpt.index = cpt.index.astype(str)
    cpt.columns = cpt.columns.astype(str)

parameter_name_by_pk = {}
for name, pk in parameter_pk_by_name.items():
    parameter_name_by_pk[str(pk)] = name

def build_language_pk_by_id():
    language_pk_by_id = {}
    for lpk in language_by_pk:
        try:
            language_pk_by_id[language_by_pk[lpk]["id"]] = lpk
        except KeyError:
            print("no id field in language pk {}".format(lpk))

    with open("../external_data/wals_derived/language_pk_by_id.json", "w", encoding='utf-8') as f:
        json.dump(language_pk_by_id, f, ensure_ascii=False, indent=4)



def build_param_pk_by_de_pk():
    param_pk_by_de_pk = {}
    for ppk in domain_elements_pk_by_parameter_pk:
        depks =  domain_elements_pk_by_parameter_pk[ppk]
        for depk in depks:
            if depk not in param_pk_by_de_pk.keys():
                param_pk_by_de_pk[depk] = ppk

    with open("../external_data/wals_derived/param_pk_by_de_pk.json", "w", encoding='utf-8') as f:
        json.dump(param_pk_by_de_pk, f, ensure_ascii=False, indent=4)


def build_param_name_by_de_name():
    param_name_by_de_name = {}
    for de_pk, info in domain_element_by_pk.items():
        ppk = info["parameter_pk"]
        p_name = parameter_name_by_pk[str(ppk)]
        param_name_by_de_name[info["name"]] = p_name

    with open("../external_data/wals_derived/param_name_by_de_name.json", "w", encoding='utf-8') as f:
        json.dump(param_name_by_de_name, f, ensure_ascii=False, indent=4)


def build_params_pk_by_language_pk():
    params_pk_by_language_pk = {}
    for language_pk in domain_elements_by_language:
        params_pk_by_language_pk[language_pk] = []
        for depk in domain_elements_by_language[language_pk]:
            if str(depk) in param_pk_by_de_pk.keys():
                ppk = param_pk_by_de_pk[str(depk)]
                if ppk not in params_pk_by_language_pk[language_pk]:
                    params_pk_by_language_pk[language_pk].append(ppk)
            else:
                print("build_params_pk_by_language_pk: {} not in param_pk_by_de_pk".format(depk))

    with open("../external_data/wals_derived/params_pk_by_language_pk.json", "w", encoding='utf-8') as f:
        json.dump(params_pk_by_language_pk, f, ensure_ascii=False, indent=4)



def get_careful_name_of_de_pk(depk):
    info = domain_element_by_pk[str(depk)]
    if "name" in info.keys():
        if info["name"] != "" and str(info["name"]).lower() != "nan":
            return info["name"]
    elif "description" in info.keys():
        if info["description"] != "" and str(info["description"]).lower() != "nan":
            return info["description"]
    else:
        return(str(depk))

def extract_wals_cp_matrix_from_general_data(ppk1, ppk2, active_wals_cpt):
    """ creates the conditional probability matrix P(p1 | p2) and returns it as  df"""
    # if rows of extracted cpt samples have only zeros, making impossible a normalization,
    # the values of such rows are changed to uniform distributions, expressing the absence of information.

    if str(ppk1) in domain_elements_pk_by_parameter_pk and str(ppk2) in domain_elements_pk_by_parameter_pk:

        p1_de_pk_list = domain_elements_pk_by_parameter_pk[ppk1]
        p2_de_pk_list = domain_elements_pk_by_parameter_pk[ppk2]
        # P1 GIVEN P2 DF
        # keep only p1 on rows
        filtered_cpt_p1 = active_wals_cpt.loc[p1_de_pk_list]
        # keep only given p2 on columns
        filtered_cpt_p1_given_p2 = filtered_cpt_p1[p2_de_pk_list]
        # normalization: all the columns of each row (primary event) should sum up to 1
        filtered_cpt_p1_given_p2_normalized = filtered_cpt_p1_given_p2.apply(u.normalize_column, axis=0)

        return filtered_cpt_p1_given_p2_normalized
    else:
        # either wrong or not wals ppk
        return None

def compute_MRF_potential_function_from_general_data(ppk1, ppk2):
    """ use geometric mean to compute potential function from conditional probabilities.
    potentials are considered uniform across all languages."""

    # if rows of extracted cpt samples have only zeros, making impossible a normalization,
    # the values of such rows are changed to uniform distributions, expressing the absence of information.

    # storing potentials as pickles as new ones are created, as it takes time
    potential_filename = str(ppk1) + "_" + str(ppk2) + ".pkl"
    if potential_filename in os.listdir("../data/potentials/"):
        with open("../data/potentials/"+potential_filename, "rb") as f:
            return pickle.load(f)
    else:
        def normalize_row(row):
            row_sum = row.sum()
            if row_sum == 0:
                # All values are 0, assign uniform distribution using Pandas
                return pd.Series([1 / len(row)] * len(row), index=row.index)
            else:
                # Normalize the row
                return row / row_sum

        cpt = pd.read_json("../external_data/wals_derived/de_conditional_probability_df.json")
        p1_de_pk_list = domain_elements_pk_by_parameter_pk[str(ppk1)]
        p2_de_pk_list = domain_elements_pk_by_parameter_pk[str(ppk2)]

        # P2 GIVEN P1 DF

        # keep only p1 on lines (primary)
        filtered_cpt_p2_given_p1 = cpt.loc[p1_de_pk_list]
        # keep only p2 on columns (secondary)
        filtered_cpt_p2_given_p1 = filtered_cpt_p2_given_p1[p2_de_pk_list]
        # normalization: all the columns of each row (primary event) should sum up to 1
        filtered_cpt_p2_given_p1_normalized = filtered_cpt_p2_given_p1.apply(normalize_row, axis=1)
        # P1 GIVEN P2 DF
        # keep only p2 on lines (primary)
        filtered_cpt_p1_given_p2 = cpt.loc[p2_de_pk_list]
        # keep only p1 on columns (secondary)
        filtered_cpt_p1_given_p2 = filtered_cpt_p1_given_p2[p1_de_pk_list]
        # normalization: all the columns of each row (primary event) should sum up to 1
        filtered_cpt_p1_given_p2_normalized = filtered_cpt_p1_given_p2.apply(normalize_row, axis=1)

        potential_function = np.sqrt(filtered_cpt_p2_given_p1_normalized * filtered_cpt_p1_given_p2_normalized.T)

        with open("../data/potentials/"+potential_filename, "wb") as f:
            pickle.dump(potential_function, f)

        return potential_function

def compute_wals_param_distribution(parameter_pk, language_whitelist):
    param_distribution = {}
    total_count = 0
    if str(parameter_pk) in domain_elements_pk_by_parameter_pk:
        de_pks = domain_elements_pk_by_parameter_pk[str(parameter_pk)]
        for de_pk in de_pks:
            c = 0
            if str(de_pk) in value_by_domain_element_pk:
                for valueset in value_by_domain_element_pk[str(de_pk)]:
                    valueset_pk = valueset["valueset_pk"]
                    # increment counter only if language in whitelist
                    if "language_pk" in valueset_by_pk[str(valueset_pk)]:
                        if str(valueset_by_pk[str(valueset_pk)]["language_pk"]) in language_whitelist:
                            c += 1
                            total_count += 1
                    else:
                        print(" 'language pk' not in valueset_by_pk")
            else:
                print("de_pk {} not in value_by_domain_element_pk".format(de_pk))
            param_distribution[str(de_pk)] = c
        for de_pk in param_distribution.keys():
            if total_count != 0:
                param_distribution[de_pk] = param_distribution[de_pk]/total_count

    else:
        print("Parameter pk {} not in domain_elements_pk_by_parameter_pk".format(parameter_pk))
    return param_distribution

def get_language_pks_by_family(family):
    if family in language_pk_by_family:
        return language_pk_by_family[family]
    else:
        print("Language family {} not in list of known families".format(family))
        return None

def get_language_pks_by_subfamily(subfamily):
    if subfamily in language_pk_by_subfamily:
        return language_pk_by_subfamily[subfamily]
    else:
        print("Language subfamily {} not in list of known subfamilies".format(subfamily))

def get_language_pks_by_genus(genus):
    if genus in language_pk_by_genus:
        return language_pk_by_genus[genus]
    else:
        print("Language genus {} not in list of known genuses".format(genus))

def get_language_pks_by_macroarea(macroarea):
    if macroarea in language_pk_by_macroarea:
        return language_pk_by_macroarea[macroarea]
    else:
        print("Language macroarea {} not in list of known macroareas".format(macroarea))

def build_number_of_params_by_language_id():
    out_dict = {}
    available_languages_filtered = []
    c = 0
    n = len(language_pk_id_by_name)
    for language in language_pk_id_by_name:
        c += 1
        id = language_pk_id_by_name[language]["id"]
        n_param = len(get_language_data_by_id(id))
        out_dict[id] = n_param
        print("{} / {}".format(c, n))

    with open("./external_data/wals_derived/n_param_by_language_id.json", "w", encoding='utf-8') as f:
        json.dump(out_dict, f, ensure_ascii=False)


def build_domain_elements_by_language_and_languages_by_domain_element():
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
        language_by_pk = json.load(f)
    domain_elements_by_language = {}
    languages_by_domain_element = {}
    c = 0
    for language_pk in language_by_pk.keys():
        c += 1
        language_domain_elements = []
        language_id = language_by_pk[language_pk]["id"]
        print("language {}, {}% completion".format(language_by_pk[language_pk]["name"], c/len(language_by_pk)))
        result_dict = get_language_data_by_id(language_id)
        try:
            for parameter in result_dict.keys():
                language_domain_elements.append(result_dict[parameter]["domainelement_pk"])
            domain_elements_by_language[language_pk] = language_domain_elements
            for domain_element in language_domain_elements:
                if domain_element in languages_by_domain_element:
                    languages_by_domain_element[domain_element].append(language_pk)
                else:
                    languages_by_domain_element[domain_element] = [language_pk]
        except:
            print("issue with a result dict on language {}".format(language_id))

    with open("./external_data/wals_derived/domain_elements_by_language.json", "w", encoding='utf-8') as f:
        json.dump(domain_elements_by_language, f, ensure_ascii=False)
    with open("./external_data/wals_derived/languages_by_domain_element.json", "w", encoding='utf-8') as f:
        json.dump(languages_by_domain_element, f, ensure_ascii=False)


#  ================ COMPUTING AND STORING CONDITIONAL PROBABILITY TABLE ========

# ---------------------------------------------------------------------------
# HYPER-PARAMETERS
N_MIN = 1     # keep edge only if we saw B in ≥ N_MIN languages
K_MIN = 1     # …and A∧B in ≥ K_MIN languages
EPSILON = 0.001   # Beta(α,β) prior → avoid 0   (α=β=1)
# ---------------------------------------------------------------------------

def compute_conditional_de_proba(a_pk, b_pk, language_pks, return_counts = False):
    """
    Posterior-mean estimate of  P(A|B)
    P(A|B) estimated as (count(A=ai | B=bj) + epsilon) / (count(B=bj) + epsilon * vocabulary_size)
    Lidstone smoothing with epsilon to avoid zeros.
    """
    b_count = 0
    a_and_b = 0

    for lang_pk in language_pks:
        values = domain_elements_by_language[str(lang_pk)]
        has_a = int(a_pk) in values
        has_b = int(b_pk) in values
        if has_b:
            b_count += 1
            if has_a:
                a_and_b += 1

    if b_count == 0:
        print("no b_count for a_pk {} and b_pk {} for language {}".format(
            get_careful_name_of_de_pk(a_pk),
            get_careful_name_of_de_pk(b_pk),
            language_by_pk.get(str(lang_pk), "no language with that pk")
        ))
        return None  # undefined
    else:
        # Bayesian posterior mean
        p_hat = (a_and_b + EPSILON) / (b_count + EPSILON)

        if return_counts:
            return p_hat, b_count, a_and_b

        return p_hat


def build_conditional_probability_table(filtered_params=True,
                                        language_filter=None,
                                        exclude_lids=None):
    """
    Build a CPT with *None* where counts are too small.
    """
    language_filter = language_filter or {}

    # ---- 1. which languages ------------------------------------------------
    if language_filter:
        language_pks = set()
        for key, table in [
            ("family",     language_pk_by_family),
            ("subfamily",  language_pk_by_subfamily),
            ("genus",      language_pk_by_genus),
            ("macroarea",  language_pk_by_macroarea),
        ]:
            for label in language_filter.get(key, []):
                language_pks |= set(table.get(label, []))
    if exclude_lids:
        exclude_pks = [language_pk_by_id.get(lid, None) for lid in exclude_lids]
        print("exclude pks: {}".format(exclude_pks))
        exclude_pks = set([item for item in exclude_pks if item is not None])
        print("WALS CPT computation: {} language pks from exclusion list not found".format(len(exclude_lids) - len(exclude_pks)))
        language_pks = set(language_by_pk.keys())
        language_pks -= exclude_pks
        print("WALS CPT computation: Excluded {} languages".format(len(exclude_lids)))
        print("Full hash of excluded languages: ")
        print(u.generate_hash_from_list(exclude_lids))
    else:
        language_pks = set(language_by_pk.keys())

    language_pks = list(language_pks)
    # to test
    # language_pks = ['2534', '2343', '1821']

    # ---- 2. which domain-element values -----------------------------------
    lookup_file = (
        "../external_data/wals_derived/"
        "domain_element_by_pk_lookup_table_filtered.json"
        if filtered_params else
        "../external_data/wals_derived/"
        "domain_element_by_pk_lookup_table.json"
    )
    domain_element_pk_list = list(json.load(open(lookup_file, encoding='utf-8')).keys())

    # ---- 3. compute CPT ----------------------------------------------------
    cpt = pd.DataFrame(index=domain_element_pk_list,
                       columns=domain_element_pk_list, dtype=float)
    cpt_trust = pd.DataFrame(index=domain_element_pk_list,
                       columns=domain_element_pk_list, dtype=int)


    for i, a_pk in enumerate(domain_element_pk_list, 1):
        print(f"Row {i}/{len(domain_element_pk_list)}  value={a_pk}")
        for b_pk in domain_element_pk_list:
            if compute_conditional_de_proba(a_pk, b_pk, language_pks, return_counts=True) is None:
                cpt.at[a_pk, b_pk] = np.nan
                cpt_trust.at[a_pk, b_pk] = np.nan
            else:
                p_hat, b_count, a_and_b = compute_conditional_de_proba(a_pk, b_pk, language_pks, return_counts=True)

                if p_hat is None:
                    cpt.at[a_pk, b_pk] = np.nan
                    continue

                # too little support? → mark as None
                if b_count < N_MIN or a_and_b < K_MIN:
                    cpt.at[a_pk, b_pk] = np.nan
                else:
                    cpt.at[a_pk, b_pk] = p_hat

                # trust table
                cpt_trust.at[a_pk, b_pk] = a_and_b

    # ---- 4. save -----------------------------------------------------------
    out = Path("../external_data/wals_derived/partial_cpt")
    out.mkdir(exist_ok=True, parents=True)

    suffix = []
    for key in ["family", "subfamily", "genus", "macroarea"]:
        if key in language_filter and language_filter[key]:
            suffix.append(key + "_" + "-".join(language_filter[key]))
    if exclude_lids:
        suffix.append("languages_excluded_hash_{}".format(u.generate_hash_from_list(exclude_lids)))

    fname = "de_conditional_probability" + ("_" + "_".join(suffix) if suffix else "") + ".json"
    f_trust_name = "de_conditional_probability_trust_" + ("_" + "_".join(suffix) if suffix else "") + ".json"

    cpt.to_json(out / fname)
    cpt_trust.to_json(out / f_trust_name)

    return os.path.join(out, fname)



def compute_row(args):
    """Compute one row of the conditional probability table, used by multiprocessing."""
    a_pk, domain_element_pk_list, language_pks = args
    row = {}
    trust_row = {}

    print(f"Computing row: {get_careful_name_of_de_pk(a_pk)}")

    for b_pk in domain_element_pk_list:
        result = compute_conditional_de_proba(a_pk, b_pk, language_pks, return_counts=True)

        if result is None:
            row[b_pk] = np.nan
            trust_row[b_pk] = np.nan
            continue

        p_hat, b_count, a_and_b = result

        if p_hat is None or b_count < N_MIN or a_and_b < K_MIN:
            row[b_pk] = np.nan
        else:
            row[b_pk] = p_hat

        trust_row[b_pk] = a_and_b

    return a_pk, row, trust_row


def build_conditional_probability_table_multiprocessing(filtered_params=True,
                                                        language_filter=None,
                                                        exclude_lids=None):
    """Main function to build the conditional probability table."""
    language_filter = language_filter or {}

    # ---- 1. which languages ------------------------------------------------
    if language_filter:
        language_pks = set()
        for key, table in [
            ("family",     language_pk_by_family),
            ("subfamily",  language_pk_by_subfamily),
            ("genus",      language_pk_by_genus),
            ("macroarea",  language_pk_by_macroarea),
        ]:
            for label in language_filter.get(key, []):
                language_pks |= set(table.get(label, []))
    elif exclude_lids:
        exclude_pks = [language_pk_by_id.get(lid) for lid in exclude_lids]
        exclude_pks = set(filter(None, exclude_pks))
        language_pks = set(language_by_pk.keys()) - exclude_pks
    else:
        language_pks = set(language_by_pk.keys())

    language_pks = list(language_pks)

    # ---- 2. which domain-element values -----------------------------------
    lookup_file = (
        "../external_data/wals_derived/"
        "domain_element_by_pk_lookup_table_filtered.json"
        if filtered_params else
        "../external_data/wals_derived/"
        "domain_element_by_pk_lookup_table.json"
    )
    domain_element_pk_list = list(json.load(open(lookup_file, encoding='utf-8')))

    # ---- 3. compute CPT ----------------------------------------------------
    num_processes = min(cpu_count() - 1, len(domain_element_pk_list))
    args_list = [(a_pk, domain_element_pk_list, language_pks) for a_pk in domain_element_pk_list]

    with Pool(num_processes) as pool:
        results = pool.map(compute_row, args_list)

    cpt = pd.DataFrame(index=domain_element_pk_list, columns=domain_element_pk_list, dtype=float)
    cpt_trust = pd.DataFrame(index=domain_element_pk_list, columns=domain_element_pk_list, dtype=int)

    for a_pk, row, trust_row in results:
        for b_pk in domain_element_pk_list:
            cpt.at[a_pk, b_pk] = row.get(b_pk, np.nan)
            cpt_trust.at[a_pk, b_pk] = trust_row.get(b_pk, np.nan)

    # ---- 4. Save -----------------------------------------------------------
    out = Path("../external_data/wals_derived/experimental_cpt")
    out.mkdir(exist_ok=True, parents=True)

    suffix = []
    for key in ["family", "subfamily", "genus", "macroarea"]:
        if key in language_filter and language_filter[key]:
            suffix.append(f"{key}_{'-'.join(language_filter[key])}")
    if exclude_lids:
        suffix.append(f"languages_excluded_hash_{u.generate_hash_from_list(exclude_lids)}")

    fname = "de_conditional_probability" + ("_" + "_".join(suffix) if suffix else "") + ".json"
    f_trust_name = "de_conditional_probability_trust_" + ("_" + "_".join(suffix) if suffix else "") + ".json"

    cpt.to_json(out / fname)
    cpt_trust.to_json(out / f_trust_name)

    print("Saved to:", os.path.join(out, fname))
    return os.path.join(out, fname)


#   ========================


# def compute_conditional_de_proba(domain_element_a_pk, domain_element_b_pk, filtered_language_pk=[]):
#     """
#     compute the conditional probability P(a | b).
#     The conditional proba will be computed only with the language pks in the list
#     """
#     total_language_count = len(filtered_language_pk)
#     total_observation_count = 0
#     a_count = 0
#     b_count = 0
#     a_and_b_count = 0
#     for language_pk in filtered_language_pk:
#         total_observation_count += 1
#         language_id = language_by_pk[language_pk]["id"]
#         a = False
#         b = False
#         if int(domain_element_a_pk) in domain_elements_by_language[str(language_pk)]:
#             a = True
#             a_count += 1
#         if int(domain_element_b_pk) in domain_elements_by_language[str(language_pk)]:
#             b = True
#             b_count += 1
#         if a and b:
#             a_and_b_count += 1
#     # P(A|B) = P(A inter B)/P(B)
#     joint_probability =  a_and_b_count / total_observation_count
#     marginal_probability_b = b_count / total_observation_count
#     if b_count != 0:
#         p_a_given_b = a_and_b_count / b_count
#     else:
#         p_a_given_b = None
#
#     return {"a": domain_element_a_pk, "b": domain_element_b_pk, "p_a_given_b": p_a_given_b, "a_count":a_count, "b_count":b_count, "a_and_b_count": a_and_b_count,
#             "marginal_proba_b": marginal_probability_b, "joint_probability": joint_probability}
#
# def build_conditional_probability_table(filtered_params=True, language_filter={}):
#     print("BUILDING D.E. CONDITIONAL PROBABILITY TABLE")
#     """the conditional probability table shows the probability of having value a given value b,
#     for all pairs of values, by measuring them across all languages where they both appear.
#      the filtered_params argument says if we use a filtered list of parameters
#      the language_filter argument is a dict that restricts the languages the cpt is computed on
#      by any of family, subfamily, genus and macroarea."""
#
#     # load convenient lookup tables
#     if filtered_params:
#         with open ("../external_data/wals_derived/domain_element_by_pk_lookup_table_filtered.json") as f:
#             domain_element_by_pk_lookup_table = json.load(f)
#         print("build_conditional_probability_table loaded FILTERED domain element list")
#     else:
#         with open ("../external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
#             domain_element_by_pk_lookup_table = json.load(f)
#         print("build_conditional_probability_table loaded FULL domain element list")
#
#     # use language filter param to list all language pks to use
#     if language_filter != {}:
#         filtered_language_pk = []
#         if "family" in language_filter.keys():
#             for fam in language_filter["family"]:
#                 if fam in language_pk_by_family.keys():
#                     filtered_language_pk += (language_pk_by_family[fam])
#                 else:
#                     print("{} not in language_pk_by_family".format(fam))
#         if "subfamily" in language_filter.keys():
#             for fam in language_filter["subfamily"]:
#                 if fam in language_pk_by_subfamily.keys():
#                     filtered_language_pk += (language_pk_by_subfamily[fam])
#                 else:
#                     print("{} not in language_pk_by_subfamily".format(fam))
#         if "genus" in language_filter.keys():
#             for fam in language_filter["genus"]:
#                 if fam in language_pk_by_genus.keys():
#                     filtered_language_pk += (language_pk_by_genus[fam])
#                 else:
#                     print("{} not in language_pk_by_genus".format(fam))
#         if "macroarea" in language_filter:
#             for fam in language_filter["macroarea"].keys():
#                 if fam in language_pk_by_macroarea.keys():
#                     filtered_language_pk += (language_pk_by_macroarea[fam])
#                 else:
#                     print("{} not in language_pk_by_macroarea".format(fam))
#         filtered_language_pk = list(set(filtered_language_pk))
#     else:
#         filtered_language_pk = list(language_by_pk.keys())
#
#     domain_element_pk_list = list(domain_element_by_pk_lookup_table.keys())
#
#     full_proba_dict = {}
#
#     # create df
#     cpt = pd.DataFrame(index=domain_element_pk_list, columns=domain_element_pk_list)
#
#     #populate df
#     de_count = len(domain_element_pk_list)
#     c = 0
#     for domain_element_1_pk in domain_element_pk_list:
#         c += 1
#         print("Domain element {}, {}% total completion".format(domain_element_1_pk, 100 * c / de_count))
#         for domain_element_2_pk in domain_element_pk_list:
#             proba_dict = compute_conditional_de_proba(domain_element_1_pk, domain_element_2_pk, filtered_language_pk)
#             p_1_given_2 = proba_dict["p_a_given_b"]
#             cpt.at[domain_element_1_pk, domain_element_2_pk] = p_1_given_2
#             full_proba_dict[str(domain_element_1_pk) + " | " + str(domain_element_2_pk)] = proba_dict
#
#     output_folder = "../external_data/wals_derived/partial_cpt/"
#     output_filename = "de_conditional_probability"
#     if "family" in language_filter.keys():
#         output_filename += "_family_" + "-".join(language_filter["family"])
#     if "subfamily" in language_filter.keys():
#         output_filename += "_subfamily_" + "-".join(language_filter["subfamily"])
#     if "genus" in language_filter.keys():
#         output_filename += "_genus_" + "-".join(language_filter["genus"])
#     if "macroarea" in language_filter.keys():
#         output_filename += "_macroarea" + "-".join(language_filter["macroarea"])
#     output_filename += ".json"
#
#     # with open("./external_data/wals_derived/full_de_conditional_probability.json", "w", encoding='utf-8') as f:
#     #     json.dump(full_proba_dict, f)
#     cpt.to_json(output_folder + output_filename)
#     return cpt

def get_available_wals_languages_dict():
    language_dict = {}
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
        language_by_pk_lookup_table = json.load(f)
    for lpk in language_by_pk_lookup_table.keys():
        language_dict[language_by_pk_lookup_table[lpk]["name"]] = {
            "pk": lpk,
            "id": language_by_pk_lookup_table[lpk]["id"]
        }

    with open("./external_data/wals_derived/language_pk_id_by_name.json", "w", encoding='utf-8') as f:
        json.dump(language_dict, f, ensure_ascii=False)

    return language_dict

def get_wals_language_data_by_id_or_name(language_id, language_name=None):
    try:
        with open("./external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
            language_by_pk_lookup_table = json.load(f)
        with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", encoding='utf-8') as f:
            valueset_by_pk_lookup_table = json.load(f)
        with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json", encoding='utf-8') as f:
            domainelement_by_pk_lookup_table = json.load(f)
        with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json", encoding='utf-8') as f:
            parameter_pk_by_name = json.load(f)
        values = u.csv_to_dict("./external_data/wals-master/raw/value.csv")
    except FileNotFoundError:
        with open("../external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
            language_by_pk_lookup_table = json.load(f)
        with open("../external_data/wals_derived/valueset_by_pk_lookup_table.json", encoding='utf-8') as f:
            valueset_by_pk_lookup_table = json.load(f)
        with open("../external_data/wals_derived/domain_element_by_pk_lookup_table.json", encoding='utf-8') as f:
            domainelement_by_pk_lookup_table = json.load(f)
        with open("../external_data/wals_derived/parameter_pk_by_name_lookup_table.json", encoding='utf-8') as f:
            parameter_pk_by_name = json.load(f)
        values = u.csv_to_dict("../external_data/wals-master/raw/value.csv")

    if language_id == None and language_name != None:
        language_pk_found = False
        for pk in language_by_pk_lookup_table.keys():
            if language_by_pk_lookup_table[pk]["name"] == language_name:
                selected_language_pk = pk
                language_pk_found = True
                break
    else:
        language_pk_found = False
        for pk in language_by_pk_lookup_table.keys():
            if language_by_pk_lookup_table[pk]["id"] == language_id:
                selected_language_pk = pk
                language_pk_found = True
                break
    if language_pk_found:
        valueset_list = []
        vpks = []
        # retrieving all value_pk associated with this language_pk
        for pk in valueset_by_pk_lookup_table:
            if str(valueset_by_pk_lookup_table[pk]["language_pk"]) == selected_language_pk:
                vpks.append(pk)
        #print("vpks: ",vpks)
        for item in values:
            if str(item["valueset_pk"]) in vpks:
                valueset_list.append({"valueset_pk":item["valueset_pk"], "domainelement_pk":item["domainelement_pk"]})
        # now getting an organized dict with parameter and parameter_value for that language
        result_dict = {}
        for item in valueset_list:
            parameter_pk = domainelement_by_pk_lookup_table[str(item["domainelement_pk"])]["parameter_pk"]
            for name in parameter_pk_by_name:
                if str(parameter_pk_by_name[name]) == str(parameter_pk):
                    parameter_name = name
                    break
                else:
                    #print("no match for parameter pk {}".format(parameter_pk))
                    parameter_name = None
            domainelement_name = domainelement_by_pk_lookup_table[str(item["domainelement_pk"])]["name"]
            result_dict[parameter_pk] = {
                "parameter": parameter_name,
                "value": domainelement_name,
                "domainelement_pk": item["domainelement_pk"],
                "valueset_pk": item["valueset_pk"]
            }
        return result_dict
    else:
        print("language pk with id {} not found".format(language_id))
        return {}

def build_parameter_pk_by_name_lookup_table():
    print("build_parameter_pk_by_name_lookup_table")
    parameter = u.csv_to_dict("../external_data/wals-master/raw/parameter.csv")
    parameter_pk_by_name_lookup_table = {}
    for entry in parameter:
        parameter_pk_by_name_lookup_table[entry["name"]] = str(entry["pk"])
    # store the lookup table in a file

    with open("../external_data/wals_derived/parameter_pk_by_name_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(parameter_pk_by_name_lookup_table, f, ensure_ascii=False)

    return parameter_pk_by_name_lookup_table

def load_parameter_pk_by_name_lookup_table():
    if "parameter_pk_by_name_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json", encoding='utf-8') as f:
            return json.load(f)
    else:
        print("domain_elements_pk_by_parameter_pk_lookup_table not found in the file system, building it.")
        return build_parameter_pk_by_name_lookup_table()

def build_domain_elements_pk_by_parameter_pk_lookup_table():
    print("build_domain_element_pk_by_parameter_pk_lookup_table")
    domain_element = u.csv_to_dict("../external_data/wals-master/raw/domainelement.csv")
    domain_elements_pk_by_parameter_pk_lookup_table = {}
    for entry in domain_element:
        if entry["parameter_pk"] not in domain_elements_pk_by_parameter_pk_lookup_table:
            domain_elements_pk_by_parameter_pk_lookup_table[entry["parameter_pk"]] = [str(entry["pk"])]
        else:
            domain_elements_pk_by_parameter_pk_lookup_table[entry["parameter_pk"]].append(str(entry["pk"]))
    # store the lookup table in a file

    with open("../external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(domain_elements_pk_by_parameter_pk_lookup_table, f, ensure_ascii=False)

    return domain_elements_pk_by_parameter_pk_lookup_table

def load_domain_elements_pk_by_parameter_pk_lookup_table():
    if "domain_elements_pk_by_parameter_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", encoding='utf-8') as f:
            return json.load(f)
    else:
        print("domain_elements_pk_by_parameter_pk_lookup_table not found in the file system, building it.")
        return build_domain_elements_pk_by_parameter_pk_lookup_table()

def build_domain_element_by_pk_lookup_table():
    print("build_domain_element_by_pk_lookup_table")
    domain_element = u.csv_to_dict("./external_data/wals-master/raw/domainelement.csv")
    domain_element_by_pk_lookup_table = {}
    for entry in domain_element:
        if entry["pk"] not in domain_element_by_pk_lookup_table:
            domain_element_by_pk_lookup_table[entry["pk"]] = entry
        else:
            domain_element_by_pk_lookup_table[entry["pk"]].append(entry)
    # store the lookup table in a file

    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(domain_element_by_pk_lookup_table, f, ensure_ascii=False)

    return domain_element_by_pk_lookup_table

def load_domain_element_by_pk_lookup_table():
    if "domain_element_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open ("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
            return json.load(f)
    else:
        print("domain_element_by_pk_lookup_table not found in the file system, building it.")
        return build_domain_element_by_pk_lookup_table()

def build_value_by_domain_element_pk_lookup_table():
    print("build_value_by_domain_element_pk_lookup_table")
    values = u.csv_to_dict("./external_data/wals-master/raw/value.csv")
    value_by_domain_element_pk_lookup_table = {}
    for value in values:
        if value["domainelement_pk"] not in value_by_domain_element_pk_lookup_table:
            value_by_domain_element_pk_lookup_table[value["domainelement_pk"]] = [value]
        else:
            value_by_domain_element_pk_lookup_table[value["domainelement_pk"]].append(value)
    # store the lookup table in a file

    with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(value_by_domain_element_pk_lookup_table, f, ensure_ascii=False)

    return value_by_domain_element_pk_lookup_table

def load_value_by_domain_element_pk_lookup_table():
    if "value_by_domain_element_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", "r", encoding='utf-8') as f:
            return json.load(f)
    else:
        print("build_value_by_domain_element_pk_lookup_table not found in the file system, building it.")
        return build_value_by_domain_element_pk_lookup_table()

def build_valueset_by_pk_lookup_table():
    print("build_valueset_by_pk_lookup_table")
    valueset = u.csv_to_dict("./external_data/wals-master/raw/valueset.csv")
    valueset_by_pk_lookup_table = {}
    for v in valueset:
        valueset_by_pk_lookup_table[v["pk"]] = v
    # store the lookup table in a file

    with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(valueset_by_pk_lookup_table, f, ensure_ascii=False)

    return valueset_by_pk_lookup_table

def load_valueset_by_pk_lookup_table():
    if "valueset_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", "r", encoding='utf-8') as f:
            return json.load(f)
    else:
        print("valueset_by_pk_lookup_table not found in the file system, building it.")
        return build_valueset_by_pk_lookup_table()

def build_language_by_pk_lookup_table():
    print("build_language_by_pk_lookup_table")
    language = u.csv_to_dict("./external_data/wals-master/raw/language.csv")
    language_by_pk_lookup_table = {}
    for l in language:
        language_by_pk_lookup_table[l["pk"]] = l
    # store the lookup table in a file

    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(language_by_pk_lookup_table, f, ensure_ascii=False)

    return language_by_pk_lookup_table

def load_language_by_pk_lookup_table():
    if "language_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/language_by_pk_lookup_table.json", "r", encoding='utf-8') as f:
            return json.load(f)
    else:
        print("language_by_pk_lookup_table not found in the file system, building it.")
        return build_language_by_pk_lookup_table()

def build_language_info_by_id_lookup_table():
    print("build_language_info_by_id_lookup_table")
    language_info_by_id_lookup_table = {}
    languagesMSD = u.csv_to_dict("./external_data/wals-master/raw/languagesMSD.csv")
    for l in languagesMSD:
        language_info_by_id_lookup_table[l["ID"]] = {
            "name": l["NameNEW"],
            "macroarea": l["MacroareaNEW"],
            "family":l["FamilyNEW"],
            "subfamily":l["SubfamilyNEW"],
            "genus":l["GenusNEW"]
        }
    # store the lookup table in a file

    with open("./external_data/wals_derived/language_info_by_id_lookup_table.json", "w", encoding='utf-8') as f:
        json.dump(language_info_by_id_lookup_table, f, ensure_ascii=False)

    return language_info_by_id_lookup_table

def load_language_info_by_id_lookup_table():
    if "language_info_by_id_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/language_info_by_id_lookup_table.json", "r", encoding='utf-8') as f:
            return json.load(f)
    else:
        print("language_info_by_id_lookup_table not found in the file system, building it.")
        return build_language_info_by_id_lookup_table()

def update_delimiter_file():
    delimiters = {
    "marquesan (Nuku Hiva)": [" ", ".", ",", ";", ":", "!", "?", "…"],
    "rapa": [" ", ".", ",", ";", ":", "!", "?", "…"],
    "paumotu": [" ", ".", ",", ";", ":", "!", "?", "…"],
    "mangareva": [" ", ".", ",", ";", ":", "!", "?", "…"],
    "tahitian": [" ", ".", ",", ";", ":", "!", "?", "…"],
    "french": [" ", ".", ",", ";", ":", "!", "?", "…", "'"],
    "english": [" ", ".", ",", ";", ":", "!", "?", "…", "'"]
}
    wals_language_dict = get_available_wals_languages_dict()
    for language_name in wals_language_dict.keys():
        if language_name not in delimiters.keys():
            delimiters[language_name] = [" ", ".", ",", ";", ":", "!", "?", "…", "'"]

    with open("./data/delimiters.json", "w", encoding='utf-8') as f:
        json.dump(delimiters, f, ensure_ascii=False)


def build_domain_elements_pk_by_parameter_pk_lookup_table_filtered():
    """creates the reduced domain_element_by_pk json based on a limited list of paramaters"""
    with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json", encoding='utf-8') as f:
        filtered_params = json.load(f)
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json", encoding='utf-8') as f:
        domain_element_by_pk_lookup_table = json.load(f)
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", encoding='utf-8') as f:
        domain_elements_pk_by_parameter_pk = json.load(f)

    filtered_de = {}

    for param_name in filtered_params.keys():
        param_pk = filtered_params[param_name]
        if str(param_pk) in domain_elements_pk_by_parameter_pk.keys():
            for depk in domain_elements_pk_by_parameter_pk[str(param_pk)]:
                if str(depk) in domain_element_by_pk_lookup_table.keys():
                    filtered_de[str(depk)] = domain_element_by_pk_lookup_table[str(depk)]
                else:
                    print("{} no in domain_element_by_pk_lookup_table".format(str(depk)))
        else:
            print("{} not in domain_elements_pk_by_parameter_pk".format(param_pk))


    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table_filtered.json", "w", encoding='utf-8') as f:
        json.dump(filtered_de, f, ensure_ascii=False)


def build_language_pk_by_family_subfamily_genus_macroarea():
    with open("./external_data/wals_derived/language_info_by_id_lookup_table.json", encoding='utf-8') as f:
        language_info_by_id = json.load(f)
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", encoding='utf-8') as f:
        language_by_pk = json.load(f)

    language_pk_by_id = {}
    for pk in language_by_pk.keys():
        if str(pk) in language_by_pk.keys():
            language_pk_by_id[language_by_pk[str(pk)]["id"]] = pk
        else:
            print("{} not in language_by_pk_lookup_table".format(pk))

    language_pk_by_family = {}
    language_pk_by_subfamily = {}
    language_pk_by_genus = {}
    language_pk_by_macroarea = {}

    for language_id in language_info_by_id.keys():
        if language_id in language_pk_by_id.keys():
            lpk = str(language_pk_by_id[language_id])
            family = str(language_info_by_id[language_id]["family"])
            subfamily = str(language_info_by_id[language_id]["subfamily"])
            genus = str(language_info_by_id[language_id]["genus"])
            macroarea = str(language_info_by_id[language_id]["macroarea"])
            if family != "nan":
                if family in language_pk_by_family.keys():
                    language_pk_by_family[family].append(lpk)
                else:
                    language_pk_by_family[family] = [lpk]
            if subfamily != "nan":
                if subfamily in language_pk_by_subfamily.keys():
                    language_pk_by_subfamily[subfamily].append(lpk)
                else:
                    language_pk_by_subfamily[subfamily] = [lpk]
            if genus != "nan":
                if genus in language_pk_by_genus.keys():
                    language_pk_by_genus[genus].append(lpk)
                else:
                    language_pk_by_genus[genus] = [lpk]
            if macroarea != "nan":
                if macroarea in language_pk_by_macroarea.keys():
                    language_pk_by_macroarea[macroarea].append(lpk)
                else:
                    language_pk_by_macroarea[macroarea] = [lpk]
        else:
            print("{} not in language_pk_by_id")


    with open("./external_data/wals_derived/language_pk_by_family.json", "w", encoding='utf-8') as f:
        json.dump(language_pk_by_family, f, ensure_ascii=False)
    with open("./external_data/wals_derived/language_pk_by_subfamily.json", "w", encoding='utf-8') as f:
        json.dump(language_pk_by_subfamily, f, ensure_ascii=False)
    with open("./external_data/wals_derived/language_pk_by_genus.json", "w", encoding='utf-8') as f:
        json.dump(language_pk_by_genus, f, ensure_ascii=False)
    with open("./external_data/wals_derived/language_pk_by_macroarea.json", "w", encoding='utf-8') as f:
        json.dump(language_pk_by_macroarea, f, ensure_ascii=False)

