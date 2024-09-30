import os
import json
from libs import utils as u
import pandas as pd
import math
import numpy as np
import pickle

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
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
        parameter_pk_by_name = json.load(f)
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json") as f:
        language_by_pk = json.load(f)
    with open("./external_data/wals_derived/domain_elements_by_language.json") as f:
        domain_elements_by_language = json.load(f)
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
        domain_element_by_pk = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_family.json") as f:
        language_pk_by_family = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_subfamily.json") as f:
        language_pk_by_subfamily = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_genus.json") as f:
        language_pk_by_genus = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_macroarea.json") as f:
        language_pk_by_macroarea = json.load(f)
    with open("./external_data/wals_derived/language_pk_id_by_name.json") as f:
        language_pk_id_by_name = json.load(f)
    with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json") as f:
        value_by_domain_element_pk = json.load(f)
    with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json") as f:
        valueset_by_pk = json.load(f)
    with open("./external_data/wals_derived/n_param_by_language_id.json") as f:
        n_param_by_language_id = json.load(f)
    with open("./external_data/wals_derived/language_info_by_id_lookup_table.json") as f:
        language_info_by_id = json.load(f)
    with open("./external_data/wals_derived/param_pk_by_de_pk.json") as f:
        param_pk_by_de_pk = json.load(f)
    with open("./external_data/wals_derived/params_pk_by_language_pk.json") as f:
        params_pk_by_language_pk = json.load(f)
    with open("./external_data/wals_derived/language_pk_by_id.json") as f:
        language_pk_by_id = json.load(f)
    cpt = pd.read_json("./external_data/wals_derived/de_conditional_probability_df.json")
except FileNotFoundError:
    with open("../external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
        parameter_pk_by_name = json.load(f)
    with open("../external_data/wals_derived/language_by_pk_lookup_table.json") as f:
        language_by_pk = json.load(f)
    with open("../external_data/wals_derived/domain_elements_by_language.json") as f:
        domain_elements_by_language = json.load(f)
    with open("../external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    with open("../external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
        domain_element_by_pk = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_family.json") as f:
        language_pk_by_family = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_subfamily.json") as f:
        language_pk_by_subfamily = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_genus.json") as f:
        language_pk_by_genus = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_macroarea.json") as f:
        language_pk_by_macroarea = json.load(f)
    with open("../external_data/wals_derived/language_pk_id_by_name.json") as f:
        language_pk_id_by_name = json.load(f)
    with open("../external_data/wals_derived/value_by_domain_element_pk_lookup_table.json") as f:
        value_by_domain_element_pk = json.load(f)
    with open("../external_data/wals_derived/valueset_by_pk_lookup_table.json") as f:
        valueset_by_pk = json.load(f)
    with open("../external_data/wals_derived/language_info_by_id_lookup_table.json") as f:
        language_info_by_id = json.load(f)
    with open("../external_data/wals_derived/param_pk_by_de_pk.json") as f:
        param_pk_by_de_pk = json.load(f)
    with open("../external_data/wals_derived/params_pk_by_language_pk.json") as f:
        params_pk_by_language_pk = json.load(f)
    with open("../external_data/wals_derived/language_pk_by_id.json") as f:
        language_pk_by_id = json.load(f)
    cpt = pd.read_json("../external_data/wals_derived/de_conditional_probability_df.json")

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
    with open("../external_data/wals_derived/language_pk_by_id.json", "w") as f:
        json.dump(language_pk_by_id, f, indent=4)


def build_param_pk_by_de_pk():
    param_pk_by_de_pk = {}
    for ppk in domain_elements_pk_by_parameter_pk:
        depks =  domain_elements_pk_by_parameter_pk[ppk]
        for depk in depks:
            if depk not in param_pk_by_de_pk.keys():
                param_pk_by_de_pk[depk] = ppk
    with open("../external_data/wals_derived/param_pk_by_de_pk.json", "w") as f:
        json.dump(param_pk_by_de_pk, f, indent=4)

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
    with open("../external_data/wals_derived/params_pk_by_language_pk.json", "w") as f:
        json.dump(params_pk_by_language_pk, f, indent=4)


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

def compute_CP_potential_function_from_general_data(ppk1, ppk2):
    """ creates the conditional probability matrix P(ppk2 | ppk1) and returns it as  df"""

    # if rows of extracted cpt samples have only zeros, making impossible a normalization,
    # the values of such rows are changed to uniform distributions, expressing the absence of information.

    def normalize_row(row):
        row_sum = row.sum()
        if row_sum == 0:
            # All values are 0, assign uniform distribution using Pandas
            return pd.Series([1 / len(row)] * len(row), index=row.index)
        else:
            # Normalize the row
            return row / row_sum

    p1_de_pk_list = domain_elements_pk_by_parameter_pk[str(ppk1)]
    p2_de_pk_list = domain_elements_pk_by_parameter_pk[str(ppk2)]

    # P2 GIVEN P1 DF

    # keep only p1 on lines (primary)
    filtered_cpt_p2_given_p1 = cpt.loc[p1_de_pk_list]
    # keep only p2 on columns (secondary)
    filtered_cpt_p2_given_p1 = filtered_cpt_p2_given_p1[p2_de_pk_list]
    # normalization: all the columns of each row (primary event) should sum up to 1
    filtered_cpt_p2_given_p1_normalized = filtered_cpt_p2_given_p1.apply(normalize_row, axis=1)

    return filtered_cpt_p2_given_p1_normalized

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

def compute_param_distribution(parameter_pk, language_whitelist):
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
            param_distribution[de_pk] = param_distribution[de_pk]/total_count
    else:
        print("Parameter pk {} not in domain_elements_pk_by_parameter_pk".format(parameter_pk))
    return param_distribution

def get_language_pks_by_family(family):
    if family in language_pk_by_family:
        return language_pk_by_family[family]
    else:
        print("Language family {} not in list of known families".format(family))
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
    with open("./external_data/wals_derived/n_param_by_language_id.json", "w") as f:
        json.dump(out_dict, f)



def build_domain_elements_by_language_and_languages_by_domain_element():
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json") as f:
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
    with open("./external_data/wals_derived/domain_elements_by_language.json", "w") as f:
        json.dump(domain_elements_by_language, f)
    with open("./external_data/wals_derived/languages_by_domain_element.json", "w") as f:
        json.dump(languages_by_domain_element, f)

def compute_conditional_de_proba(domain_element_a_pk, domain_element_b_pk, filtered_language_pk=[]):
    """
    compute the conditional probability of having domain_element_b in a language knowing that we have domain_element a
    The conditional proba will be computed only with the language pks in the list
    """
    total_language_count = len(filtered_language_pk)
    total_observation_count = 0
    a_count = 0
    b_count = 0
    a_and_b_count = 0
    for language_pk in filtered_language_pk:
        total_observation_count += 1
        language_id = language_by_pk[language_pk]["id"]
        a = False
        b = False
        a_and_b = False
        if int(domain_element_a_pk) in domain_elements_by_language[str(language_pk)]:
            a = True
            a_count += 1
        if int(domain_element_b_pk) in domain_elements_by_language[str(language_pk)]:
            b = True
            b_count += 1
        if a and b:
            a_and_b_count += 1
    # P(B|A) = P(A inter B)/P(A)
    joint_probability =  a_and_b_count / total_observation_count
    marginal_probability_a = a_count / total_observation_count
    if a_count != 0:
        p_b_knowing_a = a_and_b_count / a_count
    else:
        p_b_knowing_a = None

    return {"a": domain_element_a_pk, "b": domain_element_b_pk, "p_b_knowing_a": p_b_knowing_a, "a_count":a_count, "b_count":b_count, "a_and_b_count": a_and_b_count,
            "marginal_proba_a": marginal_probability_a, "joint_probability": joint_probability}

def build_conditional_probability_table(filtered_params=True, language_filter={}):
    print("BUILDING D.E. CONDITIONAL PROBABILITY TABLE")
    """the conditional probability table shows the probability of having value b knowing value a,
    for all pairs of values, by measuring them across all languages where they both appear. 
     the filtered_params argument says if we use a filtered list of parameters
     the language_filter argument is a dict that restricts the languages the cpt is computed on
     by any of family, subfamily, genus and macroarea."""

    # load convenient lookup tables
    if filtered_params:
        with open ("./external_data/wals_derived/domain_element_by_pk_lookup_table_filtered.json") as f:
            domain_element_by_pk_lookup_table = json.load(f)
        print("build_conditional_probability_table loaded FILTERED domain element list")
    else:
        with open ("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
            domain_element_by_pk_lookup_table = json.load(f)
        print("build_conditional_probability_table loaded FULL domain element list")

    # use language filter param to list all language pks to use
    if language_filter != {}:
        filtered_language_pk = []
        if "family" in language_filter.keys():
            for fam in language_filter["family"]:
                if fam in language_pk_by_family.keys():
                    filtered_language_pk += (language_pk_by_family[fam])
                else:
                    print("{} not in language_pk_by_family".format(fam))
        if "subfamily" in language_filter.keys():
            for fam in language_filter["subfamily"]:
                if fam in language_pk_by_subfamily.keys():
                    filtered_language_pk += (language_pk_by_subfamily[fam])
                else:
                    print("{} not in language_pk_by_subfamily".format(fam))
        if "genus" in language_filter.keys():
            for fam in language_filter["genus"]:
                if fam in language_pk_by_genus.keys():
                    filtered_language_pk += (language_pk_by_genus[fam])
                else:
                    print("{} not in language_pk_by_genus".format(fam))
        if "macroarea" in language_filter:
            for fam in language_filter["macroarea"].keys():
                if fam in language_pk_by_macroarea.keys():
                    filtered_language_pk += (language_pk_by_macroarea[fam])
                else:
                    print("{} not in language_pk_by_macroarea".format(fam))
        filtered_language_pk = list(set(filtered_language_pk))
    else:
        filtered_language_pk = list(language_by_pk.keys())

    domain_element_pk_list = list(domain_element_by_pk_lookup_table.keys())

    full_proba_dict = {}

    # create df
    cpt = pd.DataFrame(index=domain_element_pk_list, columns=domain_element_pk_list)

    #populate df
    de_count = len(domain_element_pk_list)
    c = 0
    for domain_element_a_pk in domain_element_pk_list:
        c += 1
        print("Domain element {}, {}% total completion".format(domain_element_a_pk, 100 * c / de_count))
        for domain_element_b_pk in domain_element_pk_list:
            proba_dict = compute_conditional_de_proba(domain_element_a_pk, domain_element_b_pk, filtered_language_pk)
            p_b_knowing_a = proba_dict["p_b_knowing_a"]
            cpt.at[domain_element_a_pk, domain_element_b_pk] = p_b_knowing_a
            full_proba_dict[str(domain_element_a_pk) + " | " + str(domain_element_b_pk)] = proba_dict

    output_folder = "./external_data/wals_derived/partial_cpt/"
    output_filename = "de_conditional_probability"
    if "family" in language_filter.keys():
        output_filename += "_family_" + "-".join(language_filter["family"])
    if "subfamily" in language_filter.keys():
        output_filename += "_subfamily_" + "-".join(language_filter["subfamily"])
    if "genus" in language_filter.keys():
        output_filename += "_genus_" + "-".join(language_filter["genus"])
    if "macroarea" in language_filter.keys():
        output_filename += "_macroarea" + "-".join(language_filter["macroarea"])
    output_filename += ".json"

    # with open("./external_data/wals_derived/full_de_conditional_probability.json", "w") as f:
    #     json.dump(full_proba_dict, f)
    cpt.to_json(output_folder + output_filename)
    return cpt

def build_conditional_probability_table_per_subfamily():
    c = 0
    for subfamily in language_pk_by_subfamily:
        c += 1
        print("Language subfamily {} with {} languages, {} subfamilies/{} completed".format(subfamily, len(language_pk_by_subfamily[subfamily]), c, len(language_pk_by_subfamily)))
        build_conditional_probability_table(filtered_params=True, language_filter={"subfamily":[subfamily]})

def get_available_wals_languages_dict():
    language_dict = {}
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json") as f:
        language_by_pk_lookup_table = json.load(f)
    for lpk in language_by_pk_lookup_table.keys():
        language_dict[language_by_pk_lookup_table[lpk]["name"]] = {
            "pk": lpk,
            "id": language_by_pk_lookup_table[lpk]["id"]
        }
    with open("./external_data/wals_derived/language_pk_id_by_name.json", "w") as f:
        json.dump(language_dict, f)
    return language_dict


def get_language_data_by_id(language_id):
    try:
        with open("./external_data/wals_derived/language_by_pk_lookup_table.json") as f:
            language_by_pk_lookup_table = json.load(f)
        with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json") as f:
            valueset_by_pk_lookup_table = json.load(f)
        with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
            domainelement_by_pk_lookup_table = json.load(f)
        with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
            parameter_pk_by_name = json.load(f)
        values = u.csv_to_dict("./external_data/wals-master/raw/value.csv")
    except FileNotFoundError:
        with open("../external_data/wals_derived/language_by_pk_lookup_table.json") as f:
            language_by_pk_lookup_table = json.load(f)
        with open("../external_data/wals_derived/valueset_by_pk_lookup_table.json") as f:
            valueset_by_pk_lookup_table = json.load(f)
        with open("../external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
            domainelement_by_pk_lookup_table = json.load(f)
        with open("../external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
            parameter_pk_by_name = json.load(f)
        values = u.csv_to_dict("../external_data/wals-master/raw/value.csv")

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
    parameter = u.csv_to_dict("./external_data/wals-master/raw/parameter.csv")
    parameter_pk_by_name_lookup_table = {}
    for entry in parameter:
        parameter_pk_by_name_lookup_table[entry["name"]] = entry["pk"]
    # store the lookup table in a file
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json", "w") as f:
        json.dump(parameter_pk_by_name_lookup_table, f)
    return parameter_pk_by_name_lookup_table

def load_parameter_pk_by_name_lookup_table():
    if "parameter_pk_by_name_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
            return json.load(f)
    else:
        print("domain_elements_pk_by_parameter_pk_lookup_table not found in the file system, building it.")
        return build_parameter_pk_by_name_lookup_table()

def build_domain_elements_pk_by_parameter_pk_lookup_table():
    print("build_domain_element_by_parameter_pk_lookup_table")
    domain_element = u.csv_to_dict("./external_data/wals-master/raw/domainelement.csv")
    domain_elements_pk_by_parameter_pk_lookup_table = {}
    for entry in domain_element:
        if entry["parameter_pk"] not in domain_elements_pk_by_parameter_pk_lookup_table:
            domain_elements_pk_by_parameter_pk_lookup_table[entry["parameter_pk"]] = [entry["pk"]]
        else:
            domain_elements_pk_by_parameter_pk_lookup_table[entry["parameter_pk"]].append(entry["pk"])
    # store the lookup table in a file
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", "w") as f:
        json.dump(domain_elements_pk_by_parameter_pk_lookup_table, f)
    return domain_elements_pk_by_parameter_pk_lookup_table

def load_domain_elements_pk_by_parameter_pk_lookup_table():
    if "domain_elements_pk_by_parameter_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
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
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json", "w") as f:
        json.dump(domain_element_by_pk_lookup_table, f)
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
    with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", "w") as f:
        json.dump(value_by_domain_element_pk_lookup_table, f)
    return value_by_domain_element_pk_lookup_table

def load_value_by_domain_element_pk_lookup_table():
    if "value_by_domain_element_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", "r") as f:
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
    with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", "w") as f:
        json.dump(valueset_by_pk_lookup_table, f)
    return valueset_by_pk_lookup_table

def load_valueset_by_pk_lookup_table():
    if "valueset_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", "r") as f:
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
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", "w") as f:
        json.dump(language_by_pk_lookup_table, f)
    return language_by_pk_lookup_table

def load_language_by_pk_lookup_table():
    if "language_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/language_by_pk_lookup_table.json", "r") as f:
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
    with open("./external_data/wals_derived/language_info_by_id_lookup_table.json", "w") as f:
        json.dump(language_info_by_id_lookup_table, f)
    return language_info_by_id_lookup_table

def load_language_info_by_id_lookup_table():
    if "language_info_by_id_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/language_info_by_id_lookup_table.json", "r") as f:
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
    with open("./data/delimiters.json", "w") as f:
        json.dump(delimiters, f)

def build_domain_elements_pk_by_parameter_pk_lookup_table_filtered():
    """creates the reduced domain_element_by_pk json based on a limited list of paramaters"""
    with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
        filtered_params = json.load(f)
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
        domain_element_by_pk_lookup_table = json.load(f)
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
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

    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table_filtered.json", "w") as f:
        json.dump(filtered_de, f)

def build_language_pk_by_family_subfamily_genus_macroarea():
    with open("./external_data/wals_derived/language_info_by_id_lookup_table.json") as f:
        language_info_by_id = json.load(f)
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json") as f:
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

    with open("./external_data/wals_derived/language_pk_by_family.json", "w") as f:
        json.dump(language_pk_by_family, f)
    with open("./external_data/wals_derived/language_pk_by_subfamily.json", "w") as f:
        json.dump(language_pk_by_subfamily, f)
    with open("./external_data/wals_derived/language_pk_by_genus.json", "w") as f:
        json.dump(language_pk_by_genus, f)
    with open("./external_data/wals_derived/language_pk_by_macroarea.json", "w") as f:
        json.dump(language_pk_by_macroarea, f)