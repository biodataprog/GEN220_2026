# Genome Annotation and Gene Prediction

An assembled genome is only a string of `A`, `C`, `G` and `T`. **Annotation** finds the features in it. There are two parts:

1. **Structural annotation** - *where* are the genes? The start, stop, exons and introns of each gene (plus tRNAs, rRNAs and repeats). This is **gene prediction**, the focus of this lecture.
2. **Functional annotation** - *what* do the genes do? Names, protein domains (Pfam, InterPro), GO terms, enzyme (EC) numbers, pathways. See the [Protein domains](Protein_domains) and [Orthology](Orthology) lectures.

The result is usually a **GFF3** file (one line per gene, mRNA, exon and CDS feature - see [Genomic Data Ranges](Ranges_Features_overlap)) plus FASTA files of the predicted transcripts and proteins.

## How gene predictors work

* **Ab initio** prediction uses only the genome sequence. A statistical model (usually a hidden Markov model) has learned what coding sequence looks like - codon usage, start and stop codons, splice site signals, typical exon and intron lengths - and finds the most likely gene structure.
* **Evidence-based** prediction uses outside data, called **informant** or **extrinsic** evidence:
    * **RNA-Seq** reads aligned to the genome show which regions are transcribed and where the introns are (spliced reads).
    * **Proteins** from related species, aligned to the genome, show where conserved coding exons are.
* Most modern pipelines **combine** both: the evidence is turned into **hints** that guide the ab initio predictor, and/or several predictions are merged into a consensus.

Ab initio models must be **trained** for each species (or a close relative), because codon usage, GC content and splice signals differ between organisms.

---

# Part 1: Bacteria and archaea

Prokaryotic gene prediction is comparatively easy:

* ~85-90% of the genome is coding, so genes are packed together
* there are (almost) no introns - each gene is one open reading frame (ORF) from a start codon (`ATG`, `GTG`, `TTG`) to a stop codon
* the main difficulties are picking the right **start** codon, short genes (< 100 codons), and genes that overlap

## Setup

We will annotate the bacterial genome you assembled in the [Genome Assembly](Assembly) lecture, and compare the result to the reference genome's annotation.

```bash
mkdir -p ~/bigdata/Annotation/bacteria
cd ~/bigdata/Annotation/bacteria
mkdir -p logs
ln -sf ~/bigdata/Assembly/SRR27638394.flye.polypolish.fasta genome.fasta
ln -sf /bigdata/gen220/shared/data/assembly/bacteria/reference/* .
```


## Prodigal

[Prodigal](https://github.com/hyattpd/Prodigal) (PROkaryotic DYnamic programming Gene-finding ALgorithm) trains itself on the genome you give it - it learns the GC skew, start codon usage and ribosome binding site motif from the long ORFs - and then predicts genes. It is fast (seconds for a bacterial genome) and is used inside most bacterial pipelines. [Pyrodigal](https://github.com/althonos/pyrodigal) is a faster re-implementation with the same results that you can also call from Python.

```bash
module load prodigal
prodigal -h
```

Useful options:

* `-i`: input genome FASTA
* `-o`: output gene coordinates; `-f gff` to make it GFF format
* `-a`: write the protein translations; `-d`: write the gene (nucleotide) sequences
* `-p single` (default): one genome, at least ~100 kb so it can train
* `-p meta`: pre-trained models, for metagenomes, plasmids, phages or very small contigs
* `-g 11`: genetic code (11 = bacteria/archaea; 4 for *Mycoplasma*)

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 1 --mem 2gb --time 0:30:00
#SBATCH -J prodigal
#SBATCH -o logs/%x.%j.log
module load prodigal

set -euo pipefail
prodigal -i genome.fasta -f gff -o prodigal.gff -a prodigal.faa -d prodigal.cds.fna
```

```bash
grep -c ">" prodigal.faa
head -5 prodigal.gff
```

**Questions**:

1. How many genes were predicted? How does that compare to the number of protein-coding genes in the reference annotation (`grep -c -P "\tCDS\t" Lmono_EGDe.gff`)?
2. What fraction of the genome is coding? (Hint: add up the gene lengths from the GFF with `awk` or Python.)
3. Prodigal's FASTA headers report `start_type`, `rbs_motif` and `gc_cont`. Count how many genes start with `ATG`, `GTG` and `TTG`.

## Other prokaryotic tools

Prodigal only finds protein-coding genes. Full prokaryotic annotation pipelines also find RNA genes and add functional names:

| Tool | What it does |
| ---- | ------------ |
| [tRNAscan-SE](http://lowelab.ucsc.edu/tRNAscan-SE/) | tRNA genes |
| [barrnap](https://github.com/tseemann/barrnap) | rRNA genes (5S, 16S, 23S) |
| [Infernal](http://eddylab.org/infernal/) + [Rfam](https://rfam.org/) | other non-coding RNAs |
| [Bakta](https://github.com/oschwengers/bakta) | full pipeline: Pyrodigal + tRNA/rRNA/ncRNA + functional annotation from a large database. **The current recommended tool.** |
| [Prokka](https://github.com/tseemann/prokka) | the older full pipeline (Prodigal + names from UniProt); still widely used but no longer updated |
| [NCBI PGAP](https://github.com/ncbi/pgap) | the pipeline NCBI uses to annotate RefSeq genomes; slower but required style for GenBank submission |

### Bakta

Bakta needs a large database; the cluster has a shared copy.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J bakta
#SBATCH -o logs/%x.%j.log
module load bakta

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
BAKTA_DB=/srv/projects/db/bakta/4.0

bakta --db $BAKTA_DB --threads $CPU --output bakta --prefix Lmono_EGDe \
      --genus Listeria --species monocytogenes --strain EGD-e \
      genome.fasta
```

The output folder has a GFF3 (`.gff3`), GenBank (`.gbff`), proteins (`.faa`), a summary (`.txt`) and a circular genome plot (`.png`/`.svg`).

```bash
cat bakta/Lmono_EGDe.txt
```

---

# Part 2: Eukaryotes

Eukaryotic genes are much harder to predict:

* genes have **introns**, so the predictor must find the splice sites (`GT...AG`) and the correct reading frame across every exon
* genes can be far apart and the genome can be mostly non-coding (only ~1-2% of the human genome codes for protein; ~40-60% of a fungal genome)
* **repeats and transposons** contain ORFs that look like genes
* **alternative splicing** - one gene can make several different transcripts
* UTRs (untranslated regions), non-coding RNA genes, pseudogenes

## Demo data

We will use *Zancudomyces culisetae* strain HAW-14-8 (ARSEF 9014), a gut fungus of mosquito larvae (Harpellales, Kickxellomycotina). Its genome is small (~27 Mb) and it was sequenced with Illumina, Nanopore and PacBio, plus RNA-Seq (Yang & Wang 2025, *G3* [doi:10.1093/g3journal/jkaf204](https://doi.org/10.1093/g3journal/jkaf204); BioProject [PRJNA1254182](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1254182)).

| Data | Accession | Size |
| ---- | --------- | ---- |
| Genome assembly (PacBio HiFi, 26 contigs) | [GCA_052426225.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCA_052426225.1/) | 27.1 Mb |
| RNA-Seq (NovaSeq 2x150) | [SRR33256489](https://www.ncbi.nlm.nih.gov/sra/SRR33256489) | 22.9 M read pairs, 3.3 GB |
| Published BRAKER proteins and CDS | [Zenodo 10.5281/zenodo.15271765](https://doi.org/10.5281/zenodo.15271765) | |
| Proteins from related species | UniProt Swiss-Prot reviewed fungal proteins (38,561) | 20 MB |

The authors published their predicted proteins and coding sequences but not a GFF file of the gene models, so in this lecture we compare our predictions to each other and to their protein set.

```bash
mkdir -p ~/bigdata/Annotation/euk
cd ~/bigdata/Annotation/euk
mkdir -p logs fastq
ln -sf /bigdata/gen220/shared/data/assembly/Zculisetae/genome.fasta .
ln -sf /bigdata/gen220/shared/data/assembly/Zculisetae/published_braker.aa.fasta .
# BRAKER runs in a container that can only see this folder, so copy (don't link) the proteins
cp /bigdata/gen220/shared/data/assembly/Zculisetae/swissprot_fungi.fasta .
ln -sf /bigdata/gen220/shared/data/assembly/Zculisetae/fastq/* fastq/
```

To download the data yourself:

```bash
module load ncbi_datasets
datasets download genome accession GCA_052426225.1 --include genome
unzip ncbi_dataset.zip
cp ncbi_dataset/data/GCA_052426225.1/*.fna genome.fasta
# RNA-Seq from the SRA (run this inside a job, from $SCRATCH; see the Assembly lecture)
module load sratoolkit
prefetch SRR33256489
fasterq-dump --threads 8 --split-files -O fastq SRR33256489/SRR33256489.sra
pigz fastq/SRR33256489_*.fastq
```

## Step 1: Mask repeats

Mask repeats **before** gene prediction, so the predictor doesn't call transposon ORFs as genes.

* **Soft-masking** changes repeats to lower case (`acgt`) - the sequence is kept, and predictors can choose to avoid starting genes there. This is what most predictors want.
* **Hard-masking** replaces repeats with `N`.

[RepeatModeler](https://github.com/Dfam-consortium/RepeatModeler) builds a library of the repeat families in *this* genome; [RepeatMasker](https://www.repeatmasker.org/) then finds and masks every copy (with the custom library and/or known repeats from [Dfam](https://www.dfam.org/)).

We use `funannotate` (see below) to prepare the genome. It removes small duplicated contigs (`clean`), sorts the contigs by size and gives them short names (`sort`), and soft-masks repeats (`mask`). Every later step uses the same `genome.masked.fasta`, so the contig names match between all of the predictions.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J mask
#SBATCH -o logs/%x.%j.log
module load funannotate

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}

funannotate clean -i genome.fasta -o genome.cleaned.fasta
funannotate sort  -i genome.cleaned.fasta -b scaffold -o genome.sorted.fasta
# -m tantan masks only simple, low-complexity repeats - fast, and good enough for class
funannotate mask  -i genome.sorted.fasta -o genome.masked.fasta -m tantan --cpus $CPU
```

For a real project, use `-m repeatmodeler` instead, which runs RepeatModeler and RepeatMasker to find the transposons too. It takes many hours, so submit it to the `epyc` partition with a longer `--time`.

## Step 2: Prepare the informant data

### RNA-Seq evidence

Align the RNA-Seq reads to the genome with a **splice-aware** aligner (see the [RNASeq](RNASeq) lecture). The spliced alignments give the intron positions, which is the strongest evidence for gene structure.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 16 --mem 32gb --time 2:00:00
#SBATCH -J hisat2
#SBATCH -o logs/%x.%j.log
module load hisat2
module load samtools

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
ACC=SRR33256489

hisat2-build -p $CPU genome.masked.fasta genome_idx
hisat2 -p $CPU -x genome_idx --max-intronlen 3000 \
    -1 fastq/${ACC}_1.fastq.gz -2 fastq/${ACC}_2.fastq.gz | \
    samtools sort --threads $CPU -o rnaseq.bam -
samtools index rnaseq.bam
```

`--max-intronlen` should match the organism: fungal introns are short (usually < 1 kb), but plant and animal introns can be 10-100 kb or more.

You can also **assemble** transcripts from the RNA-Seq, either genome-guided with [StringTie](https://ccb.jhu.edu/software/stringtie/) or de novo with [Trinity](https://github.com/trinityrnaseq/trinityrnaseq). Pipelines like [PASA](https://github.com/PASApipeline/PASApipeline) (used inside funannotate) align these transcripts to the genome and use them to build gene models and add UTRs.

```bash
module load stringtie
stringtie -p 8 -o stringtie.gtf rnaseq.bam
```

### Protein evidence

Proteins from related species show where conserved exons are, even for genes that weren't expressed in your RNA-Seq sample.

* [OrthoDB](https://www.orthodb.org/) protein sets by clade (e.g. all Fungi, all Metazoa, Viridiplantae) are what BRAKER recommends; they are big (the Fungi set is 7.7 GB), so in class we use the smaller Swiss-Prot set.
* [UniProt/Swiss-Prot](https://www.uniprot.org/) curated proteins are what funannotate uses by default.
* Or the proteomes of a few closely related, well-annotated genomes.

[miniprot](https://github.com/lh3/miniprot) is a fast spliced protein-to-genome aligner. We use the curated (Swiss-Prot) fungal proteins from UniProt:

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J miniprot
#SBATCH -o logs/%x.%j.log
module load miniprot

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
miniprot -t $CPU --gff genome.masked.fasta swissprot_fungi.fasta > miniprot.gff
```

Older tools that do the same job (more slowly): Exonerate, GenomeThreader, ProtHint (in BRAKER), DIAMOND + Exonerate (in funannotate).

## Step 3: Gene prediction

### Ab initio predictors

| Tool | Notes |
| ---- | ----- |
| [AUGUSTUS](https://github.com/Gaius-Augustus/Augustus) | HMM predictor; can use hints from RNA-Seq and proteins; many pre-trained species |
| [GeneMark-ES / ET / EP / ETP](https://genemark.bme.gatech.edu/) | self-training (ES needs no training data); ET uses RNA-Seq introns, EP uses proteins, ETP uses both |
| [SNAP](https://github.com/KorfLab/SNAP), [GlimmerHMM](https://ccb.jhu.edu/software/glimmerhmm/) | older HMM predictors, used by MAKER and funannotate as extra predictions |
| [Helixer](https://github.com/weberlab-hhu/Helixer) | deep-learning predictor with pre-trained models for fungi, plants, invertebrates and vertebrates; needs no training or evidence (runs best on a GPU) |

### AUGUSTUS

AUGUSTUS comes with trained parameters for many species. See the list with:

```bash
module load augustus
augustus --species=help
```

Run with a pre-trained species close to yours. The second run adds **hints**: AUGUSTUS can take evidence as a "hints" file (GFF lines with `src=E` for EST/RNA-Seq or `src=P` for protein) plus a config file that says how much to trust each source. `bam2hints` turns the spliced RNA-Seq alignments into intron hints.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 1 --mem 4gb --time 2:00:00
#SBATCH -J augustus
#SBATCH -o logs/%x.%j.log
module load augustus

set -euo pipefail
# no Zancudomyces model exists; rhizopus_oryzae is the closest pre-trained fungus (also distant!)
SPECIES=rhizopus_oryzae

# ab initio: genome sequence only
augustus --species=$SPECIES --gff3=on --softmasking=1 genome.masked.fasta > augustus.gff3

# with RNA-Seq intron hints
bam2hints --intronsonly --in=rnaseq.bam --out=hints.introns.gff
augustus --species=$SPECIES --gff3=on --softmasking=1 \
    --hintsfile=hints.introns.gff --extrinsicCfgFile=$AUGUSTUS_CONFIG_PATH/extrinsic/extrinsic.M.RM.E.W.cfg \
    genome.masked.fasta > augustus.hints.gff3
```

AUGUSTUS runs on one CPU, so to go faster you can split the genome into chunks (one per contig) and run them as a SLURM array job.

**Training**: for a species with no close pre-trained relative, AUGUSTUS must be trained from a set of good gene models (`etraining`, `optimize_augustus.pl`). This needs a *writeable* copy of the AUGUSTUS config folder:

```bash
cp -r $AUGUSTUS_CONFIG_PATH ~/bigdata/augustus_config
export AUGUSTUS_CONFIG_PATH=~/bigdata/augustus_config
```

Doing the training by hand is tedious - BRAKER and funannotate do it for you.

### BRAKER

[BRAKER](https://github.com/Gaius-Augustus/BRAKER) automatically trains GeneMark and AUGUSTUS using your evidence, then predicts genes with hints. Which version runs depends on the evidence you give it:

| Mode | Evidence | Command options |
| ---- | -------- | --------------- |
| BRAKER1 | RNA-Seq only | `--bam=rnaseq.bam` |
| BRAKER2 | proteins only | `--prot_seq=proteins.fa` |
| BRAKER3 | RNA-Seq **and** proteins (best) | `--bam=rnaseq.bam --prot_seq=proteins.fa` |

[GALBA](https://github.com/Gaius-Augustus/GALBA) is a related pipeline for when you only have proteins from very closely related species.

BRAKER has many dependencies, so the cluster module runs it from a container (Singularity). The container can only see files in the folder you run it from, so the genome, BAM file and proteins must be real files there, not links to other folders. For real projects use the OrthoDB protein set for your clade from the [BRAKER OrthoDB page](https://bioinf.uni-greifswald.de/bioinf/partitioned_odb12/).

```bash
#!/bin/bash -l
#SBATCH -p epyc -N 1 -n 1 -c 16 --mem 64gb --time 24:00:00
#SBATCH -J braker3
#SBATCH -o logs/%x.%j.log
module load braker/3.0.8

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
PROTEINS=swissprot_fungi.fasta

braker.pl --genome=genome.masked.fasta \
    --bam=rnaseq.bam --prot_seq=$PROTEINS \
    --species=Zculisetae_braker --fungus --gff3 \
    --threads=$CPU --workingdir=braker
```

`--fungus` turns on the GeneMark branch-point model for fungal introns; leave it off for other eukaryotes. The final predictions are in `braker/braker.gff3`, `braker/braker.aa` and `braker/braker.codingseq`.

### funannotate

[funannotate](https://github.com/nextgenusfs/funannotate) is a complete annotation pipeline developed for fungi (it also works for other small eukaryotes). It runs several predictors (AUGUSTUS, GeneMark, SNAP, GlimmerHMM, and optionally BRAKER/PASA predictions), weights them with the evidence, and combines them into one consensus set with [EVidenceModeler](https://github.com/EVidenceModeler/EVidenceModeler). It also produces files ready for GenBank submission.

The main steps:

| Step | What it does |
| ---- | ------------ |
| `funannotate clean` | remove small contigs that are duplicates of larger ones |
| `funannotate sort` | sort contigs by length and give them simple names (NCBI requires names < 16 characters) |
| `funannotate mask` | soft-mask repeats (tantan, RepeatMasker or RepeatModeler) |
| `funannotate train` | use the RNA-Seq to build transcripts (Trinity + PASA) and high-quality training genes |
| `funannotate predict` | train and run the ab initio predictors with the evidence, combine with EVM |
| `funannotate update` | use the RNA-Seq again to add UTRs and alternative transcripts (PASA) |
| `funannotate annotate` | add functional annotation (Pfam, InterPro, eggNOG, CAZymes, MEROPS, BUSCO, ...) |

```bash
#!/bin/bash -l
#SBATCH -p epyc -N 1 -n 1 -c 16 --mem 64gb --time 48:00:00
#SBATCH -J funannotate
#SBATCH -o logs/%x.%j.log
module load funannotate

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
SPECIES="Zancudomyces culisetae"
STRAIN=HAW-14-8
ACC=SRR33256489
# funannotate trains AUGUSTUS, so it needs a writeable copy of the AUGUSTUS config folder
if [ ! -d ~/bigdata/augustus_config ]; then
    cp -r /opt/linux/rocky/8.x/x86_64/pkgs/augustus/3.5.0/env/config ~/bigdata/augustus_config
fi
export AUGUSTUS_CONFIG_PATH=~/bigdata/augustus_config

# genome.masked.fasta was made with funannotate clean/sort/mask in Step 1
# RNA-Seq: Trinity + PASA (use --stranded RF for dUTP stranded libraries, or no)
funannotate train -i genome.masked.fasta -o fun \
    --left fastq/${ACC}_1.fastq.gz --right fastq/${ACC}_2.fastq.gz \
    --stranded no --jaccard_clip \
    --species "$SPECIES" --strain $STRAIN --cpus $CPU

funannotate predict -i genome.masked.fasta -o fun \
    --species "$SPECIES" --strain $STRAIN \
    --busco_db fungi --cpus $CPU

funannotate update -i fun --cpus $CPU
```

The predictions are in `fun/predict_results/` (after `predict`) and `fun/update_results/` (after `update`): `.gff3`, `.proteins.fa`, `.mrna-transcripts.fa`, and `.gbk`/`.tbl` files for NCBI. Look at `fun/logfiles/funannotate-predict.log` to see how many genes each predictor found and how EVM weighted them.

---

# Part 3: Evaluating gene predictions

There is no single right answer for gene prediction, so we compare different evidence and different versions.

## Summary statistics

Start with the basic numbers: number of genes, mean gene/exon/intron length, exons per gene, single-exon genes. [AGAT](https://github.com/NBISweden/AGAT) has many tools for GFF files, including statistics and format fixes:

```bash
module load agat/1.4.0
agat_sp_statistics.pl --gff braker/braker.gff3 -o braker.stats.txt
agat_sp_statistics.pl --gff fun/update_results/*.gff3 -o funannotate.stats.txt
```

Compare the methods to each other and to related species. Red flags: far too many genes (repeats predicted as genes, or genes split in pieces), far too few (merged genes or missing evidence), or lots of very short single-exon genes.

## Extract the proteins

Make the protein sequences from any GFF3 + genome with [gffread](https://github.com/gpertea/gffread):

```bash
module load gffread
gffread -g genome.masked.fasta -y augustus.proteins.fa augustus.gff3
# proteins with internal stop codons ('.' or '*') mean a broken gene model
grep -v ">" augustus.proteins.fa | grep -c "\*.\+"
```

## BUSCO in protein mode

Run BUSCO (see [Genome Assembly](Assembly)) on the **predicted proteins** with `-m proteins`. Compare it to BUSCO in `-m genome` mode on the assembly:

* genome BUSCO tells you how complete the **assembly** is
* protein BUSCO tells you how many of those genes the **annotation** found correctly

If the genome BUSCO is 98% complete but the protein BUSCO is 85%, the gene predictor missed or broke ~13% of the conserved genes.

```bash
#!/bin/bash -l
#SBATCH -p short -N 1 -n 1 -c 8 --mem 16gb --time 2:00:00
#SBATCH -J busco_prot
#SBATCH -o logs/%x.%j.log
module load busco

set -euo pipefail
CPU=${SLURM_CPUS_PER_TASK:-1}
LINEAGE=fungi_odb12.2   # no more specific lineage for Kickxellomycotina

for PROT in augustus.proteins.fa braker/braker.aa fun/update_results/*.proteins.fa
do
    NAME=$(basename $PROT .fa)
    busco -i $PROT -m proteins -l $LINEAGE -c $CPU -o busco_$NAME --out_path busco --offline --download_path $BUSCO_LINEAGES
done
busco -i genome.masked.fasta -m genome -l $LINEAGE -c $CPU -o busco_genome --out_path busco --offline --download_path $BUSCO_LINEAGES
```

A high **Duplicated** count in protein mode often means the predictor made several overlapping models for one gene, or the file has every alternative transcript (keep one protein per gene before running BUSCO).

## RNA-Seq support: are the predicted exons expressed?

A gene model is believable when RNA-Seq reads cover its exons and spliced reads match its introns. Use the `rnaseq.bam` from above.

**Exons covered by reads** - pull out the exons and count reads on each with `bedtools` (see [Genomic Data Ranges](Ranges_Features_overlap)):

```bash
module load bedtools
module load samtools

# exons from the GFF3 as BED (GFF is 1-based, BED is 0-based)
awk -F'\t' 'BEGIN{OFS="\t"} $3=="exon" {print $1,$4-1,$5,$9,".",$7}' braker/braker.gff3 | \
    sort -k1,1 -k2,2n > braker.exons.bed

# number of reads overlapping each exon (column 7)
bedtools multicov -bams rnaseq.bam -bed braker.exons.bed > braker.exons.counts.bed

# fraction of exons with at least 5 reads
awk '{n++; if ($7 >= 5) e++} END {printf "%d of %d exons (%.1f%%) have >= 5 reads\n", e, n, 100*e/n}' braker.exons.counts.bed
```

(If the exon features are missing, use `$3=="CDS"`.)

**Introns supported by spliced reads** - the `hints.introns.gff` file from the AUGUSTUS step lists every intron seen in the RNA-Seq alignments, with the number of reads in `mult=`. Turn both it and the annotated introns into BED files and count the exact matches:

```bash
module load agat/1.4.0
module load bedtools

# RNA-Seq introns: chrom, start, end, number of reads (no mult= means 1 read)
awk -F'\t' 'BEGIN{OFS="\t"} {n=1; if (match($9, /mult=[0-9]+/)) n=substr($9, RSTART+5, RLENGTH-5); print $1,$4-1,$5,n}' \
    hints.introns.gff | sort -k1,1 -k2,2n > rnaseq.introns.bed

# annotated introns (AGAT adds intron features between the exons)
agat_sp_add_introns.pl --gff braker/braker.gff3 -o braker.introns.gff3
awk -F'\t' 'BEGIN{OFS="\t"} $3=="intron" {print $1,$4-1,$5}' braker.introns.gff3 | sort -k1,1 -k2,2n -u > braker.introns.bed

# -f 1.0 -r : both ends must match exactly
wc -l < braker.introns.bed
bedtools intersect -a braker.introns.bed -b rnaseq.introns.bed -f 1.0 -r -u | wc -l
```

**Exercise**: write a short Python script that reads `rnaseq.introns.bed` and `braker.introns.bed` and reports (1) how many annotated introns are supported by at least 3 reads, and (2) how many well-supported RNA-Seq introns (>= 10 reads) are *not* in the annotation - possible missed genes or exons.

## Comparing annotations with gffcompare

[gffcompare](https://ccb.jhu.edu/software/stringtie/gffcompare.shtml) compares a predicted annotation to a reference annotation (or two versions to each other) and reports how many bases, exons, introns, transcripts and genes (loci) match.

For a model organism you would use the curated annotation as the reference (`-r`). *Z. culisetae* has no published GFF, so we use one of our own predictions as the reference and ask how much the others agree with it. Here we treat the funannotate `update` models (which use the RNA-Seq the most) as the reference and compare the BRAKER prediction to them.

```bash
module load gffcompare
cp fun/update_results/*.gff3 funannotate.gff3
gffcompare -r funannotate.gff3 -o cmp_braker braker/braker.gff3
cat cmp_braker.stats
```

```text
#= Summary for dataset: braker/braker.gff3
#     Query mRNAs :    6012 in    5980 loci  (5113 multi-exon transcripts)
#= Reference mRNAs :    6600 in    6582 loci  (...)
#-----------------| Sensitivity | Precision  |
        Base level:    95.1     |    96.2    |
        Exon level:    80.4     |    82.0    |
      Intron level:    90.3     |    91.5    |
Intron chain level:    75.2     |    78.0    |
  Transcript level:    70.3     |    71.1    |
       Locus level:    72.0     |    73.5    |
```

(These numbers are only an example.)

* **Sensitivity** = fraction of the *reference* features found by the prediction (how much did we find?)
* **Precision** = fraction of the *predicted* features that are in the reference (how much of what we predicted is right?)
* *Exon* and *intron* matches must be exact at both ends, so they are much harder than *base* level. *Intron chain* means every intron of the transcript matches.

The `cmp_braker.braker.gff3.tmap` file lists, for each predicted transcript, the closest reference transcript and a **class code**:

| Code | Meaning |
| ---- | ------- |
| `=` | all introns match the reference exactly |
| `c` | contained in a reference transcript (fragment) |
| `k` | contains a reference transcript |
| `j` | at least one intron matches, but not all (different structure) |
| `e`, `o` | overlaps a reference exon / gene on the same strand |
| `x` | overlaps a reference gene on the opposite strand |
| `i` | entirely inside a reference intron |
| `u` | intergenic - no overlap with any reference gene (new gene, or a false prediction) |

```bash
# count predictions by class code (column 3)
cut -f3 cmp_braker.braker.gff3.tmap | sort | uniq -c | sort -nr
```

Compare **versions** the same way. For example, compare the funannotate `predict` and `update` results, or BRAKER with and without RNA-Seq, by giving several files at once. The `cmp_all.tracking` file then shows which transcripts each method shares. (Without `-r`, gffcompare just merges and compares the inputs to each other.)

```bash
gffcompare -r funannotate.gff3 -o cmp_all augustus.hints.gff3 augustus.gff3 braker/braker.gff3 fun/update_results/*.gff3
```

**Questions**:

1. Which method has the highest sensitivity and precision at the exon and transcript levels?
2. How much does adding RNA-Seq evidence improve AUGUSTUS compared to the ab initio run?
3. Look at the `u` (intergenic) predictions. Do they have RNA-Seq support? Do they have BLAST hits to proteins in other species? Are they new genes, or overlapping repeats?
4. Our "reference" here is also a prediction. Are there funannotate genes with **no** RNA-Seq support? Which method's genes have the best RNA-Seq support overall?
5. Compare your predicted proteins to the published BRAKER proteins (`published_braker.aa.fasta`) with BLASTP or DIAMOND. How many of your proteins have an identical (100% identity, full length) match?

## Viewing annotations

Load the genome, the different GFF3 files and the RNA-Seq BAM into [IGV](https://igv.org/) or [JBrowse 2](https://jbrowse.org/jb2/) (see [Genome Browsers](Genome_Browsers)) and look at genes where the predictions disagree. Seeing the reads, the spliced alignments and the gene models side by side is the best way to understand why a predictor made a mistake.

## Further reading

* Hyatt D et al. (2010) Prodigal: prokaryotic gene recognition and translation initiation site identification. *BMC Bioinformatics* 11:119. [doi:10.1186/1471-2105-11-119](https://doi.org/10.1186/1471-2105-11-119)
* Schwengers O et al. (2021) Bakta: rapid and standardized annotation of bacterial genomes via alignment-free sequence identification. *Microb Genom* 7:000685. [doi:10.1099/mgen.0.000685](https://doi.org/10.1099/mgen.0.000685)
* Stanke M et al. (2006) AUGUSTUS: ab initio prediction of alternative transcripts. *Nucleic Acids Res* 34:W435-W439. [doi:10.1093/nar/gkl200](https://doi.org/10.1093/nar/gkl200)
* Gabriel L et al. (2024) BRAKER3: Fully automated genome annotation using RNA-seq and protein evidence with GeneMark-ETP, AUGUSTUS, and TSEBRA. *Genome Res* 34:769-777. [doi:10.1101/gr.278090.123](https://doi.org/10.1101/gr.278090.123)
* Palmer JM, Stajich JE (2020) Funannotate. [doi:10.5281/zenodo.1134477](https://doi.org/10.5281/zenodo.1134477)
* Pertea G, Pertea M (2020) GFF Utilities: GffRead and GffCompare. *F1000Research* 9:304. [doi:10.12688/f1000research.23297.2](https://doi.org/10.12688/f1000research.23297.2)
* Yandell M, Ence D (2012) A beginner's guide to eukaryotic genome annotation. *Nat Rev Genet* 13:329-342. [doi:10.1038/nrg3174](https://doi.org/10.1038/nrg3174)
