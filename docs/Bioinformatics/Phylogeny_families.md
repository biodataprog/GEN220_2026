# Odds and Ends

Last day of class is usually a mix of trying to find gaps or fill in holes.

I discussed phylogenetic tree building.

```bash
# run these in an interactive session, e.g.
# srun -p short -N 1 -n 1 -c 2 --mem 4G --time 2:00:00 --pty bash -l
git clone https://github.com/biodataprog/GEN220_2025_classexamples.git
cd GEN220_2025_classexamples/Trees
module load muscle
module load fasttree
module load iqtree
module load trimal
module load clipkit
CPU=${SLURM_CPUS_PER_TASK:-1}

# build an alignment of sequences already identified as homologs
# previously I had started with MET12 (S. cerevisiae) enzyme
more  MET12.fa # single sequence
ls -l MET12.hit_seqs.fasta # the collection of homologs for MET12 in a few yeast fungi
# denovo multiple alignment - writes in multi-fasta format
muscle -align MET12.hit_seqs.fasta -output MET12.hit_seqs.fasaln

# trim sequences - using automated parameters - see http://trimal.cgenomics.org/trimal for more info
trimal -automated1 -in MET12.hit_seqs.fasaln -out MET12.hit_seqs.mfa.trim
# this is an alternative alignment trimmer
clipkit MET12.hit_seqs.fasaln 
# build a tree w fastree (FastTreeMP uses multiple processors, FastTree uses 1 processor only)
# FastTreeMP uses OpenMP: OMP_NUM_THREADS sets how many CPUs it uses
OMP_NUM_THREADS=$CPU FastTreeMP <  MET12.hit_seqs.fasaln >  MET12.hit_seqs.tre

# build a tree with IQ-TREE 3: -B = ultrafast bootstrap replicates, --alrt = SH-aLRT test replicates,
# -T = number of threads (-T AUTO instead lets IQ-TREE test and pick the optimal number)
iqtree3 -s MET12.hit_seqs.fasaln -T $CPU -B 1000 --alrt 1000
```

Some links

* [Muscle](https://www.drive5.com/muscle/) - Multiple alignment tool
* [TrimAl](http://trimal.cgenomics.org/trimal) - alignment trimming tool
* [clipkit](https://jlsteenwyk.com/ClipKIT/) - alignment trimming tool
* [HMMER](http://hmmer.org/) - HMMER - Hidden Markov Model for biosequence analyses.
* [FastTree](http://www.microbesonline.org/fasttree/) - Fast Phylogenetic Tree construction
* [IQ-TREE](http://www.iqtree.org/) - Phylogenetic Tree construction
* [RAxML](https://cme.h-its.org/exelixis/web/software/raxml/index.html); [a tutorial](http://evomics.org/learning/phylogenetics/raxml/)
* [iTOL](https://itol.embl.de/) - Tree visualization (web-based) tool
* [FigTree](http://tree.bio.ed.ac.uk/software/figtree/) - Tree visualization (can run on HPCC if you have X11 enabled: `module load figtree; figtree`)
* [ggtree](https://guangchuangyu.github.io/software/ggtree/)  - R package for Tree rendering

```bash
module load hmmer

# build an HMM from a multiple alignment
hmmbuild MET12.hmm MET12.hit_seqs.fasaln
```

This is a little circular I am searching the HMM back against the original sequences, but if you wanted to instead search this HMM against a database of proteins (eg swissprot or your collection of proteins from species)

```bash
module load hmmer
module load samtools
# domtbl is the result file which has columns of data that are parseable instead of more complicated hmmsearch output which is for viewing
hmmsearch -E 1e-3 --domtblout MET12.search.domtbl MET12.hmm DATABASE > MET12.search.hmmsearch
# you could download a database like swissprot
#curl -O https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot.fasta.gz
#gunzip uniprot_sprot.fasta.gz
DB=uniprot_sprot.fasta
# or one on the cluster
cp /srv/projects/db/Swissprot/2023_03/uniprot_sprot.fasta $DB
hmmsearch -E 1e-3 --domtblout MET12.search.domtbl MET12.hmm $DB > MET12.search.hmmsearch

# retrieve these hits
grep -v ^# MET12.search.domtbl | awk '{print $1}' | sort -u | samtools faidx -r - uniprot_sprot.fasta > MET12.sprot_hits.fasta

# to align a set of proteins back to an HMM (which is instead of doing a denovo multiple alignment and much faster)
hmmalign MET12.hmm MET12.sprot_hits.fasta  > MET12.sprot_hits.stk
# convert the stockholm format to multifasta (afa)
esl-reformat afa MET12.sprot_hits.stk > MET12.sprot_hits.fasaln
# convert the stockholm format to clustal
esl-reformat clustal MET12.sprot_hits.stk >  MET12.sprot_hits.clustalw

# rebuild a tree
clipkit MET12.sprot_hits.fasaln
# build a tree w fastree (FastTreeMP uses multiple processors, FastTree uses 1 processor only)
FastTreeMP <  MET12.sprot_hits.fasaln.clipkit >  MET12.sprot_hits.tre
# read this tree
cat MET12.sprot_hits.tre
# try copy and pasting this and opening in iTOL
# https://itol.embl.de/
```
