import json
from libs import utils
from libs import wals_utils as wu, grambank_utils as gu, grambank_wals_utils as gwu
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# with open("../data/binary_truth_table_tmp.json", "r") as f:
#     tt = json.load(f)
# print(len(tt.keys()))
# df = pd.DataFrame(tt)
# plt.figure(figsize=(12, 30))
# sns.heatmap(df.T)
# plt.title('Truth table')
# plt.tight_layout()
# plt.savefig("../tmp_heatmap.png", format="png")
# plt.show()

# gwu.build_wals_given_grambank_cpt_df()
# gwu.build_grambank_given_wals_cpt_df()

# print(gwu.compute_grambank_given_wals_cp("81","GB136"))
# print(gwu.compute_wals_given_grambank_cp("GB136", "81"))

#wu.build_conditional_probability_table(filtered_params=True, language_filter={})
gu.build_grambank_conditional_probability_table(language_filter={})