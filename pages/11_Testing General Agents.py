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

def reset_all_but_language():
  st.session_state["observed_params_pk"] = []
  st.session_state["observed_params_name"] = []
  st.session_state["unknown_params_pk"] = []
  st.session_state["unknown_params_names"] = []
  st.session_state["expected_beliefs"] = {}
  st.session_state["peak_beliefs_injected"] = False
  st.session_state["success_score"] = {"success": 0, "failure": 0}
  st.session_state["current_ga"] = None

st.title("Testing General Agents")

available_param_names_pk_by_name = {
  "Semantic Distinctions of Evidentiality": 77,
  "Coding of Evidentiality": 78,
  "Suppletion According to Tense and Aspect": 79,
  "Verbal Number and Suppletion": 80,
  "Order of Object, Oblique, and Verb": 84,
  "Order of Adposition and Noun Phrase": 85,
  "Order of Numeral and Noun": 89,
  "Order of Relative Clause and Noun": 90,
  "Order of Adverbial Subordinator and Clause": 94,
  "Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase": 95,
  "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
  "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
  "Alignment of Case Marking of Full Noun Phrases": 98,
  "Alignment of Case Marking of Pronouns": 99,
  "Ditransitive Constructions: The Verb 'Give'": 105,
  "Reciprocal Constructions": 106,
  "Verb-Initial with Clause-Final Negative": 151,
  "Verb-Initial with Preverbal Negative": 155,
  "SONegV Order": 157,
  "Obligatory Double Negation": 158,
  "Multiple Negative Constructions in SOV Languages": 159,
  "Double negation in verb-initial languages": 160,
  "Optional Double Negation in SVO languages": 161,
  "Obligatory Double Negation in SVO languages": 164,
  "Internally-headed relative clauses": 165,
  "Inflectional Synthesis of the Verb": 22,
  "Locus of Marking in the Clause": 23,
  "Locus of Marking in Possessive Noun Phrases": 24,
  "Locus of Marking: Whole-language Typology": 25,
  "Prefixing vs. Suffixing in Inflectional Morphology": 26,
  "Case Syncretism": 28,
  "Syncretism in Verbal Person/Number Marking": 29,
  "Number of Genders": 30,
  "Sex-based and Non-sex-based Gender Systems": 31,
  "Systems of Gender Assignment": 32,
  "Coding of Nominal Plurality": 33,
  "Occurrence of Nominal Plurality": 34,
  "Plurality in Independent Personal Pronouns": 35,
  "The Associative Plural": 36,
  "Indefinite Articles": 38,
  "Inclusive/Exclusive Distinction in Independent Pronouns": 39,
  "Inclusive/Exclusive Distinction in Verbal Inflection": 40,
  "Distance Contrasts in Demonstratives": 41,
  "Pronominal and Adnominal Demonstratives": 42,
  "Third Person Pronouns and Demonstratives": 43,
  "Politeness Distinctions in Pronouns": 45,
  "Indefinite Pronouns": 46,
  "Intensifiers and Reflexive Pronouns": 47,
  "Position of Case Affixes": 51,
  "Ordinal Numerals": 53,
  "Distributive Numerals": 54,
  "Numeral Classifiers": 55,
  "Conjunctions and Universal Quantifiers": 56,
  "Genitives, Adjectives and Relative Clauses": 60,
  "Adjectives without Nouns": 61,
  "Action Nominal Constructions": 62,
  "Nominal and Verbal Conjunction": 64,
  "Perfective/Imperfective Aspect": 65,
  "The Past Tense": 66,
  "The Future Tense": 67,
  "The Perfect": 68,
  "Position of Tense-Aspect Affixes": 69,
  "Negative Morphemes": 112,
  "Symmetric and Asymmetric Standard Negation": 113,
  "Subtypes of Asymmetric Standard Negation": 114,
  "Negative Indefinite Pronouns and Predicate Negation": 115,
  "Predicative Adjectives": 118,
  "Nominal and Locational Predication": 119,
  "Zero Copula for Predicate Nominals": 120,
  "Relativization on Subjects": 122,
  "Relativization on Obliques": 123,
  "'Want' Complement Subjects": 124,
  "Prenominal relative clauses": 144,
  "The Position of Negative Morphemes in Object-Initial Languages": 145,
  "Postnominal relative clauses": 146,
  "NegSOV Order": 147,
  "Obligatory Double Negation in SOV languages": 149,
  "SOVNeg Order": 150,
  "Numeral Bases": 131,
  "Languages with two Dominant Orders of Subject, Object, and Verb": 168,
  "Optional Double Negation": 170,
  "Verb-Initial with Negative that is Immediately Postverbal or between Subject and Object": 173,
  "Optional Double Negation in SOV languages": 174,
  "SNegOV Order": 175,
  "The Position of Negative Morphemes in SOV Languages": 176,
  "Languages with different word order in negative clauses": 178,
  "The Position of Negative Morphemes in Verb-Initial Languages": 179,
  "Optional Triple Negation": 181,
"Zero Marking of A and P Arguments": 187,
  "Exponence of Tense-Aspect-Mood Inflection": 188,
  "Productivity of the Antipassive Construction": 189,
"Reduplication": 27,
  "Definite Articles": 37,
  "Gender Distinctions in Independent Personal Pronouns": 44,
  "Person Marking on Adpositions": 48,
  "Number of Cases": 49,
  "Asymmetrical Case-Marking": 50,
  "Position of Pronominal Possessive Affixes": 57,
  "Obligatory Possessive Inflection": 58,
  "Possessive Classification": 59,
  "Noun Phrase Conjunction": 63,
  "The Morphological Imperative": 70,
  "The Prohibitive": 71,
  "Imperative-Hortative Systems": 72,
  "Situational Possibility": 74,
  "Epistemic Possibility": 75,
  "Overlap between Situational and Epistemic Modal Marking": 76,
  "Order of Subject, Object and Verb": 81,
  "Order of Subject and Verb": 82,
  "Order of Object and Verb": 83,
  "Order of Genitive and Noun": 86,
  "Order of Adjective and Noun": 87,
  "Order of Demonstrative and Noun": 88,
  "Order of Degree Word and Adjective": 91,
  "Position of Polar Question Particles": 92,
  "Position of Interrogative Phrases in Content Questions": 93,
  "Alignment of Verbal Person Marking": 100,
  "Expression of Pronominal Subjects": 101,
  "Verbal Person Marking": 102,
  "Third Person Zero of Verbal Person Marking": 103,
  "Order of Person Markers on the Verb": 104,
  "Passive Constructions": 107,
  "Polar Questions": 116,
  "Predicative Possession": 117,
  "Comparative Constructions": 121,
  "Purpose Clauses": 125,
  "'When' Clauses": 126,
  "Reason Clauses": 127,
  "Utterance Complement Clauses": 128,
  "Postverbal Negative Morphemes": 143,
  "SVNegO Order": 148,
  "Position of Negative Word With Respect to Subject, Object, and Verb": 152,
  "SNegVO Order": 156,
  "SVONeg Order": 162,
  "The Position of Negative Morphemes in SVO Languages": 167,
  "Preverbal Negative Morphemes": 169,
  "Order of Negative Morpheme and Verb": 172,
  "NegSVO Order": 177,
  "Number of Possessive Nouns": 191
}

cq_observable_params_pk_by_name = {
  "Order of Object, Oblique, and Verb": 84,
  "Order of Adposition and Noun Phrase": 85,
  "Order of Numeral and Noun": 89,
  "Order of Relative Clause and Noun": 90,
  "Order of Adverbial Subordinator and Clause": 94,
  "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
  "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
  "Ditransitive Constructions: The Verb 'Give'": 105,
  "Reciprocal Constructions": 106,
  "SONegV Order": 157,
  "Syncretism in Verbal Person/Number Marking": 29,
  "Coding of Nominal Plurality": 33,
  "Plurality in Independent Personal Pronouns": 35,
  "Indefinite Articles": 38,
  "Inclusive/Exclusive Distinction in Independent Pronouns": 39,
  "Inclusive/Exclusive Distinction in Verbal Inflection": 40,
  "Third Person Pronouns and Demonstratives": 43,
  "Indefinite Pronouns": 46,
  "Numeral Classifiers": 55,
  "Nominal and Verbal Conjunction": 64,
  "Perfective/Imperfective Aspect": 65,
  "The Past Tense": 66,
  "The Future Tense": 67,
  "The Perfect": 68,
  "Negative Morphemes": 112,
  "Symmetric and Asymmetric Standard Negation": 113,
  "Negative Indefinite Pronouns and Predicate Negation": 115,
  "Predicative Adjectives": 118,
  "Nominal and Locational Predication": 119,
  "Relativization on Subjects": 122,
  "'Want' Complement Subjects": 124,
  "The Position of Negative Morphemes in Object-Initial Languages": 145,
  "NegSOV Order": 147,
  "Obligatory Double Negation in SOV languages": 149,
  "SOVNeg Order": 150,
  "Languages with two Dominant Orders of Subject, Object, and Verb": 168,
  "Optional Double Negation": 170,
  "Optional Double Negation in SOV languages": 174,
  "SNegOV Order": 175,
  "The Position of Negative Morphemes in SOV Languages": 176,
  "Languages with different word order in negative clauses": 178,
  "The Position of Negative Morphemes in Verb-Initial Languages": 179,
  "Definite Articles": 37,
  "Gender Distinctions in Independent Personal Pronouns": 44,
  "Person Marking on Adpositions": 48,
  "Possessive Classification": 59,
  "Noun Phrase Conjunction": 63,
  "The Morphological Imperative": 70,
  "The Prohibitive": 71,
  "Imperative-Hortative Systems": 72,
  "Situational Possibility": 74,
  "Epistemic Possibility": 75,
  "Order of Subject, Object and Verb": 81,
  "Order of Subject and Verb": 82,
  "Order of Object and Verb": 83,
  "Order of Genitive and Noun": 86,
  "Order of Adjective and Noun": 87,
  "Order of Demonstrative and Noun": 88,
  "Order of Degree Word and Adjective": 91,
  "Position of Polar Question Particles": 92,
  "Position of Interrogative Phrases in Content Questions": 93,
  "Expression of Pronominal Subjects": 101,
  "Verbal Person Marking": 102,
  "Third Person Zero of Verbal Person Marking": 103,
  "Polar Questions": 116,
  "Predicative Possession": 117,
  "Comparative Constructions": 121,
  "Purpose Clauses": 125,
  "'When' Clauses": 126,
  "Reason Clauses": 127,
  "Postverbal Negative Morphemes": 143,
  "SVNegO Order": 148,
  "Position of Negative Word With Respect to Subject, Object, and Verb": 152,
  "SNegVO Order": 156,
  "SVONeg Order": 162,
  "The Position of Negative Morphemes in SVO Languages": 167,
  "Preverbal Negative Morphemes": 169,
  "Order of Negative Morpheme and Verb": 172,
  "NegSVO Order": 177,
  "Number of Possessive Nouns": 191
}

infospot = st.empty()

cola, cols, cold = st.columns(3)
number_of_languages_used_for_testing = cola.slider("Number of languages tested", 1, 50, value=1, step=1)
number_of_ga_parameters = cols.slider("Number of parameters by General Agent", 2, 30, value=10, step=1)
prob_obs = cols.slider("Probability of the true value given observations", .5, 1.0, value=0.6, step=0.01)
min_available_params = cola.slider("Minimum amount of known parameters in the target language", 10, 100, value=50, step=1)
observed_unknown_ratio = cold.slider("Ratio of observed versus unknown parameters by General Agent", .2, 1.0, value=0.5, step=0.01)
if st.button("Submit new values"):
  reset_all_but_language()
  st.rerun()

available_languages = list(wu.language_pk_id_by_name.keys())
# remove languages with less than min_available_params
available_languages_filtered = []
for lid, n_param in wu.n_param_by_language_id.items():
  if n_param > min_available_params:
    available_languages_filtered.append(lid)
st.write("{} languages available for testing.".format(len(available_languages_filtered)))

# select random languages
if st.button("Change test language(s)") or st.session_state["languages_used_for_testing"] == []:
  #reset params and ga
  reset_all_but_language()

  if number_of_languages_used_for_testing < len(available_languages_filtered):
      st.session_state["languages_used_for_testing"] = random.sample(available_languages_filtered, number_of_languages_used_for_testing)
  else:
      st.session_state["languages_used_for_testing"] = available_languages

# for each language, run the test process

for lid in st.session_state["languages_used_for_testing"]:
  l_info = wu.language_info_by_id[lid]
  st.subheader("Language {} of the {} family.".format(l_info["name"], l_info["family"]))

  # random parameter selection
  if st.button("Refresh parameters randomization") or st.session_state["observed_params_name"] == []:
    #reset ga
    st.session_state["current_ga"] = None
    # identify the parameters in the target language usable for testing
    general_available_params_pk_in_target_language =  list(wu.get_language_data_by_id(lid).keys())
    # filter with available_param_names_pk_by_name representing our grammatical parameters of interest.
    available_params_pk_in_target_language = []
    for ppk in general_available_params_pk_in_target_language:
      if ppk in available_param_names_pk_by_name.values():
        available_params_pk_in_target_language.append(ppk)

    available_observable_params_pk_in_target_language = []
    available_non_observable_params_pk_in_target_language = []
    for ppk in available_params_pk_in_target_language:
      if ppk in cq_observable_params_pk_by_name.values():
        available_observable_params_pk_in_target_language.append(ppk)
      else:
        available_non_observable_params_pk_in_target_language.append(ppk)

    st.write("{} grammatical parameters with known values. {} are observable with CQ's, {} are not.".format(len(available_params_pk_in_target_language),len(available_observable_params_pk_in_target_language), len(available_non_observable_params_pk_in_target_language)))

    # select General Agent params
    n_params_observed =  int(round(observed_unknown_ratio * number_of_ga_parameters,0))
    if n_params_observed > len(available_observable_params_pk_in_target_language):
      n_params_observed = len(available_observable_params_pk_in_target_language)
      print("not enough observable params in target language to satisfy the initial request.")

    n_params_unknown = number_of_ga_parameters - n_params_observed
    if n_params_unknown > len(available_non_observable_params_pk_in_target_language):
      n_params_unknown = len(available_non_observable_params_pk_in_target_language)
      print("not enough non-observable params in target language to satisfy the initial request.")

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
    reset_all_but_language()
    st.rerun()

  if st.session_state["observed_params_name"] != []:
    ga_param_name_list = st.session_state["observed_params_name"] + st.session_state["unknown_params_names"]
    if st.session_state["current_ga"] is None:
      st.write("Creating General Agent...")
      st.session_state["current_ga"] = agents.GeneralAgent(str(time.time()), l_info["name"],
                                 parameter_names=ga_param_name_list,
                                 language_stat_filter={})
      # language_stat_filter={"family":["Austronesian"]}
      st.write("General Agent {} created".format(st.session_state["current_ga"].name))

    # injecting peak beliefs in simulated observed parameters
    if not st.session_state["peak_beliefs_injected"]:
      for lp_name in st.session_state["current_ga"].language_parameters.keys():
        if lp_name in st.session_state["observed_params_name"]:
          # this parameter is considered as observed. Finding its true value
          true_depk = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[lp_name]]["domainelement_pk"]
          st.session_state["current_ga"].language_parameters[lp_name].inject_peak_belief(true_depk, prob_obs, locked=True)
      st.session_state["peak_beliefs_injected"] = True

    # beliefs evaluation dict
    # expected beliefs
    if st.session_state["expected_beliefs"] == {}:
      for lpn in st.session_state["current_ga"].language_parameters.keys():
        st.session_state["expected_beliefs"][lpn] = {}
        true_depk = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[lpn]]["domainelement_pk"]
        for value in st.session_state["current_ga"].language_parameters[lpn].beliefs:
          if str(value) == str(true_depk):
            st.session_state["expected_beliefs"][lpn][str(value)] = 1
          else:
            st.session_state["expected_beliefs"][lpn][str(value)] = 0

    # run messaging
    if st.button("run one messaging cycle"):
      st.session_state["current_ga"].run_belief_update_cycle()
      # for lpn in st.session_state["current_ga"].language_parameters.keys():
      #   st.write("param {}'s belief history".format(lpn))
      #   st.write(st.session_state["current_ga"].language_parameters[lpn].beliefs_history)
    if st.button("run 10 messaging cycles"):
      infodis = st.empty()
      for i in range(9):
        infodis.write("Messaging {}/{}".format(i + 1, 10))
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








