# Python script to load in a CSV of sentences and use module features.py
# to extract triples for each class-label defined in the the sentences CSV


import nltk
from nltk import word_tokenize
import csv
import sys

import features  # module to extract feature from a line of text

# Read in a list of sentences in a CSV with a classifier  in the second column
FNAME = "./analysis/sentences.csv"

# Write out to FOUT, format:
#    POS-POS-POS,Class-Label
#    NNP-VBP-DT, Q
#    WRB-VBZ-PRP, C
#    ....
FOUT = "./analysis/all_triples.csv"

fout = open(FOUT, 'w')

with open(FNAME) as f:
    next(f)
    reader = csv.reader(f, delimiter=',')
    
    for row in reader:
        #print(row)
        sentence,label = row
        
        sentence = features.strip_sentence(sentence)  #Strip punctuation
        pos = features.get_pos(sentence) 
        print("------------------\n Processing", sentence)
        triples = features.get_triples(pos)
        print("Class", label, "Triples: ", triples)
        
        for t in triples:
            fout.write(str(t) + ", " + label + "\n")
                
fout.close()        

