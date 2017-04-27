import base64
import argparse
import pickle

""" 
  Trivial Password Obsfucation Utility
  Not really secure at all - key could be protected  or require manual entry to improve this
"""

CONFIG_LOC = "./config/"
KEY_LOC = "./config/"

PWD_FILE = CONFIG_LOC + ".pwd"
KEY_FILE = KEY_LOC + ".key"

def get_key():
    try:
        with open(KEY_FILE) as f:
            key = str(f.readlines())
        return(key)
    except:
        print("Can't locate key, exiting")
        exit(1)

def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = (ord(clear[i]) + ord(key_c)) % 256
        enc.append(enc_c)
    return base64.urlsafe_b64encode(bytes(enc))

def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + enc[i] - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def store_pwd(encoded):
    pickle.dump( encoded, open( PWD_FILE, "wb" ) )
        
def get_pwd():
    encoded = pickle.load( open( PWD_FILE, "rb" ) )
    return(encoded)
   
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Password Config Util', formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument('-s', '--set', dest = "password", help='Store encoded password')
    group.add_argument('-g', '--get', dest = "get", help='Get encoded password', action='store_true')
    args = vars(parser.parse_args())    
    
    key = get_key()
        
    if args["password"]:
        print("Saving Encoded Password")
        # Encode Pwd
        encoded = encode(key, args["password"])
        #Store it
        store_pwd(encoded)
    
    elif args["get"]:
        print("Get Encoded Password:")
        # Get from PWD file
        encoded = get_pwd()
        # Decode Pwd
        decoded = decode(key, encoded)
        print(decoded)
    else:
        print("Error - unknown option") 
        parser.print_usage()
        exit(1)   
