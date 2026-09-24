#!/usr/bin/env python3
"""Workshop problem 4: summary statistics for the yeast ORF FASTA file."""
import gzip
from collections import Counter

fastafile = "S_cerevisiae.ORFs.fasta.gz"


def read_fasta(filename):
    """Read a FASTA file (plain or .gz) and return a dict of id -> sequence."""
    opener = gzip.open if filename.endswith(".gz") else open
    pieces = {}
    seq_id = None
    with opener(filename, "rt") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(">"):
                seq_id = line[1:].split()[0]
                pieces[seq_id] = []
            elif seq_id is not None and line:
                pieces[seq_id].append(line)
    return {sid: "".join(parts) for sid, parts in pieces.items()}


def gc_content(seq):
    """Return the fraction of G and C bases in seq (0.0 if seq is empty)."""
    if len(seq) == 0:
        return 0.0
    seq = seq.upper()
    return (seq.count("G") + seq.count("C")) / len(seq)


def strand_from_name(name):
    """Return 'W' or 'C' from a yeast systematic name, or 'other'."""
    if name.startswith("Y") and len(name) >= 7 and name[6] in "WC":
        return name[6]
    return "other"


def print_percent_table(counter, total, top=5):
    """Print the most common items of a Counter with their percentages."""
    for item, n in counter.most_common(top):
        print(f"  {item}\t{n}\t{100 * n / total:.1f}%")


if __name__ == "__main__":
    assert gc_content("GGAT") == 0.5
    assert strand_from_name("YAL001C") == "C"
    assert strand_from_name("YBR111W-A") == "W"
    assert strand_from_name("Q0010") == "other"

    seqs = read_fasta(fastafile)
    n = len(seqs)
    lengths = [len(seq) for seq in seqs.values()]
    print(f"1. {n} sequences; shortest {min(lengths)}, longest {max(lengths)},"
          f" mean {sum(lengths) / n:.1f} bp")

    all_gc = sum([seq.count("G") + seq.count("C") for seq in seqs.values()])
    print(f"2. overall GC content: {100 * all_gc / sum(lengths):.2f}%")

    first_codons = Counter([seq[:3] for seq in seqs.values()])
    last_codons = Counter([seq[-3:] for seq in seqs.values()])
    print("3. first codons:")
    print_percent_table(first_codons, n)
    print("   last codons:")
    print_percent_table(last_codons, n)

    strands = Counter([strand_from_name(name) for name in seqs])
    print(f"4. Watson (W): {strands['W']}  Crick (C): {strands['C']}"
          f"  other: {strands['other']}")
