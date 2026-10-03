UNIX practice
====

On the UNIX command line. Go into your bigdata folder. If you have not used the cluster before then you will be in the `gen220` project. Or you may have your own lab bigdata folder.

See [Text Editors in UNIX](https://hpcc.ucr.edu/manuals/linux_basics/text/)
While it takes a few steps to install and setup, [VisualStudio](https://code.visualstudio.com/download) is a great resource
you can edit on your local machine but saves changes on HPCC. See <https://hpcc.ucr.edu/manuals/hpc_cluster/selected_software/vscode/>

__This should work__

```bash
cd ~/bigdata
```

__but if it doesn't__

```bash
cd /bigdata/gen220/$USER # will go into your bigdata folder for the class
```

__But if you already had an account on the cluster then__

```bash
# if the above doesn't work you are likely already in a lab group on HPCC
cd /bigdata/$GROUP/$USER # should work since $USER is your login and $GROUP is your primary lab group
# you can see what groups you are in by typing
groups
```


For your homework:

1. Accept the homework 1 problem - (see link in Canvas). 
2. Make a folder for this class and go into it (`~/bigdata` already points to your class folder `/bigdata/gen220/$USER`; see [UNIX I](../UNIX/00_Login_Notebook)):

   ```bash
   mkdir -p ~/bigdata/gen220
   cd ~/bigdata/gen220
   ```

3. Get the class data (see [UNIX II](../UNIX/01_Tools)):

   ```bash
   git clone https://github.com/biodataprog/GEN220.git        # small example files in GEN220/data
   git clone https://github.com/biodataprog/GEN220_data.git   # genomes and tables
   ls GEN220_data/tabular
   ```

   The `tabular` folder has the comma delimited table you will use below.

4. Checkout the homework 1 github repository created in step 1 (if you [setup SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) in github)

   ```bash
   git clone git@github.com:biodataprog/2026-hw1-YOURGITHUBID.git
   ```

   OR for the https will need to [create a token as your password](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

   ```bash
   git clone https://github.com/biodataprog/2026-hw1-YOURGITHUBID.git
   ```

5. Go into your folder (`cd 2026-hw1-YOURGITHUBID`). The [Git and GitHub guide](../Resources/Git_tutorial) (Recipe A) walks through these clone/commit/push steps in more detail.

6. Edit a script in there called `filesize.sh`; you can do this in jupyter on web, you can edit on the command line with `nano`, `vi`, or `emacs`, or you can [use visual studio tunnel](https://docs.google.com/presentation/d/1pEXb4H47atpWruV0qxoYcZxtLc3dPk9ehIXNkf8Zv1g/edit)
7. Add some code to this script which achieves the directions at the bottom of this page
8. Test it out (run the `./filesize.sh`).
9. To submit your homework (and you can do this more than once), this requires doing `git commit` and then `git push`

   ```bash
   # stage the file (needed the first time you commit a new file, and after every change)
   git add filesize.sh
   # this step saves a version of the code
   git commit -m "This is a homework 1 solution"
   # this step will push the data from HPCC or your computer UP to the github site
   # this step will request your username (YOURGITHUBID) and your password (that TOKEN I mentioned before).
   # if you have setup github account with SSH keys then it will ask you for your SSH key password
   git push
   ```

10. You can repeat doing edits to the file, commit, and push to github.

Tasks for Homework 1
====

Your goal is to write a shell script, `filesize.sh`, that examines the IUCN Red List table of threatened species (`threatened-species.csv.gz`) using only UNIX tools. Every task below is one or more commands (usually a pipeline) in the script.

## About the data

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

__Heads up:__ columns 1-8 are safe to pull out with `cut -d,`. Later columns (especially `taxonomic_authority`, e.g. `"Smith, 2010"`) can contain commas inside quotation marks, which shifts the fields to the right of them. Task 5 explores this.

## What to put in `filesize.sh`

Begin the script with `#!/usr/bin/env bash` and put the data file path in a variable (`FILE=threatened-species.csv.gz`). Before each answer, `echo` a short label so your output is readable, for example `echo "Number of lines:"`. Comments (`#`) explaining each step are expected.

**Task 1 - Get the data.** Copy `threatened-species.csv.gz` from `GEN220_data/tabular` into your homework folder with `cp` (or run the provided `./setup.sh`). Don't `git add` the data file.

**Task 2 - File basics.**
   * Print the size of the compressed file, using `ls -lh` or `du -h`.
   * Print the number of lines in the file (use `zcat` and `wc -l`).
   * Print the number of *species* (rows) - one fewer than the line count, since the first line is the header. Do this in the script with `$(( ))` arithmetic or by using `tail -n +2` in the pipe.
   * Print the compressed size vs. uncompressed size (`zcat | wc -c`), and the ratio if you like (`gzip -l` also reports it).

**Task 3 - Explore the taxonomy with `cut`, `sort`, `uniq`.** (Work through the `cut` and `sort and uniq` sections of the [UNIX III lab](../UNIX/02b_Data_processing_lab) first.) In every pipeline, remove the header with `tail -n +2`.
   * How many *unique* phyla are there (column 3)? How many unique orders (column 5)? Print each as a single number (`sort -u | wc -l`).
   * Print the number of species in each kingdom (column 2), most to least: `... | sort | uniq -c | sort -nr`.
   * Print the number of species in each phylum, most to least.
   * Print the 10 largest families (column 6) by number of species: `sort | uniq -c | sort -nr | head -n 10`.
   * Print the 10 genera (column 7) with the most threatened species.
   * How many classes (column 4) are there within the kingdom ANIMALIA only? (Hint: `grep` or `awk` to select, then `cut`.)

**Task 4 - Selecting rows.**
   * How many species are in the kingdom FUNGI? Use a method that cannot accidentally match other columns, e.g. `awk -F, '$2=="FUNGI"' | wc -l`. Compare with `grep -c ',FUNGI,'` - do they agree?
   * How many *species names* (column 8) start with the genus `Panthera`? List them with `cut -d, -f8` and `grep '^Panthera'`.
   * Make a smaller table of just the FUNGI: save columns `taxonid`, `phylum_name`, `scientific_name` (columns 1,3,8) to a file `fungi.tsv` with tabs as the separator (select the rows with `awk`, then `cut -d, -f1,3,8 | tr ',' '\t'`). Print its first 5 lines and line count in the script. Commit `fungi.tsv` to your repo.
   * Count the species that have no value for `main_common_name` (`awk -F, '$14==""'`) and report what fraction of rows that is. (Look carefully: does it work for all rows, given the comma problem above? Add a comment with your thoughts.)

**Task 5 - A gotcha: why you cannot trust `cut` on column 13 (`category`).** The IUCN status is in column 13. Try the obvious thing:

   ```bash
   zcat threatened-species.csv.gz | tail -n +2 | cut -d, -f13 | sort | uniq -c | sort -nr | head
   ```

   You will see strange values such as ` 2010"` and `"FRASER RIVER` in the output instead of just statuses like `LC`, `EN`, `CR`. Quoted commas inside the `taxonomic_authority` and `population` columns push the fields over. In your script:
   * Run the pipeline above and save the output in a comment or `echo` that explains in 2-3 sentences what went wrong.
   * Count how many rows contain a double quote: `zcat ... | grep -c '"'`.
   * Show a correct count of the *critically endangered* species (`CR`) by matching the whole field with `grep -c ',CR,'`. (Compare with the naive `cut -f13` count: they differ. Explain in a comment why `,CR,` is the more reliable match.)
   * __Bonus__: print the count for each of the statuses `LC`, `NT`, `VU`, `EN`, `CR`, `EW`, `EX`, `DD` with a `for` loop (`for s in LC NT VU EN CR EW EX DD; do ... done`). Then answer: which is most common, and what proportion of the table is *actually threatened* (`VU`, `EN`, `CR`)? Your script should use UNIX tools only.

**Task 6 - Commit and push.** Check in your changes with `git add filesize.sh fungi.tsv`, `git commit -m 'a message'` and `git push`. Check the repository page on github.com to make sure your files are there - your last push before the deadline is what gets graded. Run `git status` before pushing: it should not list the `.csv.gz` file as staged.

## Checklist before you submit

* `./filesize.sh` runs from start to finish with no errors (`chmod +x filesize.sh` if you get permission denied). Run it from a clean state with `bash filesize.sh`.
* Every answer is preceded by a label printed with `echo`.
* You used `zcat`; you did not unzip the data into your repo.
* Your script contains comments in your own words.
* Your latest push is on GitHub.
