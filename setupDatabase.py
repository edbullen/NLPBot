import os

import warnings
warnings.filterwarnings("ignore")  # suppress warnings when we try to drop non-existant tabs

import utils  # General utils including config params and database connection

conf = utils.get_config()

DBHOST = conf["MySQL"]["server"] 
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]
DBCHARSET = conf["MySQL"]["dbcharset"]

def try_drop(cursor,table_name):
    SQL = 'DROP TABLE IF EXISTS ' + table_name
    print(SQL)
    cursor.execute(SQL)

print("Configuring Tables for database configuration: \n \tServer: {0} \n \tDB-User: {1} \n \tDB-Name: {2}".format(DBHOST,DBUSER, DBNAME))
print("\n** ALL EXISTING TABLES AND DATA WILL BE LOST **\n")

response = utils.query_yes_no("Continue?")

if response:
    
## Tab Config and Make Connection to Database ##
    
    charTypeShort = "VARCHAR(16) COLLATE utf8_general_ci"
    charTypeMedium = "VARCHAR(64) COLLATE utf8_general_ci"
    charTypeLong = "VARCHAR(768) COLLATE utf8_general_ci"
    
    print("Connecting to database...", end=" ")
    connection = utils.db_connection(DBHOST, DBUSER, DBNAME, DBCHARSET)
    cursor = connection.cursor()
    print("connected.")
    
#### Table Create Sections ####
    
    print("\nCreating words table:")
    try:
        try_drop(cursor, "words")
        SQL = 'CREATE TABLE words ( hashid ' + charTypeShort + ' UNIQUE, word ' + charTypeMedium +' UNIQUE )'
        print(SQL)
        cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)
        
    print("\nCreating sentences table:")
    try:
        try_drop(cursor, "sentences")
        SQL = 'CREATE TABLE sentences (hashid ' + charTypeShort + ' UNIQUE, sentence ' + charTypeLong + ' , used INT  DEFAULT 0 NOT NULL)'    
        print(SQL)
        cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)
        
    print("\nCreating statements table:")
    try:
        try_drop(cursor, "statements")
        SQL = 'CREATE TABLE statements (sentence_id ' + charTypeShort + ', word_id ' + charTypeShort + ' , class ' + charTypeShort + ')'    
        print(SQL)
        cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)
        
    print("\nAdding statements table INDEXES:")
    try:
        indexes = ['ALTER TABLE statements add INDEX statements_sentenceid_idx (sentence_id)',
                   'ALTER TABLE statements add INDEX statements_wordid_idx (word_id)']
        for index in indexes:
            SQL = index
            print(SQL)
            cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)

        
    print("\nCreating associations table:")
    try:
        try_drop(cursor, "associations")
        SQL = 'CREATE TABLE associations (word_id ' + charTypeShort + ' NOT NULL, sentence_id ' + charTypeShort + ' NOT NULL, weight REAL NOT NULL)'
        print(SQL)
        cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)
    
    print("\nAdding associations table INDEXES:")
    try:
        indexes = ['ALTER TABLE associations add INDEX associations_wordid_idx (word_id)',
                   'ALTER TABLE associations add INDEX associations_sentenceid_idx (sentence_id)']
        for index in indexes:
            SQL = index
            print(SQL)
            cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)
        
        
    print("\nCreating results table:")
    try:
        try_drop(cursor, "results")
        SQL = 'CREATE TABLE results (connection_id INTEGER, sentence_id TEXT, sentence TEXT, weight REAL)'
        print(SQL)
        cursor.execute(SQL)
    except Exception as e:
        print("\n** ERROR **", e)
        
    print("\nDone.")
##############################    
    
else:
    exit(0)