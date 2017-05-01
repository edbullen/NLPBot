import chatbot   # Test the ML classification routing in chatbot.py
import features  # custom fn extract features from a sentence
import utils

import sys
import profile

conf = utils.get_config()

DBHOST = conf["MySQL"]["server"] 
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]

test = "The Oracle 12c database will be released in March"

if len(sys.argv) > 1:
    sentence = sys.argv[1]
else:
    sentence = test
    
print("storing statement", sentence)    

print("Connecting to database...")
connection = utils.db_connection(DBHOST, DBUSER, DBNAME)
cursor =  connection.cursor()
connectionID = utils.db_connectionID(cursor)
print("...connected")

#profile.run('chatbot.store_statement(sentence, cursor)')
chatbot.store_statement(sentence, cursor)

connection.commit()

print("done")