import re
from collections import Counter
import string
from string import punctuation
from math import sqrt
import hashlib
import sys

weight = 0

# Based on a blog-post Here: http://rodic.fr/blog/python-chatbot-1/

import utils  # General utils including config params and database connection
conf = utils.get_config()

ACCURACY_THRESHOLD = 0.03
NO_DATA = "Sorry I don't know what to say"

toBool = lambda str: True if str == "True" else False 
DEBUG_ASSOC = toBool(conf["DEBUG"]["assoc"]) 
DEBUG_WEIGHT = toBool(conf["DEBUG"]["weight"])
DEBUG_ITEMID = toBool(conf["DEBUG"]["itemid"])
DEBUG_MATCH = toBool(conf["DEBUG"]["match"])

#Strip non-alpha chars out - basic protection for SQL strings built out of concat ops
##clean = lambda str: ''.join(ch for ch in str if ch.isalnum())

def hashtext(stringText):
    """Return a string with first 16 numeric chars from hashing a given string
    """
    
    #hashlib md5 returns same hash for given string each time
    return hashlib.md5(str(stringText).encode('utf-8')).hexdigest()[:16]


def item_id(entityName, text, cursor):
    """Retrieve an entity's unique ID from the database, given its associated text.
    If the row is not already present, it is inserted.
    The entity can either be a sentence or a word."""
    
    #entityName = clean(entityName)
    #text = clean(text)
        
    tableName = entityName + 's'
    columnName = entityName

    #check whether 16-char hash of this text exists already
    hashid = hashtext(text)
    
    SQL = 'SELECT hashid FROM ' + tableName + ' WHERE hashID = %s'
    if (DEBUG_ITEMID == True): print("DEBUG ITEMID: " + SQL)
    cursor.execute(SQL, (hashid))
    row = cursor.fetchone()
    
    if row:
        if (DEBUG_ITEMID == True): print("DEBUG ITEMID: item found, just return hashid:",row["hashid"], " for ", text )
        return row["hashid"]
        
    else:
        if (DEBUG_ITEMID == True): print("DEBUG ITEMID: no item found, insert new hashid into",tableName, " hashid:", hashid, " text:",text )
        SQL = 'INSERT INTO ' + tableName + ' (hashid, ' + columnName + ') VALUES (%s, %s)'
        
        cursor.execute(SQL, (hashid, text))
        return hashid 


def get_words(text):
    """Retrieve the words present in a given string of text.
    The return value is a list of tuples where the first member is a lowercase word,
    and the second member the number of time it is present in the text.  Example:
      IN:  "Did the cow jump over the moon?"
      OUT: dict_items([('cow', 1), ('jump', 1), ('moon', 1), ('?', 1), ('over', 1), ('the', 2), ('did', 1)])
    """
    puncRegexp = re.compile('[%s]' % re.escape(string.punctuation))
    text = puncRegexp.sub('',text )
        
    wordsRegexpString = '\w+'
    wordsRegexp = re.compile(wordsRegexpString)
    wordsList = wordsRegexp.findall(text.lower())
    
    return Counter(wordsList).items()    


def set_association(words, sentence_id, cursor):
    """ Pass in "words" which is a list of tuples - each tuple is word,count
    ("a_word" and count of occurences - i.e. ("the", 3) means the occurred 3 times in sentence)
    Nothing is returned by this function - it just updates the associations table in the database
    
    If current association for a word_id is 0, a new word-sentence association is added
    
    If current association for a word_id is > 0, the word-sentence association is updated with a new weight
    which is just the existing association weight (passed back by get_association) and the new weight
    """

    words_length = sum([n * len(word) for word, n in words]) # int giving number of chars in words
    
    # Looping through Bot-Words, associating them with Human Sentence
    for word, n in words:                 
    
        word_id = item_id('word', word, cursor) # if the ID doesn't exist, a new word + hash ID is inserted
        weight = sqrt(n / float(words_length))  # repeated words get higher weight.  Longer sentences reduces their weight
                
        #Association shows that a Bot-Word is associated with a Human-Sentence
        # Bot learns by associating our responses with its words
        association = get_association(word_id,sentence_id, cursor)
        
        if association > 0:
            
            if (DEBUG_ASSOC == True): print("DEBUG_ASSOC: got an association for", word, " value: ", association, " with sentence_id:", sentence_id)
                                            
            SQL = 'UPDATE associations SET weight = %s WHERE word_id = %s AND sentence_id = %s'
            if (DEBUG_ASSOC == True): print("DEBUG_ASSOC:", SQL, weight, word_id, sentence_id) 
            cursor.execute(SQL, (association+weight, word_id, sentence_id))
           
        else:
            
            SQL = 'INSERT INTO associations (word_id, sentence_id, weight) VALUES (%s, %s, %s)'
            if (DEBUG_ASSOC == True): print("DEBUG_ASSOC:", SQL,word_id, sentence_id, weight)
            cursor.execute(SQL, (word_id, sentence_id, weight))


def get_association(word_id,sentence_id, cursor):
    """Get the weighting associating a Word with a Sentence-Response
    If no association found, return 0
    This is called in the set_association routine to check if there is already an association
    
    associations are referred to in the get_matches() fn, to match input sentences to response sentences
    """
    SQL = 'SELECT weight FROM associations WHERE word_id =%s AND sentence_id =%s'
    if (DEBUG_ASSOC == True): print("DEBUG_ASSOC:", SQL,word_id, sentence_id)
    cursor.execute(SQL, (word_id,sentence_id))
    row = cursor.fetchone()
    
    if row:
        weight = row["weight"]
    else:
        weight = 0
    return weight


def get_matches(words, cursor):
    """ Retrieve the most likely sentence-answer from the database
    pass in humanWords, calculate a weighting factor for different sentences based on data in associations table  
    """
    results = []
    listSize = 10
    
    # Removed temp tables due to  GTID configuration issue in mySQL
    #cursor.execute('CREATE TEMPORARY TABLE results(sentence_id TEXT, sentence TEXT, weight REAL)')
    cursor.execute('DELETE FROM results WHERE connection_id = connection_id()')
    
    # calc "words_length" for weighting calc
    words_length = sum([n * len(word) for word, n in words])  
    
    if (DEBUG_MATCH == True): print("DEBUG_MATCH: words list", words, " words_length:", words_length )
    
    for word, n in words:
        #weight = sqrt(n / float(words_length))  # repeated words get higher weight.  Longer sentences reduces their weight
        weight = (n / float(words_length))
        SQL = 'INSERT INTO results \
                 SELECT connection_id(), associations.sentence_id, sentences.sentence, %s * associations.weight/(1+sentences.used) \
                 FROM words \
                 INNER JOIN associations ON associations.word_id=words.hashid \
                 INNER JOIN sentences ON sentences.hashid=associations.sentence_id \
                 WHERE words.word = %s'
        if (DEBUG_MATCH == True): print("DEBUG_MATCH: ", SQL, " weight = ",weight , "word = ", word)
        cursor.execute(SQL, (weight, word)) 
    
    if (DEBUG_MATCH == True): print("DEBUG_MATCH: ", SQL)
    cursor.execute('SELECT sentence_id, sentence, SUM(weight) AS sum_weight \
                    FROM results \
                    WHERE connection_id = connection_id() \
                    GROUP BY sentence_id, sentence  \
                    ORDER BY sum_weight DESC')
    
    # Fetch an ordered "listSize" number of results
    for i in range(0,listSize):
        row = cursor.fetchone()
        if row:
            results.append([row["sentence_id"], row["sentence"], row["sum_weight"]])
            if (DEBUG_MATCH == True): print("**",[row["sentence_id"], row["sentence"], row["sum_weight"]],"\n")
            
        else:
            break
    #cursor.execute('DROP TEMPORARY TABLE results')
    cursor.execute('DELETE FROM results WHERE connection_id = connection_id()')
        
    return results

def feedback_stats(sentence_id, cursor, previous_sentence_id = None, sentiment = True):
    """
    Feedback usage of sentence stats, tune model based on user response.
    Simple BOT Version 1 just updates the sentance used counter
    """
       
    SQL = 'UPDATE sentences SET used=used+1 WHERE hashid=%s'
    cursor.execute(SQL, (sentence_id))
    
def train_me(inputSentence, responseSentence, cursor):
    inputWords = get_words(inputSentence) #list of tuples of words + occurrence count
    responseSentenceID = item_id('sentence', responseSentence, cursor) 
    set_association(inputWords, responseSentenceID, cursor)
    
def chat_flow(cursor, humanSentence, weight):
   
    # Take the human-words and try to find a matching response based on a weighting-factor
    humanWords = get_words(humanSentence)        
    matches = get_matches(humanWords, cursor)    #get_matches returns ordered list of matches for words:
                                                 #                         sentence_id, sentence, weight 
    trainMe = False # if true, the bot requests some help
    
    if len(matches) == 0:
        botSentence = NO_DATA
        trainMe = True
    else:
        sentence_id, botSentence, weight = matches[0]
        if weight > ACCURACY_THRESHOLD:
            # tell the database the sentence has been used and feedback other stats / weighting updates
            feedback_stats(sentence_id, cursor)
            train_me(botSentence, humanSentence, cursor)
        else:
            botSentence = NO_DATA
            trainMe = True
                        
    return botSentence, weight, trainMe

    
if __name__ == "__main__":    
    
    conf = utils.get_config()
    
    DBHOST = conf["MySQL"]["server"] 
    DBUSER = conf["MySQL"]["dbuser"]
    DBNAME = conf["MySQL"]["dbname"]
    
    print("Starting Bot...") 
    # initialize the connection to the database
    print("Connecting to database...")
    connection = utils.db_connection(DBHOST, DBUSER, DBNAME)
    cursor =  connection.cursor()
    connectionID = utils.db_connectionID(cursor)
    print("...connected")
    
    trainMe = False
    botSentence = 'Hello!'
    while True:
        
        # Output bot's message
        if DEBUG_WEIGHT: 
            print('Bot> ' + botSentence + ' DEBUG_WEIGHT:' + str(round(weight,5)) )
        else:
            print('Bot> ' + botSentence)
            
        if trainMe:
            print('Bot> Please can you train me - enter a response for me to learn (Enter to Skip)' )
            previousSentence = humanSentence
            humanSentence = input('>>> ').strip()
            
            if len(humanSentence) > 0:
                train_me(previousSentence, humanSentence, cursor)
                print("Bot> Thanks I've noted that" )
            else:
                print("Bot> OK, moving on..." )
                trainMe = False
         
        # Ask for user input; if blank line, exit the loop
        humanSentence = input('>>> ').strip()
        if humanSentence == '' or humanSentence.strip(punctuation).lower() == 'quit' or humanSentence.strip(punctuation).lower() == 'exit':
            break
    
        botSentence, weight, trainMe = chat_flow(cursor, humanSentence, weight)
    
        connection.commit()
