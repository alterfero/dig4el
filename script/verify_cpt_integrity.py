import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm

def verify_square_table_integrity(filepath):
    with open(filepath, "r", encoding='utf-8') as f:
        table = json.load(f)

    keys = set(table.keys())
    success = True

    for row_key in keys:
        row = table[row_key]

        if not isinstance(row, dict):
            print(f"[ERROR] Row '{row_key}' is not a dictionary.")
            success = False
            continue

        missing_columns = keys - set(row.keys())
        extra_columns = set(row.keys()) - keys

        if missing_columns:
            print(f"[ERROR] Row '{row_key}' is missing columns: {sorted(missing_columns)}")
            success = False
        if extra_columns:
            print(f"[ERROR] Row '{row_key}' contains unexpected columns: {sorted(extra_columns)}")
            success = False

        for col_key, val in row.items():
            if val is not None and not isinstance(val, (int, float)):
                print(f"[ERROR] Invalid value at ({row_key}, {col_key}): {val}")
                success = False

    all_columns = {col for row in table.values() if isinstance(row, dict) for col in row}
    missing_top_keys = all_columns - keys
    if missing_top_keys:
        print(f"[ERROR] Some column keys are missing at top level: {sorted(missing_top_keys)}")
        success = False

    if success:
        print("✅ Integrity check passed.")
    else:
        print("❌ Integrity check failed.")

    return table

def visualize_table_colored(table):
    keys = sorted(table.keys(), key=int)
    size = len(keys)
    matrix = np.full((size, size), np.nan)

    key_to_idx = {key: idx for idx, key in enumerate(keys)}

    for i_key, row in table.items():
        for j_key, val in row.items():
            i, j = key_to_idx[i_key], key_to_idx[j_key]
            if val is not None:
                matrix[i, j] = val

    cmap = cm.get_cmap("coolwarm").copy()
    cmap.set_bad(color="black")

    plt.figure(figsize=(60, 60))
    img = plt.imshow(matrix, cmap=cmap, interpolation='nearest', norm=Normalize(vmin=0, vmax=1))
    plt.colorbar(img, label="Probability")
    plt.title("Square Table Visualization (Probabilities)")
    plt.xticks(ticks=np.arange(size), labels=keys, rotation=90)
    plt.yticks(ticks=np.arange(size), labels=keys)
    plt.xlabel("Columns")
    plt.ylabel("Rows")
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    filepath = "../external_data/wals_derived/de_conditional_probability_trust_df.json"
    table = verify_square_table_integrity(filepath)
    visualize_table_colored(table)
