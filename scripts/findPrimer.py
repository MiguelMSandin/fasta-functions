#!/usr/bin/env python3

import argparse
from Bio import SeqIO

parser = argparse.ArgumentParser(description="From a targeted fasta file (t/target), find all possible specific primers/probes of length 'l', that matches at least 'm%' of the sequences (or 'M' sequences) in the targeted file and has a maximum specificity of 's%' of the sequences (or 'S' sequences) to the reference (r/reference) database.")

# Add the arguments to the parser
parser.add_argument("-t", "--target", required=True,
					help="A fasta file with the sequences you want to find a primer to match.")

parser.add_argument("-r", "--reference", dest="reference", required=True,
					help="A reference file to look against. The targeted group shouldn't be included in the reference. If you are not sure whether it is included or not use the option '-s/--specificity'.")

parser.add_argument("-o", "--output", dest="output", required=True,
					help="The name of the output fasta and log files. Please note the extensions '.fasta' and '.tsv' will be added to the specify name respectively ('output.fasta' and 'output.tsv').")

parser.add_argument("-l", "--length", dest="length", required=False, action='store', default='18+22',
					help="The desire length of the primers to be searched. Several lengths can be selected by specifying a range with a '+' sign in between. By default it will look for primers of length 18, 19, 20, 21 and 22 base pairs ('18+22').")

parser.add_argument("-s", "--specificity", dest="specificity", required=False, action='store', type=float, default=0.01,
					help="The maximum percentage of sequences that can be matched in the reference file (0 >= s >= 1). Default = 0.01")

parser.add_argument("-S", "--specificityAbs", dest="specificityAbs", required=False, action='store', type=int, default=None,
					help="Same as '-s/--specificity' but absolute values.")

parser.add_argument("-m", "--minimum", dest="minimum", required=False, action='store', type=float, default=0.8,
					help="The minimum percentage of sequences that the primer has to match in the target file (0 >= m >= 1). Default = 0.8")

parser.add_argument("-M", "--minimumAbs", dest="minimumAbs", required=False, action='store', type=int, default=None,
					help="Same as '-m/--minimum' but absolute values.")

parser.add_argument("-p", "--probe", dest="probe", required=False, default=None, action="store_true",
					help="If selected, will also return the reverse complement of the primer found to be used for reverse primers or probes in the logfile.")

parser.add_argument("-b", "--best", dest="best", required=False, default=None, action="store_true",
					help="If selected, will search for the best scoring primers and output the results to 'OUTPUT_best.tsv'.")

parser.add_argument("-v", "--verbose", dest="verbose", required=False, default=None, action="store_true",
					help="If selected, will print information to the console.")

args = parser.parse_args()

if args.verbose is not None:
	verbose = True
	print("  Setting variables...")
else:
	verbose = False

# Setting the range of lengths _____________________________________________________________________
if '+' in args.length:
	mi = args.length.split('+')[0]
	ma = args.length.split('+')[1]
	lengths = range(int(mi), int(ma)+1)
else:
	lengths = int(args.length)
if verbose:
	print("    Lengths:    ", *lengths)

# Setting the specificities ________________________________________________________________________
if args.specificityAbs is not None:
	specificity = args.specificityAbs
	ext = "sequences"
elif args.specificity != 0.01:
	specificity = args.specificity
	ext = "%"
	if args.specificityAbs is not None:
		print("    Warning!! '-s/--specificity' has been parsed by '-S/--specificityAbs'. Taking absolute values.")
else:
	specificity = 0.01
	ext = "%"
	if args.specificityAbs is not None:
		print("    Warning!! '-s/--specificity' has been parsed by '-S/--specificityAbs'. Taking absolute values.")
if verbose:
	print("    Specificity:", specificity, ext)

if args.minimumAbs is not None:
	minimum = args.minimumAbs
	ext = "sequences"
elif args.minimum != 0.8:
	minimum = args.minimum
	ext = "%"
else:
	minimum = 0.8
	ext = "%"
	if args.minimumAbs is not None:
		print("    Warning!! '-m/--minimum' has been parsed by '-M/--minimumAbs'. Taking absolute values.")
if verbose:
	print("    Minimum:    ", minimum, ext)

if args.probe is not None:
	from Bio.Seq import Seq
	if verbose:
		print("    Reverse-complement option selected (-p/--probe)")

# Reading target file ______________________________________________________________________________
if verbose:
	print("  Reading target file...", end="")

target = {}
w1 = 0
for line in SeqIO.parse(open(args.target), "fasta"):
	target[line.id] = str(line.seq.upper())
	if "-" in line.seq:
		w1 += 1

if verbose:
	print("\r    Sequences in target file ('", str(args.target), "'):   ", len(target), sep="")
	if w1 > 0:
		print("    Warning!!", args.target, "contains gaps")

# Reading reference file ___________________________________________________________________________
if verbose:
	print("  Reading reference file...", end="")

ref = {}
w2 = 0
for line in SeqIO.parse(open(args.reference), "fasta"):
	ref[line.id] = str(line.seq.upper())
	if "-" in line.seq:
		w2 += 1

if verbose:
	print("\r    Sequences in reference file ('", str(args.reference), "'):   ", len(ref), sep="")
	if w2 > 0:
		print("    Warning!!", args.reference, "contains gaps")

# Start the search _________________________________________________________________________________
primers = set()
logFile = str(args.output + ".tsv")
fasFile = str(args.output + ".fasta")
with open(logFile, "w") as logfile, open(fasFile, "w") as fasfile:
	if args.probe is not None:
		print("identifier\tlength\tsequence\tsequence_revCom\tmatch_ref\tmatch_ref_abs\tmatch_target\tmatch_target_abs", file=logfile)
	else:
		print("identifier\tlength\tsequence\tmatch_ref\tmatch_ref_abs\tmatch_target\tmatch_target_abs", file=logfile)
	for length in lengths:  # Loop through the different lengths
		if verbose:
			print("  Searching primers of", str(length), "base pairs...")
			i = 0
		for tv in target.values():  # Loop through all the sequences in the target file
			if verbose:
				i += 1
				print("\r    ", str(i), "/", len(target), sep="", end="")
				if i == len(target):
					print("\r    Completed")
			l = len(tv)
			for p in range(0, l-length+1):  # Split the target ith sequence into potential primers of length 'l' 
				pprimer = tv[int(p):(int(p+length))]
				if pprimer not in primers:  # Check if the potential primer is already in the list
					r = 0
					c = 0
					for toCheck in target.values():  # Check how many times the potential primer is repeated in the target file
						if pprimer in toCheck:
							r += 1
					if args.minimumAbs is not None:  # Check if the potential primer is repeated more than 'M' times
						R = r
					else:  # Check if the potential primer is repeated more than 'm' times
						R = r/len(target)
					if R >= minimum:  # Check if the potential primer matches the requirements against the target file
						for toCheck in ref.values():  # Check how many times the potential primer is repeated in the reference file
							if pprimer in toCheck:
								c += 1
					if args.specificityAbs is not None:  # Check if the potential primer is repeated less than 'S' times
						C = c
					else:  # Check if the potential primer is repeated less than 's' times
						C = c/len(ref)
					if C <= specificity and R >= minimum:  # Check if the potential primer matches the requirements 
							primers.add(pprimer)
							if args.probe is not None:
								print("primer" + str(len(primers)) + "\t" + str(len(pprimer)) + "\t" + str(pprimer) + "\t" + str(Seq(pprimer).reverse_complement()) + "\t" + str(c/len(ref)) + "\t" + str(c) + "\t" + str(r/len(target)) + "\t" + str(r), file=logfile)
								print(">primer" + str(len(primers)) + "\n" + pprimer, file=fasfile)
							else:
								print("primer" + str(len(primers)) + "\t" + str(pprimer) + "\t" + str(c/len(ref)) + "\t" + str(c) + "\t" + str(r/len(target)) + "\t" + str(r), file=logfile)
								print(">primer" + str(len(primers)) + "\n" + pprimer, file=fasfile)

if args.best is not None:
	if verbose:
		print("  Searching best scoring primers...")
	import pandas as pd
	log = pd.read_csv(logFile, sep="\t")
	match_ref = min(log["match_ref"])
	match_target = max(log["match_target"])
	best = log[(log["match_ref"] == match_ref) & (log["match_target"] == match_target)]
	bestFile = str(args.output + "_best.tsv")
	best.to_csv(bestFile, sep="\t")

if verbose:
	print("Done")
