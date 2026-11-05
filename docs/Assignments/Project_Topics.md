Project Topics
=====

**Contents**

* [Project overview](#project-overview): requirements, [deliverables and timeline](#deliverables-and-timeline), scoping advice

**Project ideas**

* [Mutating for Fun](#mutating-for-fun)
* [Transporterland](#transporterland)
* [From SNPs to Genes to Functions](#from-snps-to-genes-to-functions)
* [Genome (RE)assembly and Organelle Genomes](#genome-reassembly-and-organelle-genomes)
* [Secondary Metabolism: Biosynthetic Gene Clusters](#secondary-metabolism-biosynthetic-gene-clusters)
* [Gene Structure Across Species ("Team Gene")](#gene-structure-across-species-team-gene)
* [Transcriptome Differences ("Team Transcriptome")](#transcriptome-differences-team-transcriptome)
* [Protein Content and Adaptation ("Team Proteins")](#protein-content-and-adaptation-team-proteins)
* [Hidden Passengers ("Team Russian Doll")](#hidden-passengers-team-russian-doll)
* [Microbiome and Metagenome Comparisons ("Team Microbiome")](#microbiome-and-metagenome-comparisons-team-microbiome)
* [Superfolding: Protein Structure Prediction](#superfolding-protein-structure-prediction)
* [Workflow Engineering (Nextflow / Snakemake)](#workflow-engineering-nextflow-snakemake)
* [Propose your own](#propose-your-own)

---

# Project overview

Projects are done in teams of 2-3 and are 50% of the course grade. The goal is to ask a biological question that can be answered with public data, build a reproducible pipeline (shell, Python, SLURM; Nextflow/Snakemake optional) to answer it, and report what you found, including what did not work.

A good project has these parts:

1. **A question or hypothesis** that can be answered yes/no or with a number ("Do UV-derived mutants show more C>T transitions than EMS-derived mutants?"), not just "run tool X on data Y".
2. **Public data** you can download without special permission (NCBI SRA/GenBank/RefSeq, Ensembl, FungiDB/EnsemblFungi, UniProt, Pfam/InterPro, 1000 Genomes, etc.). Check early that the data exist and are small enough to process on the HPCC.
3. **A pipeline** that goes from raw input to a result table or figure, with scripts in your team's GitHub repository. Someone else should be able to re-run it from your README.
4. **A comparison or control** so that the result means something (a second species, a second condition, shuffled/simulated data, a known answer).
5. **Interpretation**: what does the result tell you, how confident are you, and what would you do next?

## Deliverables and timeline

| When | What |
| :--- | :--- |
| Oct-22 (Th) | Topics presented; start forming teams |
| Oct-29 (Th) | **Abstract due:** team members, question, data source(s), tools, expected outputs (about half a page) |
| Nov-17 (Tu) | **Halfway milestone:** short progress report (repository link, pipeline running on at least one sample/species, first results or a table/figure, problems) |
| Dec-3 (Th) | **Presentation:** 10 minute class presentation ([info](Project_Presentation)) |
| Dec-9 (Wed) | **Final report due** ([template](Project_Report_Template)); must include each person's contribution |

## Choosing and scoping a project

* Start small: get one sample or one species working end to end, then scale up with a loop, SLURM array job, or workflow.
* Prefer data that are small enough to run in minutes to an hour per sample. Bacterial and fungal genomes and subsampled reads are good starts; a full human genome is not.
* Every topic below has a *core* task (everyone should reach it) and *extensions* (pick one if time allows). You may also propose your own idea - talk to me before the abstract is due.
* Using AI coding tools is fine, but you must be able to explain and test every step. Validate against a known answer or simulated data.

---

# Mutating for Fun

**Idea:** Find the mutations in strains derived from a mutagenesis or evolution experiment and describe their pattern.

**Questions that can be tested**

* Which genes carry candidate causal mutations in each isolate relative to the reference genome? Are the same genes hit in independent isolates (parallel evolution)?
* Is there a mutational bias? EMS should give mostly G:C > A:T transitions, UV mostly C>T at dipyrimidines, and spontaneous mutation spectra differ again. Can you tell the mutagen from the spectrum alone?
* What fraction of mutations are synonymous, missense, nonsense, frameshift or intergenic? Is that different from random expectation given gene length and codon content (simulate random mutations on the reference to get the null)?
* How many mutations do you detect as a function of read depth? Where do false positives come from (repeats, low mapping quality)?
* In a mapping-by-sequencing design (mutant vs. wild-type bulks), does allele frequency along chromosomes point to the causal region?

**Data:** Lenski *E. coli* long-term evolution experiment ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4988878/), [Data Carpentry download guide](https://datacarpentry.github.io/organization-genomics/data)); Arabidopsis mapping-by-sequencing ([Nucleic Acids Res.](https://academic.oup.com/nar/article/47/21/e140/5572568)); or any small bacterial/yeast mutant collection in SRA.

**Tools:** BWA, samtools, bcftools or GATK, bedtools (SNPs/variants and ranges lectures), a GFF for effect annotation (SnpEff or your own Python).

**Extensions:** Simulate mutations with a known spectrum and measure your pipeline's sensitivity/precision; compare two variant callers; make a Circos-style or Manhattan plot of mutation density.

---

# Transporterland

**Idea:** Build a tool to catalog the transporter proteins in a proteome and compare across species.

**Questions that can be tested**

* How many members of a family (e.g. MFS, ABC, amino acid/polyamine permeases, P-type ATPases, aquaporins) does each species encode, and does that track lifestyle? (Do parasites/obligate symbionts lose transporters? Do plant-associated or saprotrophic fungi expand sugar transporters?)
* Is the number of predicted transmembrane (TM) helices consistent within a family (e.g. MFS typically 12; some families 10, 14, or 4)? Which proteins are outliers, and are they mis-annotated gene models?
* Do the families expanded in one species cluster as recent duplicates (tandem arrays in the genome, high % identity), or are they ancient orthologs shared across species?
* Does a Pfam-HMM-only definition give the same set as BLAST against curated transporters (TCDB)? Where do they disagree?

**Data:** Proteomes from UniProt/RefSeq/EnsemblFungi for 3-10 species chosen to contrast lifestyle; Pfam HMMs (e.g. Sugar_tr PF00083, MFS_1 PF07690, ABC_tran PF00005, AA_permease PF00324); [TCDB](https://tcdb.org) as a reference set.

**Tools:** HMMER (`hmmsearch`), TM predictors (DeepTMHMM, Phobius, or TMHMM if available), BLAST, Python/pandas for summary tables.

**Extensions:** Cluster families with orthology tools; align and make a tree of one family; test for GO or domain enrichment among the species-specific expanded families.

Quick links:

* <https://en.wikipedia.org/wiki/Membrane_transport_protein>
* <https://en.wikipedia.org/wiki/Ion_transporter>

---

# From SNPs to Genes to Functions

**Idea:** Take a VCF from a population or strain collection, map variants onto a GFF gene annotation, and ask what kinds of genes are changing.

**Questions that can be tested**

* What proportion of variants fall in coding, intronic, UTR, splice-site, and intergenic regions, and how does this compare to the proportion of the genome in each?
* Is the ratio of nonsynonymous to synonymous variants (per gene) different from 1 or from the genome average? Which genes have an excess of high-impact (nonsense, frameshift, splice) variants?
* Are variants enriched in particular functional classes - Pfam domains, GO terms, or pathways (e.g. defense/NLR genes, transporters, secreted proteins)? Use a hypergeometric/Fisher test and correct for multiple testing.
* Do variants cluster in particular regions of chromosomes (hotspots), and is that explained by gene density or mapping problems?
* How do results change if you filter variants by quality or allele frequency?

**Data:** Any VCF + GFF + genome FASTA. Examples: yeast 1002 genomes, *Arabidopsis* 1001 genomes subsets, fungal population datasets, or the course HW variant data.

**Tools:** Python (pandas, regex or a GFF parser), bedtools intersect, `scipy.stats`, GO annotation from UniProt/InterPro.

**Extensions:** Write the pipeline so any VCF/GFF pair works from the command line (argparse); add a simulated-random-variant control.

---

# Genome (RE)assembly and Organelle Genomes

**Idea:** Newer assemblers and organelle-targeted tools can recover sequences missing from deposited assemblies.

**Questions that can be tested**

* Does a modern assembler give a more contiguous assembly than the published one (N50, number of contigs, BUSCO completeness)? What is gained or lost?
* Can you assemble and circularize the mitochondrial (or chloroplast, plasmid) genome from reads that were only used for the nuclear assembly? Does its size and gene content (tRNA, rRNA, cox/nad genes) match closely related species?
* Are there contigs in the deposited assembly that are actually organelle or contaminant (read coverage much higher/lower, different GC)?

**Data:** A list of [SRA](https://www.ncbi.nlm.nih.gov/sra) accessions for fungal or small eukaryotic or bacterial genomes; subsample reads to make runs tractable.

**Tools:** NOVOPlasty, AAFTF, Unicycler, SPAdes, BUSCO, QUAST, mitochondrial annotation (MITOS, or BLAST against related mt genomes).

**Extensions:** Compare gene order across several species' mitochondrial genomes.

---

# Secondary Metabolism: Biosynthetic Gene Clusters

**Idea:** Many bacteria and fungi make natural products (antibiotics, toxins, pigments) from clustered genes: polyketide synthases (PKS), nonribosomal peptide synthetases (NRPS), terpene synthases and others.

**Questions that can be tested**

* How many secondary metabolite clusters (and what types) does each genome have? Does the count differ with lifestyle or taxonomy (e.g. *Streptomyces* vs. other bacteria; plant pathogens vs. saprobes among fungi)?
* Are the core enzymes (PKS, NRPS) conserved between species? Build a tree from the KS or A domains: do they form clusters by predicted product rather than by species?
* Do clusters tend to sit near chromosome ends or in regions with lower conservation (use synteny/ortholog presence)?
* Do known clusters (e.g. aflatoxin, penicillin, a siderophore) get found by your pipeline?

**Data:** Genomes with GFF annotations (RefSeq/EnsemblFungi) for 3-10 species; MIBiG reference clusters for validation.

**Tools:** antiSMASH (web or command line) or your own HMM-based detection (Pfam KS, AMP-binding, Condensation, Terpene_synth); MAFFT + FastTree/IQ-TREE for comparisons; Python for summary.

**Extensions:** Compare cluster content to MIBiG and report which clusters are likely novel.

---

# Gene Structure Across Species ("Team Gene")

**Idea:** Use GFF annotations to measure features of genes.

**Questions that can be tested**

* How do gene length, exon number, intron length, and UTR length differ among species or lineages? Are genes in compact genomes (yeast, many fungi) different from large-genome organisms (plants, animals)?
* Is intron length correlated with gene expression level or with genome size?
* Do GC content or codon usage differ between exons of highly and lowly expressed genes?
* Are annotation methods a confounder (different annotation pipelines can give different UTR/intron results)? How would you check?

**Data:** GFF3 + genome FASTA for 5+ species; optional RNA-seq for expression.

**Tools:** Python (pandas, matplotlib/seaborn), bedtools, gffutils or your own parser.

---

# Transcriptome Differences ("Team Transcriptome")

**Idea:** Find genes that change under a condition and say what they do.

**Questions that can be tested**

* Which genes are differentially expressed between two conditions with replicates? Are replicates more similar to each other than to other conditions (PCA/correlation)?
* Are up- and down-regulated genes enriched for particular functional classes (GO, Pfam, KEGG)?
* How sensitive is the answer to the choice of aligner/quantifier or to the fold-change and p-value cutoffs?
* Do the results agree with the published paper's findings?

**Data:** Public RNA-seq with at least 2 conditions x 3 replicates in SRA/GEO from a small genome (yeast, fungus, bacterium, Arabidopsis); subsample reads to save time.

**Tools:** HISAT2/STAR or Salmon/kallisto, featureCounts/htseq-count, DESeq2 or edgeR (R) or PyDESeq2; enrichment test in Python/R.

---

# Protein Content and Adaptation ("Team Proteins")

**Idea:** Does protein sequence content reflect lifestyle?

**Questions that can be tested**

* Do thermophiles vs. mesophiles differ in amino acid composition (e.g. more charged residues Glu/Lys/Arg, fewer Gln/Asn/Thr)? Can a simple classifier (logistic regression/random forest from amino acid frequencies) predict growth temperature for held-out species? Does it work for halophiles (acidic proteome)?
* Which Pfam domains are over- or under-represented among species from different environments? Which are species-specific?
* Does the predicted isoelectric point distribution of the proteome differ between environments?
* Which proteins are outliers, and what are they?

**Data:** Proteomes from 10-30 species with known growth temperature or salinity (e.g. from BacDive, or the species descriptions); Pfam annotation by HMMER.

**Tools:** Biopython (`ProtParam`), HMMER, scikit-learn, pandas.

---

# Hidden Passengers ("Team Russian Doll")

**Idea:** Genome assemblies and read sets often contain unexpected organisms: bacteria in eukaryote assemblies, phages in bacteria.

**Questions that can be tested**

* Do any contigs in a set of published eukaryotic assemblies match bacterial genomes (taxonomic assignment by BLAST/DIAMOND or k-mer tools) and do they differ in coverage and GC from the host contigs? Are they contamination or true endosymbionts/horizontal transfer?
* What fraction of bacterial genomes in a set contain prophage? Does prophage content relate to genome size or lifestyle?
* Do gene content and GC of putative integrated viruses differ from the host?

**Data:** Eukaryotic assemblies and reads from SRA (insects, nematodes, and protists are known to carry endosymbionts), RefSeq bacterial genomes.

**Tools:** BLAST/DIAMOND, Kraken2 or Centrifuge, geNomad/VirSorter2/PHASTER (phage detection), samtools for coverage.

---

# Microbiome and Metagenome Comparisons ("Team Microbiome")

**Idea:** Compare communities between sites, hosts, or treatments.

**Questions that can be tested**

* Does community composition (taxa abundances at genus or family level) differ between conditions? Use alpha diversity (Shannon) and beta diversity (Bray-Curtis) with a PCoA plot.
* Which taxa are differentially abundant, and does that fit expectations from the original study?
* In metagenomes, are specific enzyme classes or Pfam domains (e.g. cellulases, antibiotic resistance genes, nitrogen metabolism) more abundant in one dataset than another, after normalizing for sequencing depth?
* How robust are your results to rarefaction or subsampling?

**Data:** Published OTU/ASV tables (start from the processed table, not raw reads) or subsampled metagenomes from SRA/MGnify.

**Tools:** Python (pandas, scipy, matplotlib), scikit-bio, HMMER or DIAMOND against reference sets.

---

# Superfolding: Protein Structure Prediction

**Idea:** Use predicted structures to learn something about a protein or family.

**Questions that can be tested**

* Do predicted structures of family members share a fold even when their sequence identity is low? How well do predicted models (pLDDT) agree with a known experimental structure for a protein that has one?
* Are low-confidence regions of a protein also predicted as intrinsically disordered or as transmembrane segments?
* Do mutations found in a variant dataset fall in confident, buried positions more than expected?

**Data:** Proteins of interest from UniProt; [AlphaFold Database](https://alphafold.ebi.ac.uk) precomputed models; PDB.

**Tools:** [ColabFold notebook](https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/AlphaFold2.ipynb) (runs on Google Colab), Biopython PDB module, a structure viewer (PyMOL/ChimeraX/Mol*), Foldseek for structure comparison.

---

# Workflow Engineering (Nextflow / Snakemake)

**Idea:** Rather than a new biological question, build a robust workflow for a task from this course and evaluate it. Best suited for students with prior programming experience.

**Questions that can be tested**

* Can a [Nextflow](https://www.nextflow.io/) (see also [nf-core](https://nf-co.re/)) or [Snakemake](https://snakemake.readthedocs.io/en/stable/) pipeline reproduce a result you or a published paper obtained by hand (e.g. the variant calling or RNA-seq pipelines above)?
* Does it scale: how does runtime change with 1, 5, 20 samples on the HPCC with SLURM? Where are the bottlenecks?
* Does it resume correctly after a failure, and does a collaborator get the same output from your README?

**Deliverable:** A workflow repository with a test dataset, config file, documentation, and a short benchmark.

---

# Propose your own

Have a question from your own research? Bring it. A short abstract (question, data source, what the pipeline would do, how you would know it worked) is enough to start the conversation. Data from your lab can be used only if you can share enough of it (or a subsample) with the team and instructor.

Requirement to check before you commit to a topic:

* Where will the data come from, and how big is it?
* What is the control or comparison?
* What would a "negative" result look like, and would you still have something to report?
