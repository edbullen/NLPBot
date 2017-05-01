import chatbot   # Test the ML classification routing in chatbot.py
import features  # custom fn extract features from a sentence
import utils

import sys
import profile

conf = utils.get_config()

DBHOST = conf["MySQL"]["server"] 
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]

test = "When will Oracle 12c Release 2 be released?"

if len(sys.argv) > 1:
    sentence = sys.argv[1]
else:
    sentence = test
    
print("Connecting to database...")
connection = utils.db_connection(DBHOST, DBUSER, DBNAME)
cursor =  connection.cursor()
connectionID = utils.db_connectionID(cursor)
print("...connected")

results = chatbot.get_answer(sentence, cursor)

for row in results:
    print(row)

#connection.commit()

print("done")