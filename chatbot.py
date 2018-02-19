import re
from collections import Counter
import string
from string import punctuation
from math import sqrt
import hashlib
import sys
import os
import pickle
import random

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from nltk.parse.stanford import StanfordDependencyParser

weight = 0

import utils  # General utils including config params and database connection
import features # module for extracting features from sentence to use wuth ML models 
conf = utils.get_config()

ACCURACY_THRESHOLD = 0.03
NO_CHAT_DATA = "Sorry I don't know what to say."
NO_ANSWER_DATA = "Sorry, I can't find an answer to that."

STATEMENT_STORED = ["Thanks, I've made a note of that.",
                    "Thanks for telling me that.",
                    "OK, I've stored that information.",
                    "OK, I've made a note of that."]

toBool = lambda str: True if str == "True" else False 

## Get Config from Config.ini File ##
DEBUG_ASSOC = toBool(conf["DEBUG"]["assoc"]) 
DEBUG_WEIGHT = toBool(conf["DEBUG"]["weight"])
DEBUG_ITEMID = toBool(conf["DEBUG"]["itemid"])
DEBUG_MATCH = toBool(conf["DEBUG"]["match"])
DEBUG_ANSWER = toBool(conf["DEBUG"]["answer"])

JAVA_HOME = conf["Java"]["bin"]
STANFORD_NLP = conf["StanfordNLP"]["corejar"]
STANFORD_MODELS = conf["StanfordNLP"]["modelsjar"]

RF_MODEL_LOCATION = './RFmodel.ml'
os.environ['JAVAHOME'] = JAVA_HOME  # Set this to where the JDK is 

## End of Config ##

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
    
    alreadyExists = False

    #check whether 16-char hash of this text exists already
    hashid = hashtext(text)
    
    SQL = 'SELECT hashid FROM ' + tableName + ' WHERE hashID = %s'
    if (DEBUG_ITEMID == True): print("DEBUG ITEMID: " + SQL)
    cursor.execute(SQL, (hashid))
    row = cursor.fetchone()
    
    if row:
        if (DEBUG_ITEMID == True): print("DEBUG ITEMID: item found, just return hashid:",row["hashid"], " for ", text )
        alreadyExists = True
        return row["hashid"], alreadyExists
        
    else:
        if (DEBUG_ITEMID == True): print("DEBUG ITEMID: no item found, insert new hashid into",tableName, " hashid:", hashid, " text:",text )
        SQL = 'INSERT INTO ' + tableName + ' (hashid, ' + columnName + ') VALUES (%s, %s)'
        alreadyExists = False
        cursor.execute(SQL, (hashid, text))
        return hashid, alreadyExists 


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
    
        word_id, exists = item_id('word', word, cursor) # if the ID doesn't exist, a new word + hash ID is inserted
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
    """ Retrieve the most likely sentence-response from the database
    pass in humanWords, calculate a weighting factor for different sentences based on data in 
    associations table.
    passback ordered list of results (maybe only need to return single row?)  
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
    Simple BOT Version 1 just updates the sentence used counter
    """
       
    SQL = 'UPDATE sentences SET used=used+1 WHERE hashid=%s'
    cursor.execute(SQL, (sentence_id))
    
def train_me(inputSentence, responseSentence, cursor):
    inputWords = get_words(inputSentence) #list of tuples of words + occurrence count
    responseSentenceID, exists = item_id('sentence', responseSentence, cursor) 
    set_association(inputWords, responseSentenceID, cursor)
    
    
def sentence_rf_class(sentence):
    """
    Pass in a sentence, with unique ID and pass back a classification code
    Use a pre-built Random Forest model to determine classification based on
    features extracted from the sentence.  
    """
    # Load a pre-built Random Forest Model
    with open(RF_MODEL_LOCATION, 'rb') as f:
        rf = pickle.load(f)
    
    id = hashtext(sentence)  #features needs an ID passing in at moment - maybe redundant?
    fseries = features.features_series(features.features_dict(id,sentence))
    width = len(fseries)
    fseries = fseries[1:width-1]  #All but the first and last item (strip ID and null class off)
    
    #Get a classification prediction from the Model, based on supplied features
    sentence_class = rf.predict([fseries])[0].strip()
    
    return sentence_class

def get_grammar(sentence):
    """
    Use Stanford CoreNLP to extract grammar from Stanford NLP Java utility
    Return 
       root topic (lower-case string - "Core"),
       subj (list with main subj first, compounds after) 
       obj (list with main obj first, compounds after)
    """
    os.environ['JAVAHOME'] = JAVA_HOME  # Set this to where the JDK is
    dependency_parser = StanfordDependencyParser(path_to_jar=STANFORD_NLP, path_to_models_jar=STANFORD_MODELS)
    
    regexpSubj = re.compile(r'subj')
    regexpObj = re.compile(r'obj')
    regexpMod = re.compile(r'mod')
    regexpNouns = re.compile("^N.*|^PR.*")
    
    sentence = sentence.lower()

    #return grammar Compound Modifiers for given word
    def get_compounds(triples, word):
        compounds = []
        for t in triples:
            if t[0][0] == word:
                if t[2][1] not in ["CC", "DT", "EX", "LS", "RP", "SYM", "TO", "UH", "PRP"]:
                    compounds.append(t[2][0])
        
        mods = []
        for c in compounds:
            mods.append(get_modifier(triples, c))
        
        compounds.append(mods)
        return compounds
    
    def get_modifier(triples, word):
        modifier = []
        for t in triples:
            if t[0][0] == word:
                 if regexpMod.search(t[1]):
                     modifier.append(t[2][0])
                     
        return modifier

    #Get grammar Triples from Stanford Parser
    result = dependency_parser.raw_parse(sentence)
    dep = next(result)  # get next item from the iterator result
    
    #Get word-root or "topic"
    root = [dep.root["word"]]
    root.append(get_compounds(dep.triples(), root[0]))
    root.append(get_modifier(dep.triples(), root[0]))
    
    subj = []
    obj = []
    lastNounA = ""
    lastNounB = ""
    
    for t in dep.triples():
        if regexpSubj.search(t[1]):
            subj.append(t[2][0] )
            subj.append(get_compounds(dep.triples(),t[2][0]))
        if regexpObj.search(t[1]):
            obj.append(t[2][0])
            obj.append(get_compounds(dep.triples(),t[2][0]))
        if regexpNouns.search(t[0][1]):
            lastNounA = t[0][0]
        if regexpNouns.search(t[2][1]):
            lastNounB = t[2][0]
    
    return list(utils.flatten([root])), list(utils.flatten([subj])), list(utils.flatten([obj])), list(utils.flatten([lastNounA])), list(utils.flatten([lastNounB]))
    
def store_statement(sentence, cursor):
    
    #Write the sentence to SENTENCES with hashid = id, used = 1 OR update used if already there
    sentence_id, exists = item_id('sentence', sentence, cursor)
    
    SQL = 'UPDATE sentences SET used=used+1 WHERE hashid=%s'
    cursor.execute(SQL, (sentence_id))
    
    #If the sentence already exists, assume the statement grammar is already there
    if not exists:
        topic, subj,obj,lastNounA, lastnounB = get_grammar(sentence)
        lastNouns = lastNounA + lastnounB
        
        #topic
        for word in topic:
            word_id, exists = item_id('word', word, cursor)
            SQL = "INSERT INTO statements (sentence_id, word_id, class) VALUES (%s, %s, %s) "
            cursor.execute(SQL, (sentence_id, word_id, 'topic'))
        #subj
        for word in subj:
            word_id, exists = item_id('word', word, cursor)
            SQL = "INSERT INTO statements (sentence_id, word_id, class) VALUES (%s, %s, %s) "
            cursor.execute(SQL, (sentence_id, word_id, 'subj'))
        
        #obj
        for word in obj:
            word_id, exists = item_id('word', word, cursor)
            SQL = "INSERT INTO statements (sentence_id, word_id, class) VALUES (%s, %s, %s) "
            cursor.execute(SQL, (sentence_id, word_id, 'obj'))
        
        #lastNouns
        for word in lastNouns:
            word_id, exists = item_id('word', word, cursor)
            SQL = "INSERT INTO statements (sentence_id, word_id, class) VALUES (%s, %s, %s) "
            cursor.execute(SQL, (sentence_id, word_id, 'nouns'))

def get_answer(sentence, cursor):
    """ Retrieve the most likely question-answer response from the database
    pass in humanWords "sentence", extract a grammar for it, query from statements
    table based on subject and other grammar components,
    passback ordered list of results , up to "listSize" in size  
    """
    results = []
    listSize = 10
    
    topic,subj,obj,lastNounA,lastNounB = get_grammar(sentence)
    subj_topic = subj + topic
    subj_obj = subj + obj
   
    full_grammar = topic + subj + obj + lastNounA + lastNounB 
    full_grammar_in = ' ,'.join(list(map(lambda x: '%s', full_grammar))) # SQL in-list fmt
    subj_in = ' ,'.join(list(map(lambda x: '%s', subj_topic))) # SQL in-list fmt
    
    if (DEBUG_ANSWER == True): print("DEBUG_ANSWER: grammar: SUBJ", subj, " TOPIC", topic, " OBJ:", obj, " L-NOUNS:", lastNounA + lastNounB)
    if (DEBUG_ANSWER == True): print("DEBUG_ANSWER: subj_in", subj_in, "\nsubj_topic", subj_topic, "\nfull_grammar_in", full_grammar_in, "\nfull_grammer", full_grammar)
    
   
    SQL1 = """SELECT count(*) score, statements.sentence_id sentence_id, sentences.sentence
    FROM statements
    INNER JOIN words ON statements.word_id = words.hashid
    INNER JOIN sentences ON sentences.hashid = statements.sentence_id
    WHERE words.word IN (%s) """
    SQL2 = """
    AND statements.sentence_id in (
        SELECT sentence_id
        FROM statements
        INNER JOIN words ON statements.word_id = words.hashid
        WHERE statements.class in ('subj','topic')  -- start with subset of statements covering question subj/topic
        AND words.word IN (%s)
    )
    GROUP BY statements.sentence_id, sentences.sentence
    ORDER BY score desc
    """
    
    SQL1 = SQL1 % full_grammar_in
    SQL2 = SQL2 % subj_in
    SQL = SQL1 + SQL2
    #if (DEBUG_ANSWER == True): print("SQL: ", SQL, "\n  args full_grammer_in: ", full_grammar_in, "\n  args subj_in", subj_in)
    
    cursor.execute(SQL, full_grammar + subj_topic)
    for i in range(0,listSize):
        row = cursor.fetchone()
        if row:
            results.append([row["sentence_id"], row["score"], row["sentence"]])
            if (DEBUG_ANSWER == True): print("DEBUG_ANSWER: ", row["sentence_id"], row["score"], row["sentence"])
        else:
            break
    
    # increment score for each subject / object match - sentence words are in row[2] col
    i = 0
    top_score = 0 # top score
    for row in results:  
        word_count_dict = get_words(row[2])   
        subj_obj_score = sum( [value for key, value in word_count_dict if key in subj_obj] )
        results[i][1] = results[i][1] + subj_obj_score
        if results[i][1] > top_score: top_score = results[i][1]
        i = i + 1
    
    #filter out the top-score results
    results = [l for l in results if l[1] == top_score]
    
    return results   
    
def chat_flow(cursor, humanSentence, weight):
   
    trainMe = False # if true, the bot requests some help
    checkStore = False # if true, the bot checks if we want to store this as a fact
    humanWords = get_words(humanSentence)
    weight = 0
    
    #Get the sentence classification based on RF model
    classification = sentence_rf_class(humanSentence)
    
    ## Statement ##
    if classification == 'S':   
        # Verify - do we want to store it?
        checkStore = True
        botSentence = "OK, I think that is a Statement."
             
        ##store_statement(humanSentence, cursor)
        ##botSentence = random.choice(STATEMENT_STORED)

    ## Question
    elif classification == 'Q':
        answers = get_answer(humanSentence, cursor)
        if len(answers) > 0:
            answer = ""
            weight = int(answers[0][1])  #2018-02-19
            if weight > 1:               #2018-02-19
                for a in answers:
                     answer = answer + "\n" + a[2]

                botSentence = answer
                #weight = answers[0:1] 2018-02-19
                ##sentence_id, weight, botSentence = answers[0]
            else:
                botSentence = NO_ANSWER_DATA
        else:
            botSentence = NO_ANSWER_DATA
                        
    ## Chat ##
    elif classification == 'C':
        # Take the human-words and try to find a matching response based on a weighting-factor
        chat_matches = get_matches(humanWords, cursor)    #get_matches returns ordered list of matches for words:
        
        if len(chat_matches) == 0:
            botSentence = NO_CHAT_DATA
            trainMe = True
        else:
            sentence_id, botSentence, weight = chat_matches[0]
            if weight > ACCURACY_THRESHOLD:
                # tell the database the sentence has been used and other feedback
                feedback_stats(sentence_id, cursor)
                train_me(botSentence, humanSentence, cursor)
            else:
                botSentence = NO_CHAT_DATA
                trainMe = True
    else:
        raise RuntimeError('unhandled sentence classification') from error
                        
    return botSentence, weight, trainMe, checkStore

    
if __name__ == "__main__":    
    
    conf = utils.get_config()
    regexpYes = re.compile(r'yes')
    
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
    checkStore = False
    
    botSentence = 'Hello!'
    while True:
        
        # Output bot's message
        if DEBUG_WEIGHT: 
            #print('Bot> ' + botSentence + ' DEBUG_WEIGHT:' + str(round(weight,5)) ) #2018-02-19
            print('Bot> ' + botSentence + ' DEBUG_WEIGHT:' + str(round(weight,5) ) )
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
        
        if checkStore:
            print('Bot> Shall I store that as a fact for future reference?  ("yes" to store)' )
            previousSentence = humanSentence
            humanSentence = input('>>> ').strip()
            
            if regexpYes.search(humanSentence.lower()):
                #Store previous Sentence
                store_statement(previousSentence, cursor)
                print(random.choice(STATEMENT_STORED))

            else:
                print("Bot> OK, moving on..." )
                checkStore = False
         
        # Ask for user input; if blank line, exit the loop
        humanSentence = input('>>> ').strip()
        if humanSentence == '' or humanSentence.strip(punctuation).lower() == 'quit' or humanSentence.strip(punctuation).lower() == 'exit':
            break
    
        botSentence, weight, trainMe, checkStore = chat_flow(cursor, humanSentence, weight)
    
        connection.commit()
