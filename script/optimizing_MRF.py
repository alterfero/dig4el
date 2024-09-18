import pickle
import os
import json
from libs import wals_utils as wu
from libs import prob_utils as pu
import seaborn as sns
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import numpy as np
from scipy.stats import norm
import math

with open("../external_data/wals_derived/parameter_pk_by_name_filtered.json", "rb") as f:
    parameter_pk_by_name = json.load(f)
    param_pk_list = [value for value in parameter_pk_by_name.values()]
param_name_by_pk = {}
for name, pk in parameter_pk_by_name.items():
    param_name_by_pk[str(pk)] = name

def build_mutual_information_between_params_df():

    midf = pu.create_mutual_information_df(param_pk_list)
    plt.figure(figsize=(24, 20))
    sns.heatmap(midf, cmap='viridis', square=True)
    plt.title('Maximal Potential Value Between Parameters')
    plt.tight_layout()
    plt.savefig("./heatmap.png", format="png")
    plt.show()
    return midf

def analyze_mutual_information_between_params_df():
    with open("../data/mutual_information_between_parameters_df.pkl", "rb") as f:
        midf = pickle.load(f)
    #midf = build_mutual_information_df()
    unstacked = midf.unstack()
    sorted_series = unstacked.sort_values(ascending=False)
    mean = sorted_series.mean()
    std = sorted_series.std()

    plt.figure(figsize=(20, 12))
    sns.histplot(sorted_series, kde=True, bins=100, stat="density", color='blue', label='Data')
    x = np.linspace(sorted_series.min(), sorted_series.max(), 100)
    plt.plot(x, norm.pdf(x, mean, std), color='red', label='Gaussian fit')
    plt.title('Density and Gaussian Fit')
    plt.xlabel('Values')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig("./density_of_mutual_information.png", format="png")
    plt.show()
    c = 0
    for index, value in sorted_series.items():
        if index[0] > index[1]:
            c += 1
            print("Rank {}: {}  <======>  {} ({})".format(c, param_name_by_pk[str(index[0])], param_name_by_pk[str(index[1])], value))
        if c>100:
            break

def analyze_cp_between_values():
    de_cpt = pd.read_json("../external_data/wals_derived/de_conditional_probability_df.json")
    plt.figure(figsize=(24, 20))
    sns.heatmap(de_cpt, cmap='viridis', square=True)
    plt.title('Conditional Probabilities between values')
    plt.tight_layout()
    plt.savefig("./de_cpt_heatmap.png", format="png")
    plt.show()

    unstacked = de_cpt.unstack()
    sorted_series = unstacked.sort_values(ascending=False)
    mean = sorted_series.mean()
    std = sorted_series.std()
    sns.histplot(sorted_series, kde=True, bins=100, stat="density", color='blue', label='Data')
    x = np.linspace(sorted_series.min(), sorted_series.max(), 100)
    plt.plot(x, norm.pdf(x, mean, std), color='red', label='Gaussian fit')
    plt.title('Density and Gaussian Fit')
    plt.xlabel('Values')
    plt.ylabel('Density')
    plt.legend()
    plt.savefig("./density_of_conditional_probabilities.png", format="png")
    plt.show()

def create_inference_graph_from_cpt_and_known_values():
    de_cpt = pd.read_json("../external_data/wals_derived/de_conditional_probability_df.json")
    starting_de = [386]
    threshold = 0.1
    inference_graph = pu.inference_graph_from_cpt_with_belief_propagation(de_cpt, starting_de, threshold)
    return inference_graph
def build_param_de_pk_tree():
    def get_careful_name_of_de_pk(depk, domain_element_by_pk):
        info = domain_element_by_pk[str(depk)]
        if "name" in info.keys():
            if info["name"] != "":
                return info["name"]
        elif "description" in info.keys():
            if info["description"] != "":
                return info["description"]
        else:
            return (str(depk) + "_no_name")
    with open("../external_data/wals_derived/parameter_pk_by_name_filtered.json", "rb") as f:
        parameter_pk_by_name = json.load(f)
    with open("../external_data/wals_derived/domain_element_by_pk_lookup_table.json", "rb") as f:
        domain_element_by_pk = json.load(f)
    with open("../external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json", "rb") as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    param_de_pk_tree = {}
    for pname, ppk in parameter_pk_by_name.items():
        param_de_pk_tree[str(ppk)] = {"name": pname, "de":{}}
        depks = domain_elements_pk_by_parameter_pk[str(ppk)]
        for depk in depks:
            de_name = str(get_careful_name_of_de_pk(depk, domain_element_by_pk))
            if de_name.lower() == "nan":
                de_name = str(depk)+"_element"
            param_de_pk_tree[str(ppk)]["de"][str(depk)] = {"name":de_name, "children":{}}
    with open("../external_data/wals_derived/param_de_tree.json", "w") as fi:
        json.dump(param_de_pk_tree, fi, indent=4)
    return param_de_pk_tree

ig = create_inference_graph_from_cpt_and_known_values()
print(ig)