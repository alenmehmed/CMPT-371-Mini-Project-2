# Include Python's Socket Library
from socket import *

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

class GoBackNReceiver:
     expectedseqnum = 1
     send_pkt = Packet()

     def A(self):
          self.expectedseqnum = 1
          self.send_pkt = Packet(seqnum=0,data='ACK',checksum=)

     def not_corrupt(self, rev_pkt):
          return (parse(rev_pkt)['UDP_checksum'] % 16) == 0 
          # Returns 1 if divisible by 16, 0 otherwise 

     def rdt_rcv(self,rcv_pkt, clientAddress):
          if not self.not_corrupt(rcv_pkt):
               # State machine says extract & deliver?
               check_sum = parse(rcv_pkt)['UDP_checksum']
               sndpkt = Packet(checksum=check_sum, seqnum=self.expectedseqnum, data='ACK')
               self.udt_send(sndpkt, clientAddress)
               self.expectedseqnum = self.expectedseqnum + 1

     def udt_send(self, sndpkt, clientAddress):
          serverSocket.sendto(sndpkt.encode(), clientAddress)

# Bind the server port to the socket
serverSocket.bind(('',serverPort))

# Create GoBackN Receiver
Receiver = GoBackNReceiver()
print ("The server is ready to receive")

while True: # Forever Loop
    # Read from UDP Socket into message & client address
    message, clientAddress = serverSocket.recvfrom(2048)
    
    Receiver.rdt_rcv(message, clientAddress)

    send_packet = Packet(checksum=parse(message)['UDP_checksum'], 
                         seqnum=Receiver.nextseqnum, 
                         data='ACK')

    Receiver.udt_send(send_packet, clientAddress)

