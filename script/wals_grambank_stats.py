import json
import pandas as pd
import os
from matplotlib_venn import venn2
import matplotlib.pyplot as plt

with open("/Users/sebastienchristian/Desktop/d/01-These/Engine/v1/external_data/wals-master/cldf/languages.csv", "r") as fw:
    lw = pd.read_csv(fw)

with open("/Users/sebastienchristian/Desktop/d/01-These/Engine/v1/external_data/grambank-1.0.3/cldf/languages.csv", "r") as fg:
    lg = pd.read_csv(fg)

# NORMALIZE

# --- WALS ---
lw_norm = lw.rename(columns={
    "Family": "Family_name"
})

lw_norm = lw_norm[[
    "Name",
    "Glottocode",
    "ISO639P3code",
    "Macroarea",
    "Family_name"
]].copy()

lw_norm["Source"] = "WALS"


# --- Grambank ---
lg_norm = lg.rename(columns={
    "Family_name": "Family_name"
})

lg_norm = lg_norm[[
    "Name",
    "Glottocode",
    "ISO639P3code",
    "Macroarea",
    "Family_name"
]].copy()

lg_norm["Source"] = "Grambank"

# DROP ROWS WITHOUT GLOTTOCODE

lw_norm = lw_norm.dropna(subset=["Glottocode"])
lg_norm = lg_norm.dropna(subset=["Glottocode"])

# OVERLAP

wals_gl = set(lw_norm["Glottocode"])
gram_gl = set(lg_norm["Glottocode"])

common = wals_gl & gram_gl
wals_only = wals_gl - gram_gl
gram_only = gram_gl - wals_gl

print("WALS:", len(wals_gl))
print("Grambank:", len(gram_gl))
print("Common:", len(common))
print("WALS only:", len(wals_only))
print("Grambank only:", len(gram_only))
print("Total union:", len(wals_gl | gram_gl))

# UNIFIED TABLE FOR FAMILY/MACROAREA ANALYSIS

combined = pd.concat([lw_norm, lg_norm], ignore_index=True)

def overlap_status(gl):
    if gl in common:
        return "Both"
    elif gl in wals_only:
        return "WALS only"
    else:
        return "Grambank only"

combined["Overlap"] = combined["Glottocode"].apply(overlap_status)

# FAMILIES

family_counts = (
    combined.groupby(["Family_name", "Overlap"])
    .size()
    .unstack(fill_value=0)
    .sort_values("Both", ascending=False)
)

print(family_counts.head(20))

# VISUALS

from matplotlib_venn import venn2
import matplotlib.pyplot as plt

plt.figure()
venn2(
    subsets=(len(wals_only), len(gram_only), len(common)),
    set_labels=("WALS", "Grambank")
)
plt.title("Language Coverage Overlap (Glottocode-based)")
plt.show()

macro_counts = (
    combined.groupby(["Macroarea", "Overlap"])
    .size()
    .unstack(fill_value=0)
)

macro_counts.plot(kind="bar")
plt.ylabel("Number of Languages")
plt.title("Macroarea Representation by Database")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()