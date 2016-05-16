import uuid
import base64

from scapy import route
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.layers.inet import UDP
from scapy.all import sr

NO_ERROR = 0
INVALID_PACKET = 1
NO_FREE_PORTS = 2

# TODO: Currently sending some number of packets each time. Should later
# optimize this number and also make sure the size is under 64 kb.
SEND_N_PACKETS = 5

SERVER_IP = "131.215.172.230"
available_ports = range(30000,50000)     #ports will be removed from this list while in use
sessions = {}

class Session:
	def __init__(self, id):
		self.id = id
		self.pending_response_packets = []

	def request(self):
		if len(self.pending_response_packets) == 0:
		    return None
		else:
		    response_packets = []
		    while (len(self.pending_response_packets) != 0) and (len(response_packets) < SEND_N_PACKETS):
		        response_packets.append(self.pending_response_packets.pop(0))
		    return response_packets

	def forward(self, message):
		pkt = IP(message)        #parse the binary data to a scapy IP packet
		print "Forwarding packet"
		pkt.show2()

		if IP not in pkt:
                    return INVALID_PACKET
		original_src = pkt[IP].src   #store the original source IP
		pkt[IP].src = SERVER_IP      #spoof the source IP so the packet comes back to us
		del pkt[IP].chksum           #invalidate the checksum
                if len(available_ports) == 0:
                    return NO_FREE_PORTS
		port = available_ports.pop(0)        #get a port from our pool of available ports
		if TCP in pkt:
			protocol = TCP
			original_sport = pkt[TCP].sport  #store the original source port
			pkt[TCP].sport = port            #spoof the source port
			#pkt[TCP].dport = ____
			del pkt[TCP].chksum              #invalidate the checksum
		elif UDP in pkt:
			protocol = UDP
			original_sport = pkt[UDP].sport  #ditto
			pkt[UDP].sport = port
			#pkt[UDP].dport = ____
			del pkt[UDP].chksum
		else:
			return INVALID_PACKET

		pkt = IP(str(pkt))   #recalculate all the checksums

		print "After spoofing, packet looks like:"
		pkt.show2()

		#send packet and receive responses.
		#self.ans will contain a list of tuples of sent packets and their responses
		#self.unans will contain a list of unanswered packets
		#note: we may need to do some work to make this asynchronous
		self.ans, self.unans = sr(pkt)

		#un-spoof the source IP address and port,
		#then add to the list of packets waiting to be sent back
		for pair in self.ans:
			response = pair[1]
			response[IP].src = original_src
			response[protocol].sport = original_sport
			self.pending_response_packets.append(base64.b64encode(str(response)))

		available_ports.append(port)  #return port to available pool
                return NO_ERROR


def handle_message(message):
	response = ""
	components = iter(message.split('-'))
	type = components.next()
	if (type == 'b'):
		response = got_begin_session()
	elif (type == 'f'):
		response = got_forward_packet(components)
	elif (type == 'r'):
		response = got_request_packet(components)
	elif (type == 'e'):
		response = got_end_session(components)
	elif (type == 'test'):
		# reverse the string
		response = message[::-1]
	else:
		# This should never happen
		response = "f-1-Message type `" + type + "` is unkown"
	return response

def got_begin_session():
	session_id = uuid.uuid4().hex[-8:]
	sessions[session_id] = Session(session_id)
	return "s-" + str(session_id)

def got_forward_packet(components):
	session_id = components.next()
	session = sessions[session_id]
	try:
            while True:
	        packet = base64.b64decode(components.next())
	        err = session.forward(packet)
        except StopIteration:
            pass
        if err == NO_ERROR:
	    return "s"
        elif err == INVALID_PACKET:
            return "f-0-Packet is Invalid"
        elif err == NO_FREE_PORT:
            return "f-0-Could not find a free port"

def got_request_packet(components):
	session_id = components.next()
	data = sessions[session_id].request()
	if data == None:
		return "f-0-No Respone Received"
	else:
		response = "s"
		for packet in data:
			response += "-" + packet
		return response

def got_end_session(components):
	session_id = components.next()
	del sessions[session_id]
	return "s"
