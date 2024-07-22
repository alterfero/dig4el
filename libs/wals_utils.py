import os
import json
from libs import utils as u

# parameter.csv list parameters by pk and their names
#
# domainelement.csv lists all the existing values of these parameters, referencing parameter pk
#
# value.csv and valueset.csv tell what languages uses which value by referencing the value id, the language pk and the parameter pk
# They share the same pk.
#
# language.csv contains all the languages with their pk, id, name and location

def get_language_data_by_id(language_id):
    with open("./external_data/wals_derived/language_by_pk_lookup_table.json") as f:
        language_by_pk_lookup_table = json.load(f)
    with open("./external_data/wals_derived/valueset_by_pk_lookup_table.json") as f:
        valueset_by_pk_lookup_table = json.load(f)
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
        domainelement_by_pk_lookup_table = json.load(f)
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
        parameter_pk_by_name = json.load(f)
    values = u.csv_to_dict("./external_data/wals-master/raw/value.csv")
    for pk in language_by_pk_lookup_table.keys():
        if language_by_pk_lookup_table[pk]["id"] == language_id:
            selected_language_pk = pk
            print("selected language pk: {}".format(selected_language_pk))
            break
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
                print("no match for parameter pk {}".format(parameter_pk))
                parameter_name = None
        domainelement_name = domainelement_by_pk_lookup_table[str(item["domainelement_pk"])]["name"]
        result_dict[parameter_pk] = {
            "parameter": parameter_name,
            "value": domainelement_name,
            "domainelement_pk": item["domainelement_pk"],
            "valueset_pk": item["valueset_pk"]
        }

    return result_dict



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