from __future__ import annotations
import json
import os
import pandas as pd
import re
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from libs import general_agents
from libs import wals_utils as wu
from libs.utils import generate_hash_from_list
from scipy.stats import gaussian_kde, bootstrap
from matplotlib.patches import Patch

# Language ids used for testing. These are all the 116 languages in WALS with data for the 15 parameters
# pertaining to canonical word orders. This filtering is performed in Testing_general_agents.py
experimental_candidates_lids = ["abk", "ace", "adi", "ame", "arg", "obo", "aeg", "anj", "may", "bto", "bud", "baw", "bkr",
                "bul", "ccm", "nko", "cct", "chv", "tin", "cle", "cpl", "chr", "coo", "cso", "wel", "dsh",
                "ger", "din", "ndy", "est", "eng", "bsq", "fij", "fin", "fre", "fua", "fut", "krb", "gae",
                "gmw", "orh", "hai", "hau", "htc", "arm", "arw", "iaa", "iba", "ind", "jpn", "jng", "kmj",
                "abu", "khs", "kch", "kmh", "klm", "awt", "kwo", "knr", "kos", "tla", "kis", "ksg", "krr",
                "lug", "lmp", "lmn", "lon", "mlu", "mad", "mxo", "mxc", "mxp", "min", "tab", "mmn", "mau",
                "mng", "mao", "brm", "kho", "nav", "ngz", "nht", "nun", "otm", "tsh", "pal", "poh", "qim",
                "rot", "sdw", "san", "ngm", "spa", "sul", "mup", "svs", "swe",
                "twe", "tml", "ttn", "tgk", "tha", "len", "tsi", "tur", "tzu", "ung", "wal", "wol", "wlf",
                "sio", "cnt", "yur"]


# INFERENTIAL PROCESS =======================================================================================
# Languages from experimental_candidates_lids are excluded one by one, and a CPT created without it, then
# the system runs 10 epochs of inferences.

def process_excluded_language(excluded_lid: str):
    print("LEAVE ONE OUT: {}".format(excluded_lid))
    excluded_lids = [excluded_lid]
    experimental_lids = [lid for lid in experimental_candidates_lids
                         if lid not in excluded_lids]

    excluded_pks = [wu.language_pk_by_id.get(lid, None)
                    for lid in excluded_lids]
    excluded_pks = [item for item in excluded_pks if item is not None]
    if len(excluded_pks) != len(excluded_lids):
        print("!! some language ids did not get a language pk")

    # Parameters considered observed
    obs = {
      "Order of Subject, Object and Verb": 81,
      "Order of Subject and Verb": 82,
      "Order of Object and Verb": 83,
      "Order of Adjective and Noun": 87,
      "Order of Demonstrative and Noun": 88,
      "Order of Numeral and Noun": 89,
      "Order of Relative Clause and Noun": 90
    }
    obs_pk_list = [str(v) for v in obs.values()]

    # Parameters to infer
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
    nobs_pk_list = [str(v) for v in nobs.values()]


    # CREATE OR LOAD CONDITIONAL PROBABILITY TABLE ============================================================
    # Either load if existing or create and save a conditional probability table without the excluded languages.
    # if existing, the file is in ../external_data/wals_derived/partial_cpt/
    # filemame is "de_conditional_probability_df_new_" + u.generate_hash_from_list(excluded_lids) + ".json"
    # we use the 16 first characters of a hash as a unique short encoder of the excluded languages.

    if not os.path.exists("../external_data/wals_derived/partial_cpt/"):
        os.makedirs("../external_data/wals_derived/partial_cpt/")
    hash_value = generate_hash_from_list(excluded_lids)
    cpt_filename = f"../external_data/wals_derived/partial_cpt/de_conditional_probability_languages_excluded_hash_{hash_value}.json"
    if os.path.exists(cpt_filename):
        print(f"Loading existing conditional probability table from {cpt_filename}")
    else:
        print(f"Creating new conditional probability table with {excluded_lid} excluded, saving to {cpt_filename}")
        # Build the conditional probability table excluding the specified languages
        cpt_filename = wu.build_conditional_probability_table(exclude_lids=excluded_lids)

    CPT = pd.read_json(cpt_filename)
    CPT.index = CPT.index.astype(str)
    CPT.columns = CPT.columns.astype(str)
    print("CPT loaded")

    ga_param_name_list = list(obs.keys()) + list(nobs.keys())

    # Running max_epoch number of test across all languages
    for epoch in range(1, 30):
        # GA CREATION =========================================================================================
        # excluded languages not used to build priors
        ga = general_agents.GeneralAgent("experimental GA",
                             parameter_names=ga_param_name_list,
                             language_stat_filter={
                                 "exclusion_list": excluded_pks  # experimental languages excluded from priors
                             },
                             active_wals_cpt=CPT)  # using a CPT that does not use experimental languages

        # ITERATING OVER TEST LANGUAGES
        general_result_dict = {}
        c = 0
        for lid in excluded_lids:
            c += 1
            lname = wu.language_info_by_id[lid]["name"]
            print("language: {}, {}/{}".format(lname, c, len(experimental_lids)))
            general_result_dict[lname] = {}

            # priors
            ga.reset_language_parameters_beliefs_with_wals()

            # simulated observations
            for lp_name in ga.language_parameters.keys():
                if lp_name in obs.keys():
                    # this parameter is considered as observed with a probability of 1.
                    # finding the true value
                    language_data = wu.get_wals_language_data_by_id_or_name(lid)
                    ppk = int(wu.parameter_pk_by_name[lp_name])
                    true_depk = language_data[ppk]["domainelement_pk"]
                    # injecting it
                    ga.language_parameters[lp_name].inject_peak_belief(true_depk,
                                                                       1,
                                                                       locked=True)
            # belief propagation
            for i in range(3):
                ga.run_belief_update_cycle()

            # record score
            evaluation = {"success": 0, "failure": 0}
            for upn in nobs.keys():
                general_result_dict[lname][upn] = {}
                expected_value = wu.get_wals_language_data_by_id_or_name(lid)[int(wu.parameter_pk_by_name[upn])][
                    "domainelement_pk"]
                current_consensus = max(ga.language_parameters[upn].beliefs,
                                        key=ga.language_parameters[upn].beliefs.get)

                general_result_dict[lname][upn]["expected"] = wu.get_careful_name_of_de_pk(str(expected_value))
                general_result_dict[lname][upn]["consensus"] = wu.get_careful_name_of_de_pk(str(current_consensus))

                if str(expected_value) == str(current_consensus):
                    evaluation["success"] += 1
                    general_result_dict[lname][upn]["success"] = True
                else:
                    evaluation["failure"] += 1
                    general_result_dict[lname][upn]["success"] = False

            if (evaluation["success"] + evaluation["failure"]) != 0:
                score = evaluation["success"] / (evaluation["success"] + evaluation["failure"])
            else:
                score = 0

            general_result_dict[lname]["score_percent"] = round(score * 100, 0)

        # format results across languages

        average_score = 0
        truth_table = {}
        binary_truth_table = {}
        scoring_table = {}
        for language in general_result_dict.keys():
          truth_table[language] = {}
          binary_truth_table[language] = {}
          scoring_table[language] = {}
          scoring_table[language]["score"] = general_result_dict[language]["score_percent"]
          average_score += general_result_dict[language]["score_percent"]
          for upn in general_result_dict[language].keys():
            if upn != "score_percent":
              if general_result_dict[language][upn]["success"]:
                truth_table[language][upn] = "1"
                binary_truth_table[language][upn] = 1
              else:
                truth_table[language][upn] = "0"
                binary_truth_table[language][upn] = 0
        average_score = average_score / len(general_result_dict)

        with open("../test_results/truth_table_{}_excluded_epoch_{}.json".format(excluded_lid, epoch), "w") as f:
            json.dump(truth_table, f, ensure_ascii=False)

# RESULT ANALYSIS =======================================================================================
def analyze_results():
    RESULT_DIR = Path("../test_results").resolve()
    PATTERN = re.compile(r"truth_table_(?P<code>[A-Za-z]{3})_excluded_epoch_(?P<epoch>\d+)")


    def parse_result_file(fp: Path) -> list[dict]:
        """Return a list of dicts (one per parameter) for the file `fp`."""
        match = PATTERN.match(fp.name)
        if not match:
            raise ValueError(f"Unexpected filename: {fp.name}")
        lang_code = match["code"]
        epoch = int(match["epoch"])

        with fp.open("r", encoding="utf‑8") as f:
            data = json.load(f)

        if len(data) != 1:
            raise ValueError(f"{fp}: Expected exactly one language record.")
        lang_name, param_dict = next(iter(data.items()))

        rows = []
        for param, correct in param_dict.items():
            rows.append(
                {
                    "language_code": lang_code,
                    "language_name": lang_name,
                    "epoch": epoch,
                    "parameter": param,
                    "correct": int(correct),  # ensure 0/1
                }
            )
        return rows


    # -----------------------------------------------------------------------------
    # Ingest
    # -----------------------------------------------------------------------------
    records = []
    for file in RESULT_DIR.glob("truth_table_*_excluded_epoch_*"):
        records.extend(parse_result_file(file))

    df = pd.DataFrame.from_records(records)
    if df.empty:
        raise SystemExit("No data found – check RESULT_DIR pattern.")

    # -----------------------------------------------------------------------------
    # Derived metrics
    # -----------------------------------------------------------------------------
    # Accuracy per (language, epoch) run
    run_acc = (
        df.groupby(["language_code", "epoch"], sort=False)["correct"]
        .mean()
        .rename("run_accuracy")
        .reset_index()
    )

    run_acc2 = (
        df.groupby(["language_name", "epoch"], sort=False)["correct"]
        .mean()
        .rename("run_accuracy")
        .reset_index()
    )
    # Accuracy per language (across all epochs) using bootstrap CIs
    lang_records = []
    for name, grp in run_acc2.groupby("language_name", sort=False):
        vals = grp["run_accuracy"].to_numpy()
        ci = bootstrap((vals,), np.mean, confidence_level=0.95,
                       n_resamples=5000, method="percentile").confidence_interval
        lang_records.append(
            {
                "language_name": name,
                "mean": vals.mean(),
                "median": np.median(vals),
                "ci_lower": ci.low,
                "ci_upper": ci.high,
                "n_epochs": len(vals),
            }
        )
    lang_acc = (
        pd.DataFrame(lang_records)
        .sort_values("mean", ascending=False)
        .reset_index(drop=True)
    )

    # Accuracy per parameter (across languages × epochs)
    param_acc = (
        df.groupby("parameter", sort=False)["correct"]
        .agg(["median", "mean", "std", "min", "max", "count"])
        .reset_index()
        .rename(columns={"count": "n_observations"})
    )

    # -----------------------------------------------------------------------------
    # Export numeric summaries
    # -----------------------------------------------------------------------------
    SUMMARY_DIR = Path("../test_result_analysis/summaries")
    SUMMARY_DIR.mkdir(exist_ok=True)
    lang_acc.to_csv(SUMMARY_DIR / "per_language_accuracy.csv", index=False)
    param_acc.to_csv(SUMMARY_DIR / "per_parameter_accuracy.csv", index=False)
    run_acc.to_csv(SUMMARY_DIR / "per_run_accuracy.csv", index=False)


    # -----------------------------------------------------------------------------
    # Plotting helpers
    # -----------------------------------------------------------------------------
    def make_boxplot(
            data,
            labels,
            title: str,
            xlabel: str,
            ylabel: str,
            filename: Path,
            figsize=(9, 10),
            rotation=90,
            horizontal: bool = False,
    ):
        plt.figure(figsize=figsize)
        bp = plt.boxplot(
            data,
            labels=labels,
            showfliers=False,
            vert=not horizontal,
            patch_artist=True,
            boxprops=dict(facecolor="lightblue", color="black"),
            medianprops=dict(color="red"),
            whiskerprops=dict(color="black"),
            capprops=dict(color="black"),
        )
        plt.title(title, fontweight="bold")
        if horizontal:
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.yticks(rotation=rotation)
            plt.xlim(-0.05, 1.05)
            plt.grid(axis="x", alpha=0.3)
        else:
            plt.ylabel(ylabel)
            plt.xlabel(xlabel)
            plt.xticks(rotation=rotation)
            plt.ylim(-0.05, 1.05)
            plt.grid(axis="y", alpha=0.3)

        legend_elements = [
            Patch(facecolor="lightblue", edgecolor="black", label="IQR"),
            Line2D([0], [0], color="red", label="Median"),
            Line2D([0], [0], color="black", label="Whiskers"),
        ]
        plt.legend(handles=legend_elements, loc="lower right")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        plt.close()
        print(f"Saved {filename}")

    def make_errorbar_plot(
            df: pd.DataFrame,
            title: str,
            xlabel: str,
            ylabel: str,
            filename: Path,
            figsize=(9, 10),
            rotation=0,
            horizontal: bool = True,
    ):
        """Plot mean accuracy with bootstrap CI as error bars."""
        plt.figure(figsize=figsize)
        positions = np.arange(len(df))
        if horizontal:
            plt.errorbar(
                df["mean"],
                positions,
                xerr=[df["mean"] - df["ci_lower"], df["ci_upper"] - df["mean"]],
                fmt="o",
                color="black",
                ecolor="lightblue",
                capsize=3,
            )
            plt.yticks(positions, df["language_name"], rotation=rotation)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xlim(-0.05, 1.05)
            plt.grid(axis="x", alpha=0.3)
        else:
            plt.errorbar(
                positions,
                df["mean"],
                yerr=[df["mean"] - df["ci_lower"], df["ci_upper"] - df["mean"]],
                fmt="o",
                color="black",
                ecolor="lightblue",
                capsize=3,
            )
            plt.xticks(positions, df["language_name"], rotation=rotation)
            plt.ylabel(ylabel)
            plt.xlabel(xlabel)
            plt.ylim(-0.05, 1.05)
            plt.grid(axis="y", alpha=0.3)
        plt.title(title, fontweight="bold")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        plt.close()
        print(f"Saved {filename}")


    # -----------------------------------------------------------------------------

    # 1. Accuracy per language with bootstrap confidence intervals
    lang_acc_sorted = lang_acc.sort_values("mean", ascending=False)
    n = len(lang_acc_sorted)
    half = n // 2
    chunk1 = lang_acc_sorted.iloc[:half]
    chunk2 = lang_acc_sorted.iloc[half:]
    make_errorbar_plot(
        chunk1,
        title="",
        xlabel="Accuracy (0–1)",
        ylabel="Language",
        filename=Path("../test_result_analysis/accuracy_per_language_ci_chunk1.png"),
        rotation=0,
        horizontal=True,
    )
    make_errorbar_plot(
        chunk2,
        title="",
        xlabel="Accuracy (0–1)",
        ylabel="Language",
        filename=Path("../test_result_analysis/accuracy_per_language_ci_chunk2.png"),
        rotation=0,
        horizontal=True,
    )
    # -----------------------------------------------------------------------------
    # 2. Boxplot: accuracy distribution per parameter
    # -----------------------------------------------------------------------------
    param_order = param_acc.sort_values("median", ascending=False)["parameter"].tolist()
    box_data_param = [
        df.loc[df.parameter == p, "correct"].tolist() for p in param_order
    ]

    make_boxplot(
        box_data_param,
        param_order,
        title="Inference accuracy distribution per grammatical parameter",
        xlabel="Proportion correct",
        ylabel="Grammatical parameter",
        filename=Path("../test_result_analysis/accuracy_per_parameter_boxplot.png"),
        rotation=45,
    )

    # -----------------------------------------------------------------------------
    # 3. Boxplot: overall distribution of language‑median accuracies
    # -----------------------------------------------------------------------------
    make_boxplot(
        [lang_acc["median"].tolist()],
        ["all languages"],
        title="Distribution of median accuracy across languages",
        xlabel="Median accuracy",
        ylabel="",
        filename=Path("../test_result_analysis/language_median_accuracy_boxplot.png"),
        rotation=0,
        figsize=(4, 6),
    )

    # -----------------------------------------------------------------------------
    # 3. accuracy distribution bar plot
    # -----------------------------------------------------------------------------
    BIN_WIDTH = 0.05
    bins = np.arange(0, 1 + BIN_WIDTH, BIN_WIDTH)  # 0.00–1.00 in 0.05 steps

    values = run_acc.groupby("language_code")["run_accuracy"].mean().values
    mean_acc = values.mean()
    median_acc = np.median(values)
    q1, q3 = np.percentile(values, [25, 75])
    std = np.std(values)
    min_acc = np.min(values)
    max_acc = np.max(values)

    # Bootstrap 95% confidence interval for the median
    boot_medians = [
        np.median(np.random.choice(values, size=len(values), replace=True))
        for _ in range(5000)
    ]
    median_ci_lower, median_ci_upper = np.percentile(boot_medians, [2.5, 97.5])

    # KDE estimation for smooth trend
    kde = gaussian_kde(values, bw_method="scott")
    x_vals = np.linspace(0, 1, 500)
    y_vals = kde(x_vals)
    y_vals_scaled = y_vals * len(values) * BIN_WIDTH  # scale to match histogram counts

    # Bootstrap 95% confidence interval for the mean
    boot_means = [
        np.mean(np.random.choice(values, size=len(values), replace=True))
        for _ in range(5000)
    ]
    ci_lower, ci_upper = np.percentile(boot_means, [2.5, 97.5])

    # Plot
    plt.figure(figsize=(10, 6))

    # Histogram bars
    plt.hist(values, bins=bins, alpha=0.5, color="darkblue", edgecolor="gray", label="Number of languages")

    # KDE trend line
    #plt.plot(x_vals, y_vals_scaled, color="darkblue", linewidth=2, label="Smoothed trend (KDE)")

    # Mean and median vertical lines
    plt.axvline(mean_acc, color="orange", linestyle="--", linewidth=2, label=f"Mean = {mean_acc:.3f}")
    plt.axvline(median_acc, color="green", linestyle=":", linewidth=2, label=f"Median = {median_acc:.3f}")

    # Confidence interval whiskers
    plt.hlines(
        y=max(y_vals_scaled) * 0.9,
        xmin=ci_lower,
        xmax=ci_upper,
        color="orange",
        linewidth=3,
        label=f"95% CI for mean [{ci_lower:.3f}, {ci_upper:.3f}]",
    )
    plt.vlines(
        [ci_lower, ci_upper],
        ymin=0,
        ymax=max(y_vals_scaled) * 0.9,
        color="orange",
        linestyle=":",
        linewidth=1,
    )
    # Confidence interval whiskers for the median (horizontal line + vertical bars)
    y_median_ci = max(y_vals_scaled) * 0.8  # place below mean CI
    plt.hlines(
        y=y_median_ci,
        xmin=median_ci_lower,
        xmax=median_ci_upper,
        color="green",
        linewidth=3,
        label=f"95% CI for median [{median_ci_lower:.3f}, {median_ci_upper:.3f}]"
    )
    plt.vlines([median_ci_lower, median_ci_upper], ymin=0, ymax=y_median_ci, color="green", linestyle=":", linewidth=1)

    # Formatting
    plt.title("Distribution of leave-one-out test accuracies\nwith 95% Confidence Intervals for mean and median")
    plt.xlabel("Accuracy")
    plt.ylabel("Number of languages")
    plt.xlim(0, 1)
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()

    out_file = Path("../test_result_analysis/accuracy_distribution_barplot.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"Saved {out_file}")

    # -----------------------------------------------------------------------------
    # Save textual summary to file
    # -----------------------------------------------------------------------------
    summary_file = Path("../test_result_analysis/accuracy_summary.txt")

    with summary_file.open("w", encoding="utf-8") as f:
        f.write("Accuracy Summary (per-language average accuracy)\n")
        f.write("--------------------------------------------------\n")
        f.write(f"• Mean Accuracy: {mean_acc * 100:.1f}%\n")
        f.write(f"• Median Accuracy: {median_acc * 100:.1f}%\n")
        f.write(f"• Minimum–Maximum: {min_acc * 100:.1f}% to {max_acc * 100:.1f}%\n")
        f.write(f"• First Quartile (Q1): {q1 * 100:.1f}%\n")
        f.write(f"• Third Quartile (Q3): {q3 * 100:.1f}%\n")
        f.write(f"• Standard Deviation: {std * 100:.1f}%\n")
        f.write(f"• 95% Confidence Interval for Mean (Bootstrap): [{ci_lower * 100:.1f}%, {ci_upper * 100:.1f}%]\n")

    print(f"Saved {summary_file}")

    # -----------------------------------------------------------------------------
    # Quick textual report
    # -----------------------------------------------------------------------------
    print("\n=== GLOBAL SUMMARY ===")
    print(f"Languages analysed  : {lang_acc.shape[0]}")
    print(f"Total runs analysed : {run_acc.shape[0]}")
    print(f"Overall mean acc.   : {df['correct'].mean():.3f}")
    print(f"Language median IQR : "
          f"{lang_acc['median'].quantile(0.25):.2f}–"
          f"{lang_acc['median'].quantile(0.75):.2f}")

if __name__ == "__main__":
    from multiprocessing import Pool, cpu_count
    COMPUTE_RESULTS = True
    ANALYZE_RESULTS = True

    if COMPUTE_RESULTS:
        num_processes = min(cpu_count() - 1, len(experimental_candidates_lids))
        with Pool(num_processes) as pool:
            pool.map(process_excluded_language, experimental_candidates_lids)

    if ANALYZE_RESULTS:
        analyze_results()
