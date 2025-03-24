import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

# Load the data
with open("DIG4EL_truth_table.json", "r") as f:
    truth_table = json.load(f)

with open("../external_data/wals_derived/language_info_by_id_lookup_table.json", "r") as f:
    language_info_by_id = json.load(f)

print(f"Truth table contains {len(truth_table)} entries")
print(f"Language info contains {len(language_info_by_id)} entries")


# Helper function to determine if a value is numeric
def is_numeric(value):
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        # Check if string can be converted to a number
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


# Helper function to calculate score from truth table data
def calculate_score(data):
    if isinstance(data, dict):
        # Filter for numeric values only
        numeric_values = []
        for k, v in data.items():
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                pass
        return sum(numeric_values) / len(numeric_values) if numeric_values else None
    elif isinstance(data, list):
        # Filter for numeric values only
        numeric_values = []
        for v in data:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                pass
        return sum(numeric_values) / len(numeric_values) if numeric_values else None
    elif is_numeric(data):
        try:
            return float(data)
        except (ValueError, TypeError):
            return None
    return None


# Process each language
result_list = []

for lid, linfo in language_info_by_id.items():
    if "name" not in linfo or "family" not in linfo:
        continue  # Skip entries without necessary info

    # Convert family to string if it's not already
    if not isinstance(linfo["family"], str):
        linfo["family"] = str(linfo["family"])

    lang_name = linfo["name"]
    family = linfo["family"]

    # Try exact match first
    if lang_name in truth_table:
        data = truth_table[lang_name]
        score = calculate_score(data)
        match_type = "exact"
    else:
        # Try case-insensitive match
        found = False
        for truth_key in truth_table.keys():
            if truth_key.lower() == lang_name.lower():
                data = truth_table[truth_key]
                score = calculate_score(data)
                match_type = "case_insensitive"
                found = True
                break

        if not found:
            score = None
            match_type = "no_match"
    if family not in ["nan", "other"]:
        result_list.append({
            "id": lid,
            "name": lang_name,
            "family": family,
            "score": score,
            "match_type": match_type
        })

# Count languages and scores by family
family_counts = defaultdict(int)
family_with_scores = defaultdict(int)
family_scores = defaultdict(list)

for result in result_list:
    family = result["family"]
    family_counts[family] += 1

    if result["score"] is not None:
        family_with_scores[family] += 1
        family_scores[family].append(result["score"])

# Calculate average score per family
family_avg_scores = {}
for family, scores in family_scores.items():
    if scores:
        family_avg_scores[family] = sum(scores) / len(scores)

# Print summary statistics
print(f"\nTotal languages analyzed: {len(result_list)}")
print(f"Languages with scores: {sum(1 for r in result_list if r['score'] is not None)}")

# Print match type statistics
match_types = defaultdict(int)
for result in result_list:
    match_types[result["match_type"]] += 1

print("\nMatch type statistics:")
for match_type, count in match_types.items():
    print(f"  {match_type}: {count}")

# Print languages with scores (for debugging)
languages_with_scores = [r for r in result_list if r["score"] is not None]
print(f"\nLanguages with scores: {len(languages_with_scores)}")
print("\nSample of languages with scores (first 10):")
for lang in languages_with_scores[:10]:
    print(f"{lang['name']} ({lang['family']}): {lang['score']:.4f}")

# Print family distribution (by size)
print("\nLanguage distribution by family (top 15):")
for family, count in sorted(family_counts.items(), key=lambda x: (str(x[0]).lower(), -x[1])):
    with_scores = family_with_scores.get(family, 0)
    print(f"{family}: {count} languages ({with_scores} with scores)")

# Print average scores by family
print("\nAverage scores by language family:")
for family, avg_score in sorted(family_avg_scores.items(), key=lambda x: -x[1]):
    print(f"{family}: {avg_score:.4f} (based on {len(family_scores[family])} languages)")

# Create a plot of language family scores
if family_avg_scores:
    plt.figure(figsize=(14, 8))

    # Sort families by score
    families = [f for f, _ in sorted(family_avg_scores.items(), key=lambda x: -x[1])]
    scores = [family_avg_scores[f] for f in families]
    counts = [len(family_scores[f]) for f in families]

    # Ensure all values are strings for plotting
    families = [str(f) for f in families]

    # Create the plot - only if we have data
    if families and scores:
        bars = plt.bar(families, scores)

        # Add the count of languages on top of each bar
        for i, (bar, count) in enumerate(zip(bars, counts)):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                     f'n={count}', ha='center', va='bottom')

        plt.ylim(0, max(scores) * 1.2)
        plt.xticks(rotation=90)
        plt.xlabel('Language Family')
        plt.ylabel('Average Score')
        plt.title('Average Score by Language Family')
        plt.tight_layout()
        plt.savefig('language_family_scores.png')
        print("\nCreated chart: language_family_scores.png")

    # Create a bar chart showing coverage
    plt.figure(figsize=(14, 8))

    # Convert all family names to strings to avoid type comparison issues
    string_family_counts = {str(family): count for family, count in family_counts.items()}
    string_family_with_scores = {str(family): count for family, count in family_with_scores.items()}

    # Only include families with at least 3 languages
    coverage_data = []
    for family_str in string_family_counts.keys():
        if string_family_counts[family_str] >= 3:
            coverage = (string_family_with_scores.get(family_str, 0) / string_family_counts[family_str]) * 100
            coverage_data.append(
                (family_str, coverage, string_family_counts[family_str], string_family_with_scores.get(family_str, 0)))

    # Sort by coverage percentage
    coverage_data.sort(key=lambda x: -x[1])

    if coverage_data:
        families = [item[0] for item in coverage_data]
        coverage_values = [item[1] for item in coverage_data]

        bars = plt.bar(families, coverage_values)

        # Add counts on bars
        for i, bar in enumerate(bars):
            total = coverage_data[i][2]
            with_scores = coverage_data[i][3]
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                     f'{with_scores}/{total}', ha='center', va='bottom')

        plt.ylim(0, 105)
        plt.xticks(rotation=90)
        plt.xlabel('Language Family')
        plt.ylabel('Coverage (%)')
        plt.title('Language Family Coverage (% of Languages with Scores)')
        plt.tight_layout()
        plt.savefig('language_family_coverage.png')
        print("Created chart: language_family_coverage.png")

# Calculate the distribution of language families in the dataset
print("\nDistribution of language families in the dataset:")
total_languages = len(result_list)
family_percentages = {}

for family, count in sorted(family_counts.items(), key=lambda x: -x[1])[:20]:
    percentage = (count / total_languages) * 100
    family_percentages[family] = percentage
    print(f"{family}: {percentage:.2f}% ({count} languages)")

# Calculate overall coverage statistics
total_with_scores = sum(family_with_scores.values())
overall_coverage = (total_with_scores / total_languages) * 100
print(f"\nOverall coverage: {overall_coverage:.2f}% ({total_with_scores}/{total_languages} languages)")

# Create a family distribution plot
plt.figure(figsize=(14, 8))
top_families = sorted(family_percentages.items(), key=lambda x: -x[1])[:15]
family_names = [str(f[0]) for f in top_families]
family_percs = [f[1] for f in top_families]

bars = plt.bar(family_names, family_percs)
plt.xticks(rotation=90)
plt.xlabel('Language Family')
plt.ylabel('Percentage of Dataset (%)')
plt.title('Distribution of Top 15 Language Families in Dataset')
plt.tight_layout()
plt.savefig('language_family_distribution.png')
print("Created chart: language_family_distribution.png")

# Save results for further analysis
output_data = {
    "summary": {
        "total_languages": len(result_list),
        "languages_with_scores": len(languages_with_scores),
        "match_types": dict(match_types),
        "overall_coverage": overall_coverage
    },
    "family_stats": {
        str(family): {
            "count": family_counts[family],
            "with_scores": family_with_scores.get(family, 0),
            "average_score": family_avg_scores.get(family, None) if family in family_avg_scores else None,
            "coverage": (family_with_scores.get(family, 0) / family_counts[family]) * 100 if family_counts[
                                                                                                 family] > 0 else 0,
            "percentage_of_dataset": (family_counts[family] / total_languages) * 100
        }
        for family in family_counts
    },
    "languages": [
        {
            "id": r["id"],
            "name": r["name"],
            "family": r["family"],
            "score": r["score"],
            "match_type": r["match_type"]
        }
        for r in result_list
    ]
}

with open('language_analysis_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("\nSaved detailed results to language_analysis_results.json")