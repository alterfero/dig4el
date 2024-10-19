import streamlit as st
import pandas as pd
from libs import utils as u, wals_utils as wu, general_agents
import json
import random
import time


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
if "ga_domains" not in st.session_state:
  st.session_state["ga_domains"] = []
if "ga_params_by_domain" not in st.session_state:
  with open("./external_data/wals_derived/ga_params_by_domain.json", "r") as f:
    st.session_state["ga_params_by_domain"] = json.load(f)
if "available_param_pk_by_name" not in st.session_state:
  st.session_state["available_param_pk_by_name"] = {}
if "available_param_pk_by_name" not in st.session_state:
  st.session_state["available_param_pk_by_name"] = {}

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
  st.session_state["ga_domains"] = []

obs = {
  "Order of Subject, Object and Verb": 81,
  "Order of Subject and Verb": 82,
  "Order of Object and Verb": 83,
  "Order of Adjective and Noun": 87,
  "Order of Demonstrative and Noun": 88,
  "Order of Numeral and Noun": 89,
  "Order of Relative Clause and Noun": 90
}

obs_pk_list = [str(v) for v in obs.values()]

#nobs = {"Order of Object, Oblique, and Verb": 84}

nobs = {
  "Order of Object, Oblique, and Verb": 84,
  "Order of Adposition and Noun Phrase": 85,
  "Order of Adverbial Subordinator and Clause": 94,
  "Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase": 95,
  "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
  "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
  "Order of Genitive and Noun": 86,
  "Order of Degree Word and Adjective": 91
}

# nobs = {
#   "Order of Object, Oblique, and Verb": 84,
#   "Order of Adposition and Noun Phrase": 85,
#   "Order of Adverbial Subordinator and Clause": 94,
#   "Order of Genitive and Noun": 86,
#   "Order of Degree Word and Adjective": 91
# }

nobs_pk_list = [str(v) for v in nobs.values()]

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

colo, colp = st.columns(2)
colo.title("Testing General Agents")
with colp.popover("i"):
  st.markdown("This page allows to test General Agents. Choose one or multiple general domains, then select languages, either by hand-picking them, "
              "or making a random selection, within a language family or not.")
  st.markdown(
    "The testing process searches the common parameters known by WALS across these languages and simulates the observation of a portion of these parameters, "
    "and the guessing of the others via a Markov Random Field consensus. Results presented take only into account the parameters simulated as unknown.")
  st.markdown(
    "The more languages tested at once, the less available common parameters there may be if they are not hand-picked carefully. ")
  st.markdown( "This is the prototype of a work in progress, features will evolve and behaviors will improve over time.")

if st.button("Reset all"):
  reset_all()
  st.rerun()

#do = st.multiselect("General Agent domain(s)", st.session_state["ga_params_by_domain"].keys())
do = ["word order"]
lff = st.selectbox("Optional focus on a language family", ["ALL"] + list( wu.language_pk_by_family.keys()), index=0)
fl = st.multiselect("Choose languages instead of random selection", list(wu.language_pk_id_by_name.keys()), placeholder="Leave empty for a random language selection")
with st.expander("optional process parameters"):
  cola, cols, cold = st.columns(3)
  nl = cola.slider("Number of languages tested", 1, 500, value=1, step=1)
  #ngap = cols.slider("Maximum size of General Agent", 2, 100, value=50, step=1)
  pobs = cols.slider("Probability of the true value given observations", .5, 1.0, value=0.9, step=0.01)
  #map = cola.slider("Minimum amount of known parameters in the target language", 10, 100, value=50, step=1)
  #our = cold.slider("Number of parameters to guess for each parameter observed", 1, 5, value=2, step=1)

if st.button("Submit new values"):
  if len(do) > 0:
    st.session_state["ga_domains"] = do
    available_param_pk_by_name = {}
    observable_params_pk_by_name = {}
    # for ga_domain in st.session_state["ga_domains"]:
    #     for pname in st.session_state["ga_params_by_domain"][ga_domain]["available_param_pk_by_name"].keys():
    #       if pname not in available_param_pk_by_name.keys():
    #         available_param_pk_by_name[pname] = st.session_state["ga_params_by_domain"][ga_domain]["available_param_pk_by_name"][pname]
    # for ga_domain in st.session_state["ga_domains"]:
    #     for pname in st.session_state["ga_params_by_domain"][ga_domain]["observable_params_pk_by_name"].keys():
    #       if pname not in observable_params_pk_by_name.keys():
    #         observable_params_pk_by_name[pname] = st.session_state["ga_params_by_domain"][ga_domain]["observable_params_pk_by_name"][pname]
    # st.session_state["available_param_pk_by_name"] = available_param_pk_by_name
    # st.session_state["observable_params_pk_by_name"] = observable_params_pk_by_name
    if fl == []:
      st.session_state["languages chosen by user"] = False
      st.session_state["number_of_languages_used_for_testing"] = nl
      #st.session_state["number_of_ga_parameters"] = ngap
      st.session_state["prob_obs"] = pobs
      st.session_state["min_available_params"] = map
      #st.session_state["observed_unknown_multiplier"] = our
      st.session_state["language_family_filter"] = lff
      st.session_state["new_user_params"] = True
      st.session_state["languages_used_for_testing"] = []
    else:
      st.session_state["languages chosen by user"] = True
      st.session_state["number_of_languages_used_for_testing"] = len(fl)
      #st.session_state["number_of_ga_parameters"] = ngap
      st.session_state["prob_obs"] = pobs
      st.session_state["min_available_params"] = map
      #st.session_state["observed_unknown_multiplier"] = our
      st.session_state["language_family_filter"] = lff
      st.session_state["new_user_params"] = True
      st.session_state["languages_used_for_testing"] = []
      for language_name in fl:
        st.session_state["languages_used_for_testing"].append(wu.language_pk_id_by_name[language_name]["id"])
    st.rerun()
  else:
    st.warning("Select at least one General Agent domain")

st.subheader("General Agent domain(s)")
if len(st.session_state["ga_params_by_domain"]) > 0:
  st.write(", ".join(st.session_state["ga_domains"]))

if len(st.session_state["ga_domains"]) > 0:
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

    # remove languages that don't show values for obs+nobs
    available_languages = []
    for fflid in family_filtered_language_id_list:
      lpk = wu.language_pk_by_id[fflid]
      available_param_pk_list = wu.params_pk_by_language_pk[str(lpk)]
      if set(obs_pk_list+nobs_pk_list).intersection(available_param_pk_list) == set(obs_pk_list+nobs_pk_list):
        available_languages.append(fflid)

    if len(available_languages) > 0:
      st.write("{} languages with a matching set of parameters.".format(len(available_languages)))

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
      st.warning("No language available for testing in this family.")

  else:
    # user has chosen languages
    keep = []
    reject = []
    for fflid in st.session_state["languages_used_for_testing"]:
      lpk = wu.language_pk_by_id[fflid]
      available_param_pk_list = wu.params_pk_by_language_pk[str(lpk)]
      if set(obs_pk_list + nobs_pk_list).intersection(available_param_pk_list) == set(obs_pk_list + nobs_pk_list):
        keep.append(fflid)
      else:
        reject.append(fflid)
    if reject != []:
      st.write("Languages {} won't be used for testing. Key parameters unknown.".
               format(", ".join([wu.language_info_by_id[rid]["name"] for rid in reject])))
    st.session_state["languages_used_for_testing"] = keep

    tl = []
    for ltid in st.session_state["languages_used_for_testing"]:
      tl.append(wu.language_info_by_id[ltid]["name"])
    comma_separated_string = ', '.join(tl)
    st.write("Languages chosen by user for testing: {}".format(comma_separated_string))

  # Parameters
  st.session_state["observed_params_name"] = list(obs.keys())
  st.session_state["unknown_params_names"] = list(nobs.keys())

  if len(st.session_state["languages_used_for_testing"]) > 0 and (st.session_state["observed_params_name"] != [] or st.session_state["new_user_params"]):
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
  if len(st.session_state["languages_used_for_testing"]) > 0:
    st.subheader("General Agent status")
    if st.session_state["observed_params_name"] != [] or st.session_state["new_user_params"]:

      ga_param_name_list = st.session_state["observed_params_name"] + st.session_state["unknown_params_names"]
      if st.session_state["current_ga"] is None or st.session_state["new_user_params"]:
        st.write("Creating General Agent with {} parameters...".format(len(ga_param_name_list)))
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
        st.write("General Agent created")

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
        binary_truth_table = {}
        scoring_table = {}
        for language in general_result_dict.keys():
          truth_table[language] = {}
          binary_truth_table[language] = {}
          scoring_table[language] = {}
          scoring_table[language]["score"] = general_result_dict[language]["score_percent"]
          average_score += general_result_dict[language]["score_percent"]
          for upn in general_result_dict[language].keys():
            if upn != "score_percent":
              if general_result_dict[language][upn]["success"]:
                truth_table[language][upn] = "✅"
                binary_truth_table[language][upn] = 1
              else:
                truth_table[language][upn] = "❌"
                binary_truth_table[language][upn] = 0
        average_score = average_score / len(general_result_dict)

        # display results

        st.metric("**Average accuracy guessing unknown values through consensus**", value = str(round(average_score,2))+"%")
        st.write("**Consensus accuracy on unknown values by language.**")
        st.bar_chart(pd.DataFrame(scoring_table).T)
        st.write("**Truth table of consensus on unknown values by language.**")
        st.table(truth_table)

        with open("./data/binary_truth_table_tmp.json", "w") as f:
          json.dump(binary_truth_table, f)
        st.write("**detailed consensus by language**")
        st.table(general_result_dict)
else:
  st.write("**Select at least one General Agent domain**")









