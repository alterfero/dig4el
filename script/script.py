import json
from libs import utils
from libs import wals_utils as wu
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

with open("../data/binary_truth_table_tmp.json", "r") as f:
    tt = json.load(f)
print(len(tt.keys()))
df = pd.DataFrame(tt)
plt.figure(figsize=(12, 30))
sns.heatmap(df.T)
plt.title('Truth table')
plt.tight_layout()
plt.savefig("../tmp_heatmap.png", format="png")
plt.show()
