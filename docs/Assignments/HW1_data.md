About the data: threatened species table
====

Background for [Homework 1](HW1). Read this before you start the tasks.

## The table

The file is a gzip-compressed, comma-separated table with one species per row and a header line. The columns are:

| # | column | # | column |
|---|--------|---|--------|
| 1 | taxonid | 8 | scientific_name |
| 2 | kingdom_name | 9 | taxonomic_authority |
| 3 | phylum_name | 10 | infra_rank |
| 4 | class_name | 11 | infra_name |
| 5 | order_name | 12 | population |
| 6 | family_name | 13 | category (IUCN status, e.g. `CR`, `EN`, `VU`) |
| 7 | genus_name | 14 | main_common_name |

Look at it first, before writing any code (`zcat file | head`, `zless`). Note that the file is compressed: use `zcat` (or `gzip -dc`) to read it, and never decompress it into your repository (it is ~18 MB uncompressed, and you should not commit data files).

## A warning about commas in the data

The file is comma-separated, but a few text fields themselves contain commas. When that happens the field is wrapped in double quotes so the comma is not a separator, for example (an illustrative row; the authority field is quoted):

```
...,Eugenia,Eugenia oreophila,"Smith, 2010",,,,LC,
```

`cut -d,` does not know about quotes: it splits `"Smith, 2010"` into two fields, and every column after it moves one to the right. Only 14 of the columns are *supposed* to exist, but about 80,000 of the rows contain a quote, so this matters. Columns 1-8 come before any quoted field and are always safe. Columns 9-14 (`taxonomic_authority`, `population`, `main_common_name`) can contain quoted text, so `cut -f13` for `category` will give wrong answers.

__The simple fix__: delete every quoted piece of text *before* you cut. The text inside quotes is never one of the fields you want to count here, and removing it leaves exactly 14 columns on every row.

```bash
# remove "...." (anything between a pair of double quotes), then split on commas as usual
zcat threatened-species.csv.gz | tail -n +2 | sed 's/"[^"]*"//g' | cut -d, -f13 | sort | uniq -c | sort -nr
```

Use `sed 's/"[^"]*"//g'` any time you need a column after column 8. (The only column this fix cannot be used to *read* is `main_common_name`, since its quoted values get deleted too.) Check it worked: after the `sed`, `awk -F, '{print NF}' | sort | uniq -c` should print a single line saying 14.
