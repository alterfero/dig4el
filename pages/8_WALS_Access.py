import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu
import os
import json
from streamlit_agraph import agraph, Node, Edge, Config

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


if "parameter_pk_by_name_lookup_table" not in st.session_state:
    st.session_state["parameter_pk_by_name_lookup_table"] = wu.load_parameter_pk_by_name_lookup_table()
    print("parameter_pk_by_name_lookup_table loaded")

if "value_by_domain_element_pk_lookup_table" not in st.session_state:
    st.session_state["value_by_domain_element_pk_lookup_table"] = wu.load_value_by_domain_element_pk_lookup_table()
    print("value_by_domain_element_pk_lookup_table loaded")

if "valueset_by_pk_lookup_table" not in st.session_state:
    st.session_state["valueset_by_pk_lookup_table"] = wu.load_valueset_by_pk_lookup_table()
    print("valueset_by_pk_lookup_table loaded")

if "language_by_pk_lookup_table" not in st.session_state:
    st.session_state["language_by_pk_lookup_table"] = wu.load_language_by_pk_lookup_table()
    print("language_by_pk_lookup_table loaded")

if "domain_elements_pk_by_parameter_pk_lookup_table" not in st.session_state:
    st.session_state["domain_elements_pk_by_parameter_pk_lookup_table"] = wu.build_domain_elements_pk_by_parameter_pk_lookup_table()
    print("domain_elements_pk_by_parameter_pk_lookup_table loaded")

if "domain_elements_by_pk_lookup_table" not in st.session_state:
    st.session_state["domain_elements_by_pk_lookup_table"] = wu.load_domain_element_by_pk_lookup_table()
    print("domain_elements_by_pk_lookup_table loaded")

if "language_info_by_id_lookup_table" not in st.session_state:
    st.session_state["language_info_by_id_lookup_table"] = wu.load_language_info_by_id_lookup_table()
    print("language_info_by_id_lookup_table loaded")

st.header("Exploration of WALS data")
with st.popover("Credits"):
    st.markdown("Dryer, Matthew S. & Haspelmath, Martin (eds.) 2013. The World Atlas of Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology. (Available online at https://wals.info)")
    st.markdown("Dataset version 2020.3, https://doi.org/10.5281/zenodo.7385533")
    st.markdown("Dataset under Creative Commons licence CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")

with st.expander("Language monography"):
    language_id_by_name = {}
    for language_id in st.session_state["language_info_by_id_lookup_table"].keys():
        language_info = st.session_state["language_info_by_id_lookup_table"][language_id]
        language_id_by_name[language_info["name"]] = language_id
    selected_language_name = st.selectbox("languages", list(language_id_by_name.keys()))
    selected_language_id = language_id_by_name[selected_language_name]
    # retrieving language_pk
    result_dict = wu.get_language_data_by_id(selected_language_id)
    st.write("{} parameters with a value for {}.".format(len(result_dict), selected_language_name))
    result_df = pd.DataFrame(result_dict).T
    st.dataframe(result_df)



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
    selected_subfamilies = colq.multiselect("language subfamilies", language_subfamilies)
    selected_genuses = colq.multiselect("language genuses", language_genuses)
    selected_macroareas = colq.multiselect("macroareas", language_macroareas)
    selected_language_names = colq.multiselect("languages", list(language_id_by_name.keys()))
    selected_param = colw.selectbox("Choose a parameter to observe", st.session_state["parameter_pk_by_name_lookup_table"].keys())
    if selected_families==[] and selected_subfamilies==[] and selected_macroareas==[] and len(selected_language_names)==1:
        colw.subheader("Language monography")
        language_id = language_id_by_name[selected_language_names[0]]
        colw.write("id: {}".format(language_id))
        language_info = st.session_state["language_info_by_id_lookup_table"][language_id]
        colw.write("Macro area: {}".format(language_info["macroarea"]))
        colw.write("Family: {}".format(language_info["family"]))
        colw.write("Subfamily: {}".format(language_info["subfamily"]))
        colw.write("Genus: {}".format(language_info["genus"]))

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

    param_pk = st.session_state["parameter_pk_by_name_lookup_table"][selected_param]
    selected_param_domain_element_pks = st.session_state["domain_elements_pk_by_parameter_pk_lookup_table"][param_pk]
    result_dict = {}
    # for each domain element, access all existing languages in the selected languages that match this value
    for de_pk in selected_param_domain_element_pks:
        if str(de_pk) in st.session_state["domain_elements_by_pk_lookup_table"]:
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
    if st.checkbox("List languages"):
        for v in result_dict:
            st.subheader(v)
            for l in result_dict[v]:
                info = st.session_state["language_info_by_id_lookup_table"][l]
                st.write("***{}***, family: {}, genus: {}, macroarea: {}".format(info["name"], info["family"], info["genus"], info["macroarea"]))


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
    st.bar_chart(selected_param_recap_df, y_label="values of the parameter", x_label="number of languages",
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












