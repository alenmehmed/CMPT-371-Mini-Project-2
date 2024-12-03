# Include Python's Socket Library
import pickle
import struct

# Timer library
import time
from socket import *

# Define Server IP Address and Port
serverName = 'localhost'
serverPort = 12000
# Build Server Address Using IP Address and Port
serverAddress=(serverName, serverPort)

# Create UDP Socket for Client
clientSocket = socket(AF_INET, SOCK_DGRAM)

class Packet:
     def __init__(self, seqnum, data):
          self.seq_num = seqnum
          self.data = data
          
class Err(Exception):
     pass

class GoBackNSender:
     timer = 0.0
     start = 0.0
     end = 0.0
     timeout_time = 5 # Call timeout like 60 seconds
     sndpkt = []

     # N is max number of unacknoweldged packets in pipeline (Window size)
     N = 16
     # base - seq num of oldest acknowledged packet
     base = 1
     nextseqnum = 1

     def A(self):
          self.base = 1
          self.nextseqnum = 1

     def make_packet(self, str):
          return Packet(self.nextseqnum, str)

     def rdt_send(self, send_pkt, clientSocket, serverAddress):
          if(self.timedout()):
               self.timeout(serverAddress)
          else:
               # print(self.nextseqnum)
               if(self.nextseqnum < self.base + self.N):
                    # Get packet (with checksum, data, and nextseqnum) and send over
                    self.sndpkt.append(send_pkt)
                    self.udt_send(clientSocket, serverAddress, self.nextseqnum - 1)
                    if(self.base == self.nextseqnum):
                         self.start_timer()
                    self.nextseqnum += 1
               else:
                    # Window is full, don't send data
                    print("window full")
                    while not self.timedout() and self.timer_running():
                         time.sleep(1)

                    print(self.nextseqnum, self.base)
                    if self.timedout() and not self.nextseqnum == self.base:
                         print("timed out")
                         self.timeout(serverAddress)


     def rdt_rev(self,rev_pkt):
          if not self.not_corrupt(rev_pkt):
               self.A()
          else:
               self.base = self.checksum(rev_pkt) + 1
               if (self.base == self.nextseqnum):
                    self.pause_timer()
               else:
                    self.start_timer()

     def not_corrupt(self, rev_pkt):
          return (self.checksum(rev_pkt) % 16) == 0 
          # Returns 1 if divisible by 16, 0 otherwise 


     def timeout(self, serverAddress):
          self.start_timer()
          # send packets from base to nextseqnum - 1
          msg = None
          try:
               for i in range(self.base - 1, self.nextseqnum - 1):
                    print("resending packet " + str(i))
                    self.udt_send(clientSocket, serverAddress, i)
                    clientSocket.settimeout(3)
                    try:
                         msg, _ = clientSocket.recvfrom(2048)
                    except:
                         pass
                    print(str(self.base) + " " + str(pickle.loads(msg).seq_num))
                    if(self.base == pickle.loads(msg).seq_num):
                         raise Err("")
                    self.base = pickle.loads(msg).seq_num
                    print("setting base to " + str(self.base))
          except Err:
               timeout(self, serverAddress)

          clientSocket.settimeout(None)

     def start_timer(self):
          self.timer = 0.0
          self.start = time.time()
          self.end = 0.0

     def pause_timer(self):
          self.end = time.time()
          self.timer = self.timer + (self.end - self.start)
          self.start = 0.0
          self.end = 0.0
     
     def timedout(self):
          # Update timer
          now = time.time()
          self.timer = self.timer + (now - self.start)
          self.start = time.time()
          # Now check timer
          if(self.timer > self.timeout_time):
               return True
          else:
               return False
          
     def timer_running(self):
          return self.start != self.end
          
     def udt_send(self, clientSocket, serverAddress, seqnum):
          clientSocket.sendto(pickle.dumps(self.sndpkt[seqnum]), serverAddress)

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

# Create GoBackN Sender
Sender = GoBackNSender()

seq = 1
while seq <= 32:
     packet = Sender.make_packet('Packet ' + str(seq))
     seq += 1
     Sender.rdt_send(packet, clientSocket, serverAddress)

# # Create packets
# Packet1 = Packet(1, 'Packet1')
# Packet2 = Packet(2, 'Packet2')
# Packet3 = Packet(3, 'Packet3')

# # Message sent to the Server
# Sender.rdt_send(Packet1, clientSocket, serverAddress)
# Sender.rdt_send(Packet2, clientSocket, serverAddress)
# Sender.rdt_send(Packet3, clientSocket, serverAddress)

# Read reply characters from socket into string
while(True):  
     modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

     # Print received string
     print('Modified message: ' +str(pickle.loads(modifiedMessage).data))
     print('seqnum: ' + str(pickle.loads(modifiedMessage).seq_num))

     time.sleep(1)
