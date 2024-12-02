# Include Python's Socket Library
from socket import *

import pickle

import struct
# Specify Server Port
serverPort = 12000

# 1e) Declare socket UDP DGRAM 
serverSocket = socket(AF_INET, SOCK_DGRAM)

# -------REQUIREMENTS------------
# 1) Pipelined Reliable Transfer protocol

# a) Pipelined - TODO: Decide Go-Back-N or selective repeat
# b) Connection Oriented and Reliable - I think that's covered by TCP connection already so we're good
# c) Flow control - TODO: Receiver buffer? Module 3 Slide 70
# d) Congestion control - TODO: Various TCP congestion control methods in Module 3 slides 93-103 
# e) Specify which socket type 

# Sequence numbers in between:
# [0, base - 1] - Already transmitted and acknowledged packets
# [base, nextseqnum - 1] - Transmitted but not acknowledged
# [nextseqnum, base + N - 1] - Packets that can be sent immediately
# Sequence numbers greater than base + N cannot be used
# until an unacknowledged packet currently in the pipeline (specifically, the
# packet with sequence number base) has been acknowledged.

class Packet:
     def __init__(self, seqnum, data):
          self.seq_num = seqnum
          self.data = data

class GoBackNReceiver:
     expectedseqnum = 1

     def A(self):
          self.expectedseqnum = 1
          self.send_pkt = Packet(seqnum=0,data='ACK')

     def not_corrupt(self, rev_pkt):
          return (self.checksum(rev_pkt) % 16) == 0 
          # Returns 1 if divisible by 16, 0 otherwise 

     def rdt_rcv(self,rcv_pkt, clientAddress):
          if not self.not_corrupt(rcv_pkt):
               check_sum = self.checksum(rcv_pkt)
               sndpkt = Packet(seqnum=self.expectedseqnum, data='ACK')
               self.udt_send(sndpkt, clientAddress)
               self.expectedseqnum = self.expectedseqnum + 1

     def udt_send(self, sndpkt, clientAddress):
          serverSocket.sendto(pickle.dumps(sndpkt), clientAddress)

     def checksum(self, packet):
          # Step 1: Initialize the checksum sum to 0
          checksum = 0

          # Step 2: Add the packet data in 16-bit chunks (2 bytes each)
          # Iterate over the packet in chunks of 2 bytes
          for i in range(0, len(packet), 2):
               # If there's an odd byte at the end, we pad with 0
               if i + 1 < len(packet):
                    # Unpack 2 bytes into an unsigned short (16-bit)
                    word = struct.unpack("!H", packet[i:i+2])[0]
               else:
                    # Last byte (odd length), pad with 0 at the second byte
                    word = struct.unpack("!H", packet[i:i+1] + b'\x00')[0]
               
               checksum += word
               # Add carry over from 16-bit sum
               checksum = (checksum & 0xFFFF) + (checksum >> 16)

          # Step 3: One's complement the sum and return it
          checksum = ~checksum & 0xFFFF
          return checksum

# Bind the server port to the socket
serverSocket.bind(('',serverPort))

# Create GoBackN Receiver
Receiver = GoBackNReceiver()
print ("The server is ready to receive")

while True: # Forever Loop
    # Read from UDP Socket into message & client address
    message, clientAddress = serverSocket.recvfrom(2048)
    
    Receiver.rdt_rcv(message, clientAddress)

