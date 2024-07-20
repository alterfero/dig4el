import os
import json
from libs import utils as u

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

def build_domain_elements_pk_by_parameter_pk_lookup_table(domain_element):
    print("build_domain_element_by_parameter_pk_lookup_table")
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

def load_domain_elements_pk_by_parameter_pk_lookup_table(domain_element):
    if "domain_elements_pk_by_parameter_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
            return json.load(f)
    else:
        print("domain_elements_pk_by_parameter_pk_lookup_table not found in the file system, building it.")
        return build_domain_elements_pk_by_parameter_pk_lookup_table(domain_element)

def build_domain_element_by_pk_lookup_table(domain_element):
    print("build_domain_element_by_pk_lookup_table")
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

def load_domain_element_by_pk_lookup_table(domain_element):
    if "domain_element_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open ("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
            return json.load(f)
    else:
        print("domain_element_by_pk_lookup_table not found in the file system, building it.")
        return build_domain_element_by_pk_lookup_table(domain_element)

def build_value_by_domain_element_pk_lookup_table(values):
    print("build_value_by_domain_element_pk_lookup_table")
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

def load_value_by_domain_element_pk_lookup_table(values):
    if "value_by_domain_element_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/value_by_domain_element_pk_lookup_table.json", "r") as f:
            return json.load(f)
    else:
        print("build_value_by_domain_element_pk_lookup_table not found in the file system, building it.")
        return build_value_by_domain_element_pk_lookup_table(values)

def build_valueset_by_pk_lookup_table(valueset):
    print("build_valueset_by_pk_lookup_table")
    valueset_by_pk_lookup_table = {}
    for v in valueset:
        valueset_by_pk_lookup_table[v["pk"]] = v
    # store the lookup table in a file
    with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", "w") as f:
        json.dump(valueset_by_pk_lookup_table, f)
    return valueset_by_pk_lookup_table

def load_valueset_by_pk_lookup_table(valueset):
    if "valueset_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json", "r") as f:
            return json.load(f)
    else:
        print("valueset_by_pk_lookup_table not found in the file system, building it.")
        return build_valueset_by_pk_lookup_table(valueset)

def build_language_by_pk_lookup_table(language):
    print("build_language_by_pk_lookup_table")
    language_by_pk_lookup_table = {}
    for l in language:
        language_by_pk_lookup_table[l["pk"]] = l
    # store the lookup table in a file
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json", "w") as f:
        json.dump(language_by_pk_lookup_table, f)
    return language_by_pk_lookup_table

def load_language_by_pk_lookup_table(language):
    if "language_by_pk_lookup_table.json" in os.listdir("./external_data/wals_derived/"):
        with open("./external_data/wals_derived/language_by_pk_lookup_table.json", "r") as f:
            return json.load(f)
    else:
        print("language_by_pk_lookup_table not found in the file system, building it.")
        return build_language_by_pk_lookup_table(language)

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