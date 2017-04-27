import socket
import select
import argparse

#ADDR="vhost1"
#PORT=9999

# arg-parse
parser = argparse.ArgumentParser(description='Interactive Chat Client using TCP Sockets')
parser.add_argument('-a', '--addr',  dest = 'host', default = 'vhost1', help='remote host-name or IP address', required=True)
parser.add_argument('-p', '--port',  dest = 'port', type = int, default = 9999, help='TCP port', required=True)

args = parser.parse_args()
ADDR = args.host
PORT = args.port

sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (ADDR, PORT)

print("Connecting to server", ADDR, " at port ", PORT)

sckt.connect((ADDR, PORT))
while True:
    #Check that our connection is still alive before trying  to do anything
    try:
        ready_to_read, ready_to_write, in_error = select.select([sckt,], [sckt,], [], 5)
    except select.error:
        sckt.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
        sckt.close()
        print('connection error')
        break

    l = 0
    while l < 1 :      #put this loop in to check message has text ... catches strange CR issue on windows
        message = input('>>> ').strip()
        l = len(message)
    
    if (message == "exit" or message == "quit"):
        sckt.send(message.encode())
        sckt.send("".encode())
        break
    
    #sckt.send(message)
    sckt.send(message.encode())
    #print("Sent {}".format(message))  # DEBUG
    #print("Received {}".format(sckt.recv(1024).decode()))
    print(sckt.recv(1024).decode())

print("Connection closed")
