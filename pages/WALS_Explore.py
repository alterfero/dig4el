import copy

import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu
import os
import json
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

wals_data_folder = "./external_data/wals-master/raw/"


# parameter.csv list parameters by pk and their names
#
# domainelement.csv lists all the existing values of these parameters, referencing parameter pk
#
# value.csv and valueset.csv tell what languages uses which value by referencing the value id, the language pk and the parameter pk
# They share the same pk.
#
# language.csv contains all the languages with their pk, id, name and location

def filter_differing_parameters(languages_data):
    languages_dict = {}
    for language in languages_data:
        languages_dict[language] = {}
        for index in languages_data[language]:
            item = languages_data[language][index]
            languages_dict[language][item["parameter"]] = item["value"]

    # Get the set of all parameters for all languages
    all_params_list = []
    for language in languages_dict.values():
        all_params_list += language.keys()
    all_params_set = set(all_params_list)

    # Find common parameters that are present in all languages
    common_params = copy.deepcopy(set(all_params_set))
    for language in languages_dict.values():
        common_params.intersection_update(language.keys())

    # Filter out parameters that have the same value across all languages
    differing_params = set()
    for param in common_params:
        try:
            values = set(params.get(param) for params in languages_dict.values())
            if len(values) > 1:  # If there are different values for this parameter
                differing_params.add(param)
        except:
            print("issue with param {}".format(param))

    # Filter languages' dictionaries to keep only differing parameters
    filtered_languages = {}
    for language, params in languages_dict.items():
        filtered_languages[language] = {param: value for param, value in params.items() if param in differing_params}

    diff_dict = {}
    for param in differing_params:
        diff_dict[param] = {}
        for l in filtered_languages.keys():
            diff_dict[param][l] = filtered_languages[l][param]

    return pd.DataFrame(diff_dict).T.sort_index()

#load the different WALS data and derived lookup tables
if "parameters" not in st.session_state:
    parameters = u.csv_to_dict(wals_data_folder + "parameter.csv")
    st.session_state["parameters"] = parameters
    #print("{} parameters: {}".format(len(parameters), parameters[10]))

if "value_by_domain_element_pk_lookup_table" not in st.session_state:
    st.session_state["value_by_domain_element_pk_lookup_table"] = wu.load_value_by_domain_element_pk_lookup_table()
if "valueset_by_pk_lookup_table" not in st.session_state:
    st.session_state["valueset_by_pk_lookup_table"] = wu.load_valueset_by_pk_lookup_table()
if "language_by_pk_lookup_table" not in st.session_state:
    st.session_state["language_by_pk_lookup_table"] = wu.load_language_by_pk_lookup_table()
if "domain_elements_pk_by_parameter_pk_lookup_table" not in st.session_state:
    st.session_state["domain_elements_pk_by_parameter_pk_lookup_table"] = wu.domain_elements_pk_by_parameter_pk
if "domain_elements_by_pk_lookup_table" not in st.session_state:
    st.session_state["domain_elements_by_pk_lookup_table"] = wu.load_domain_element_by_pk_lookup_table()
if "language_info_by_id_lookup_table" not in st.session_state:
    st.session_state["language_info_by_id_lookup_table"] = wu.load_language_info_by_id_lookup_table()

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")
    st.page_link("pages/Grammatical_Description.py", label="Generate Grammars", icon=":material/menu_book:")

    st.write("**Expert features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")
    st.page_link("pages/Concept_graph_editor.py", label="Edit Concept Graph", icon=":material/device_hub:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.header("Exploration of WALS data")
with st.popover("Credits"):
    st.markdown("Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology. (Available online at https://wals.info)")
    st.markdown("Dataset version 2020.3, https://doi.org/10.5281/zenodo.7385533")
    st.markdown("Dataset under Creative Commons licence CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")

with st.expander("Language monography"):
    with st.popover("i"):
        st.markdown("Select a language to see information available about it in WALS.")
    language_id_by_name = {}
    for language_id in st.session_state["language_info_by_id_lookup_table"].keys():
        language_info = st.session_state["language_info_by_id_lookup_table"][language_id]
        language_id_by_name[language_info["name"]] = language_id
    selected_language_name = st.selectbox("languages", list(language_id_by_name.keys()))
    selected_language_id = language_id_by_name[selected_language_name]

    st.write("id: {}".format(selected_language_id))
    language_info = st.session_state["language_info_by_id_lookup_table"][selected_language_id]
    st.write("Macro area: {}".format(language_info["macroarea"]))
    st.write("Family: {}".format(language_info["family"]))
    st.write("Subfamily: {}".format(language_info["subfamily"]))
    st.write("Genus: {}".format(language_info["genus"]))

    # retrieving language_pk
    result_dict = wu.get_wals_language_data_by_id_or_name(selected_language_id)
    st.write("{} parameters with a value for {}.".format(len(result_dict), selected_language_name))
    result_df = pd.DataFrame(result_dict).T
    st.dataframe(result_df)

with st.expander("Language Diff"):
    with st.popover("i"):
        st.markdown("See differences between two languages")
    language_id_by_name = {}
    for language_id in st.session_state["language_info_by_id_lookup_table"].keys():
        language_info = st.session_state["language_info_by_id_lookup_table"][language_id]
        language_id_by_name[language_info["name"]] = language_id
    selected_languages_name = st.multiselect("languages", list(language_id_by_name.keys()), key="sln")
    #selected_language_id = language_id_by_name[selected_language_name]
    selected_languages_id = [language_id_by_name[ln] for ln in selected_languages_name]

    st.write("ids: {}".format(" ,".join(selected_languages_id)))

    languages_dict = {}
    for lid in selected_languages_id:
        languages_dict[lid] = wu.get_wals_language_data_by_id_or_name(lid)
    #st.write(languages_dict)
    filtered_languages_dict = filter_differing_parameters(languages_dict)
    st.dataframe(filtered_languages_dict, use_container_width=True)


with st.expander("Exploration by language and parameter"):
    with st.popover("i"):
        st.markdown("Select a group of languages (manually or by filtering by criteria) and a parameter to see how the values of this parameter are distributed across the selected languages. ")
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
    colq.markdown("**Select one or multiple languages**")
    selected_families = colq.multiselect("language families", language_families)
    selected_subfamilies = colq.multiselect("language subfamilies", language_subfamilies)
    selected_genuses = colq.multiselect("language genuses", language_genuses)
    selected_macroareas = colq.multiselect("macroareas", language_macroareas)
    selected_language_names = colq.multiselect("languages", list(language_id_by_name.keys()))
    colw.markdown("**Select the parameter to observe across these languages.**")
    selected_param = colw.selectbox("Choose a parameter to observe", wu.parameter_pk_by_name.keys())

    selected_language_ids = []
    for language_name in selected_language_names:
        selected_language_ids.append(language_id_by_name[language_name])
    for k in st.session_state["language_info_by_id_lookup_table"]:
        v = st.session_state["language_info_by_id_lookup_table"][k]
        if v["family"] in selected_families:
            if k not in selected_language_ids:
                selected_language_ids.append(k)
        if v["subfamily"] in selected_subfamilies:
            if k not in selected_language_ids:
                selected_language_ids.append(k)
        if v["genus"] in selected_genuses:
            if k not in selected_language_ids:
                selected_language_ids.append(k)
        if v["macroarea"] in selected_macroareas:
            if k not in selected_language_ids:
                selected_language_ids.append(k)
    st.write("{} languages selected".format(len(selected_language_ids)))
    current_languages = []
    for l in selected_language_ids:
        current_languages.append(st.session_state["language_info_by_id_lookup_table"][l]["name"])

    param_pk = str(wu.parameter_pk_by_name[selected_param])
    selected_param_domain_element_pks = wu.domain_elements_pk_by_parameter_pk[param_pk]
    result_dict = {}
    # for each domain element, access all existing languages in the selected languages that match this value
    for de_pk in selected_param_domain_element_pks:
        if str(de_pk) in wu.domain_element_by_pk:
            de_name = st.session_state["domain_elements_by_pk_lookup_table"][str(de_pk)]["name"]
            result_dict[de_name] = []
            values_pk = [v["pk"] for v in st.session_state["value_by_domain_element_pk_lookup_table"][str(de_pk)]]
            for value_pk in values_pk:
                language_pk = st.session_state["valueset_by_pk_lookup_table"][str(value_pk)]["language_pk"]
                language_id = st.session_state["language_by_pk_lookup_table"][str(language_pk)]["id"]
                if language_id in selected_language_ids:
                    result_dict[de_name].append(language_id)
        else:
            print("no {} in domain_elements_by_pk_lookup_table".format(de_pk))
    stats_dict = {}
    for k in result_dict.keys():
        stats_dict[k] = len(result_dict[k])

    if len(result_dict) != 0:
        nodes = []
        edges = []
        #print(selected_param)
        nodes.append(Node(id=selected_param,
                          label=selected_param,
                          size=50,
                          color="brown",
                          title=selected_param,
                          symbolType="circle"))
        for v in result_dict:
            #print(v)
            nodes.append(Node(id=v,
                              label=v,
                              size=30,
                              color="green",
                              title=v,
                              symbolType="circle"))
            edges.append(Edge(source=selected_param,
                              physics=True,
                              target=v,
                              type="SMOOTH",
                              color="brown"))
            c = 0
            for l in result_dict[v]:
                c += 1
                if c<300:
                    nodes.append(Node(id=l,
                                      label=st.session_state["language_info_by_id_lookup_table"][l]["name"],
                                      size=15,
                                      color="blue",
                                      title=l,
                                      symbolType="circle"))
                    edges.append(Edge(source=v,
                                      physics=True,
                                      target=l,
                                      type="SMOOTH",
                                      color="brown"))
        # ---- graph
        config = Config(width=800,
                        height=600,
                        directed=True,
                        physics=True,
                        dashed=True,
                        hierarchical=False,
                        nodeHighlightBehavior=True,
                        highlightColor="#F7A7A6",  # or "blue"
                        collapsible=True,
                        automaticRearrangeAfterDropNode=False,
                        node={'labelProperty': 'label'},
                        link={'labelProperty': 'label', 'renderLabel': True}
                        # **kwargs e.g. node_size=1000 or node_color="blue"
                        )
        return_value = agraph(nodes=nodes,
                              edges=edges,
                              config=config)

    stats_df = pd.DataFrame(stats_dict, index=["number of languages"]).T
    st.bar_chart(stats_df, y_label="values of the parameter", x_label="number of languages",
                 horizontal=True)
    st.dataframe(stats_df)
    if st.checkbox("List languages"):
        for v in result_dict:
            st.subheader(v)
            for l in result_dict[v]:
                info = st.session_state["language_info_by_id_lookup_table"][l]
                st.write("***{}***, family: {}, genus: {}, macroarea: {}".format(info["name"], info["family"], info["genus"], info["macroarea"]))


with st.expander("Exploration by parameter and value"):
    with st.popover("i"):
        st.markdown("Select a parameter to see its distribution across all languages. Selecting a value of this parameter lists all the languages using this value.")
    #for parameter in parameters:
    params_dict = {}
    for param in st.session_state["parameters"]:
        param_values = []
        #browse values for that parameter
        for domain_element_pk in wu.domain_elements_pk_by_parameter_pk[str(param["pk"])]:
            if str(domain_element_pk) in wu.domain_element_by_pk:
                domain_element = wu.domain_element_by_pk[str(domain_element_pk)]
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

    selected_param = st.selectbox("Choose a parameter", wu.parameter_pk_by_name.keys())
    selected_param_pk = wu.parameter_pk_by_name[selected_param]
    selected_param_recap_dict = {}
    selected_param_proba_distribution = {}
    total_languages = 0
    for value in params_dict[int(selected_param_pk)]["param_values"]:
        total_languages += len(value["languages"])
        selected_param_recap_dict[value["name"]] = len(value["languages"])
    for value in selected_param_recap_dict:
        selected_param_proba_distribution[value] = selected_param_recap_dict[value] / total_languages
    selected_param_recap_df = pd.DataFrame.from_dict(selected_param_recap_dict, orient="index", columns=["value"])
    #st.dataframe(selected_param_recap_df)
    st.bar_chart(selected_param_recap_df, y_label="values of the parameter", x_label="number of languages",
                 horizontal=True)
    st.write("Probability distribution computed on {} languages:".format(total_languages))
    st.write(selected_param_proba_distribution)
    #st.write(params_dict[selected_param_pk]["param_values"])
    selected_value = st.selectbox("Choose a value", selected_param_recap_dict.keys())
    selected_language_dict = {}
    for value in params_dict[int(selected_param_pk)]["param_values"]:
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










