#!/usr/bin/env python3
"""Workshop problem 3: count species per kingdom, genus and category."""
import csv
import gzip
from collections import Counter, defaultdict

datafile = "threatened-species.csv.gz"
threatened = {"CR", "EN", "VU"}

# 1. why we need the csv module: count lines that do not split into 14 fields
bad_lines = 0
with gzip.open(datafile, "rt") as fh:
    for line in fh:
        if len(line.rstrip("\n").split(",")) != 14:
            bad_lines += 1
print("lines that split(',') gets wrong:", bad_lines)

kingdoms = Counter()
species_in_genus = defaultdict(set)      # genus -> set of species names
fungal_categories = Counter()
threatened_fungi = Counter()             # genus -> number of threatened rows

with gzip.open(datafile, "rt", newline="") as fh:
    for row in csv.DictReader(fh):
        kingdoms[row["kingdom_name"]] += 1
        species_in_genus[row["genus_name"]].add(row["scientific_name"])
        if row["kingdom_name"] == "FUNGI":
            fungal_categories[row["category"]] += 1
            if row["category"] in threatened:
                threatened_fungi[row["genus_name"]] += 1

# 2. rows per kingdom
print("\nRows per kingdom:")
for kingdom, n in kingdoms.most_common():
    print(f"{kingdom}\t{n}")

# 3. genera with the most distinct species names
print("\nGenera with the most species:")
genus_sizes = {genus: len(names) for genus, names in species_in_genus.items()}
ranked = sorted(genus_sizes.items(), key=lambda pair: pair[1], reverse=True)
for genus, n in ranked[:10]:
    print(f"{genus}\t{n}")

# 4. fungi
print("\nFungi by Red List category:")
for category, n in fungal_categories.most_common():
    print(f"{category}\t{n}")
print("\nFungal genera with the most threatened (CR/EN/VU) species:")
for genus, n in threatened_fungi.most_common(5):
    print(f"{genus}\t{n}")
