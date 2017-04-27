This is a simple Chatbot written in **Python 3.5** with a MySQL database backend.  The code extends my other SimpleBot demo (https://github.com/edbullen/SimpleBot) and introduces some NLP and Machine Learning capagilities

## Python Library Dependencies ##

[pymysql](http://pymysql.readthedocs.io/en/latest/)  
...TODO!   

## Files and Components ##

...TODO!  

**Core**
+ `chatbot.py` - main ChatBot library 
+ `utils.py` - generic function utilities used by ChatBot (config, DB conn etc) 
+ `botserver.py` - Multi-Threaded server to allow multiple clients to connect to the ChatBot via network sockets
+ `simpleclient.py` - Simple network sockets client to connect to `botserver`

**Setup and Test**
+ `config.ini` - sample config file to copy into the ./config directory
+ `pwdutil.py` - store an encoded password for connecting to the database schema
+ `setupDatabase.py` - drop and recreate the database tables (existing data gets lost)
+ `pingDB.py` - test the database configuration: create test table, insert data,  query it, drop the test table.
+ `dataDump.py` - Dump out a database table in CSV format
+ `dataLoad.py` - Load a database table in CSV format

## Install and Setup ##

...TODO!


### MySQL Database Setup ###

**Database User**
Create a dedicated database for the SimpleBot data-store.

As `root` user in MySQL, create a dedicated MySQL user for the NLPBot to connect to the datastore:

```
CREATE USER 'nlpbot'@'localhost' IDENTIFIED BY '<myPassword123>';  

GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP on nlpbot.* 
   TO 'nlpbot'@'localhost';

GRANT CREATE TEMPORARY TABLES  on simplebot.* 
   TO 'nlpbot'@'localhost';
``` 

The user-name must match the user configured in the ChatBot `config.ini` file.  

Replace `localhost` with the remote host that the ChatBot will be accessing the mySQL database *from*.


Set an appropriate password; this will need to be initialised (stored locally in encoded form) for the ChatBot later on (see the next section of this README). 


**Initialisation of Database Password for ChatBot**

Password authentication details for the ChatBot to access the MySQL database are stored locally.  To avoid storing the actual password in clear-text the password is stored in encoded form.

A separate file called
`./config/.key` 
must be created in the config sub-directory with a single key phrase in it and no other text or characters - i.e.

```
$ echo "thisIsSecret" > ./.key
$ chmod 400 .key
```
(this is NOT the database password).  Set appropriate file permissions on this file.

When the `.key` file is in place, initialise password access to the remote MySQL database using 

`python pwdutil.py -s password`

where "password" is the appropriate real password for the ChatBot MySQL database user account (so this is not the key phrase set above).

NOTE - the approach taken here is not very secure.  It is better than storing the database password in clear text, but is still very limited and this configuration is not suitable for sensitive data.  

**Test Database Configuration**
A simple `pingDB.py` script is provided to test database access and base functionality.

The script connects as the configured mySQL user, creates a table "bot_test_tab", inserts a row, selects it back out and then drops the table.

Expected output is below:

```
$ python ./pingDB.py
Warning: (1051, "Unknown table 'simplebot.bot_test_tab'")
  self._do_get_result()
execute drop_test_tab Args: None Response 0
execute create_test_tab Args: None Response 0
execute insert_test_tab Args: ('a', 1) Response 1
execute select_test_tab Args: 1 Response 1
execute drop_test_tab Args: None Response 0
```

**Setup the Database Schema**


Run the python script `setupDatabase.py` to create the database schema.  EG:

```
$ python setupDatabase.py
Configuring Tables for database configuration:
        Server: localhost
        DB-User: simplebot
        DB-Name: simplebot
Continue? [Y/n] y
Connecting to database... connected.

Creating words table:
DROP TABLE IF EXISTS words
CREATE TABLE words ( hashid VARCHAR(16) COLLATE utf8_general_ci UNIQUE, word VARCHAR(64) COLLATE utf8_general_ci UNIQUE )
...
(etc,etc)
...
Done.

```




## PyData 2017 Slides ##
[GitHub Preview Viewer for HTML Slides](http://htmlpreview.github.io/?https://github.com/edbullen/NLPBot/blob/master/slides/slides.html)