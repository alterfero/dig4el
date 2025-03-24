import json
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load JSON data from a file (replace 'data.json' with your file path)
with open('language_analysis_results.json', 'r') as f:
    data = json.load(f)

# Extract relevant information
family_scores = []
for family, stats_data in data["family_stats"].items():
    if "average_score" in stats_data:
        family_scores.append({
            "family": family,
            "average_score": stats_data["average_score"],
            "with_scores": stats_data["with_scores"]
        })

# Convert to DataFrame
df = pd.DataFrame(family_scores)

# Remove NaN and infinite values
df = df.replace([np.inf, -np.inf], np.nan).dropna()

# Compute Descriptive Statistics
desc_stats = df.describe()
print("Descriptive Statistics:\n", desc_stats)

# Bootstrapping for confidence intervals
def bootstrap_ci(data, num_samples=1000, ci=95):
    boot_means = [np.mean(np.random.choice(data, size=len(data), replace=True)) for _ in range(num_samples)]
    lower = np.percentile(boot_means, (100 - ci) / 2)
    upper = np.percentile(boot_means, 100 - (100 - ci) / 2)
    return lower, upper

bootstrap_results = {fam: bootstrap_ci(df[df["family"] == fam]["average_score"].values) for fam in df["family"].unique()}
print("\nBootstrapped Confidence Intervals:")
for fam, (low, high) in bootstrap_results.items():
    print(f"{fam}: {low:.3f} - {high:.3f}")

# Compute pairwise effect sizes (Cohen's d)
def cohens_d(x, y):
    return (np.mean(x) - np.mean(y)) / np.sqrt((np.std(x, ddof=1) ** 2 + np.std(y, ddof=1) ** 2) / 2)

effect_sizes = {}
families = df["family"].unique()
for i in range(len(families)):
    for j in range(i + 1, len(families)):
        fam1, fam2 = families[i], families[j]
        x, y = df[df["family"] == fam1]["average_score"].values, df[df["family"] == fam2]["average_score"].values
        if len(x) > 1 and len(y) > 1:
            effect_sizes[(fam1, fam2)] = cohens_d(x, y)

print("\nPairwise Effect Sizes (Cohen's d):")
for (fam1, fam2), d in effect_sizes.items():
    print(f"{fam1} vs {fam2}: {d:.3f}")

# Visualization: Box Plot of Scores by Family
plt.figure(figsize=(10, 5))
sns.boxplot(x="family", y="average_score", data=df)
plt.xticks(rotation=45)
plt.title("Average Scores by Language Family")
plt.xlabel("Language Family")
plt.ylabel("Average Score")
plt.show()

# Visualization: Bar Chart of Scores with Number of Languages
plt.figure(figsize=(10, 5))
sns.barplot(x="family", y="average_score", hue="family", data=df, edgecolor="black", legend=False)
for index, row in df.iterrows():
    plt.text(index, row.average_score, f"{int(row.with_scores)}", ha='center', va='bottom', fontsize=10)
plt.xticks(rotation=45)
plt.title("Average Scores by Language Family with Number of Languages")
plt.xlabel("Language Family")
plt.ylabel("Average Score")
plt.show()
