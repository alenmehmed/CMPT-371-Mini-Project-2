# Include Python's Socket Library
from socket import *

# Timer library
import time

# Define Server IP Address and Port
serverName = 'localhost'
serverPort = 12000
# Build Server Address Using IP Address and Port
serverAddress=(serverName, serverPort)

# Create UDP Socket for Client
clientSocket = socket(AF_INET, SOCK_DGRAM)

# From: https://github.com/houluy/UDP/blob/master/udp.py
VERSION_OFF     = 0
IHL_OFF         = VERSION_OFF
DSCP_OFF        = IHL_OFF + 1
ECN_OFF         = DSCP_OFF
LENGTH_OFF      = DSCP_OFF + 1
ID_OFF          = LENGTH_OFF + 2
FLAGS_OFF       = ID_OFF + 2
OFF_OFF         = FLAGS_OFF
TTL_OFF         = OFF_OFF + 2
PROTOCOL_OFF    = TTL_OFF + 1
IP_CHECKSUM_OFF = PROTOCOL_OFF + 1
SRC_IP_OFF      = IP_CHECKSUM_OFF + 2
DEST_IP_OFF     = SRC_IP_OFF + 4
SRC_PORT_OFF    = DEST_IP_OFF + 4
DEST_PORT_OFF   = SRC_PORT_OFF + 2
UDP_LEN_OFF     = DEST_PORT_OFF + 2
UDP_CHECKSUM_OFF= UDP_LEN_OFF + 2
DATA_OFF        = UDP_CHECKSUM_OFF + 2

IP_PACKET_OFF   = VERSION_OFF
UDP_PACKET_OFF  = SRC_PORT_OFF

def parse(data):
    packet = {}
#     packet['version']       = data[VERSION_OFF] >> 4
#     packet['IHL']           = data[IHL_OFF] & 0x0F
#     packet['DSCP']          = data[DSCP_OFF] >> 2
#     packet['ECN']           = data[ECN_OFF] & 0x03
#     packet['length']        = (data[LENGTH_OFF] << 8) + data[LENGTH_OFF + 1]
#     packet['Identification']= (data[ID_OFF] << 8) + data[ID_OFF + 1]
#     packet['Flags']         = data[FLAGS_OFF] >> 5
#     packet['Offset']        = ((data[OFF_OFF] & 0b11111) << 8) + data[OFF_OFF + 1]
#     packet['TTL']           = data[TTL_OFF]
#     packet['Protocol']      = data[PROTOCOL_OFF]
# Only need these
    packet['Checksum']      = (data[IP_CHECKSUM_OFF] << 8) + data[IP_CHECKSUM_OFF + 1]
    packet['src_ip']        = '.'.join(map(str, [data[x] for x in range(SRC_IP_OFF, SRC_IP_OFF + 4)]))
    packet['dest_ip']       = '.'.join(map(str, [data[x] for x in range(DEST_IP_OFF, DEST_IP_OFF + 4)]))
    packet['src_port']      = (data[SRC_PORT_OFF] << 8) + data[SRC_PORT_OFF + 1]
    packet['dest_port']     = (data[DEST_PORT_OFF] << 8) + data[DEST_PORT_OFF + 1]
    packet['udp_length']    = (data[UDP_LEN_OFF] << 8) + data[UDP_LEN_OFF + 1]
    packet['UDP_checksum']  = (data[UDP_CHECKSUM_OFF] << 8) + data[UDP_CHECKSUM_OFF + 1]
    packet['data']          = ''.join(map(chr, [data[DATA_OFF + x] for x in range(0, packet['udp_length'] - 8)]))

    return packet

class Packet:
     def __init__(self, checksum, seqnum, data):
          self.check_sum = checksum
          self.seq_num = seqnum
          self.data = data

class GoBackNSender:
     timer = 0.0
     start = 0.0
     end = 0.0
     timeout_time = 60.0 # Call timeout like 60 seconds

     sndpkt = []

     # N is max number of unacknoweldged packets in pipeline (Window size)
     N = 16
     # base - seq num of oldest acknowledged packet
     base = 1
     nextseqnum = 1

     def A(self):
          self.base = 1
          self.nextseqnum = 1

     def rdt_send(self, send_pkt, clientSocket, serverAddress):
          if(self.nextseqnum < self.base + self.N):
               # Get packet (with checksum, data, and nextseqnum) and send over
               self.sndpkt.append(send_pkt)
               self.udt_send(clientSocket, serverAddress, parse(send_pkt)['UDP_checksum'])
               if(self.base == nextseqnum):
                    self.start_timer()
               nextseqnum = nextseqnum + 1
          else:
               # Window is full, don't send data
               pass

     def rdt_rev(self,rev_pkt):
          if not self.not_corrupt(rev_pkt):
               self.A()
          else:
               self.base = rev_pkt.seqnum + 1
               if (self.base == self.nextseqnum):
                    self.pause_timer()
               else:
                    self.start_timer()

     def not_corrupt(self, rev_pkt):
          return (parse(rev_pkt)['UDP_checksum'] % 16) == 0 
          # Returns 1 if divisible by 16, 0 otherwise 

     def timeout(self, serverAddress):
          self.start_timer()
          # send packets from base to nextseqnum - 1
          for i in range(self.base, self.nextseqnum):
               self.udt_send(clientSocket, serverAddress, i)

     def start_timer(self):
          self.timer = 0.0
          self.start = time.time()
          self.end = 0.0

     def pause_timer(self):
          self.end = time.time()
          self.timer = self.timer + (self.end - self.start)
          self.start = 0.0
          self.end = 0.0
     
     def check_timer(self, serverAddress):
          # Update timer
          now = time.time()
          self.timer = self.timer + (now - self.start)
          self.start = time.time()
          # Now check timer
          if(self.timer > self.timeout_time):
               self.timeout(serverAddress)
          else:
               pass

     def udt_send(self, clientSocket, serverAddress, seqnum):
          clientSocket.sendto(self.sndpkt[seqnum].encode(), serverAddress)

# Create GoBackN Sender
Sender = GoBackNSender()

# Create packets
message = 'HELLO'

# Message sent to the Server
Sender.rdt_send(message.encode(), clientSocket, serverAddress)

# Read reply characters from socket into string
modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

# Print received string
print(modifiedMessage.decode())

# Close the client socket
clientSocket.close()