# Include Python's Socket Library
from socket import *

# Timer library
import time

# Specify Server Port
serverPort = 12000

# -------REQUIREMENTS------------
# 1) Pipelined Reliable Transfer protocol

# a) Pipelined - TODO: Decide Go-Back-N or selective repeat
# b) Connection Oriented and Reliable - I think that's covered by TCP connection already so we're good
# c) Flow control - TODO: Receiver buffer? Module 3 Slide 70
# d) Congestion control - TODO: Various TCP congestion control methods in Module 3 slides 93-103 
# e) Specify which TCP socket type - I chose STREAM

# Define packet size as 1024 bytes
PACKET_SIZE = 1024
# N is max number of unacknoweldged packets in pipeline (Window size)
N = 16
# base - seq num of oldest acknowledged packet
base = 1
nextseqnum = 1

# Sequence numbers in between:
# [0, base - 1] - Already transmitted and acknowledged packets
# [base, nextseqnum - 1] - Transmitted but not acknowledged
# [nextseqnum, base + N - 1] - Packets that can be sent immediately
# Sequence numbers greater than base + N cannot be used
# until an unacknowledged packet currently in the pipeline (specifically, the
# packet with sequence number base) has been acknowledged.

timer = 0.0
start = 0.0

def A():
     # This is our initalization function essentially
     global nextseqnum, base
     base = 1
     nextseqnum = 1

def rdt_send(data, connectionSocket):
     if(nextseqnum < base + N):
          # Create packet (with checksum, data, and nextseqnum) and send over
          # State machine uses udt_send() (unreliable data transfer send)
          connectionSocket.send(data.encode())
          if(base == nextseqnum):
               start_timer()
          nextseqnum = nextseqnum + 1
     else:
          # Window is full, don't send data
          pass

def rdt_rev(rev_pkt):
     if corrupt(rev_pkt):
          A()
     if not_corrupt(rev_pkt):
          # how to get ack num of rev_pkt?
          base = getacknum(rev_pkt) + 1
          if (base == nextseqnum):
               pause_timer()
          else:
               start_timer()


def corrupt(rev_pkt):
     return True

def not_corrupt(rev_pkt):
     return False

def timeout():
     start_timer()
     # send packets from base to nextseqnum - 1

def start_timer():
     global start
     start = time.time()

def pause_timer():
     global timer, start
     timer = timer + start
     start = 0.0

# 1e) Declare socket STREAM
serverSocket = socket(AF_INET,SOCK_STREAM)

# Bind the server port to the socket
serverSocket.bind(('',serverPort))

# Server begins listening for incoming TCP connections
serverSocket.listen(1)
print ('The server is ready to receive')

while True: # Loop forever

     # Server waits on accept for incoming requests.
     # New socket created on return
     connectionSocket, addr = serverSocket.accept()
     
     # Go-Back-N protocol 
     sentence = connectionSocket.recv(PACKET_SIZE).decode()

     # Send the reply
     capitalizedSentence = sentence.upper()
     connectionSocket.send(capitalizedSentence.encode())
     
     # Close connection to client (but not welcoming socket)
     connectionSocket.close()
