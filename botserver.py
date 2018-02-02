import socket
import threading
import os
from string import punctuation
import random
import re
import logging

import chatbot
import utils

LOGFILE = './log/botserver.log'
conf = utils.get_config()
toBool = lambda str: True if str == "True" else False 

DEBUG_SERVER = toBool(conf["DEBUG"]["server"])
LOGGING_FMT = '%(asctime)s %(threadName)s %(message)s'

regexpYes = re.compile(r'yes')

if DEBUG_SERVER:
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=LOGGING_FMT)
else:
    logging.basicConfig(filename=LOGFILE, level=logging.INFO, format=LOGGING_FMT)

def session(connection):
    i = 0   # counter for how many times we have been round the loop
#    startMessage = "Starting Bot...\n"
    
    # Get Config
    conf = utils.get_config()
    DBHOST = conf["MySQL"]["server"] 
    DBUSER = conf["MySQL"]["dbuser"]
    DBNAME = conf["MySQL"]["dbname"]
    
    logging.info("Starting Bot session-thread...") 

    # initialize the connection to the database
    logging.info("   session-thread connecting to database...")
    DBconnection = utils.db_connection(DBHOST, DBUSER, DBNAME)
    DBcursor =  DBconnection.cursor()
    DBconnectionID = utils.db_connectionID(DBcursor)
    logging.info("   ...connected")
    
    botSentence = 'Hello!'
    weight = 0
    
    trainMe = False
    checkStore = False
#    startMessage = startMessage + ("...started\n")
    
    def receive(connection):
        
        logging.debug("   receive(connection): PID {}, thread {} \n".format(pid, thread))
        received = connection.recv(1024)
        if not received:
            #logging.info("Closing connection {}".format(thread))
            return False
        else:
            #logging.debug("    Received {}, echoing".format(received))
            return received
   
    while True:
        pid = os.getpid()
        thread = threading.current_thread()
        
        # pass received message to chatbot
        received = receive(connection)
        humanSentence = received.decode().strip()
        
        if humanSentence == '' or humanSentence.strip(punctuation).lower() == 'quit' or humanSentence.strip(punctuation).lower() == 'exit':
            break

        # Chatbot processing
        botSentence, weight, trainMe, checkStore = chatbot.chat_flow(DBcursor, humanSentence, weight)
        logging.debug("   Received botSentence {} from chatbot.chat_flow".format(botSentence))
        
        if trainMe:
            logging.debug("   trainMe is True")
            send = "Please train me - enter a response for me to learn (or \"skip\" to skip)' ".encode()
            connection.send(send)
            previousSentence = humanSentence
            received = receive(connection)
            humanSentence = received.decode().strip()
            logging.debug("   trainMe received {}".format(humanSentence))
                        
            if humanSentence != "skip":
                chatbot.train_me(previousSentence, humanSentence, DBcursor)
                botSentence = "Thanks I've noted that"
                #connection.send(send)
            else:
                botSentence = "OK, moving on..."
                #connection.send(send)
                trainMe = False
                
        if checkStore:
            logging.debug("CheckStore is True")
            send = 'Shall I store that as a fact for future reference?  ("yes" to store)'.encode()
            connection.send(send)
            previousSentence = humanSentence
            received = receive(connection)
            humanSentence = received.decode().strip()
            logging.debug("   checkStore received {}".format(humanSentence))
            
            if regexpYes.search(humanSentence.lower()):
                #Store previous Sentence
                logging.debug("   Storing...")
                chatbot.store_statement(previousSentence, DBcursor)
                logging.debug("   Statement Stored.")
                botSentence = random.choice(chatbot.STATEMENT_STORED)
            else:
                botSentence = "OK, moving on..."
                checkStore = False

        DBconnection.commit()
        logging.debug("   sending botSentence back: {}".format(botSentence))
        send = botSentence.encode()
                
#        if i == 0:
#            send = startMessage.encode() + send
        connection.send(send)
#        i = i + 1
    logging.info("   Closing Session")

if __name__ == "__main__":
    logging.info("-----------------------------")
    logging.info("--  Starting BotServer     --")
    print("Starting...")
    print("Logging to ", LOGFILE)
    
    LISTEN_HOST = conf["Server"]["listen_host"]
    LISTEN_PORT = int(conf["Server"]["tcp_socket"])
    LISTEN_QUEUE = int(conf["Server"]["listen_queue"])
    
    # Set up the listening socket
    sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    sckt.bind((LISTEN_HOST, LISTEN_PORT))
    sckt.listen(LISTEN_QUEUE)
    print("...socket set up")
    logging.info("Server Listener set up on port " + str(LISTEN_PORT))
    
    # Accept connections in a loop
    while True:
        logging.info("Main Server Waiting for a connection")
        (connection, address) = sckt.accept()
        logging.info("Connect Received " + str(connection) + " " + str(address))
        
        #threading.Thread(target = session, args=[connection]).start()
        t = threading.Thread(target = session, args=[connection])
        t.setDaemon(True)  #set to Daemon status, allows CTRL-C to kill all threads
        t.start()
    
    logging.info("Closing Server Listen socket on " + str(LISTEN_PORT))
    sckt.close()
       
