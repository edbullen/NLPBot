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


## PyData 2017 Slides ##
[GitHub Preview Viewer for HTML Slides](http://htmlpreview.github.io/?https://github.com/edbullen/NLPBot/blob/master/slides/slides.html)