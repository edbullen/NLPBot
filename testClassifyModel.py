import csv
import sys
import pickle

import chatbot   # Test the ML classification routing in chatbot.py
import features  # custom fn extract features from a sentence

## Test fn written assuming a single line / row supplied, return single predict

test = "The Oracle 12c database will be released in March"
id = "xxxxx"
c = "X"

textout = {'Q': "QUESTION", 'C': "CHAT", 'S':"STATEMENT"}

if len(sys.argv) > 1:
    sentence = sys.argv[1]
else:
    sentence = test

prediction = chatbot.sentence_rf_class(sentence)


print("\n\nPrediction is: ", textout[prediction])
