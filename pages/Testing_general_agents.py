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
if "languages chosen by user" not in st.session_state:
  st.session_state["languages chosen by user"] = False

def reset_all():
  st.session_state["languages chosen by user"] = False
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


with st.sidebar:
  st.subheader("DIG4EL")
  st.page_link("home.py", label="Home", icon=":material/home:")

  st.write("**Base Features**")
  st.page_link("pages/2_CQ_Transcription_Recorder.py", label="Record transcription", icon=":material/contract_edit:")

  st.write("**Advanced features**")
  st.page_link("pages/4_CQ Editor.py", label="Edit CQs", icon=":material/question_exchange:")

  st.write("**Explore DIG4EL processes**")
  st.page_link("pages/DIG4EL_processes_menu.py", label="DIG4EL processes", icon=":material/schema:")

colo, colp = st.columns(2)
colo.title("Testing General Agents")
with colp.popover("i"):
  st.markdown("This page allows to test General Agents focusing on word order. Choose one or multiple languages, either by hand-picking them, "
              "or making a random selection, within a language family or not.")
  st.markdown(
    "The testing process searches the common parameters known by WALS across these languages and simulates the observation of a portion of these parameters, "
    "and the guessing of the others via a Markov Random Field consensus. Results presented take only into account the parameters simulated as unknown.")
  st.markdown(
    "The more languages tested at once, the less available common parameters there may be if they are not hand-picked carefully. ")

if st.button("Reset all"):
  reset_all()
  st.rerun()

available_param_names_pk_by_name = {
  "Order of Object, Oblique, and Verb": 84,
  "Order of Adposition and Noun Phrase": 85,
  "Order of Numeral and Noun": 89,
  "Order of Relative Clause and Noun": 90,
  "Order of Adverbial Subordinator and Clause": 94,
  "Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase": 95,
  "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
  "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
  "Languages with two Dominant Orders of Subject, Object, and Verb": 168,
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
ngap = cols.slider("Maximum number of parameters by General Agent", 2, 100, value=50, step=1)
pobs = cols.slider("Probability of the true value given observations", .5, 1.0, value=0.9, step=0.01)
map = cola.slider("Minimum amount of known parameters in the target language", 10, 100, value=50, step=1)
our = cold.slider("Number of parameters to guess for each parameter observed", 1, 5, value=2, step=1)
lff = cola.selectbox("Optional focus on a language family", ["ALL"] + list( wu.language_pk_by_family.keys()), index=0)
fl = cols.multiselect("Choose languages instead of random selection", list(wu.language_pk_id_by_name.keys()), placeholder="Leave empty for a random language selection")

if st.button("Submit new values"):

  if fl == []:
    st.session_state["languages chosen by user"] = False
    st.session_state["number_of_languages_used_for_testing"] = nl
    st.session_state["number_of_ga_parameters"] = ngap
    st.session_state["prob_obs"] = pobs
    st.session_state["min_available_params"] = map
    st.session_state["observed_unknown_multiplier"] = our
    st.session_state["language_family_filter"] = lff
    st.session_state["new_user_params"] = True
    st.session_state["languages_used_for_testing"] = []
  else:
    st.session_state["languages chosen by user"] = True
    st.session_state["number_of_languages_used_for_testing"] = len(fl)
    st.session_state["number_of_ga_parameters"] = ngap
    st.session_state["prob_obs"] = pobs
    st.session_state["min_available_params"] = map
    st.session_state["observed_unknown_multiplier"] = our
    st.session_state["language_family_filter"] = lff
    st.session_state["new_user_params"] = True
    st.session_state["languages_used_for_testing"] = []
    for language_name in fl:
      st.session_state["languages_used_for_testing"].append(wu.language_pk_id_by_name[language_name]["id"])

  st.rerun()

st.subheader("Languages used for testing")

if not st.session_state["languages chosen by user"]:
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

  st.write("{} languages with more than {} known parameters will be available for testing.".format(len(available_languages), st.session_state["min_available_params"]))

  if st.session_state["new_user_params"] or st.session_state["languages_used_for_testing"] == []:
    if st.session_state["number_of_languages_used_for_testing"] < len(available_languages):
        st.session_state["languages_used_for_testing"] = random.sample(available_languages, st.session_state["number_of_languages_used_for_testing"])
    else:
        st.session_state["languages_used_for_testing"] = available_languages

  tl = []
  for ltid in st.session_state["languages_used_for_testing"]:
    tl.append(wu.language_info_by_id[ltid]["name"])
  comma_separated_string = ', '.join(tl)
  st.write("Randomly sampled languages used for testing: {}".format("**"+comma_separated_string+"**"))
else:
  tl = []
  for ltid in st.session_state["languages_used_for_testing"]:
    tl.append(wu.language_info_by_id[ltid]["name"])
  comma_separated_string = ', '.join(tl)
  st.write("Languages chosen by user for testing: {}".format(comma_separated_string))

# random parameter selection
if st.session_state["observed_params_name"] != [] or st.session_state["new_user_params"]:

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
  st.write("{} known parameters intersection in languages used for testing.".format(len(available_params_pk_intersection_in_target_languages)))

  if st.session_state["observed_params_name"] == [] or st.session_state["new_user_params"]:
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
    #st.write("Aiming at {} observed and {} unknown parameters.".format(n_params_observed, n_params_unknown))
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

    st.write("{} parameters will be simulated as observed, {} will be simulated as unknown.".format(n_params_observed, n_params_unknown))

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

    # SPECIFIC TO LANGUAGE GROUP
st.subheader("General Agent status")
if st.session_state["observed_params_name"] != [] or st.session_state["new_user_params"]:

  ga_param_name_list = st.session_state["observed_params_name"] + st.session_state["unknown_params_names"]
  if st.session_state["current_ga"] is None or st.session_state["new_user_params"]:
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
    st.write("General Agent {} with {} parameters created".format(st.session_state["current_ga"].name, len(st.session_state["current_ga"].language_parameters.keys())))

  # last process to catch the new users params, resetting
  st.session_state["new_user_params"] = False

  # ITERATING ON TEST LANGUAGES

  st.subheader("Results")

  general_result_dict = {}
  infospot = st.empty()
  for lid in st.session_state["languages_used_for_testing"]:
    lname = wu.language_info_by_id[lid]["name"]
    general_result_dict[lname] = {}
    st.session_state["peak_beliefs_injected"] = False
    st.session_state["expected_beliefs"] = {}
    infospot.write("establishing priors, injecting beliefs and running messaging until consensus on language **{}**...".format(wu.language_info_by_id[lid]["name"]))
    #st.write("Resetting {} priors with WALS, injecting beliefs, running messaging cycles until consensus.".format(st.session_state["current_ga"].name))
    st.session_state["current_ga"].reset_language_parameters_beliefs_with_wals()
    #st.write("injecting observation-based beliefs")
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

    # run messaging
    for i in range(3):
      st.session_state["current_ga"].run_belief_update_cycle()

    # =======================
    # record and show scoring
    evaluation = {"success":0, "failure":0}
    for upn in st.session_state["unknown_params_names"]:
      general_result_dict[lname][upn] = {}
      expected_value = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[upn]]["domainelement_pk"]
      current_consensus = max(st.session_state["current_ga"].language_parameters[upn].beliefs, key=st.session_state["current_ga"].language_parameters[upn].beliefs.get)

      general_result_dict[lname][upn]["expected"] = wu.get_careful_name_of_de_pk(str(expected_value))
      general_result_dict[lname][upn]["consensus"] = wu.get_careful_name_of_de_pk(str(current_consensus))

      if str(expected_value) == str(current_consensus):
        evaluation["success"] += 1
        general_result_dict[lname][upn]["success"] = True
      else:
        evaluation["failure"] += 1
        general_result_dict[lname][upn]["success"] = False

    if (evaluation["success"] + evaluation["failure"]) != 0:
      score = evaluation["success"] / (evaluation["success"] + evaluation["failure"])
    else:
      score = 0
    #coln.write("Current accuracy of the consensus on unknown values: **{}%**".format(round(score*100,0)))

    general_result_dict[lname]["score_percent"] = round(score*100,0)
    #st.write(evaluation)

  average_score = 0
  # ===============
  # prepare results
  if st.session_state["current_ga"] is not None:
    truth_table = {}
    scoring_table = {}
    for language in general_result_dict.keys():
      truth_table[language] = {}
      scoring_table[language] = {}
      scoring_table[language]["score"] = general_result_dict[language]["score_percent"]
      average_score += general_result_dict[language]["score_percent"]
      for upn in general_result_dict[language].keys():
        if upn != "score_percent":
          if general_result_dict[language][upn]["success"]:
            truth_table[language][upn] = "✅"
          else:
            truth_table[language][upn] = "❌"
    average_score = average_score / len(general_result_dict)

    # display results

    st.metric("**Average accuracy guessing unknown values through consensus**", value = str(average_score)+"%")
    st.write("**Consensus accuracy on unknown values by language.**")
    st.bar_chart(pd.DataFrame(scoring_table).T)
    st.write("**Truth table of consensus on unknown values by language.**")
    st.table(truth_table)
    st.write("**detailed consensus by language**")
    st.table(general_result_dict)









