import json
from libs import utils
from libs import wals_utils as wu, grambank_utils as gu, grambank_wals_utils as gwu
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()  # only needed for Windows/pyinstaller safety
    wu.build_conditional_probability_table_multiprocessing()
