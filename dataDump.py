#CSV extract from database table
import sys

import csv
import string
from datetime import datetime

import utils  # General utils including config params and database connection

if len(sys.argv) < 3:
    print(len(sys.argv))
    print("\nUsage: {0} <tablename> <database_name> [ <filename.csv> ] \n".format(sys.argv[0]))
    exit(1)
    
if len(sys.argv) > 3:
    dumpfile = sys.argv[3]
else:
    dumpfile = ""
    
tablename = sys.argv[1]
DBNAME = sys.argv[2]

conf = utils.get_config()

DBHOST = conf["MySQL"]["server"] 
DBUSER = conf["MySQL"]["dbuser"]
DBCHARSET = conf["MySQL"]["dbcharset"]

def containsAny(s, set):
    """Check whether 'str' contains ANY of the chars in 'set'"""
    return 1 in [c in str(s) for c in set]

# MAIN #

print("Connecting to database...", end=" ")
connection = utils.db_connection(DBHOST, DBUSER, DBNAME, DBCHARSET)
cursor = connection.cursor()
print("connected.")

## Dump Data ##

statement = 'SELECT * FROM ' + tablename 
print("EXECUTING", statement)
cursor.execute(statement)

fieldnames=[f[0] for f in cursor.description]

# if a dumpfile was specified, open it
if dumpfile:
    try:
        f = open(dumpfile, "w")
    except EnvironmentError as err:
        print("OS error opening file: {0}".format(err))
        sys.exit(1)

# output a first-line colummn name header
if dumpfile:
    f.write(",".join(fieldnames).upper() + "\n")
else:        
    print(",".join(fieldnames).upper())        

    
for row in cursor.fetchall():
  
    line = []
    # need to comma separate strings 
    for key in fieldnames:
        val = row[key]
        # imperfect method to detect numerics and do quoting
        # - any alpha's or punctuation?  double-quote accordingly
        punc = string.punctuation.replace(".","")  # remove the "." to avoide quoting floats
        if any(c.isalpha() for c in str(val)) or containsAny(val, punc):
            val = '"' + val + '"'
        line.append(val)
    
    linestr = ",".join(map(str,line)) # comma separated line of text
    
    if dumpfile:
        f.write(linestr + "\n")
    else:
        print(linestr)

