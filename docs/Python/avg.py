#!/usr/bin/env python3
"""avg.py: a small example of a function that can be run or imported.

Run it as a script:      python3 avg.py
Import it from another:  from avg import average
"""


def average(values):
    """Return the mean of a list of numbers (0.0 for an empty list)."""
    if len(values) == 0:
        return 0.0
    total = 0.0
    for value in values:
        total += value
    return total / len(values)


if __name__ == "__main__":
    # this part runs only when the file is run directly, not when imported
    assert average([2, 4]) == 3.0
    assert average([]) == 0.0
    exon_lengths = [100, 200, 300, 150, 110, 99]
    print(f"mean exon length: {average(exon_lengths):.1f} bp")
