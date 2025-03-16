import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# Load the data
with open('DIG4EL_truth_table.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Convert the data to a DataFrame for easier manipulation
languages = []
param_values = []
for language, params in data.items():
    # Convert parameter values to integers (0 or 1)
    values = [int(params[param]) for param in params]
    languages.append(language)
    param_values.append(values)

# Create a DataFrame with languages as index and parameters as columns
param_names = list(data[list(data.keys())[0]].keys())
# Create shorter parameter names for better visualization
short_param_names = [
    "Obj-Obl-Verb",
    "Adp-NP",
    "AdvSub-Clause",
    "Obj-Verb/Adp-NP",
    "Obj-Verb/Rel-N",
    "Obj-Verb/Adj-N",
    "Gen-N",
    "Deg-Adj"
]
df = pd.DataFrame(param_values, index=languages, columns=param_names)

# Calculate success rates for each parameter
param_success_rates = df.mean().sort_values(ascending=False)
language_success_rates = df.mean(axis=1).sort_values(ascending=False)

# Create a summary text file with overall statistics
with open('inference_summary_stats.txt', 'w') as f:
    f.write("GRAMMATICAL PARAMETER INFERENCE ACCURACY SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Total languages analyzed: {len(languages)}\n")
    f.write(f"Total parameters: {len(param_names)}\n\n")
    f.write(f"Overall accuracy: {df.values.mean():.2%}\n\n")
    f.write("Parameter-wise accuracy:\n")
    for param, rate in param_success_rates.items():
        f.write(f"  - {param}: {rate:.2%}\n")
    f.write("\nTop 5 languages by accuracy:\n")
    for lang, rate in language_success_rates.head(5).items():
        f.write(f"  - {lang}: {rate:.2%}\n")
    f.write("\nBottom 5 languages by accuracy:\n")
    for lang, rate in language_success_rates.tail(5).items():
        f.write(f"  - {lang}: {rate:.2%}\n")

# Figure 1: Parameter Success Rates
plt.figure(figsize=(10, 6))
ax = plt.gca()
bars = sns.barplot(x=param_success_rates.index, y=param_success_rates.values,
                   color=sns.color_palette('viridis')[0], ax=ax)
ax.set_title('Parameter Inference Accuracy', fontsize=14, fontweight='bold')
ax.set_ylabel('Accuracy Rate', fontsize=12)
ax.set_ylim(0, 1)
ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7)  # Random guess baseline
ax.text(ax.get_xlim()[1], 0.5, 'Baseline', va='center', ha='right', color='red', fontsize=10)

# Add percentage labels
for i, p in enumerate(bars.patches):
    percentage = f'{param_success_rates.values[i]:.1%}'
    ax.annotate(percentage, (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=10)

# Set the tick positions first, then the labels
ax.set_xticks(range(len(short_param_names)))
ax.set_xticklabels(short_param_names, rotation=45, ha='right', fontsize=10)

plt.tight_layout()
plt.savefig('fig1_parameter_accuracy.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Top and Bottom Languages by Inference Success Rate
plt.figure(figsize=(12, 8))
ax = plt.gca()
n_display = 15  # Number of top/bottom languages to display

# Combine top and bottom performers
top_langs = language_success_rates.iloc[:n_display]
bottom_langs = language_success_rates.iloc[-n_display:]
combined = pd.concat([top_langs, bottom_langs])

# Create a DataFrame with a color column for hue
plot_df = pd.DataFrame({
    'Language': combined.index,
    'Accuracy': combined.values,
    'Category': ['Top'] * n_display + ['Bottom'] * n_display
})
bars = sns.barplot(x='Language', y='Accuracy', hue='Category',
                   palette={'Top': 'green', 'Bottom': 'red'},
                   data=plot_df, ax=ax, legend=False)

ax.set_title('Languages with Highest & Lowest Inference Accuracy', fontsize=14, fontweight='bold')
ax.set_ylabel('Accuracy Rate', fontsize=12)
ax.set_ylim(0, 1)
ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7)
plt.setp(ax.get_xticklabels(), rotation=90, ha='right', fontsize=10)

# Add percentage labels for languages
for i, p in enumerate(bars.patches):
    if i < len(combined):
        percentage = f'{plot_df.Accuracy.iloc[i]:.1%}'
        ax.annotate(percentage, (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=8)

# Add a legend
handles = [Patch(color='green', label='Top Performers'),
           Patch(color='red', label='Bottom Performers')]
ax.legend(handles=handles, loc='upper right')

plt.tight_layout()
plt.savefig('fig2_language_accuracy.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Heatmap of Inference Results
plt.figure(figsize=(14, 10))
ax = plt.gca()
# Sort languages by success rate
sorted_df = df.loc[language_success_rates.index]
# Take top 50 and bottom 50 languages (or all if less than 100)
n_langs = min(100, len(sorted_df))
if n_langs == 100:
    display_df = pd.concat([sorted_df.iloc[:50], sorted_df.iloc[-50:]])
else:
    display_df = sorted_df

# Create the heatmap
hm = sns.heatmap(display_df, cmap=['#ffcccc', '#99ff99'], cbar=False, ax=ax)
ax.set_title('Inference Results by Language and Parameter', fontsize=14, fontweight='bold')
plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
plt.setp(ax.get_yticklabels(), fontsize=8)
ax.set_xticklabels(short_param_names)

# Add a custom legend
legend_elements = [
    Patch(facecolor='#99ff99', label='Correct Inference (1)'),
    Patch(facecolor='#ffcccc', label='Failed Inference (0)')
]
ax.legend(handles=legend_elements, loc='upper right', frameon=True)

plt.tight_layout()
plt.savefig('fig3_inference_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Confusion Matrix across Parameters
plt.figure(figsize=(10, 8))
ax = plt.gca()
# Create a confusion-like matrix showing parameter co-inference success/failure
confusion = np.zeros((len(param_names), len(param_names)))
for i in range(len(param_names)):
    for j in range(len(param_names)):
        # Both correctly inferred
        both_correct = ((df[param_names[i]] == 1) & (df[param_names[j]] == 1)).sum() / len(df)
        # Both incorrectly inferred
        both_incorrect = ((df[param_names[i]] == 0) & (df[param_names[j]] == 0)).sum() / len(df)
        # One correct, one incorrect
        mixed = 1 - both_correct - both_incorrect

        # Assign a value that shows correlation in inference success/failure
        # High value = often both correct or both incorrect
        # Low value = often mixed results
        confusion[i, j] = both_correct + both_incorrect

sns.heatmap(confusion, annot=True, cmap='YlGnBu', fmt='.2f',
            xticklabels=short_param_names, yticklabels=short_param_names, ax=ax)
ax.set_title('Parameter Co-inference Patterns', fontsize=14, fontweight='bold')
plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
plt.setp(ax.get_yticklabels(), rotation=0, fontsize=10)

plt.tight_layout()
plt.savefig('fig4_parameter_copatterns.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 5: Overall Accuracy Distribution
plt.figure(figsize=(10, 6))
ax = plt.gca()

# Create manually defined bins to ensure alignment with tick marks
# Create 10 bins from 0 to 1
bin_edges = np.linspace(0, 1, 11)  # 11 edges for 10 bins

# Calculate distribution of accuracy scores across languages
hist = plt.hist(language_success_rates.values, bins=bin_edges,
                alpha=0.75, color=sns.color_palette('viridis')[0], edgecolor='black')

# Add a KDE curve
density = sns.kdeplot(x=language_success_rates.values, ax=ax, color='darkblue', linewidth=2)

ax.set_title('Distribution of Inference Accuracy Across Languages', fontsize=14, fontweight='bold')
ax.set_xlabel('Accuracy Rate', fontsize=12)
ax.set_ylabel('Number of Languages', fontsize=12)

# Set the x-ticks to match bin edges
ax.set_xticks(bin_edges)
ax.set_xticklabels([f'{x:.1f}' for x in bin_edges])

# Add mean line
mean_acc = language_success_rates.mean()
ax.axvline(x=mean_acc, color='red', linestyle='--')
ax.text(mean_acc, ax.get_ylim()[1] * 0.9, f'Mean: {mean_acc:.2f}',
        color='red', ha='right', fontsize=11)

# Add counts on top of bars
for i in range(len(hist[0])):
    plt.text(hist[1][i] + (hist[1][i + 1] - hist[1][i]) / 2, hist[0][i] + 0.5,
             int(hist[0][i]), ha='center', va='bottom', fontsize=10)

plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('fig5_accuracy_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a separate text file listing languages in each bin
with open('languages_by_accuracy_bin.txt', 'w') as f:
    f.write("LANGUAGES GROUPED BY INFERENCE ACCURACY HISTOGRAM BINS\n")
    f.write("=" * 60 + "\n\n")

    for i in range(len(bin_edges) - 1):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        bin_count = 0

        # Find languages in this bin
        bin_languages = []
        for lang, rate in language_success_rates.items():
            # Special handling for the last bin to include exact 1.0 values
            if i == len(bin_edges) - 2:  # Last bin
                if bin_start <= rate <= bin_end:  # Use <= for upper bound
                    bin_languages.append((lang, rate))
                    bin_count += 1
            else:
                if bin_start <= rate < bin_end:
                    bin_languages.append((lang, rate))
                    bin_count += 1

        # Sort languages by accuracy rate (descending), then by name
        bin_languages.sort(key=lambda x: (-x[1], x[0]))

        # Write bin header
        f.write(f"Bin {i + 1}: Accuracy {bin_start:.1f} to {bin_end:.1f} ({bin_count} languages)\n")
        f.write("-" * 60 + "\n")

        if bin_languages:
            # Format in columns for better readability
            for j, (lang, rate) in enumerate(bin_languages):
                f.write(f"{j + 1:3d}. {lang:<25} {rate:.2%}\n")
        else:
            f.write("No languages in this bin.\n")

        f.write("\n")

    # Add a summary section
    f.write("\nSUMMARY STATISTICS\n")
    f.write("-" * 60 + "\n")
    f.write(f"Total languages: {len(languages)}\n")
    f.write(f"Average accuracy: {language_success_rates.mean():.2%}\n")
    f.write(f"Median accuracy: {language_success_rates.median():.2%}\n")
    f.write(f"Standard deviation: {language_success_rates.std():.2%}\n")
    f.write(f"Highest accuracy: {language_success_rates.max():.2%} ({language_success_rates.idxmax()})\n")
    f.write(f"Lowest accuracy: {language_success_rates.min():.2%} ({language_success_rates.idxmin()})\n")

    # Add list of languages with 100% accuracy
    perfect_langs = [lang for lang, rate in language_success_rates.items() if rate == 1.0]
    if perfect_langs:
        f.write("\nLanguages with 100% accuracy:\n")
        for i, lang in enumerate(sorted(perfect_langs)):
            f.write(f"{i + 1}. {lang}\n")

print(
    "Created languages_by_accuracy_bin.txt with languages listed by histogram bin, including those with 100% accuracy.")

# Figure 6: Success Rate by Parameter Count (Correlation)
plt.figure(figsize=(8, 6))
ax = plt.gca()

# Calculate the number of parameters successfully inferred for each language
df['success_count'] = df.sum(axis=1)
df['success_rate'] = df.mean(axis=1)

# Create scatter plot
scatter = sns.regplot(x='success_count', y='success_rate', data=df, scatter_kws={'alpha': 0.5}, ax=ax)
ax.set_title('Relationship Between Parameter Count and Success Rate', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Successfully Inferred Parameters', fontsize=12)
ax.set_ylabel('Success Rate', fontsize=12)
ax.set_ylim(0, 1)
ax.grid(alpha=0.3)

# Calculate correlation
corr = df['success_count'].corr(df['success_rate'])
ax.text(0.05, 0.95, f'Correlation: {corr:.2f}', transform=ax.transAxes,
        fontsize=12, va='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('fig6_count_vs_rate.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualization complete! Six separate figures have been saved:")
print("1. fig1_parameter_accuracy.png - Accuracy rates by parameter")
print("2. fig2_language_accuracy.png - Top and bottom languages by accuracy")
print("3. fig3_inference_heatmap.png - Heatmap of all inference results")
print("4. fig4_parameter_copatterns.png - Co-inference patterns between parameters")
print("5. fig5_accuracy_distribution.png - Distribution of accuracy across languages")
print("6. fig6_count_vs_rate.png - Relationship between success count and rate")
print("Additionally, a summary statistics file has been created: inference_summary_stats.txt")