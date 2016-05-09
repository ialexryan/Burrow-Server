import uuid

from scapy import route
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.layers.inet import UDP
from scapy.all import sr

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
			return self.pending_response_packets.pop(0)

	def forward(self, message):
		pkt = IP(message)        #parse the binary data to a scapy IP packet
		print "Forwarding packet"
		pkt.show2()

		assert(IP in pkt)
		original_src = pkt[IP].src   #store the original source IP
		pkt[IP].src = SERVER_IP      #spoof the source IP so the packet comes back to us
		del pkt[IP].chksum           #invalidate the checksum

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
			assert(False)

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
			self.pending_response_packets.append(str(response))

		available_ports.append(port)  #return port to available pool


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
	else:
		# Once we're actually doing packet forwarding, this shouldn't happen
		# For now, reverse the string
		response = message[::-1]
	return response

def got_begin_session():
	session_id = uuid.uuid4().hex[-8:]
	sessions[session_id] = Session(session_id)
	return "s-" + str(session_id)

def got_forward_packet(components):
	session_id = components.next()
	session = sessions[session_id]
	packet = components.next()
	session.forward(packet)
	return "s" #we should probably check for failure too

def got_request_packet(components):
	session_id = components.next()
	data = sessions[session_id].request()
	if data == None:
		return "f-0"
	else:
		return "s-" + data

def got_end_session(components):
	session_id = components.next()
	del sessions[session_id]
	return "s"
