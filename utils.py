import sys
import configparser
import os
import datetime

import pwdutil   #local util for database password
import pymysql   # http://pymysql.readthedocs.io/en/latest/
                 # https://github.com/PyMySQL/PyMySQL

class ConfigFileAccessError(Exception):
    pass

def fileexists(CONFIGFILE):
    return(os.path.isfile(CONFIGFILE) )


def get_config():
    """ Load parameter and configuration values from the CONFIGFILE
    
    A nested dictionary is passed back in following format
      {"ConfigClass" : { param1 : value, param2 : value ... }
      
    The config file is in standard Python .ini fmt, EG:
        
        [MySQL]
        server: 192.168.56.100
        dbuser: simplebot
        dbname: simplebot
        dbcharset: utf8mb4
    
    The above example can then be ref'd:
    
        config = utils.get_config()
        username = config["MySQL"]["dbuser"]      
      
    """
    
    CONFIGFILE = "./config/config.ini"
    
    Config = configparser.ConfigParser()
    
    config = {}   # Dictionary of "section" keys.  Each value is a sub-dict of key-vals    
    if fileexists(CONFIGFILE):
        Config.read(CONFIGFILE)
        for section in Config.sections():

            subdict = {}
            options = Config.options(section)
            for option in options:
                key = option
                val = Config.get(section,option)
                
                subdict[option] = Config.get(section,option)
                      
            config[section] = subdict
   
    else:
        raise ConfigFileAccessError(CONFIGFILE)

    return config

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    The "answer" return value is True for "yes" or False for "no".
    - a Cut-and-Paste piece of code from Stack Overflow
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
            
#  Flatten out a list of lists (taken from SO: http://stackoverflow.com/questions/10823877/what-is-the-fastest-way-to-flatten-arbitrarily-nested-lists-in-python 
def flatten(container):
    for i in container:
        if isinstance(i, (list,tuple)):
            for j in flatten(i):
                yield j
        else:
            yield i  
                      
def db_connection(host, user, dbname, charset = "utf8mb4"):
    """
    Connect to a MySQL Database Server
    """
    key = pwdutil.get_key()
    encoded = pwdutil.get_pwd()
    password = pwdutil.decode(key,encoded)
    
    connection = pymysql.connect(host = host
                                , user = user
                                , password = password
                                , db = dbname
                                , charset = charset
                                , cursorclass=pymysql.cursors.DictCursor)
    
    return connection

def db_connectionID(cursor):
    cursor.execute('SELECT connection_id()', (None))
    value = cursor.fetchone()["connection_id()"]
    return(value)

def timestamp_string():
    timestamp_string = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    return(timestamp_string)
        
        