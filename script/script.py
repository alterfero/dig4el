import json
from libs import utils
from libs import wals_utils as wu, grambank_utils as gu
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

def wals_grambank_language_stats():
    wals_languages = list(wu.language_pk_id_by_name.keys())
    grambank_languages = [gu.grambank_language_by_lid[k]["name"] for k in gu.grambank_language_by_lid.keys()]
    full_list = (wals_languages + grambank_languages)
    lset = set(full_list)
    print(len(wals_languages), len(grambank_languages), len(lset))
    print(lset)

wals_grambank_language_stats()