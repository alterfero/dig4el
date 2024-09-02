from libs import wals_utils as wu
from libs import agents

# wu.build_domain_elements_pk_by_parameter_pk_lookup_table_filtered()

# wu.build_language_pk_by_family_subfamily_genus_macroarea()

# wu.build_conditional_probability_table(filtered_params=True, language_filter={"family":["Algic"]})

# wu.build_conditional_probability_table_per_subfamily()

def test_general_agent():
    gawo = agents.GeneralAgent("gawo", "marquesan",
                               parameter_names=["Order of Subject, Object and Verb"],
                               language_stat_filter={"family":["Austronesian"]})
    parameter_name = "Order of Subject, Object and Verb"
    observations = {'387': 0, '386': 0, '388': 0, '385': 8, '383': 2, '384': 0, '389': 0}
    gawo.update_beliefs_from_observations(parameter_name, observations, observation_influence=0.55)

test_general_agent()
