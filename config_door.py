#
#	config_door.py
#
#	Defines constants used in door application
#

import httplib2
from flask import json
import logging
import time

# Constants used on server and client
GARAGE = "Garage"
MAN = "Man"
doors = [GARAGE, MAN]
OPEN = "Open"
CLOSED = "Closed"
OFF = "Off"
ON = "On"
TIMER = "Timer"
NIGHT = "Night"
VACATION = "Vacation"
INFO = "Info"
WARNING = "Warning"
CRITICAL = "Critical"
NONE = "None"
timer_severities = [WARNING, CRITICAL]
init_wait_time = 1
max_wait_time = 8193

# logging constants
log_file = "/var/log/doors/garage.log"
log_format = "%(asctime)s: %(message)s"
date_format = "%m/%d/%Y %I:%M:%S %p"

# GPIO pin for each door
pin = {GARAGE: 23, MAN: 24}

# Servers and Clients
web_server = "blueberry"
door_server = "cranberry"
detect_server = "strawberry"

def rest_conn(host, port, path, method, data):
	"""Get/send content using REST from/to another host"""

	### Inputs ###
	#
	#	host: host to connect to
	#	port: port on host to communicate with
	#	path: path to rest resource
	#	method: http method being used - usually GET or POST
	#	data: dictionary of data to POST or empty if GET
	#
	### Outputs ###
	#
	#	data retrieved from url
	#
	###

	httplib2.debuglevel     = 0
	http                    = httplib2.Http()
	content_type_header     = "application/json"
	headers = {'Content-Type': content_type_header}
	url = "http://" + host + ":" + port + path

	# get initial state of both doors
	wait_time = init_wait_time
	host_down = True
	while host_down:

		try:
			if method == 'GET':
				response, content = http.request(url, method, headers=headers)
				logging.debug('CONNECT-Recv: ' + host + ',OK')	# log successful transmission of event
				print "Response:"
				print response
				print "Content:"
				print content
				return json.loads(content)
			elif method == 'POST':
				response, content = http.request(url, method, json.dumps(data), headers=headers)
				logging.debug('CONNECT-Send: ' + host + ',OK')	# log successful transmission of event
				print "Response:"
				print response
				print "Content:"
				print content
				return {}
			host_down = False
		except:
			print "Error Connecting ..."
			if method == 'GET':
				logging.debug('CONNECT-Recv: ' + host + ',Error')	# log unsuccessful transmission of event
			elif method == 'POST':
				logging.debug('CONNECT-Send: ' + host + ',Error')	# log unsuccessful transmission of event

			time.sleep(wait_time)
			if wait_time < max_wait_time:
				wait_time = wait_time + wait_time


def log_restart(script_name):
	"""Log restart of script"""

	### Inputs ###
	#
	#	script_name: the filename of the script running
	#
	### Outputs ###
	#
	#	None
	#
	###

	# Configure log file
	logging.basicConfig(filename=log_file, level=logging.DEBUG, format=log_format, datefmt=date_format)
	logging.debug('RESTART: ' + script_name)	# log program restart
