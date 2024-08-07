import streamlit as st
import json
import pandas as pd

# cpt is a dataframe that contains all conditional probabilities between domain_elements (values of parameters).

if "cpt" not in st.session_state:
    st.session_state["cpt"] =  pd.read_json("./external_data/wals_derived/de_conditional_probability_df.json")
if "parameter_pk_by_name" not in st.session_state:
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
        st.session_state["parameter_pk_by_name"] = json.load(f)
if "domain_elements_pk_by_parameter_pk" not in st.session_state:
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        st.session_state["domain_elements_pk_by_parameter_pk"] = json.load(f)
if "domain_element_by_pk" not in st.session_state:
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
        st.session_state["domain_element_by_pk"] = json.load(f)
if "parameter_name_by_pk" not in st.session_state:
    tmp = {}
    for name in st.session_state["parameter_pk_by_name"]:
        tmp[st.session_state["parameter_pk_by_name"][name]] = name
        st.session_state["parameter_name_by_pk"] = tmp

parameter_name_list = list(st.session_state["parameter_pk_by_name"].keys())

with st.expander("Conditional probabilities associated with the values of a parameter"):
    st.write("These conditional probabilities are computed on all languages, from WALS data.")
    selected_param = st.selectbox("Choose a parameter",parameter_name_list)
    selected_param_pk = st.session_state["parameter_pk_by_name"][selected_param]
    selected_param_de = st.session_state["domain_elements_pk_by_parameter_pk"][str(selected_param_pk)]
    selected_param_de.sort()

    selected_cpt = st.session_state["cpt"].loc[selected_param_de].sort_index()

    threshold = st.slider("conditional probability threshold", min_value=0.5, max_value=1.0, step=0.05, value=0.7)
    # put to zero all values below the threshold
    selected_cpt[selected_cpt < threshold] = 0
    # remove columns with only zeroes.
    selected_cpt = selected_cpt.loc[:, (selected_cpt != 0).any(axis=0)]
    #Remove columns with the same names as the row indexes
    selected_cpt = selected_cpt.drop(columns=[col for col in selected_cpt.columns if col in selected_cpt.index])

    #create dictionaries to rename rows and columns:
    new_row_labels = {}
    for i in selected_cpt.index:
        if str(st.session_state["domain_element_by_pk"][str(i)]["name"]) != "nan":
            new_row_labels[i] = st.session_state["domain_element_by_pk"][str(i)]["name"]
        else:
            new_row_labels[i] = "pk " + str(i)

    new_column_labels = {}
    for k in selected_cpt.columns:
        if str(st.session_state["domain_element_by_pk"][str(k)]["name"]) != "nan":
            new_label = str(st.session_state["domain_element_by_pk"][str(k)]["name"])
        elif str(st.session_state["domain_element_by_pk"][str(k)]["description"]) != "nan":
            new_label = str(st.session_state["domain_element_by_pk"][str(k)]["description"])
        else:
            new_label = "pk " + str(k)
        new_column_labels[k] = new_label

    # Rename columns
    selected_cpt = selected_cpt.rename(columns=new_column_labels)

    # Rename indexes (rows)
    selected_cpt = selected_cpt.rename(index=new_row_labels)

    st.dataframe(selected_cpt)

    with st.popover("info"):
        st.write("Rows are the values of the chosen parameter.")
        st.write("Columns are the values from other parameters that are the most conditioned by the occurrence of the value of the chosen parameter. When there is no name for the value, the identifier is used")




