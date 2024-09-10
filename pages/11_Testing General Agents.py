import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu, agents
import json
import random
import time
import altair as alt

st.set_page_config(
    page_title="DIG4EL",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "current_ga" not in st.session_state:
  st.session_state["current_ga"] = None
if "languages_used_for_testing" not in st.session_state:
  st.session_state["languages_used_for_testing"] = []
if "observed_params_pk" not in st.session_state:
    st.session_state["observed_params_pk"] = []
if "unknown_params_pk" not in st.session_state:
    st.session_state["unknown_params_pk"] = []
if "observed_params_name" not in st.session_state:
    st.session_state["observed_params_name"] = []
if "unknown_params_names" not in st.session_state:
    st.session_state["unknown_params_names"] = []
if "expected_beliefs" not in st.session_state:
    st.session_state["expected_beliefs"] = {}
if "peak_beliefs_injected" not in st.session_state:
  st.session_state["peak_beliefs_injected"] = False
if "success_score" not in st.session_state:
  st.session_state["success_score"] = {"success":0, "failure":0}
if "success_score" not in st.session_state:
  st.session_state["success_score"] = {"success":0, "failure":0}
if "number_of_languages_used_for_testing" not in st.session_state:
  st.session_state["number_of_languages_used_for_testing"] = 1
if "number_of_ga_parameters" not in st.session_state:
  st.session_state["number_of_ga_parameters"] = 10
if "prob_obs" not in st.session_state:
  st.session_state["prob_obs"] = 0.8
if "min_available_params" not in st.session_state:
  st.session_state["min_available_params"] = 50
if "observed_unknown_multiplier" not in st.session_state:
  st.session_state["observed_unknown_multiplier"] = 1
if "language_family_filter" not in st.session_state:
  st.session_state["language_family_filter"] = "ALL"
if "new_user_params" not in st.session_state:
  st.session_state["new_user_params"] = False

def reset_all():
  st.session_state["languages_used_for_testing"] = []
  st.session_state["observed_params_pk"] = []
  st.session_state["observed_params_name"] = []
  st.session_state["unknown_params_pk"] = []
  st.session_state["unknown_params_names"] = []
  st.session_state["expected_beliefs"] = {}
  st.session_state["peak_beliefs_injected"] = False
  st.session_state["success_score"] = {"success": 0, "failure": 0}
  st.session_state["current_ga"] = None
  st.session_state["language_family_filter"] = "ALL"

st.title("Testing General Agents")

available_param_names_pk_by_name = {
  "Order of Object, Oblique, and Verb": 84,
  "Order of Adposition and Noun Phrase": 85,
  "Order of Numeral and Noun": 89,
  "Order of Relative Clause and Noun": 90,
  "Order of Adverbial Subordinator and Clause": 94,
  "Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase": 95,
  "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
  "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
  "The Position of Negative Morphemes in Object-Initial Languages": 145,
  "Languages with two Dominant Orders of Subject, Object, and Verb": 168,
  "Verb-Initial with Negative that is Immediately Postverbal or between Subject and Object": 173,
  "Languages with different word order in negative clauses": 178,
  "Order of Subject, Object and Verb": 81,
  "Order of Subject and Verb": 82,
  "Order of Object and Verb": 83,
  "Order of Genitive and Noun": 86,
  "Order of Adjective and Noun": 87,
  "Order of Demonstrative and Noun": 88,
  "Order of Degree Word and Adjective": 91,
  "Position of Polar Question Particles": 92,
  "Position of Interrogative Phrases in Content Questions": 93,
  "Order of Person Markers on the Verb": 104,
  "Position of Negative Word With Respect to Subject, Object, and Verb": 152,
  "The Position of Negative Morphemes in SVO Languages": 167,
  "Preverbal Negative Morphemes": 169,
  "Order of Negative Morpheme and Verb": 172
}

cq_observable_params_pk_by_name = {
  "Order of Subject, Object and Verb": 81,
  "Order of Adjective and Noun": 87,
  "Order of Demonstrative and Noun": 88,
  "Order of Degree Word and Adjective": 91,
  "Position of Polar Question Particles": 92,
  "Position of Interrogative Phrases in Content Questions": 93,
  "Position of Negative Word With Respect to Subject, Object, and Verb": 152
}

cola, cols, cold = st.columns(3)
nl = cola.slider("Number of languages tested", 1, 50, value=1, step=1)
ngap = cols.slider("Maximum number of parameters by General Agent", 2, 30, value=10, step=1)
pobs = cols.slider("Probability of the true value given observations", .5, 1.0, value=0.6, step=0.01)
map = cola.slider("Minimum amount of known parameters in the target language", 10, 100, value=50, step=1)
our = cold.slider("Number of parameters to guess for each parameter observed", 1, 5, value=1, step=1)
lff = cola.selectbox("Optional focus on a language family", ["ALL"] + list( wu.language_pk_by_family.keys()), index=0)

if st.button("Submit new values"):
  st.session_state["number_of_languages_used_for_testing"] = nl
  st.session_state["number_of_ga_parameters"] = ngap
  st.session_state["prob_obs"] = pobs
  st.session_state["min_available_params"] = map
  st.session_state["observed_unknown_multiplier"] = our
  st.session_state["language_family_filter"] = lff
  st.session_state["new_user_params"] = True
  st.rerun()

# filter by family
if st.session_state["language_family_filter"] != "ALL":
  lfpk = wu.language_pk_by_family[st.session_state["language_family_filter"]]
  family_filtered_language_id_list = []
  for lpk in lfpk:
    try:
      family_filtered_language_id_list.append(wu.language_by_pk[lpk]["id"])
    except KeyError:
      print("key error in lfid.append(wu.language_by_pk[lpk]['id'])")
  st.write("Focusing on the {} languages from the {} family.".format(len(family_filtered_language_id_list), st.session_state["language_family_filter"]))
else:
  family_filtered_language_id_list = list(wu.language_info_by_id.keys())

# remove languages with less than min_available_params
available_languages = []
for fflid in family_filtered_language_id_list:
  if fflid in wu.n_param_by_language_id.keys():
    if wu.n_param_by_language_id[fflid] >= st.session_state["min_available_params"]:
      available_languages.append(fflid)

st.write("{} languages will be available for testing General Agents with these parameters.".format(len(available_languages)))

if st.session_state["new_user_params"] or st.session_state["languages_used_for_testing"] == []:
  if st.session_state["number_of_languages_used_for_testing"] < len(available_languages):
      st.session_state["languages_used_for_testing"] = random.sample(available_languages, st.session_state["number_of_languages_used_for_testing"])
  else:
      st.session_state["languages_used_for_testing"] = available_languages

st.write("Randomly sampled languages used for testing: {}".format(st.session_state["languages_used_for_testing"]))

# for each language, run the test process

# for lid in st.session_state["languages_used_for_testing"]:
#   l_info = wu.language_info_by_id[lid]
#   st.subheader("Language {} of the {} family.".format(l_info["name"], l_info["family"]))

# random parameter selection

# easy: define parameters based on the intersection ob known parameters in all the selected languages.
# TODO: better, establish connections in GA in relation with the available known params in each language

# easy first
params_pk_available_in_each_language = []
if len(st.session_state["languages_used_for_testing"]) > 1:
  for tlid in st.session_state["languages_used_for_testing"]:
    params_pk_available_in_each_language.append(list(wu.get_language_data_by_id(tlid).keys()))
    available_params_pk_intersection_in_target_languages = list(set(params_pk_available_in_each_language[0]).intersection(*params_pk_available_in_each_language[1:]))
else:
  available_params_pk_intersection_in_target_languages = list(wu.get_language_data_by_id(st.session_state["languages_used_for_testing"][0]).keys())
st.write("{} known parameters intersection in languages used for testing: {}".format(len(available_params_pk_intersection_in_target_languages), available_params_pk_intersection_in_target_languages))

if st.button("Refresh parameters randomization") or st.session_state["observed_params_name"] == []:
  #reset ga
  st.session_state["current_ga"] = None
  # identify the parameters in the target language usable for testing
  general_available_params_pk_in_target_language =  available_params_pk_intersection_in_target_languages
  # filter with available_param_names_pk_by_name representing our grammatical parameters of interest.
  available_params_pk_in_target_language = []
  for ppk in general_available_params_pk_in_target_language:
    if ppk in available_param_names_pk_by_name.values():
      available_params_pk_in_target_language.append(ppk)
  # separating parameters of interest between observable and non-observable
  available_observable_params_pk_in_target_language = []
  available_non_observable_params_pk_in_target_language = []
  for ppk in available_params_pk_in_target_language:
    if ppk in cq_observable_params_pk_by_name.values():
      available_observable_params_pk_in_target_language.append(ppk)
    else:
      available_non_observable_params_pk_in_target_language.append(ppk)

  st.write("{} grammatical parameters with known values. {} are observable with CQ's, {} are not.".format(len(available_params_pk_in_target_language),len(available_observable_params_pk_in_target_language), len(available_non_observable_params_pk_in_target_language)))

  # select General Agent params
  n_params_observed = len(available_observable_params_pk_in_target_language)
  n_params_unknown = n_params_observed * st.session_state["observed_unknown_multiplier"]
  st.write("Aiming at {} observed and {} unknown parameters.".format(n_params_observed, n_params_unknown))
  total_ideal = n_params_observed + n_params_unknown
  if total_ideal > st.session_state["number_of_ga_parameters"]:
    reduction_factor = st.session_state["number_of_ga_parameters"] / total_ideal
    n_params_observed = int(round(n_params_observed * reduction_factor, 0))
    n_params_unknown = int(round(n_params_unknown * reduction_factor, 0))

  if n_params_observed > len(available_observable_params_pk_in_target_language):
    n_params_observed = len(available_observable_params_pk_in_target_language)
    print("not enough observable params in target language to satisfy the initial request.")

  if n_params_unknown > len(available_non_observable_params_pk_in_target_language):
    n_params_unknown = len(available_non_observable_params_pk_in_target_language)
    print("not enough non-observable params in target language to satisfy the initial request.")

  st.write("After parameters availability check: {} parameters will be observed, {} will be unknown.".format(n_params_observed, n_params_unknown))

  n_test_ga_parameters = n_params_observed + n_params_unknown

  # select observed params
  st.session_state["observed_params_pk"] = random.sample(available_observable_params_pk_in_target_language, n_params_observed)
  st.session_state["observed_params_name"] = [wu.parameter_name_by_pk[str(pk)] for pk in st.session_state["observed_params_pk"]]

  # select unknown params
  st.session_state["unknown_params_pk"] = random.sample(available_non_observable_params_pk_in_target_language, n_params_unknown)
  st.session_state["unknown_params_names"] = [wu.parameter_name_by_pk[str(pk)] for pk in st.session_state["unknown_params_pk"]]

st.subheader("Parameters")
colq, colw = st.columns(2)
colq.write("**Simulated observed parameters:**")
for opn in st.session_state["observed_params_name"]:
  colq.write(opn)
colw.write("**Simulated unknown parameters:**")
for upn in st.session_state["unknown_params_names"]:
  colw.write(upn)

# creating GA

st.subheader("General Agent")
if st.button("Reset"):
  reset_all()
  st.rerun()

    # LANGUAGE GROUP SPECIFIC

if st.session_state["observed_params_name"] != [] or st.session_state["new_user_params"]:
  ga_param_name_list = st.session_state["observed_params_name"] + st.session_state["unknown_params_names"]
  if st.session_state["current_ga"] is None:
    st.write("Creating General Agent...")
    vowels = ["a", "e", "i", "o", "u"]
    agent_name = ""
    for pn in ga_param_name_list:
      agent_name += pn[0] + random.sample(vowels, 1)[0]
    if st.session_state["language_family_filter"] == "ALL":
      st.session_state["current_ga"] = agents.GeneralAgent(agent_name + str(time.time())[-3:],
                                 parameter_names=ga_param_name_list,
                                 language_stat_filter={})
    else:
      st.session_state["current_ga"] = agents.GeneralAgent(agent_name + str(time.time())[-3:],
                                                           parameter_names=ga_param_name_list,
                                                           language_stat_filter={"family":[st.session_state["language_family_filter"]]})
    st.write("General Agent {} created".format(st.session_state["current_ga"].name))

  # ITERATING ON TEST LANGUAGES

  for lid in st.session_state["languages_used_for_testing"]:

    st.session_state["peak_beliefs_injected"] = False
    st.session_state["expected_beliefs"] = {}

    st.write("Language **{}**".format(wu.language_info_by_id[lid]["name"]))
    st.write("Resetting {} priors with WALS".format(st.session_state["current_ga"].name))
    st.session_state["current_ga"].reset_language_parameters_beliefs_with_wals()
    st.write("injecting observation-based beliefs")
    # injecting peak beliefs in simulated observed parameters
    if not st.session_state["peak_beliefs_injected"]:
      for lp_name in st.session_state["current_ga"].language_parameters.keys():
        if lp_name in st.session_state["observed_params_name"]:
          # this parameter is considered as observed. Finding its true value
          true_depk = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[lp_name]]["domainelement_pk"]
          st.session_state["current_ga"].language_parameters[lp_name].inject_peak_belief(true_depk, st.session_state["prob_obs"], locked=True)
      st.session_state["peak_beliefs_injected"] = True

    # beliefs evaluation dict

    # expected beliefs
    if st.session_state["expected_beliefs"] == {}:
      for lpn in st.session_state["current_ga"].language_parameters.keys():
        st.session_state["expected_beliefs"][lpn] = {}
        true_depk = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[lpn]]["domainelement_pk"]
        for value in st.session_state["current_ga"].language_parameters[str(lpn)].beliefs:
          if str(value) == str(true_depk):
            st.session_state["expected_beliefs"][lpn][str(value)] = 1
          else:
            st.session_state["expected_beliefs"][lpn][str(value)] = 0

    st.write("running 10 messaging cycles")
    # run messaging
    # if st.button("run one messaging cycle"):
    #   st.session_state["current_ga"].run_belief_update_cycle()
    #   # for lpn in st.session_state["current_ga"].language_parameters.keys():
    #   #   st.write("param {}'s belief history".format(lpn))
    #   #   st.write(st.session_state["current_ga"].language_parameters[lpn].beliefs_history)
    for i in range(9):
      st.session_state["current_ga"].run_belief_update_cycle()

    # =======================
    # record and show scoring
    evaluation = {"success":0, "failure":0}
    for upn in st.session_state["unknown_params_names"]:
      expected_value = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[upn]]["domainelement_pk"]
      current_consensus = max(st.session_state["current_ga"].language_parameters[upn].beliefs, key=st.session_state["current_ga"].language_parameters[upn].beliefs.get)
      if str(expected_value) == str(current_consensus):
        evaluation["success"] += 1
      else:
        evaluation["failure"] += 1

    if (evaluation["success"] + evaluation["failure"]) != 0:
      score = evaluation["success"] / (evaluation["success"] + evaluation["failure"])
    else:
      score = 0
    st.subheader("Current accuracy of the consensus on unknown values: {}%".format(round(score*100,0)))
    st.write(evaluation)

    # ===============
    # display results
    if st.session_state["current_ga"] is not None:

      coln, colm = st.columns(2)
      coln.write("**Observed parameters**")
      for opn in st.session_state["observed_params_name"]:
        coln.write("{}".format(opn))
        #coln.write("locked: {}".format(st.session_state["current_ga"].language_parameters[opn].locked))
        result_dict = st.session_state["current_ga"].language_parameters[opn].beliefs_history

        expected_value = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[opn]]["domainelement_pk"]
        consensus = max(st.session_state["current_ga"].language_parameters[opn].beliefs, key=st.session_state["current_ga"].language_parameters[opn].beliefs.get)

        coln.write("**Expected**: {} || **Consensus**: {}".format(wu.get_careful_name_of_de_pk(expected_value), wu.get_careful_name_of_de_pk(consensus)))

        #result_dict.append(st.session_state["expected_beliefs"][opn])

        result_df = pd.DataFrame(result_dict)
        # Melt the DataFrame into long format
        df_melted = result_df.reset_index().melt(id_vars="index", var_name="parameter", value_name="value")

        # Create the heatmap
        heatmap = alt.Chart(df_melted).mark_rect().encode(
          x=alt.X('index:O', title="Messaging sequence"),  # Ordinal row index on x-axis
          y=alt.Y('parameter:O', title="Value"),  # Ordinal parameter values on y-axis
          color=alt.Color('value:Q', title="Value"),  # Color scale for value
          tooltip=['index', 'parameter', 'value']  # Tooltip for interactivity
        )
        coln.altair_chart(heatmap, use_container_width=True)

      colm.write("**Unknown parameters**")
      for upn in st.session_state["unknown_params_names"]:
        colm.write(upn)
        #coln.write("locked: {}".format(st.session_state["current_ga"].language_parameters[upn].locked))
        result_dict = st.session_state["current_ga"].language_parameters[upn].beliefs_history

        expected_value = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[upn]]["domainelement_pk"]
        consensus = max(st.session_state["current_ga"].language_parameters[upn].beliefs,
                        key=st.session_state["current_ga"].language_parameters[upn].beliefs.get)

        colm.write("**Expected**: {} || **Consensus**: {}".format(wu.get_careful_name_of_de_pk(expected_value), wu.get_careful_name_of_de_pk(consensus)))

        #result_dict.append(st.session_state["expected_beliefs"][upn])
        result_df = pd.DataFrame(result_dict)
        # Melt the DataFrame into long format
        df_melted = result_df.reset_index().melt(id_vars="index", var_name="parameter", value_name="value")

        # Create the heatmap
        heatmap = alt.Chart(df_melted).mark_rect().encode(
          x=alt.X('index:O', title="Messaging sequence"),
          # Ordinal row index on x-axis
          y=alt.Y('parameter:O', title="Value"),  # Ordinal parameter values on y-axis
          color=alt.Color('value:Q', title="Value"),  # Color scale for value
          tooltip=['index', 'parameter', 'value']  # Tooltip for interactivity
        )
        colm.altair_chart(heatmap, use_container_width=True)








