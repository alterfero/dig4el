import streamlit as st
import json
import pandas as pd

# cpt is a dataframe that contains all conditional probabilities between domain_elements (values of parameters).

if "cpt" not in st.session_state:
    st.session_state["cpt"] =  pd.read_json("./external_data/wals_derived/de_conditional_probability_df.json")
if "current_cpt" not in st.session_state:
    st.session_state["current_cpt"] = st.session_state["cpt"]
if "parameter_pk_by_name_filtered" not in st.session_state:
    with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
        st.session_state["parameter_pk_by_name_filtered"] = json.load(f)
if "parameter_pk_by_name" not in st.session_state:
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
        st.session_state["parameter_pk_by_name"] = json.load(f)
if "domain_elements_pk_by_parameter_pk" not in st.session_state:
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        st.session_state["domain_elements_pk_by_parameter_pk"] = json.load(f)
if "parameter_pk_by_domain_element_pk" not in st.session_state:
    parameter_pk_by_domain_element_pk = {}
    for param_pk in st.session_state["domain_elements_pk_by_parameter_pk"]:
        for depk in st.session_state["domain_elements_pk_by_parameter_pk"][param_pk]:
            parameter_pk_by_domain_element_pk[str(depk)] = str(param_pk)
if "domain_element_by_pk" not in st.session_state:
    with open("./external_data/wals_derived/domain_element_by_pk_lookup_table.json") as f:
        st.session_state["domain_element_by_pk"] = json.load(f)
if "parameter_name_by_pk" not in st.session_state:
    tmp = {}
    for name in st.session_state["parameter_pk_by_name"]:
        tmp[str(st.session_state["parameter_pk_by_name"][name])] = name
    st.session_state["parameter_name_by_pk"] = tmp
if "parameter_pk_by_domain_element_pk" not in st.session_state:
    tmp = {}
    for ppk in st.session_state["domain_elements_pk_by_parameter_pk"].keys():
        for depk in st.session_state["domain_elements_pk_by_parameter_pk"][str(ppk)]:
         tmp[str(depk)] = str(ppk)
    st.session_state["parameter_pk_by_domain_element_pk"] = tmp
if "obs" not in st.session_state:
    st.session_state["obs"] = []
if "obs_de_pk_list" not in st.session_state:
    st.session_state["obs_de_pk_list"] = []

parameter_name_list_filtered = list(st.session_state["parameter_pk_by_name_filtered"].keys())

with st.expander("Explore conditional probabilities associated with the values of a parameter"):
    st.write("These conditional probabilities are computed on all languages, from WALS data.")
    selected_param = st.selectbox("Choose a parameter",parameter_name_list_filtered)
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
        if str(k) in st.session_state["parameter_pk_by_domain_element_pk"].keys():
            pm_pk = st.session_state["parameter_pk_by_domain_element_pk"][str(k)]
            if str(pm_pk) in st.session_state["parameter_name_by_pk"].keys():
                pm_name = str(st.session_state["parameter_name_by_pk"][str(pm_pk)])
            else:
                pm_name = "param name unknown"
        else:
            pm_name = "param pk unknown"
        if str(st.session_state["domain_element_by_pk"][str(k)]["name"]) != "nan":
            new_label = pm_name + ": " + str(st.session_state["domain_element_by_pk"][str(k)]["name"])
        elif str(st.session_state["domain_element_by_pk"][str(k)]["description"]) != "nan":
            new_label = pm_name + ": " + str(st.session_state["domain_element_by_pk"][str(k)]["description"])
        else:
            new_label = pm_name + ": " + "pk " + str(k)
        new_column_labels[k] = new_label

    # Rename columns
    selected_cpt = selected_cpt.rename(columns=new_column_labels)

    # Rename indexes (rows)
    selected_cpt = selected_cpt.rename(index=new_row_labels)

    st.dataframe(selected_cpt.T, use_container_width=True)

    with st.popover("info"):
        st.write("Columns are the values of the chosen parameter.")
        st.write("Rows are the values from other parameters that are the most conditioned by the occurrence of the value of the chosen parameter. When there is no name for the value, the identifier is used")

st.write("Explore conditional probabilities deriving from a combination of observations")
st.write("Enter up to 5 grammatical observations made on a language below to see a list of the most probable values associated with these observations")

if st.button("Reset observations"):
    st.session_state["obs"] = []
    st.session_state["obs_de_pk_list"] = []
    st.session_state["current_cpt"] = st.session_state["cpt"]
if len(st.session_state["obs"]) < 6:
    new_pm_obs = st.selectbox("parameter "+str(len(st.session_state["obs"]) + 1), parameter_name_list_filtered, key="obs_pm"+str(len(st.session_state["obs"])))
    obs_pm_pk = st.session_state["parameter_pk_by_name"][str(new_pm_obs)]
    avail_values_pk = st.session_state["domain_elements_pk_by_parameter_pk"][str(obs_pm_pk)]
    avail_values_names = []
    for pk in avail_values_pk:
        avail_values_names.append(st.session_state["domain_element_by_pk"][str(pk)]["name"])
    obs_de_name = st.selectbox("select the observed value of that paramater", avail_values_names, key="obs_value"+str(len(st.session_state["obs"])))
    obs_de_index = avail_values_names.index(obs_de_name)
    obs_de_pk = avail_values_pk[obs_de_index]
    if st.button("add observation"):
        st.session_state["obs"].append({"param_pk":obs_pm_pk, "de_pk":obs_de_pk, "param_name":new_pm_obs, "de_name":obs_de_name})
        st.session_state["obs_de_pk_list"].append(obs_de_pk)
        st.session_state["current_cpt"] = st.session_state["cpt"]
if st.session_state["obs"] != []:
    obsc = 0
    st.write("Current observations:")
    for item in st.session_state["obs"]:
        obsc += 1
        st.write("{}. {}: {}".format(obsc, item["param_name"], item["de_name"]))

    # transform the cpt table to compute the joint conditional probability

    #remove columns that correspond to observed events
    st.session_state["current_cpt"] = st.session_state["cpt"].drop(columns=st.session_state["obs_de_pk_list"])

    # Sum the probabilities for the observed events
    prob_sum_df = st.session_state["current_cpt"].loc[st.session_state["obs_de_pk_list"]].sum()
    # Normalize the summed probabilities
    normalized_prob_df = prob_sum_df / prob_sum_df.sum()


    #renaming rows
    new_i_label = {}
    for k in normalized_prob_df.index:
        if str(k) in st.session_state["parameter_pk_by_domain_element_pk"].keys():
            pm_pk = st.session_state["parameter_pk_by_domain_element_pk"][str(k)]
            if str(pm_pk) in st.session_state["parameter_name_by_pk"].keys():
                pm_name = str(st.session_state["parameter_name_by_pk"][str(pm_pk)])
            else:
                pm_name = "param name unknown"
        else:
            pm_name = "param pk unknown"
        if str(st.session_state["domain_element_by_pk"][str(k)]["name"]) != "nan":
            new_label = pm_name + ": " + str(st.session_state["domain_element_by_pk"][str(k)]["name"])
        elif str(st.session_state["domain_element_by_pk"][str(k)]["description"]) != "nan":
            new_label = pm_name + ": " + str(st.session_state["domain_element_by_pk"][str(k)]["description"])
        else:
            new_label = pm_name + ": " + "pk " + str(k)
        new_i_label[k] = new_label


    normalized_prob_df = normalized_prob_df.rename(index=new_i_label)

    colq, colw = st.columns(2)
    percentile = colq.slider("probability percentile threshold", min_value=0.0, max_value=1.0, step=0.01, value=0.9)
    percentile_threshold = normalized_prob_df.quantile(percentile)
    colw.write("Probability threshold of percentile {}: {}".format(percentile, round(percentile_threshold,5)))

    normalized_prob_df = normalized_prob_df[normalized_prob_df >= percentile_threshold]

    normalized_prob_df = normalized_prob_df.sort_values(ascending=False)[:100]

    st.dataframe(normalized_prob_df, use_container_width=True)



