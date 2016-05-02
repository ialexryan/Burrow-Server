import uuid

sessions = {}

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
	sessions[session_id] = ""
	return "s-" + str(session_id)

def send_forward_packet(components):
	session_id = components.next()
	packet = components.next()
	# actually forward the packet
	sessions[session_id] = "I got this: " + packet
	return "s"

def send_receive_packet(components):
	session_id = components.next()
	data = sessions[session_id]
	return "s-" + data

def send_end_session(components):
	# end the session
	session_id = components.next()
	del sessions[session_id]
	return "s"
