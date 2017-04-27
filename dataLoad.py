#load a CSV into a database table

import sys

import csv
import string
from datetime import datetime

import pwdutil
import utils  # General utils including config params and database connection

if len(sys.argv) != 4:
    print(len(sys.argv))
    print("\nUsage: {0} <tablename> <database_name> <filename.csv>  \n".format(sys.argv[0]))
    exit(1)

tablename = sys.argv[1]
DBNAME = sys.argv[2]
loadfile = sys.argv[3]

ERRORFILE = "./dump/load.err"

conf = utils.get_config()

DBHOST = conf["MySQL"]["server"] 
DBUSER = conf["MySQL"]["dbuser"]
DBCHARSET = conf["MySQL"]["dbcharset"]

# MAIN #

print("\nLoading table  [" + tablename + "] in database [" + DBNAME + "] from " + loadfile + "\n\n")
print("User:", DBUSER, "\n")

i=0
failed=0

print("Connecting to database...", end=" ")
connection = utils.db_connection(DBHOST, DBUSER, DBNAME, DBCHARSET)
cursor = connection.cursor()
print("connected.")

DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
MSG = "## Starting " + tablename + " Data-Load:" + DATE + " ##"
with open(ERRORFILE, "a") as efile:
                    efile.write(MSG + "\n")


with open(loadfile,'rt', encoding = 'utf8') as f:
    
    reader = csv.reader(f, skipinitialspace=True)
    for row in reader:
        #first line = col names
        i = i + 1
        if i == 1:
            #cols = ",".join(row)
            cols = row
        else:
            #load data
            s = ""   # string for the values 
            for colval in row:
                # add quotes round strings but not numeric fields
                if any(c.isalpha() for c in colval):
                    colval = '"' + colval + '"'
                               
                
                if len(s) > 0 :
                    s = s + "," + str(colval)  #comma separate
                else:
                    s = s + str(colval)  # first string part
        
            insertString = "INSERT INTO " + tablename + " VALUES(" + s + ");"
            print(insertString) 
            #insert into database   
            try:            
                cursor.execute(insertString)
            except Exception as e:
                failed = failed + 1
                MSG = "ERROR: insert [" + s + "]failed with error " + str(e)
                print(MSG)
                with open(ERRORFILE, "a") as efile:
                    efile.write(MSG + "\n")

connection.commit()

DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
MSG = "## Completed Data-Load:" + DATE + " " + str(i)+ " rows loaded " + str(failed) + " failed ##"
with open(ERRORFILE, "a") as efile:
    efile.write(MSG + "\n")
            