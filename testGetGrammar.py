import csv
import sys
import pickle

import chatbot   # Test the ML classification routing in chatbot.py
import features  # custom fn extract features from a sentence

## Test fn written assuming a single line / row supplied, return single predict

test = "The Oracle 12c database will be released in March"
id = "xxxxx"
c = "X"

if len(sys.argv) > 1:
    sentence = sys.argv[1]
else:
    sentence = test

root, subj, obj, lastnounA, lastnounB = chatbot.get_grammar(sentence)


print("\n\nOutput is: Root:", root, " Subject:", subj, " Object:", obj, " Last NounA: ", lastnounA , " Last NounB: ", lastnounB)
