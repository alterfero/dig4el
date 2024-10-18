from libs import wals_utils as wu, grambank_utils as gu
from libs import agents


gamix = agents.GeneralAgent("gamix",
                               parameter_names=["Are there definite or specific articles?",
                                                "Are there prenominal articles?",
                                                "Order of Subject, Object and Verb",
                                                "Order of Demonstrative and Noun"],
                               language_stat_filter={}, verbose=True)

print("beliefs: ", gamix.get_beliefs())

# OBSERVATIONS
# # Adding a WALS observation
# gamix.add_observations("Order of Subject, Object and Verb",
#                       {'387': 0, '386': 0, '388': 0, '385': 8, '383': 2, '384': 0, '389': 0})
# gamix.run_belief_update_from_observations()
# print("beliefs after wals obs: ",gamix.get_beliefs())
# # Adding a Grambank observation
# gamix.add_observations("Are there definite or specific articles?",
#                        {'GB020-0':1, 'GB020-1':5})
# gamix.run_belief_update_from_observations()
# print("beliefs after grambank obs: ",gamix.get_beliefs())

# INJECTION
# print("Injecting beliefs")
# language_name = "Tahitian"
# injection_list = ["Order of Subject, Object and Verb", "Are there definite or specific articles?"]
# for lp_name in gamix.language_parameters.keys():
#     if lp_name in injection_list:
#         lp_origin = gamix.language_parameters[lp_name].origin
#         print("Injecting in parameter {} from {}".format(lp_name, lp_origin))
#         if lp_origin == "wals":
#             true_depk = wu.get_wals_language_data_by_id_or_name(language_id=None, language_name=language_name)[wu.parameter_pk_by_name[lp_name]]["domainelement_pk"]
#             print("True value: {}".format(true_depk))
#             gamix.language_parameters[lp_name].inject_peak_belief(true_depk, 0.6, locked=False)
#         elif lp_origin == "grambank":
#             true_vid = gu.get_grambank_language_data_by_id_or_name(language_id=None, language_name=language_name)[gu.grambank_pid_by_pname[lp_name]]["vid"]
#             gamix.language_parameters[lp_name].inject_peak_belief(true_vid, 0.6, locked=False)
# print("Beliefs of {} after injection: {}".format(gamix.name, gamix.get_beliefs()))

# FULL CYCLE WITH MESSAGING
for i in range(5):
    print("               ")
    print("=========================================================================")
    print("======================= START OF BELIEF UPDATE CYCLE {} ================= ".format(i))
    print("=========================================================================")
    print("               ")
    gamix.run_belief_update_cycle()

print("               ")
print("=========================================================================")
print("================================= RESULTS =============================== ".format(i))
print("=========================================================================")
print("               ")
for parameter in gamix.language_parameters.keys():
    print("Belief of {}: {}".format(parameter, gamix.language_parameters[parameter].beliefs))
    max_prob = 0
    max_value = ""
    for value in gamix.language_parameters[parameter].beliefs:
        if gamix.language_parameters[parameter].beliefs[value] > max_prob:
            max_value = value
            max_prob = gamix.language_parameters[parameter].beliefs[value]
    print("Consensus: {} with proba {}".format(max_value, max_prob))
