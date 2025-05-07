import json
from libs import utils
from libs import wals_utils as wu, grambank_utils as gu, grambank_wals_utils as gwu
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

wpl = [p for p in wu.parameter_pk_by_name_filtered.keys()]
gbpl = [p for p in gu.grambank_pid_by_pname.keys()]
t = wpl + gbpl
with open("../external_data/all_params.json", "w") as f:
    json.dump(t, f)
