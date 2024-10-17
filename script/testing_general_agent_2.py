from libs import wals_utils as wu, grambank_utils as gu
from libs import agents


# gamix = agents.GeneralAgent("gamix",
#                                parameter_names=["Order of Subject, Object and Verb",
#                                                 "Order of Demonstrative and Noun",
#                                                 "Are there definite or specific articles?"],
#                                language_stat_filter={}, verbose=True)
#
# print("beliefs: ",gamix. get_beliefs())
# print("graph: ", gamix.graph)

gu.build_grambank_conditional_probability_table()