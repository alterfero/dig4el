from libs import wals_utils as wu
from libs import agents

# wu.build_domain_elements_pk_by_parameter_pk_lookup_table_filtered()

# wu.build_language_pk_by_family_subfamily_genus_macroarea()

# wu.build_conditional_probability_table(filtered_params=True, language_filter={"family":["Algic"]})

# wu.build_conditional_probability_table_per_subfamily()

def test_general_agent():
    gawo = agents.GeneralAgent("gawo", "marquesan",
                               parameter_names=["Order of Subject, Object and Verb",
                                                "Order of Genitive and Noun",
                                                "Order of Demonstrative and Noun",
                                                "Order of Adjective and Noun",
                                                "Order of Numeral and Noun",
                                                "Order of Relative Clause and Noun",
                                                "The Position of Negative Morphemes in SVO Languages"],
                               language_stat_filter={})
    # parameter_name = "Order of Subject, Object and Verb"
    # observations = {'387': 0, '386': 0, '388': 0, '385': 8, '383': 2, '384': 0, '389': 0}
    # gawo.add_observations(parameter_name, observations)

    # injecting peak beliefs in simulated observed parameters
    print("Injecting beliefs")
    lid = "mrq"
    injection_list = ["Order of Genitive and Noun", "Order of Demonstrative and Noun"]
    for lp_name in gawo.language_parameters.keys():
        if lp_name in injection_list:
            print("Injecting in {}".format(lp_name))
            # this parameter is considered as observed. Finding its true value
            true_depk = wu.get_language_data_by_id(lid)[wu.parameter_pk_by_name[lp_name]]["domainelement_pk"]
            print("True value: {}".format(true_depk))
            gawo.language_parameters[lp_name].inject_peak_belief(true_depk, 0.6, locked=False)
            print("Beliefs of LP {} after injection: {}".format(lp_name, gawo.language_parameters[lp_name].beliefs))
            print("Beliefs history: {}".format(gawo.language_parameters[lp_name].beliefs_history))

    for i in range(5):
        print("               ")
        print("=========================================================================")
        print("======================= START OF BELIEF UPDATE CYCLE {} ================= ".format(i))
        print("=========================================================================")
        print("               ")
        gawo.run_belief_update_cycle()

    print("               ")
    print("=========================================================================")
    print("================================= RESULTS =============================== ".format(i))
    print("=========================================================================")
    print("               ")
    for parameter in gawo.language_parameters.keys():
        print("Belief of {}: {}".format(parameter, gawo.language_parameters[parameter].beliefs_history))
        max_prob = 0
        max_value = ""
        for value in gawo.language_parameters[parameter].beliefs:
            if gawo.language_parameters[parameter].beliefs[value] > max_prob:
                max_value = value
                max_prob = gawo.language_parameters[parameter].beliefs[value]
        print("Consensus: {} with proba {}".format(max_value, max_prob))



test_general_agent()
