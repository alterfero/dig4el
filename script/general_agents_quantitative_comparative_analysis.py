from __future__ import annotations
import csv
import json
from libs import general_agents
from libs import wals_utils as wu
import pandas as pd


"""
1) Load test results by language ("../test_result_analysis/summaries/per_language_accuracy.csv")
2) For each language, generate naive results based on what is expected for this language family:
    - Determine the family of this language.
    - Compute the expected value of each of the nobs parameter for that language.
    - Create a baseline_truth_table showing for which parameter these results are right or wrong.
    - Compute the accuracy of the baseline_truth_table. 
    - Compare this baseline_accuracy with the test results accuracy
"""


nobs = {
      "Order of Object, Oblique, and Verb": 84,
      "Order of Adposition and Noun Phrase": 85,
      "Order of Adverbial Subordinator and Clause": 94,
      "Relationship between the Order of Object and Verb and the Order of Adposition and Noun Phrase": 95,
      "Relationship between the Order of Object and Verb and the Order of Relative Clause and Noun": 96,
      "Relationship between the Order of Object and Verb and the Order of Adjective and Noun": 97,
      "Order of Genitive and Noun": 86,
      "Order of Degree Word and Adjective": 91
    }

# load test result
test_file_path = "../test_result_analysis/summaries/per_language_accuracy.csv"
with open(test_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    test_data = [row for row in reader]

def create_naive_vs_dig4el_accuracy_list(tested_language):
    language_name = tested_language["language_name"]
    print(language_name)
    language_test_mean_accuracy = tested_language["mean"]
    language_id = wu.language_pk_id_by_name[language_name]["id"]

    # use a general agent to compute statistical priors
    gaf = general_agents.GeneralAgent("baseline", parameter_names=[p for p in nobs.keys()],
                                      verbose=False)

    # naive accuracy
    naive_baseline_beliefs = gaf.get_beliefs()
    print(naive_baseline_beliefs)
    # compute accuracy of naive beliefs across test parameters
    naive_win_count = 0.0
    for lpn in gaf.language_parameters.keys():
        print(lpn)
        # naive depk pick
        naive_depk = max(naive_baseline_beliefs[lpn], key=naive_baseline_beliefs[lpn].get)
        print("naive pick: {}".format(naive_depk))
        # true value
        language_data = wu.get_wals_language_data_by_id_or_name(language_id)
        ppk = int(wu.parameter_pk_by_name[lpn])
        true_depk = language_data[ppk]["domainelement_pk"]
        print("true value: {}".format(true_depk))
        # accuracy
        if str(true_depk) == str(naive_depk):
            naive_win_count += 1.0
    naive_accuracy = naive_win_count/len(nobs)


    return {
            "language": language_name,
            "dig4el mean accuracy": language_test_mean_accuracy,
            "baseline accuracy": naive_accuracy,
        }

if __name__ == "__main__":
    COMPUTE = False
    ANALYZE = True
    if COMPUTE:
        from multiprocessing import Pool, cpu_count
        num_processes = min(cpu_count() - 1, len(test_data))
        #num_processes = 1
        with Pool(num_processes) as pool:
            out_list = pool.map(create_naive_vs_dig4el_accuracy_list, test_data)

        with open("../test_result_analysis/summaries/comparative_results_baseline_vs_dig4el.json", "w") as f:
            json.dump(out_list, f)
    if ANALYZE:
        with open("../test_result_analysis/summaries/comparative_results_baseline_vs_dig4el.json", "r") as f:
            results = json.load(f)

        df = pd.DataFrame(results)
        for col in ["dig4el mean accuracy", "baseline accuracy"]:
            df[col] = pd.to_numeric(df[col])
        stats = df[["dig4el mean accuracy", "baseline accuracy"]].describe()
        print(stats)

        import matplotlib.pyplot as plt

        plt.figure()
        df[["dig4el mean accuracy", "baseline accuracy"]].boxplot()
        plt.ylabel('Accuracy')
        plt.savefig('../test_result_analysis/accuracy_boxplot.png')
        plt.close()

        plt.figure()
        plt.scatter(df["baseline accuracy"], df["dig4el mean accuracy"], alpha=0.7)
        plt.plot([0, 1], [0, 1], '--', color='gray')  # Diagonal reference line
        plt.xlabel("Baseline Accuracy")
        plt.ylabel("DIG4EL Mean Accuracy")
        plt.savefig("../test_result_analysis/scatter_dig4el_vs_baseline.png")
        plt.close()










