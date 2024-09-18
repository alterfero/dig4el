import streamlit as st
import json
import pandas as pd
from libs import wals_utils as wu, prob_utils as pu
from streamlit_agraph import agraph, Node, Edge, Config
from pyvis.network import Network

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# cpt is a dataframe that contains all conditional probabilities between domain_elements (values of parameters).

if "cpt" not in st.session_state:
    st.session_state["cpt"] =  pd.read_json("./external_data/wals_derived/de_conditional_probability_df.json")
if "current_cpt" not in st.session_state:
    st.session_state["current_cpt"] = st.session_state["cpt"]
if "parameter_pk_by_name_filtered" not in st.session_state:
    with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
        st.session_state["parameter_pk_by_name_filtered"] = json.load(f)
if "param_de_tree" not in st.session_state:
    with open("./external_data/wals_derived/param_de_tree.json") as f:
        st.session_state["param_de_tree"] = json.load(f)
if "parameter_pk_by_name" not in st.session_state:
    with open("./external_data/wals_derived/parameter_pk_by_name_lookup_table.json") as f:
        st.session_state["parameter_pk_by_name"] = json.load(f)
if "domain_elements_pk_by_parameter_pk" not in st.session_state:
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        st.session_state["domain_elements_pk_by_parameter_pk"] = json.load(f)
if "parameter_pk_by_domain_element_pk" not in st.session_state:
    st.session_state["parameter_pk_by_domain_element_pk"] = {}
    for param_pk in st.session_state["domain_elements_pk_by_parameter_pk"]:
        for depk in st.session_state["domain_elements_pk_by_parameter_pk"][param_pk]:
            st.session_state["parameter_pk_by_domain_element_pk"][str(depk)] = str(param_pk)

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
if "pk1_pk2_list" not in st.session_state:
    st.session_state["pk1_pk2_list"] = []
if "selected_values" not in st.session_state:
    st.session_state["selected_values"] = []
if "inference_graph" not in st.session_state:
    st.session_state["inference_graph"] = {}
if "beliefs" not in st.session_state:
    st.session_state["beliefs"] = {}

de_blacklist = [
		1094,
		1095,
		1096,
		1097
	]

parameter_name_list_filtered = list(st.session_state["parameter_pk_by_name_filtered"].keys())

# param blacklist to , to be automated and put in an external  file.
param_pk_blacklist = ["180"]
de_pk_blacklist = []
for ppk in param_pk_blacklist:
    for depk in st.session_state["domain_elements_pk_by_parameter_pk"][ppk]:
        de_pk_blacklist.append(depk)

with st.sidebar:
    st.subheader("DIG4EL")
    st.page_link("home.py", label="Home", icon=":material/home:")

    st.write("**Base Features**")
    st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

    st.write("**Advanced features**")
    st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

    st.write("**Explore DIG4EL processes**")
    st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

st.subheader("Conditional probabilities between parameters.")

with (st.expander("Explore chains of conditional probabilities associated with a set of values")):
    with st.popover("i"):
        st.markdown("Select parameters and their observed values along with a probability threshold to get all the other values associated "
                    "with this selection through conditional probabilities. ")

    # let user select a collection of values of parameters
    thr = st.slider("conditional probability threshold", 0.3, 1.0, value=0.6, step=0.01)
    if st.button("Reset"):
        st.session_state["selected_values"] = []
        st.session_state["inference_graph"] = {}
    st.write("Add known value(s) observed in a language")
    selected_param_name = st.selectbox("Select a parameter", st.session_state["parameter_pk_by_name_filtered"], key="sp"+str(len(st.session_state["selected_values"])))
    selected_param_pk = st.session_state["parameter_pk_by_name_filtered"][selected_param_name]
    available_de_pks = st.session_state["domain_elements_pk_by_parameter_pk"][str(selected_param_pk)]
    available_de_names = [wu.get_careful_name_of_de_pk(depk) for depk in available_de_pks]
    selected_value = st.selectbox("Choose a value", available_de_names)
    if st.button("Add"):
        if available_de_pks[available_de_names.index(selected_value)] not in st.session_state["selected_values"]:
            st.session_state["selected_values"].append(available_de_pks[available_de_names.index(selected_value)])
    st.write("Currently selected value(s): **{}**".format(", ".join([wu.get_careful_name_of_de_pk(depk) for depk in st.session_state["selected_values"]])))
    if st.button("Show the belief propagation graph based on conditional propabilities with threshold {}".format(thr)):
        st.session_state["inference_graph"], st.session_state["beliefs"] = pu.inference_graph_from_cpt_with_belief_propagation(st.session_state["cpt"],
                                                                              st.session_state["selected_values"],
                                                                              thr)


    # GRAPH with agraph
    def graph_with_agraph(beliefs, inference_graph):
        if len(st.session_state["inference_graph"].keys()) > 0:
            nodes = []
            edges = []
            # Create nodes with labels indicating the belief value
            for node_id, belief_value in st.session_state["beliefs"].items():
                if belief_value > 0 and str(wu.get_careful_name_of_de_pk(node_id)).lower() != "nan":
                    if node_id in st.session_state["selected_values"]:
                        s = 30
                        c = "pink"
                    else:
                        s = 5 + 20 * belief_value
                        c = "#ffcc00"
                    param_name = st.session_state["parameter_name_by_pk"][st.session_state["parameter_pk_by_domain_element_pk"][str(node_id)]]
                    node_name = param_name + "\n" + wu.get_careful_name_of_de_pk(node_id)
                    nodes.append(Node(
                        id=node_id,
                        label=f"{wu.get_careful_name_of_de_pk(node_id)}",
                        title = node_name + "\nBelief: " + str(round(belief_value, 2)),
                        size=s ,
                        color=c if belief_value > 0.5 else "#cccccc"
                    ))

            # Create edges with labels indicating the probability
            for from_node, to_nodes in st.session_state["inference_graph"].items():
                for to_node, prob in to_nodes.items():
                    edges.append(Edge(
                        source=from_node,
                        target=to_node,
                        label=f"{prob:.2f}",
                        color="#00ccff"
                    ))

            config = Config(
        width='100%',
        height=800,
        directed=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        link={'labelProperty': 'label', 'renderLabel': True},
        node={'labelProperty': 'label'},
        physics=True,
        **dict(panAndZoom=True)
    )

            return_value = agraph(nodes=nodes, edges=edges, config=config)

    #GRAPH with pyvis
    def plot_inference_graph_pyvis(inference_graph, belief):
        net = Network(height='800px', width='100%', directed=True)
        net.barnes_hut()

        # Add nodes with belief values
        for node_id, belief_value in belief.items():
            if belief_value > 0 and node_id not in de_blacklist:
                param_name = st.session_state["parameter_name_by_pk"][
                    st.session_state["parameter_pk_by_domain_element_pk"][str(node_id)]]
                net.add_node(
                    n_id=node_id,
                    label=f"{wu.get_careful_name_of_de_pk(node_id)}",
                    title=f"{param_name}\n{wu.get_careful_name_of_de_pk(node_id)}",
                    size=50 if node_id in st.session_state["selected_values"] else 5 + 45 * belief_value,
                    color="pink" if node_id in st.session_state["selected_values"] else "#ffcc00"
                )

        # Add edges with probabilities
        for from_node, to_nodes in inference_graph.items():
            for to_node, prob in to_nodes.items():
                try:
                    net.add_edge(
                        source=from_node,
                        to=to_node,
                        value=prob,
                        title=f"Conditional Probability: {prob:.2f}",
                        label=f"{prob:.2f}",
                        color="#00ccff",
                        arrows='to',
                        physics=True
                    )
                except:
                    print("no node")

        # Customize physics options for better layout
        net.set_options("""
        var options = {
          "nodes": {
            "font": {
              "size": 16
            }
          },
          "edges": {
            "color": {
              "inherit": true
            },
            "smooth": true
          },
          "physics": {
            "enabled": true,
            "stabilization": {
            "enabled": true,
            "iterations": 1000,
            "updateInterval": 25
            },
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 200,
              "springConstant": 0.05,
              "damping": 0.3,
              "avoidOverlap": 1
            },
            "minVelocity": 0.75
          }
        }
        """)

        # Generate HTML representation of the graph
        return net.generate_html()

    # Generate the PyVis graph HTML
    html_str = plot_inference_graph_pyvis(st.session_state["inference_graph"], st.session_state["beliefs"])

    # Display the PyVis graph in Streamlit
    st.subheader("Inference Graph")
    st.components.v1.html(html_str, height=800, width=1000)


with st.expander("Show conditional probability tables between two parameters"):
    with st.popover("i"):
        st.markdown("Select two parameters to see the conditional probability table of the parameter in column given the parameter in row computed across all languages.")

    p2 = st.selectbox("Show the conditional probability of ", parameter_name_list_filtered)
    p2_pk = st.session_state["parameter_pk_by_name"][str(p2)]
    p1 = st.selectbox("given", parameter_name_list_filtered)
    p1_pk = st.session_state["parameter_pk_by_name"][str(p1)]

    p1_de_pk_list = st.session_state["domain_elements_pk_by_parameter_pk"][str(p1_pk)]
    p2_de_pk_list = st.session_state["domain_elements_pk_by_parameter_pk"][str(p2_pk)]

    # keep only p1 on lines (primary)
    filtered_cpt = st.session_state["cpt"].loc[p1_de_pk_list]
    # keep only p2 on columns (secondary)
    filtered_cpt = filtered_cpt[p2_de_pk_list]

    # renaming rows
    new_p1_label = {}
    for k in filtered_cpt.index:
        if str(k) in st.session_state["parameter_pk_by_domain_element_pk"].keys():
            pm_pk = st.session_state["parameter_pk_by_domain_element_pk"][str(k)]
            if str(pm_pk) in st.session_state["parameter_name_by_pk"].keys():
                pm_name = str(st.session_state["parameter_name_by_pk"][str(pm_pk)])
            else:
                pm_name = "param name unknown"
        else:
            pm_name = "param pk unknown"
        if str(st.session_state["domain_element_by_pk"][str(k)]["name"]) != "nan":
            new_label = str(st.session_state["domain_element_by_pk"][str(k)]["name"])
        elif str(st.session_state["domain_element_by_pk"][str(k)]["description"]) != "nan":
            new_label = str(st.session_state["domain_element_by_pk"][str(k)]["description"])
        else:
            new_label = pm_name + ": " + "pk " + str(k)
        new_p1_label[k] = new_label

    filtered_cpt = filtered_cpt.rename(index=new_p1_label)

    # rename columns
    new_p2_labels = {}
    for k in filtered_cpt.columns:
        if str(k) in st.session_state["parameter_pk_by_domain_element_pk"].keys():
            pm_pk = st.session_state["parameter_pk_by_domain_element_pk"][str(k)]
            if str(pm_pk) in st.session_state["parameter_name_by_pk"].keys():
                pm_name = str(st.session_state["parameter_name_by_pk"][str(pm_pk)])
            else:
                pm_name = "param name unknown"
        else:
            pm_name = "param pk unknown"
        if str(st.session_state["domain_element_by_pk"][str(k)]["name"]) != "nan":
            new_label = str(st.session_state["domain_element_by_pk"][str(k)]["name"])
        elif str(st.session_state["domain_element_by_pk"][str(k)]["description"]) != "nan":
            new_label = str(st.session_state["domain_element_by_pk"][str(k)]["description"])
        else:
            new_label = pm_name + ": " + "pk " + str(k)
        new_p2_labels[k] = new_label

    # Rename columns
    filtered_cpt = filtered_cpt.rename(columns=new_p2_labels)

    # normalization: all the columns of each row (primary event) should sum up to 1
    filtered_cpt_normalized = filtered_cpt.div(filtered_cpt.sum(axis=1), axis=0)

    st.write("P( {} ) | {}: ".format(p2,p1))
    st.dataframe(filtered_cpt_normalized.T)

# with st.expander("Explore joint conditional probabilities deriving from a combination of independent observations"):
#     with st.popover("i"):
#         st.markdown("This tool explores the result of the combination of multiple observations supposed independent, meaning each observation should not have a relationship with other observatiobns.")
#     st.write("Enter below grammatical observations made on a language to see a list of the most probable other values associated with these observations")
#
#     if st.button("Reset observations"):
#         st.session_state["obs"] = []
#         st.session_state["obs_de_pk_list"] = []
#         st.session_state["current_cpt"] = st.session_state["cpt"]
#     if len(st.session_state["obs"]) < 6:
#         new_pm_obs = st.selectbox("parameter "+str(len(st.session_state["obs"]) + 1), parameter_name_list_filtered, key="obs_pm"+str(len(st.session_state["obs"])))
#         obs_pm_pk = st.session_state["parameter_pk_by_name"][str(new_pm_obs)]
#         avail_values_pk = st.session_state["domain_elements_pk_by_parameter_pk"][str(obs_pm_pk)]
#         avail_values_names = []
#         for pk in avail_values_pk:
#             avail_values_names.append(st.session_state["domain_element_by_pk"][str(pk)]["name"])
#         obs_de_name = st.selectbox("select the observed value of that paramater", avail_values_names, key="obs_value"+str(len(st.session_state["obs"])))
#         obs_de_index = avail_values_names.index(obs_de_name)
#         obs_de_pk = avail_values_pk[obs_de_index]
#         if st.button("add observation"):
#             st.session_state["obs"].append({"param_pk":obs_pm_pk, "de_pk":obs_de_pk, "param_name":new_pm_obs, "de_name":obs_de_name})
#             st.session_state["obs_de_pk_list"].append(obs_de_pk)
#             st.session_state["current_cpt"] = st.session_state["cpt"]
#     if st.session_state["obs"] != []:
#         obsc = 0
#         st.write("Current observations:")
#         for item in st.session_state["obs"]:
#             obsc += 1
#             st.write("{}. {}: {}".format(obsc, item["param_name"], item["de_name"]))
#
#         # transform the cpt table to compute the joint conditional probability
#
#         #remove columns that correspond to observed events
#         st.session_state["current_cpt"] = st.session_state["cpt"].drop(columns=st.session_state["obs_de_pk_list"])
#
#         for blacklisted_de_pk in de_pk_blacklist:
#             if blacklisted_de_pk in list(st.session_state["cpt"].columns):
#                 st.session_state["current_cpt"] = st.session_state["current_cpt"].drop(columns=[blacklisted_de_pk])
#             if blacklisted_de_pk in list(st.session_state["cpt"].index):
#                 st.session_state["current_cpt"] = st.session_state["current_cpt"].drop(index=[blacklisted_de_pk])
#
#         # Sum the probabilities for the observed events
#         prob_sum_df = st.session_state["current_cpt"].loc[st.session_state["obs_de_pk_list"]].sum()
#         # Normalize the summed probabilities
#         normalized_prob_df = prob_sum_df / prob_sum_df.sum()
#
#         #renaming rows
#         new_i_label = {}
#         for k in normalized_prob_df.index:
#             if str(k) in st.session_state["parameter_pk_by_domain_element_pk"].keys():
#                 pm_pk = st.session_state["parameter_pk_by_domain_element_pk"][str(k)]
#                 if str(pm_pk) in st.session_state["parameter_name_by_pk"].keys():
#                     pm_name = str(st.session_state["parameter_name_by_pk"][str(pm_pk)])
#                 else:
#                     pm_name = "param name unknown"
#             else:
#                 pm_name = "param pk unknown"
#             if str(st.session_state["domain_element_by_pk"][str(k)]["name"]) != "nan":
#                 new_label = pm_name + ": " + str(st.session_state["domain_element_by_pk"][str(k)]["name"])
#             elif str(st.session_state["domain_element_by_pk"][str(k)]["description"]) != "nan":
#                 new_label = pm_name + ": " + str(st.session_state["domain_element_by_pk"][str(k)]["description"])
#             else:
#                 new_label = pm_name + ": " + "pk " + str(k)
#             new_i_label[k] = new_label
#
#
#         normalized_prob_df = normalized_prob_df.rename(index=new_i_label)
#
#         colq, colw = st.columns(2)
#         percentile = colq.slider("probability percentile threshold", min_value=0.0, max_value=1.0, step=0.01, value=0.9)
#         percentile_threshold = normalized_prob_df.quantile(percentile)
#         colw.write("Probability threshold of percentile {}: {}".format(percentile, round(percentile_threshold,5)))
#
#         normalized_prob_df = normalized_prob_df[normalized_prob_df >= percentile_threshold]
#
#         normalized_prob_df = normalized_prob_df.sort_values(ascending=False)[:100]
#
#         st.dataframe(normalized_prob_df, use_container_width=True)



