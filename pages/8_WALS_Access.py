import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu
import os
import json

wals_data_folder = "./external_data/wals-master/raw/"


# parameter.csv list parameters by pk and their names
#
# domainelement.csv lists all the existing values of these parameters, referencing parameter pk
#
# value.csv and valueset.csv tell what languages uses which value by referencing the value id, the language pk and the parameter pk
# They share the same pk.
#
# language.csv contains all the languages with their pk, id, name and location


#load the different WALS data and derived lookup tables
if "parameters" not in st.session_state:
    parameters = u.csv_to_dict(wals_data_folder + "parameter.csv")
    st.session_state["parameters"] = parameters
    print("{} parameters: {}".format(len(parameters), parameters[10]))

if "domainelement" not in st.session_state:
    domainelement = u.csv_to_dict(wals_data_folder + "domainelement.csv")
    st.session_state["domainelement"] = domainelement
    print("{} domainelement: {}".format(len(domainelement), domainelement[10]))

if "values" not in st.session_state:
    values = u.csv_to_dict(wals_data_folder + "value.csv")
    st.session_state["values"] = values
    print("{} values: {}".format(len(values), values[10]))

if "valueset" not in st.session_state:
    valueset = u.csv_to_dict(wals_data_folder + "valueset.csv")
    st.session_state["valueset"] = valueset
    print("{} valueset: {}".format(len(valueset), valueset[10]))

if "languages" not in st.session_state:
    languages = u.csv_to_dict(wals_data_folder + "language.csv")
    st.session_state["languages"] = languages
    print("{} languages: {}".format(len(languages), languages[10]))

if "parameter_pk_by_name_lookup_table" not in st.session_state:
    st.session_state["parameter_pk_by_name_lookup_table"] = wu.load_parameter_pk_by_name_lookup_table()
    print("parameter_pk_by_name_lookup_table loaded")

if "value_by_domain_element_pk_lookup_table" not in st.session_state:
    st.session_state["value_by_domain_element_pk_lookup_table"] = wu.load_value_by_domain_element_pk_lookup_table(st.session_state["values"])
    print("value_by_domain_element_pk_lookup_table loaded")

if "valueset_by_pk_lookup_table" not in st.session_state:
    st.session_state["valueset_by_pk_lookup_table"] = wu.load_valueset_by_pk_lookup_table(st.session_state["valueset"])
    print("valueset_by_pk_lookup_table loaded")

if "language_by_pk_lookup_table" not in st.session_state:
    st.session_state["language_by_pk_lookup_table"] = wu.load_language_by_pk_lookup_table(st.session_state["languages"])
    print("language_by_pk_lookup_table loaded")

if "domain_elements_pk_by_parameter_pk_lookup_table" not in st.session_state:
    st.session_state["domain_elements_pk_by_parameter_pk_lookup_table"] = wu.build_domain_elements_pk_by_parameter_pk_lookup_table(st.session_state["domainelement"])
    print("domain_elements_pk_by_parameter_pk_lookup_table loaded")

if "domain_elements_by_pk_lookup_table" not in st.session_state:
    st.session_state["domain_elements_by_pk_lookup_table"] = wu.load_domain_element_by_pk_lookup_table(st.session_state["domainelement"])
    print("domain_elements_by_pk_lookup_table loaded")

if "language_info_by_id_lookup_table" not in st.session_state:
    st.session_state["language_info_by_id_lookup_table"] = wu.load_language_info_by_id_lookup_table()
    print("language_info_by_id_lookup_table loaded")

st.header("Exploration of WALS data")
with st.popover("Credits"):
    st.markdown("Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology. (Available online at https://wals.info)")
    st.markdown("Dataset version 2020.3, https://doi.org/10.5281/zenodo.7385533")
    st.markdown("Dataset under Creative Commons licence CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")

with st.expander("Exploration by language and parameter"):
    language_id_by_name = {}
    language_macroareas = []
    language_families = []
    language_subfamilies = []
    language_genuses = []

    for language_id in st.session_state["language_info_by_id_lookup_table"].keys():
        language_info = st.session_state["language_info_by_id_lookup_table"][language_id]
        language_id_by_name[language_info["name"]] = language_id
        if language_info["macroarea"] not in language_macroareas:
            language_macroareas.append(language_info["macroarea"])
        if language_info["family"] not in language_families:
            language_families.append(language_info["family"])
        if language_info["subfamily"] not in language_subfamilies:
            language_subfamilies.append(language_info["subfamily"])
        if language_info["genus"] not in language_genuses:
            language_genuses.append(language_info["genus"])

    colq, colw = st.columns(2)
    selected_families = colq.multiselect("language families", language_families)
    selected_macroareas = colq.multiselect("macroareas", language_macroareas)
    selected_language_names = colq.multiselect("languages", list(language_id_by_name.keys()))
    selected_param = colw.selectbox("Choose a parameter to observe", st.session_state["parameter_pk_by_name_lookup_table"].keys())

    selected_language_ids = []
    for language_name in selected_language_names:
        selected_language_ids.append(language_id_by_name[language_name])
    for k in st.session_state["language_info_by_id_lookup_table"]:
        v = st.session_state["language_info_by_id_lookup_table"][k]
        if v["family"] in selected_families:
            if k not in selected_language_ids:
                selected_language_ids.append(k)
        if v["macroarea"] in selected_macroareas:
            if k not in selected_language_ids:
                selected_language_ids.append(k)
    st.write("{} languages selected".format(len(selected_language_ids)))

    param_pk = st.session_state["parameter_pk_by_name_lookup_table"][selected_param]
    selected_param_domain_element_pks = st.session_state["domain_elements_pk_by_parameter_pk_lookup_table"][param_pk]
    result_dict = {}
    # for each domain element, access all existing languages in the selected languages that match this value
    for de_pk in selected_param_domain_element_pks:
        de_name = st.session_state["domain_elements_by_pk_lookup_table"][str(de_pk)]["name"]
        result_dict[de_name] = []
        values_pk = [v["pk"] for v in st.session_state["value_by_domain_element_pk_lookup_table"][str(de_pk)]]
        for value_pk in values_pk:
            language_pk = st.session_state["valueset_by_pk_lookup_table"][str(value_pk)]["language_pk"]
            language_id = st.session_state["language_by_pk_lookup_table"][str(language_pk)]["id"]
            print(language_pk, language_id)
            if language_id in selected_language_ids:
                result_dict[de_name].append(language_id)
    stats_dict = {}
    for k in result_dict.keys():
        stats_dict[k] = len(result_dict[k])
    stats_df = pd.DataFrame(stats_dict, index=["number of languages"]).T
    st.bar_chart(stats_df, x_label="values of the parameter", y_label="number of languages",
                 horizontal=True)

with st.expander("Exploration by parameter and value"):
    #for parameter in parameters:
    params_dict = {}
    for param in st.session_state["parameters"]:
        param_values = []
        #browse values for that parameter
        for domain_element_pk in st.session_state["domain_elements_pk_by_parameter_pk_lookup_table"][param["pk"]]:
            if str(domain_element_pk) in st.session_state["domain_elements_by_pk_lookup_table"]:
                domain_element = st.session_state["domain_elements_by_pk_lookup_table"][str(domain_element_pk)]
                corresponding_value_pks = []
                if str(domain_element_pk) in st.session_state["value_by_domain_element_pk_lookup_table"]:
                    for valueset in st.session_state["value_by_domain_element_pk_lookup_table"][str(domain_element_pk)]:
                        corresponding_value_pks.append(valueset["pk"])
                    languages = []
                    for valueset_pk in corresponding_value_pks:
                        valueset = st.session_state["valueset_by_pk_lookup_table"][str(valueset_pk)]
                        language = st.session_state["language_by_pk_lookup_table"][str(valueset["language_pk"])]
                        languages.append({
                            "valueset_pk": valueset_pk,
                            "language_pk": valueset["language_pk"],
                            "language_id": language["id"],
                            "language_name": language["name"],
                        })
                    param_values.append({
                        "name":domain_element["name"],
                        "domain_element_pk": domain_element_pk,
                        "languages": languages
                    })
                else:
                    print("domain_element_pk {} not in  domain_elements_pk_by_parameter_pk_lookup_table".format(
                        domain_element_pk))
            else:
                print("domain_element_pk {} not in  domain_elements_by_pk_lookup_table".format(
                    domain_element_pk))
        params_dict[param["pk"]] = {"name": param["name"], "param_values": param_values}

    selected_param = st.selectbox("Choose a parameter", st.session_state["parameter_pk_by_name_lookup_table"].keys())
    selected_param_pk = st.session_state["parameter_pk_by_name_lookup_table"][selected_param]
    selected_param_recap_dict = {}
    for value in params_dict[selected_param_pk]["param_values"]:
        selected_param_recap_dict[value["name"]] = len(value["languages"])
    selected_param_recap_df = pd.DataFrame.from_dict(selected_param_recap_dict, orient="index", columns=["value"])
    #st.dataframe(selected_param_recap_df)
    st.bar_chart(selected_param_recap_df, x_label="values of the parameter", y_label="number of languages",
                 horizontal=True)
    #st.write(params_dict[selected_param_pk]["param_values"])
    selected_value = st.selectbox("Choose a value", selected_param_recap_dict.keys())
    selected_language_dict = {}
    for value in params_dict[selected_param_pk]["param_values"]:
        if value["name"] == selected_value:
            for item in value["languages"]:
                language_id = item["language_id"]
                language_info = st.session_state["language_info_by_id_lookup_table"][language_id]
                selected_language_dict[language_id] = {
                    "name": language_info["name"],
                    "macro_area": language_info["macroarea"],
                    "family": language_info["family"],
                    "subfamily": language_info["subfamily"],
                    "genus": language_info["genus"]
                }
    languages_df = pd.DataFrame.from_dict(selected_language_dict).T
    st.dataframe(languages_df)

















