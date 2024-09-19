import pickle
from libs import wals_utils as wu
from collections import deque, defaultdict
import pandas as pd
import numpy as np
import json
import os

import pandas as pd
import numpy as np
import os


def create_mutual_information__between_parameters_df(parameters):
    parameters = sorted(parameters)
    potentials_folder = "../data/potentials/"
    """
    Creates a mutual information DataFrame for the given list of parameters.

    Parameters:
    - parameters: list of parameter names.
    - potentials_folder: string, path to the folder containing pickled potentials.
    - compute_potential_function_from_general_data: function, computes potential between two parameters.

    Returns:
    - mutual_info_df: pandas DataFrame containing mutual information between parameter pairs.
    """
    # Initialize the mutual information DataFrame
    mutual_info_df = pd.DataFrame(index=parameters, columns=parameters, dtype=float)

    # Precompute the list of existing potential files for quick lookup
    potential_files = set(f for f in os.listdir(potentials_folder) if f.endswith('.pkl'))

    # Iterate over all unique pairs of parameters
    for i, param_i in enumerate(parameters):
        for j, param_j in enumerate(parameters):
            if i <= j:
                # Construct the potential filename
                filename = f"{param_i}_{param_j}.pkl"
                filepath = os.path.join(potentials_folder, filename)
                reverse_filename = f"{param_j}_{param_i}.pkl"
                reverse_filepath = os.path.join(potentials_folder, reverse_filename)

                # Check if the potential file exists
                if filename in potential_files:
                    # Load the potential from the pickle file
                    potential_df = pd.read_pickle(filepath)
                elif reverse_filename in potential_files:
                    # Load the potential from the reverse pickle file
                    potential_df = pd.read_pickle(reverse_filepath)
                else:
                    # Potential file not found, compute it
                    print(f"Computing missing potential for {param_i} and {param_j}")
                    potential_df = wu.compute_potential_function_from_general_data(param_i, param_j)

                # Compute the mutual information
                try:
                    mi = compute_mutual_information_between_parameters_df(potential_df)
                    #mi = potential_df.max().max()
                except ValueError as e:
                    print(f"Error computing MI for {param_i} and {param_j}: {e}")
                    mi = np.nan
                # Store the mutual information in the DataFrame
                mutual_info_df.loc[param_i, param_j] = mi
                mutual_info_df.loc[param_j, param_i] = mi  # Symmetric entry
                print("mutual information {}-{}: {}".format(param_i, param_j, mi))

    with open("../data/mutual_information_between_parameters_df.pkl", "wb") as f:
        pickle.dump(mutual_info_df, f)

    return mutual_info_df


def compute_mutual_information_between_parameters_df(potential_df):
    """
    Computes the mutual information between two parameters using the potential DataFrame.

    Parameters:
    - potential_df: pandas DataFrame representing the potential between two parameters.

    Returns:
    - mutual_info: float, the mutual information value.
    """
    # Convert the potential DataFrame to a numpy array
    Phi_ij = potential_df.values.astype(float)

    # Ensure all potential values are non-negative
    if np.any(Phi_ij < 0):
        raise ValueError("Potentials must be non-negative.")

    # Sum of all potential values
    Z = np.sum(Phi_ij)
    if Z == 0:
        return 0.0

    # Normalize to get the joint probability distribution
    P_ij = Phi_ij / Z

    # Compute marginal distributions
    P_i = np.sum(P_ij, axis=1)  # Sum over columns for each row
    P_j = np.sum(P_ij, axis=0)  # Sum over rows for each column

    # Compute mutual information
    mutual_info = 0.0
    n_i, n_j = P_ij.shape
    for k in range(n_i):
        for l in range(n_j):
            P_ij_kl = P_ij[k, l]
            if P_ij_kl > 0:
                P_i_k = P_i[k]
                P_j_l = P_j[l]
                mutual_info += P_ij_kl * np.log2(P_ij_kl / (P_i_k * P_j_l))

    return mutual_info


def inference_graph_from_cpt_with_belief_propagation(df, starting_vars, threshold):
    # Step 1: Build the graph from the DataFrame
    graph = defaultdict(dict)
    variables = set(df.index).union(set(df.columns))

    for from_var in df.index:
        for to_var in df.columns:
            prob = df.at[from_var, to_var]
            if pd.notna(prob):
                graph[from_var][to_var] = prob

    # Step 2: Initialize beliefs
    belief = {var: 0 for var in variables}
    for var in starting_vars:
        belief[var] = 1  # Known variables have belief 1

    # Step 3: Initialize the queue with starting variables
    queue = deque(starting_vars)
    inference_graph = defaultdict(dict)

    # Step 4: Perform belief propagation
    while queue:
        vi = queue.popleft()
        for vj, prob in graph.get(vi, {}).items():
            if prob >= threshold:
                # Calculate the new belief
                mi_j = belief[vi] * prob
                #print("belief[vi] {} * prob {} = mi_j {}".format(belief[vi], prob, mi_j))
                if mi_j >= threshold and mi_j > belief.get(vj, 0):
                    #print("vi={}, vj={}".format(vi, vj))
                    #print("belief[vi] {} * prob {} = mi_j {}".format(belief[vi], prob, mi_j))
                    belief[vj] = mi_j
                    inference_graph[vi][vj] = mi_j
                    queue.append(vj)

    # Convert inference_graph to a regular dict for readability
    inference_graph = {k: dict(v) for k, v in inference_graph.items()}
    return inference_graph, belief
