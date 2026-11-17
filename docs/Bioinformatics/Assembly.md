# Genome Assembly

Genome assembly reconstructs a genome sequence from many short (or long) sequencing reads. In this lecture we will assemble a small bacterial genome two ways:

1. **Short reads (Illumina)**: clean reads with `fastp`, assemble with `SPAdes`, then check the assembly with `QUAST`, `AAFTF` and `BUSCO`.
2. **Long reads (Oxford Nanopore and PacBio)**: assemble with `Flye`, polish, and check the result the same way.

The same strain (*Listeria monocytogenes* EGD-e) was sequenced with all three technologies, so you can compare the short-read and long-read assemblies to each other and to the finished reference genome. Part 3 applies the same steps to a small (27 Mb) fungal genome.

## Key terms

* **Read**: one sequenced fragment. Illumina reads are 100-300 bp; Nanopore and PacBio reads are often 5,000-50,000 bp or longer.
* **Coverage (depth)**: how many reads on average cover each base. Coverage = total bases sequenced / genome size. For a 5 Mb genome, 500 Mb of reads is 100x coverage.
* **Contig**: a continuous piece of assembled sequence with no gaps.
* **Scaffold**: contigs joined in order (with runs of `N` for gaps between them).
* **N50**: half of the assembly is in contigs this length or longer. Bigger is better, but it says nothing about whether the contigs are *correct*.
* **L50**: the number of contigs needed to reach half the assembly length. Smaller is better.

## Why short reads give fragmented assemblies

The assembler joins reads that overlap. A **repeat** longer than a read (for example the ~5 kb ribosomal RNA operon that bacteria have 5-10 copies of, or transposons and IS elements) cannot be placed: every copy looks the same, so the assembler stops the contig there. Short-read bacterial assemblies usually come out as 50-200 contigs that break at repeats. Long reads span those repeats, so a long-read assembly of a bacterium is often one circular chromosome plus any plasmids.

Most short-read assemblers (SPAdes, Velvet, MEGAHIT) build a **de Bruijn graph**: they cut reads into overlapping words of length *k* (k-mers) and connect k-mers that overlap by *k-1* bases. Long-read assemblers (Flye, Canu, Raven) use **overlap-layout-consensus** or **repeat graph** approaches that compare whole reads to each other.

## Setup

Make a working folder for this lecture. All of the scripts below assume you run them from this folder and that you made a `logs` folder for the job logs.

```bash
mkdir -p ~/bigdata/Assembly
cd ~/bigdata/Assembly
mkdir -p logs
```

### The demo data

We will assemble *Listeria monocytogenes* strain EGD-e, a food-borne pathogen and a classic lab strain. Its genome is one circular chromosome of 2.94 Mb with no plasmids. The Illumina and Nanopore reads were made from the same DNA prep by Hall et al. (2024, *eLife* [doi:10.7554/eLife.98300](https://doi.org/10.7554/eLife.98300)), who also built a closed genome from them that we can use as the "truth". The PacBio reads are an older kind (CLR, see Part 2) of the same strain from another lab.

| Data | Platform | Accession | Reads in class folder |
| ---- | -------- | --------- | --------------------- |
| Illumina paired-end | NextSeq 2000, 2x~120 bp after trimming | [SRR26899101](https://www.ncbi.nlm.nih.gov/sra/SRR26899101) | 3.76 M pairs, ~300x |
| Oxford Nanopore | GridION R10.4.1, Dorado sup basecalling | [SRR27638394](https://www.ncbi.nlm.nih.gov/sra/SRR27638394) | random 9% of the run, ~150x |
| Oxford Nanopore duplex | GridION R10.4.1, duplex reads | [SRR28370645](https://www.ncbi.nlm.nih.gov/sra/SRR28370645) | 34,000 reads, ~49x |
| PacBio CLR | PacBio RS II subreads | [SRR6156244](https://www.ncbi.nlm.nih.gov/sra/SRR6156244) | random 13% of the run, ~100x |
| Reference genome (same reads) | | [GCF_045288145.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_045288145.1/) | 2,944,530 bp |
| Reference genome (classic RefSeq) | | [GCF_000196035.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCF_000196035.1/) | 2,944,528 bp |

The reads have been downloaded for you into `/bigdata/gen220/shared/data/assembly/bacteria/`. Link them into your folder (don't copy - links save space):

```bash
cd ~/bigdata/Assembly
mkdir -p fastq
ln -sf /bigdata/gen220/shared/data/assembly/bacteria/fastq/* fastq/
ln -sf /bigdata/gen220/shared/data/assembly/bacteria/reference/* .
ls -l fastq
```

The reference folder has `Lmono_EGDe.fna` (genome), `Lmono_EGDe.gff` (gene annotation) and `Lmono_EGDe.faa` (proteins) for GCF_045288145.1, and the same files named `Lmono_EGDe_RefSeq.*` for the classic reference.

### Getting public data yourself

Public reads live in the NCBI [Sequence Read Archive (SRA)](https://www.ncbi.nlm.nih.gov/sra), which keeps a copy of every run on Amazon's cloud (AWS). The SRA toolkit downloads from there; from the HPCC this is much faster than other mirrors. `prefetch` downloads the compressed `.sra` file and `fasterq-dump` turns it into fastq. `fasterq-dump` writes large temporary files, so run it from `$SCRATCH` (the fast local disk on the compute node, which is cleared when the job ends) and copy only the compressed reads back.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J sra_download
#SBATCH -o logs/%x.%j.log
module load sratoolkit

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
OUT=$(pwd)/fastq
mkdir -p $OUT
cd $SCRATCH   # $SCRATCH only exists inside a job

for ACC in SRR26899101
do
    prefetch $ACC
    # paired-end reads are split into ACC_1.fastq and ACC_2.fastq
    fasterq-dump --threads $CPU --split-files -t $SCRATCH -O . $ACC/$ACC.sra
    pigz -p $CPU ${ACC}*.fastq
    mv ${ACC}*.fastq.gz $OUT/
done
```

The long-read runs are much bigger than we need (the full Nanopore run is ~1700x coverage, 4.3 GB as `.sra`). The class copies were made by streaming `fasterq-dump` output (`-Z` writes to the screen instead of a file) into `seqkit sample`, which keeps a random fraction of the reads, so the full fastq is never saved:

```bash
module load sratoolkit
module load seqkit
cd $SCRATCH
prefetch SRR27638394
# keep a random 9% of the reads; -s sets the random seed so the result is reproducible
fasterq-dump --split-spot -Z SRR27638394/SRR27638394.sra | \
    seqkit sample -s 11 -p 0.09 | pigz > ~/bigdata/Assembly/fastq/SRR27638394.fastq.gz
```

The script that staged all of the class data is on the cluster at `/bigdata/gen220/shared/data/assembly/scripts/stage_assembly_data.sh` - read it to see how each file was made.

The reference genome can be downloaded from NCBI with the `datasets` tool:

```bash
module load ncbi_datasets
datasets download genome accession GCF_045288145.1 --include genome,gff3,protein
unzip ncbi_dataset.zip
```

### How much data do I have?

`seqkit stats` gives the number of reads, the total bases and the read length distribution. Divide the total bases by the genome size to get the coverage.

```bash
module load seqkit
seqkit stats -a -T fastq/*.fastq.gz | column -t
```

---

# Part 1: Short read (Illumina) assembly

## Step 1: Read quality control and cleanup with fastp

Raw Illumina reads have adapter sequence on the ends of some reads (when the DNA fragment was shorter than the read length), and the quality drops toward the 3' end of the read. [fastp](https://github.com/OpenGene/fastp) trims adapters and low-quality bases, removes reads that get too short, and writes an HTML report that is similar to FastQC.

```bash
module load fastp
fastp --help
```

Useful options:

* `-i`/`-I`: input forward and reverse reads; `-o`/`-O`: output forward and reverse reads
* `--detect_adapter_for_pe`: find the adapter sequence by looking for overlap between the read pairs
* `--cut_right --cut_mean_quality 20`: trim from a sliding window once the mean quality drops below 20
* `-l 50`: drop reads shorter than 50 bp after trimming
* `-w`: number of threads
* `-h`/`-j`: HTML and JSON report files

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 8gb --time 1:00:00
#SBATCH -J fastp
#SBATCH -o logs/%x.%j.log
module load fastp

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
ACC=SRR26899101
mkdir -p clean reports

fastp -w $CPU --detect_adapter_for_pe \
      --cut_right --cut_mean_quality 20 -l 50 \
      -i fastq/${ACC}_1.fastq.gz -I fastq/${ACC}_2.fastq.gz \
      -o clean/${ACC}_1.fastq.gz -O clean/${ACC}_2.fastq.gz \
      -h reports/${ACC}.fastp.html -j reports/${ACC}.fastp.json
```

Copy `reports/*.fastp.html` to your laptop (or put it in your `~/.html` folder as in the [Short Reads](Short_read_aligning) lecture) and open it in a web browser. Look at:

* How many reads passed the filter?
* The quality-by-position plot before and after filtering
* The estimated insert size and the adapter content
* The duplication rate

### Too much coverage?

More data is not always better. SPAdes works best at roughly 50-100x coverage; much higher coverage takes more memory and time and can make the graph messier. Our Illumina data is ~300x, so try both: assemble all of it and a subsample of about 100x, and compare. For a 2.9 Mb genome, 1.25 million read pairs is ~100x. Use `seqtk sample` with the same random seed (`-s`) on both files so the pairs stay matched, then run SPAdes again on `clean/sub_1.fastq.gz` and `clean/sub_2.fastq.gz` with a different output folder:

```bash
module load seqtk
# 1,250,000 pairs x 2 x ~120 bp = ~300 Mb = ~100x of a 2.9 Mb genome
seqtk sample -s 11 clean/SRR26899101_1.fastq.gz 1250000 | gzip > clean/sub_1.fastq.gz
seqtk sample -s 11 clean/SRR26899101_2.fastq.gz 1250000 | gzip > clean/sub_2.fastq.gz
```

## Step 2: Assemble with SPAdes

[SPAdes](https://github.com/ablab/spades) is a de Bruijn graph assembler designed for bacterial genomes. It builds the graph with several k-mer sizes (for example 21, 33, 55, 77) and combines them: small k is better for low-coverage regions, large k is better for resolving short repeats.

```bash
module load spades
spades.py --help
```

Useful options:

* `-1`/`-2`: forward and reverse reads
* `-o`: output folder
* `--isolate`: recommended mode for high-coverage bacterial isolate data
* `--careful`: extra mismatch correction (can't be combined with `--isolate`; use one or the other)
* `-t`: threads; `-m`: memory limit in **GB** (SPAdes stops if it goes over this)
* `-k`: the list of k-mer sizes (the default is chosen from the read length, which is usually fine)
* `--tmp-dir`: where to write temporary files

Other modes for other kinds of data: `--meta` (metagenomes), `--rna` (transcriptomes), `--plasmid` (plasmids only), `--sc` (single-cell, uneven coverage).

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 16 --mem 32gb --time 2:00:00
#SBATCH -J spades
#SBATCH -o logs/%x.%j.log
module load spades

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
# SPAdes wants memory in GB; leave a little headroom below the --mem request
MEM=30
ACC=SRR26899101

spades.py --isolate -t $CPU -m $MEM \
    -1 clean/${ACC}_1.fastq.gz -2 clean/${ACC}_2.fastq.gz \
    --tmp-dir $SCRATCH \
    -o spades_${ACC}
```

When it finishes, look at the output folder:

```bash
ls spades_SRR26899101
```

* `contigs.fasta`: the assembled contigs - this is the main result
* `scaffolds.fasta`: contigs joined using the read pair information
* `assembly_graph.fastg` / `assembly_graph_with_scaffolds.gfa`: the assembly graph (view it with [Bandage](https://rrwick.github.io/Bandage/))
* `spades.log`: everything SPAdes did - check here if it failed
* `K21/`, `K33/`, ...: intermediate results for each k-mer size

The contig names tell you their length and k-mer coverage:

```bash
grep ">" spades_SRR26899101/contigs.fasta | head
# >NODE_1_length_312514_cov_45.231
```

**Question**: why are there many short contigs with very low coverage (cov < 5)? What might they be?

### Remove short and low-coverage contigs

Tiny contigs (under 500 bp or 1 kb) and contigs with much lower coverage than the rest of the genome are usually errors or contamination. Filter them out before you analyze the assembly further. `seqkit` can keep contigs above a length cutoff:

```bash
module load seqkit
seqkit seq -m 500 spades_SRR26899101/contigs.fasta > SRR26899101.spades.fasta
seqkit stats SRR26899101.spades.fasta
```

**Exercise**: write a short Python script that reads `contigs.fasta`, parses the `cov_` value out of each header, and writes only the contigs that are at least 500 bp *and* have coverage at least 10% of the median coverage.

### Plasmids

Many bacteria carry plasmids. A plasmid usually shows up as a contig (or a small group of contigs) with **higher** coverage than the chromosome, because there are several plasmid copies per cell. You can also run SPAdes in `--plasmid` mode to try to pull out only the plasmids.

## Step 3: Assess the assembly

A good assembly is:

1. **Contiguous** - few, long contigs (N50, number of contigs)
2. **Complete** - all of the genome is there (total length vs. expected genome size, BUSCO)
3. **Correct** - few misassemblies and base errors (QUAST against a reference, read mapping)
4. **Clean** - no contamination from other organisms (AAFTF sourpurge, BLAST)

### QUAST

[QUAST](https://github.com/ablab/quast) reports the contiguity statistics for one or more assemblies. If you give it a reference genome (`-r`) and gene annotation (`-g`), it also aligns the assembly to the reference and counts misassemblies, mismatches, indels and how much of the reference is covered.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 1:00:00
#SBATCH -J quast
#SBATCH -o logs/%x.%j.log
module load quast

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
REF=Lmono_EGDe.fna
GFF=Lmono_EGDe.gff

# you can list several assemblies to compare them side by side
quast.py -t $CPU -r $REF -g $GFF -o quast_illumina \
    SRR26899101.spades.fasta spades_SRR26899101/scaffolds.fasta
```

Look at `quast_illumina/report.txt` (text), `report.tsv` (for parsing) and `report.html` (interactive). Key values:

| Metric | What it means |
| ------ | ------------- |
| `# contigs` | number of contigs (>= 500 bp by default) |
| `Largest contig`, `N50`, `L50` | contiguity |
| `Total length` | compare to the reference genome size |
| `GC (%)` | should match the organism; a mix of GC values suggests contamination |
| `# misassemblies` | places where the contig joins pieces that are far apart (or on different strands) in the reference |
| `Genome fraction (%)` | percent of the reference covered by the assembly |
| `# mismatches per 100 kbp`, `# indels per 100 kbp` | base-level errors |

Without a reference, QUAST still reports the contiguity statistics. For a new species you won't have a reference, so the other checks below matter more.

### AAFTF

[AAFTF](https://github.com/stajichlab/AAFTF) (Automatic Assembly For The Fungi) is a pipeline developed in the Stajich lab that runs the steps of a short-read assembly from reads to a cleaned genome. It was written for fungi but every step works for bacteria too. Each step is a subcommand:

```bash
module load AAFTF
AAFTF -h
```

| Step | Command | What it does |
| ---- | ------- | ------------ |
| trim | `AAFTF trim` | adapter and quality trimming (bbduk or fastp) |
| filter | `AAFTF filter` | remove PhiX and other contaminant reads |
| assemble | `AAFTF assemble` | run SPAdes (or MEGAHIT) |
| vecscreen | `AAFTF vecscreen` | remove contigs or ends that match vector/adapter sequences (NCBI UniVec) |
| sourpurge | `AAFTF sourpurge` | find contigs from the wrong organism with `sourmash` and drop them |
| rmdup | `AAFTF rmdup` | remove small contigs that are duplicates of larger ones |
| polish | `AAFTF polish` / `AAFTF pilon` | correct base errors by mapping reads back to the assembly |
| sort | `AAFTF sort` | sort contigs by length and rename them |
| assess | `AAFTF assess` | assembly statistics |

The quickest use is `AAFTF assess` for the summary statistics of any assembly:

```bash
module load AAFTF
AAFTF assess -i SRR26899101.spades.fasta -r SRR26899101.spades.stats.txt
cat SRR26899101.spades.stats.txt
```

AAFTF can also run all of the steps above as a pipeline (`AAFTF pipeline`); see the [AAFTF README](https://github.com/stajichlab/AAFTF) for an example. We won't run the full pipeline in class.

### BUSCO: is the genome complete?

[BUSCO](https://busco.ezlab.org/) (Benchmarking Universal Single-Copy Orthologs) searches the assembly for a set of genes that are present in a single copy in nearly every genome of a lineage. If the assembly is complete, nearly all of them should be found once.

* **C** - Complete (found full length), split into **S** (single copy) and **D** (duplicated)
* **F** - Fragmented (only part of the gene was found)
* **M** - Missing

A good bacterial assembly should be >95% complete. Many **D**uplicated BUSCOs suggest a mixed sample (two strains or species) or an assembly that kept both haplotypes. Many **F**ragmented BUSCOs suggest base errors (frameshifts) - common in unpolished long-read assemblies.

Pick the most specific lineage that fits your organism. See all of the lineages with `busco --list-datasets`. For *Listeria* use `listeria_odb12.2` (or compare with the general `bacteria_odb12.2`).

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J busco
#SBATCH -o logs/%x.%j.log
module load busco

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
LINEAGE=listeria_odb12.2
# the busco module sets $BUSCO_LINEAGES to a shared copy of the lineage datasets
# (/srv/projects/db/BUSCO/v12.2), so use --offline instead of downloading them

for GENOME in SRR26899101.spades.fasta
do
    NAME=$(basename $GENOME .fasta)
    busco -i $GENOME -m genome -l $LINEAGE -c $CPU -o busco_$NAME --out_path busco \
        --offline --download_path $BUSCO_LINEAGES
done
```

The summary is in `busco/busco_<NAME>/short_summary*.txt`:

```text
C:99.2%[S:99.0%,D:0.2%],F:0.4%,M:0.4%,n:...
```

### Map the reads back

Every read should map somewhere in a complete, correct assembly. Mapping the reads back (as in the [Short Reads](Short_read_aligning) lecture) tells you:

* the fraction of reads that map (`samtools flagstat`) - a low value means part of the genome is missing
* the depth across each contig (`samtools coverage`) - contigs with very different depth may be plasmids, repeats collapsed into one copy, or contamination

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 1:00:00
#SBATCH -J mapback
#SBATCH -o logs/%x.%j.log
module load bwa
module load samtools

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
ACC=SRR26899101
ASM=SRR26899101.spades.fasta

bwa index $ASM
bwa mem -t $CPU $ASM clean/${ACC}_1.fastq.gz clean/${ACC}_2.fastq.gz | \
    samtools sort --threads $CPU -o ${ACC}.mapback.bam -
samtools index ${ACC}.mapback.bam
samtools flagstat ${ACC}.mapback.bam > ${ACC}.mapback.flagstat.txt
samtools coverage ${ACC}.mapback.bam > ${ACC}.mapback.coverage.tsv
```

### Viewing the assembly graph

[Bandage](https://rrwick.github.io/Bandage/) draws the assembly graph (`assembly_graph_with_scaffolds.gfa`). Install it on your laptop and copy the `.gfa` file over. You will see the contigs joined into a tangle at the repeats - this is exactly where the short-read assembly could not decide which path is right.

---

# Part 2: Long read assembly

Long reads span most bacterial repeats (including the rRNA operons), so a long-read assembly is usually complete: one contig per replicon (chromosome and each plasmid), often marked as circular.

The two long-read technologies have different error profiles:

| | Oxford Nanopore (ONT) | PacBio HiFi | PacBio CLR (older) |
| --- | --- | --- | --- |
| Read length | 5-100+ kb (ultra-long > 100 kb possible) | 10-25 kb | 5-50 kb |
| Per-read accuracy | ~95-99% (R10.4.1 + current basecallers is > 99%); duplex reads > 99.9% | > 99.9% | ~85-90% |
| Typical errors | indels in homopolymers (runs like `AAAAAAA`) | very few | random indels |
| Polishing needed? | yes (medaka; Illumina reads with Polypolish) | usually not | yes |

PacBio **HiFi** reads are made by reading the same circular DNA molecule many times and taking the consensus; before HiFi (2019), PacBio sold **CLR** (continuous long reads), which you will still find in the public databases. Our *Listeria* PacBio data is CLR. In [Part 3](#part-3-a-small-fungal-genome) we assemble a fungal genome from HiFi reads.

## Step 1: Long read QC

Look at the read length and quality distributions. `seqkit stats -a` reports the read length N50 and the mean quality (`AvgQual`):

```bash
module load seqkit
mkdir -p reports clean
seqkit stats -a -T fastq/SRR27638394.fastq.gz fastq/SRR28370645.fastq.gz fastq/SRR6156244.fastq.gz | column -t
# one line per read: name, length, mean quality - use this to plot the distributions in Python
seqkit fx2tab -n -i -l -q fastq/SRR27638394.fastq.gz > reports/SRR27638394.lengths.tsv
```

**Exercise**: plot a histogram of the read lengths (log scale on the x axis) and of the mean read quality for the Nanopore and PacBio reads, using pandas and matplotlib (see [Plotting Data with Python](../Python/09_Plotting)). [NanoPlot](https://github.com/wdecoster/NanoPlot) makes these plots for you, but it isn't installed as a module on the cluster yet; you can install it in your own environment with `conda install -c bioconda nanoplot` or `pip install NanoPlot`.

Check the read length N50, the mean read quality, and the total bases (= coverage).

### Filtering long reads

For bacteria, 50-100x of long reads is plenty. Throwing away the shortest and worst reads often gives a *better* assembly. [Filtlong](https://github.com/rrwick/Filtlong) keeps the best reads up to a target number of bases (here 300 Mb = ~100x of a 2.9 Mb genome); [chopper](https://github.com/wdecoster/chopper) is an alternative.

```bash
module load filtlong
# keep reads >= 1 kb, drop the worst 5%, keep at most 300000000 total bases
filtlong --min_length 1000 --keep_percent 95 --target_bases 300000000 \
    fastq/SRR27638394.fastq.gz | gzip > clean/SRR27638394.filt.fastq.gz
```

Don't filter HiFi reads this way - they are already high quality.

## Step 2: Assemble with Flye

[Flye](https://github.com/mikolmogorov/Flye) builds a **repeat graph** from the long reads, then resolves the repeats using reads that span them. It works for ONT and PacBio reads; you tell it which kind of reads you have:

| Option | Reads |
| ------ | ----- |
| `--nano-hq` | ONT with Guppy 5+ / Dorado (R10.4.1 or R9.4.1 SUP) - most current data |
| `--nano-raw` | older ONT data (pre-2021 basecalling) |
| `--nano-corr` | ONT reads already error-corrected |
| `--pacbio-hifi` | PacBio HiFi (CCS) |
| `--pacbio-raw` | PacBio CLR |

Other useful options:

* `--out-dir`, `--threads`
* `--genome-size 5m`: optional; needed with `--asm-coverage`
* `--asm-coverage 50`: use only the longest reads up to 50x for the first step (saves memory on very deep data)
* `--meta`: for metagenomes or samples with very uneven coverage (also helps recover small plasmids)

```bash
module load Flye
flye --help
```

### Nanopore

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 16 --mem 32gb --time 2:00:00
#SBATCH -J flye_ont
#SBATCH -o logs/%x.%j.log
module load Flye

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
ACC=SRR27638394

flye --nano-hq clean/${ACC}.filt.fastq.gz --threads $CPU --out-dir flye_${ACC}
```

The Nanopore **duplex** reads (`SRR28370645`, where both strands of each molecule were read) are fewer but more accurate. Assemble them the same way and compare:

```bash
flye --nano-hq fastq/SRR28370645.fastq.gz --threads $CPU --out-dir flye_SRR28370645
```

### PacBio CLR

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 16 --mem 32gb --time 2:00:00
#SBATCH -J flye_clr
#SBATCH -o logs/%x.%j.log
module load Flye

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
ACC=SRR6156244

flye --pacbio-raw fastq/${ACC}.fastq.gz --threads $CPU --out-dir flye_${ACC}
```

For **HiFi** reads, use `--pacbio-hifi` instead (see Part 3).

### Flye output

* `assembly.fasta`: the final assembly
* `assembly_graph.gfa`: the repeat graph (open it in Bandage)
* `assembly_info.txt`: one line per contig with its length, coverage, whether it is **circular** and how many times it repeats
* `flye.log`: the run log

```bash
column -t flye_SRR27638394/assembly_info.txt
```

```text
#seq_name  length   cov.  circ.  repeat  mult.  alt_group  graph_path
contig_1   2944530  98    Y      N       1      *          1
```

(Your numbers will be a little different.)

**Question**: How many contigs are circular? EGD-e has a single chromosome and no plasmids - did you get exactly one contig? If not, look at the length and coverage of the extra contigs: what might they be? In other strains, plasmids show up as extra circular contigs, usually with higher coverage than the chromosome.

Small plasmids (< 10 kb) are often missed by long-read assemblers because few reads come from them and the reads may be longer than the plasmid. Short-read assemblies are better at recovering them, which is one reason to combine the two kinds of data.

## Step 3: Polish

Polishing fixes the remaining base errors by aligning reads back to the assembly and taking the consensus.

**Short-read polishing: Polypolish** uses Illumina reads of the same strain to fix the remaining errors (mostly small indels in homopolymers). It needs *all* alignments of each read (`bwa mem -a`) so that it can handle repeats correctly.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J polypolish
#SBATCH -o logs/%x.%j.log
module load bwa
module load polypolish

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
SR=SRR26899101
LR=SRR27638394
cp flye_${LR}/assembly.fasta ${LR}.flye.fasta
ASM=${LR}.flye.fasta

bwa index $ASM
bwa mem -t $CPU -a $ASM clean/${SR}_1.fastq.gz > $SCRATCH/align_1.sam
bwa mem -t $CPU -a $ASM clean/${SR}_2.fastq.gz > $SCRATCH/align_2.sam
# keep only the alignments that fit the read pair's insert size
polypolish_insert_filter.py --in1 $SCRATCH/align_1.sam --in2 $SCRATCH/align_2.sam \
    --out1 $SCRATCH/filt_1.sam --out2 $SCRATCH/filt_2.sam
polypolish $ASM $SCRATCH/filt_1.sam $SCRATCH/filt_2.sam > ${LR}.flye.polypolish.fasta
```

The SAM files are large temporary files, so they go in `$SCRATCH` and disappear when the job ends.

**Long-read polishing: medaka.** Without Illumina reads, ONT assemblies are polished with [medaka](https://github.com/nanoporetech/medaka), which uses a neural network trained on ONT data. Medaka has to match the basecaller model that made the reads; for these reads that is `medaka_consensus -i reads.fastq.gz -d assembly.fasta -o medaka_out --bacteria` (or `-m r1041_e82_400bps_sup_v4.3.0`). The medaka module on the cluster is currently broken, so we skip this step.

### Rotate to a standard start

A circular chromosome has no real start or end, so Flye starts it at an arbitrary place. By convention, bacterial chromosomes start at the *dnaA* gene (near the origin of replication). [dnaapler](https://github.com/gbouras13/dnaapler) rotates the circular contigs so they start there, which makes it easier to compare assemblies:

```bash
# optional - dnaapler isn't a cluster module yet; install it yourself with: conda install -c bioconda dnaapler
dnaapler all -i SRR27638394.flye.polypolish.fasta -o dnaapler_SRR27638394 -p SRR27638394 -t 4
```

## Step 4: Assess and compare

Run the same QUAST and BUSCO checks on all of the assemblies so you can compare them side by side.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J compare
#SBATCH -o logs/%x.%j.log
module load quast
module load busco

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
REF=Lmono_EGDe.fna
GFF=Lmono_EGDe.gff
LINEAGE=listeria_odb12.2

ASSEMBLIES="SRR26899101.spades.fasta SRR27638394.flye.fasta SRR27638394.flye.polypolish.fasta flye_SRR28370645/assembly.fasta flye_SRR6156244/assembly.fasta"

quast.py -t $CPU -r $REF -g $GFF -o quast_compare \
    -l "SPAdes_Illumina,Flye_ONT,Flye_ONT_polypolish,Flye_ONT_duplex,Flye_PacBio_CLR" \
    $ASSEMBLIES

for GENOME in $ASSEMBLIES
do
    # make a name from the path: flye_SRR27638394/assembly.fasta -> flye_SRR27638394_assembly
    NAME=$(echo ${GENOME%.fasta} | tr '/' '_')
    busco -i $GENOME -m genome -l $LINEAGE -c $CPU -o busco_$NAME --out_path busco \
        --offline --download_path $BUSCO_LINEAGES
done
```

QUAST can also show the comparison as an interactive plot (`quast_compare/report.html`) and the alignment to the reference in [Icarus](https://quast.sourceforge.net/docs/manual.html#sec4) (`quast_compare/icarus.html`).

BUSCO can draw a bar chart of all of the summaries:

```bash
mkdir -p busco_summaries
cp busco/*/short_summary*.txt busco_summaries/
generate_plot.py -wd busco_summaries
```

**Questions**:

1. Which assembly has the fewest contigs? The highest N50? Is any of them a single circular chromosome?
2. Compare the `# mismatches per 100 kbp` and `# indels per 100 kbp` for the ONT assembly before and after Polypolish. Which kind of error does polishing fix?
3. Compare the BUSCO **Fragmented** count before and after polishing. Why would unpolished ONT assemblies have more fragmented genes?
4. How does the duplex assembly (fewer reads, but more accurate) compare to the simplex one? How does the noisy PacBio CLR assembly compare?
5. QUAST against `Lmono_EGDe_RefSeq.fna` (the classic reference, sequenced years earlier from another culture of the "same" strain) instead of `Lmono_EGDe.fna`. Are there real differences between the two lab stocks?
6. Where do the SPAdes contigs break? Use the Icarus viewer or align the SPAdes contigs to the Flye assembly and look at what is at the contig ends (hint: search for rRNA genes in the reference GFF).

# Part 3: A small fungal genome

Eukaryotic genomes are bigger and have more repeats (transposons, rDNA arrays, centromeres, telomeres), so the difference between short- and long-read assemblies is even larger. *Zancudomyces culisetae* (strain HAW-14-8) is a fungus that lives in the gut of mosquito larvae. Its genome is ~27 Mb. Yang & Wang (2025, *G3* [doi:10.1093/g3journal/jkaf204](https://doi.org/10.1093/g3journal/jkaf204)) sequenced it with Illumina, Nanopore and PacBio and compared the assemblies - you can check your results against theirs. We use the same genome in the [Genome Annotation](Genome_annotation_gene_prediction) lecture.

| Data | Platform | Accession | Reads in class folder |
| ---- | -------- | --------- | --------------------- |
| Illumina paired-end | NovaSeq 6000, 2x150 | [SRR33260096](https://www.ncbi.nlm.nih.gov/sra/SRR33260096) | random half of the run, ~100x |
| Oxford Nanopore | PromethION R9.4.1 | [SRR33263599](https://www.ncbi.nlm.nih.gov/sra/SRR33263599) | random 5.6% of the run, ~60x |
| PacBio HiFi | Sequel II | [SRR33259245](https://www.ncbi.nlm.nih.gov/sra/SRR33259245) | all, ~51x |
| Published assembly (HiFi, 26 contigs) | | [GCA_052426225.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCA_052426225.1/) | 27.1 Mb |

```bash
mkdir -p ~/bigdata/Assembly/fungus
cd ~/bigdata/Assembly/fungus
mkdir -p logs fastq
ln -sf /bigdata/gen220/shared/data/assembly/Zculisetae/fastq/SRR3326* fastq/
ln -sf /bigdata/gen220/shared/data/assembly/Zculisetae/Zculisetae_HAW-14-8.fna .
```

Run the same steps as for the bacterium - you can reuse your scripts with a new `ACC` - but give the jobs more memory and time:

* **fastp + SPAdes** on the Illumina reads (`SRR33260096`). Ask for `--mem 64gb` and set `MEM=60` for SPAdes. Leave out `--isolate`; for eukaryotes use the default mode or `--careful`.
* **Flye** on the Nanopore reads (`--nano-hq`, these were basecalled with Guppy 5 SUP).
* **Flye** on the HiFi reads:

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 16 --mem 64gb --time 2:00:00
#SBATCH -J flye_hifi
#SBATCH -o logs/%x.%j.log
module load Flye

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
ACC=SRR33259245

flye --pacbio-hifi fastq/${ACC}.fastq.gz --threads $CPU --out-dir flye_${ACC}
```

* **QUAST** comparing all of your assemblies to the published one (`-r Zculisetae_HAW-14-8.fna`; there is no GFF, so leave out `-g`).
* **BUSCO** with the `fungi_odb12.2` lineage.

**Questions**:

1. How many contigs does each assembly have, and what is the N50? Compare to Table 1 in Yang & Wang (2025).
2. How does the BUSCO completeness of the Illumina assembly compare to the HiFi assembly? Is the *gene space* complete even when the assembly is fragmented?
3. Look for telomere repeats (`TTAGGG`/`CCCTAA`, many copies in a row) at the ends of the long-read contigs. How many contigs are complete chromosomes, with telomeres at both ends? (Hint: `seqkit locate -p TTAGGGTTAGGGTTAGGG`, then check which hits fall in the first or last 1 kb of a contig.)
4. Is there a mitochondrial genome contig? (Hint: it will have much higher coverage in `assembly_info.txt` and a lower GC content.)

## Hybrid and other assemblers

* [Unicycler](https://github.com/rrwick/Unicycler) - hybrid assembly: builds a short-read SPAdes graph and uses long reads to resolve it. Good when long-read depth is low.
* [Trycycler](https://github.com/rrwick/Trycycler) and [Autocycler](https://github.com/rrwick/Autocycler) - assemble subsets of the long reads with several assemblers and build a consensus; the most accurate approach for complete bacterial genomes.
* [Canu](https://github.com/marbl/canu), [Raven](https://github.com/lbcb-sci/raven), [miniasm](https://github.com/lh3/miniasm) - other long-read assemblers.
* [hifiasm](https://github.com/chhylp123/hifiasm) - the standard assembler for HiFi data from eukaryotes (it separates the two haplotypes of diploids). The published *Z. culisetae* genome was assembled with hifiasm - try it on the HiFi reads and compare to Flye.
* [MEGAHIT](https://github.com/voutcn/megahit) - fast, low-memory short-read assembler, mostly used for metagenomes.

## Further reading

* Wick RR, Judd LM, Holt KE (2023) Assembling the perfect bacterial genome using Oxford Nanopore and Illumina sequencing. *PLoS Comput Biol* 19:e1010905. [doi:10.1371/journal.pcbi.1010905](https://doi.org/10.1371/journal.pcbi.1010905)
* Prjibelski A et al. (2020) Using SPAdes de novo assembler. *Curr Protoc Bioinformatics* 70:e102. [doi:10.1002/cpbi.102](https://doi.org/10.1002/cpbi.102)
* Kolmogorov M et al. (2019) Assembly of long, error-prone reads using repeat graphs. *Nat Biotechnol* 37:540-546. [doi:10.1038/s41587-019-0072-8](https://doi.org/10.1038/s41587-019-0072-8)
* Gurevich A et al. (2013) QUAST: quality assessment tool for genome assemblies. *Bioinformatics* 29:1072-1075. [doi:10.1093/bioinformatics/btt086](https://doi.org/10.1093/bioinformatics/btt086)
* Manni M et al. (2021) BUSCO update. *Mol Biol Evol* 38:4647-4654. [doi:10.1093/molbev/msab199](https://doi.org/10.1093/molbev/msab199)
* Chen S et al. (2018) fastp: an ultra-fast all-in-one FASTQ preprocessor. *Bioinformatics* 34:i884-i890. [doi:10.1093/bioinformatics/bty560](https://doi.org/10.1093/bioinformatics/bty560)
