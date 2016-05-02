import uuid

BUFFER_SIZE = 1024
sessions = {}

class Forward:
	sock = None
	
	def connect(self, host, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect(host, port)
			return (True, "s")
		except Exception as e:
			return (False, str(e))

	def send(self, message):
		# Parse out destination and port
		host = ""
		port = 8080
		err = self.connect(host, port)
		if (err[0] == False):
			return err
		self.sock.send(message)
		return err

	def recieve(self):
		return self.sock.recv(BUFFER_SIZE)

	def close(self):
		self.sock.close()


def handle_response(message):
	response = ""
	components = iter(message.split('-'))
	type = components.next()
	if (type == 'b'):
		response = send_begin_session()
	elif (type == 'f'):
		response = send_forward_packet(components)
	elif (type == 'r'):
		response = send_receive_packet(components)
	elif (type == 'e'):
		response = send_end_session(components)
	else:
		# Once we're actually doing packet forwarding, this shouldn't happen
		# For now, reverse the string
		response = message[::-1]
	return response

def send_begin_session():
	session_id = uuid.uuid4().hex[-8:]
	sessions[session_id] = Forward()
	return "s-" + str(session_id)

def send_forward_packet(components):
	session_id = components.next()
	packet = components.next()
	# actually forward the packet
	err = sessions[session_id].send(packet)
	if (err[0] == False):
		return "f-" + err[1] + packet
	else:
		return "s"

def send_receive_packet(components):
	session_id = components.next()
	data = sessions[session_id].receive()
	return "s-" + data

def send_end_session(components):
	# end the session
	session_id = components.next()
	sessions[session_id].close()
	del sessions[session_id]
	return "s"
