# Read in a CSV file of training data and use it to train a RF classification model
#
# RF model for Python sci-kit is saved to CWD in "RFmodel.ml"
#
# Assumptions: 
# CSV file is supplied with a header-line to name columns
# 1st field is ID and can be ignored
# Last field/column is the classifier
# Classifier is provided in a column called 'class'

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

import csv
import sys

import pickle

MODEL_SAVE_NAME = './RFmodel.ml'

if len(sys.argv) > 1:
    FNAME = sys.argv[1]
else:
    FNAME = './analysis/featuresDump.csv'
print("reading input from ", FNAME)

#Read CSV into data-frame
df = pd.read_csv(filepath_or_buffer = FNAME, )   
print(str(len(df)), "rows loaded")

# Strip any leading spaces from col names
df.columns = df.columns[:].str.strip()
width = df.shape[1]

features = df.columns[1:width-1]  #remove the first ID col and final class col
print("FEATURES = {}".format(features))

# Fit an RF Model for classifier "class" given features
rf = RandomForestClassifier(n_jobs=2, n_estimators = 100)
rf.fit(df[features], df['class'])

print("\nsaving model to " + MODEL_SAVE_NAME + "\n")
with open(MODEL_SAVE_NAME, 'wb') as f:
    pickle.dump(rf, f)

print("Complete.")

 