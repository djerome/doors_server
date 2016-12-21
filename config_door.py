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

# door states
OPEN = "Open"
CLOSED = "Closed"

OFF = "Off"
ON = "On"

# notification modes
OFF = "Off"
TIMER = "Timer"
NIGHT = "Night"
VACATION = "Vacation"
ALL = "All"

# notification methods
TEXT = "Text"
EMAIL = "Email"

# alarm severities
NONE = "None"
INFO = "Info"
WARNING = "Warning"
CRITICAL = "Critical"

# time format strings
time_format = {NIGHT: "%H:%M", VACATION: "%d/%m/%y %H:%M"}

timer_severities = [WARNING, CRITICAL]
init_wait_time = 1
max_wait_time = 8193

# logging constants
log_file = "/var/log/doors/garage.log"
log_format = "%(asctime)s: %(message)s"
date_format = "%m/%d/%Y %X"

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
			status = 'OK'
			if method == 'GET':
				response, content = http.request(url, method, headers=headers)
				print "Response:"
				print response
				print "Content:"
				print content
				result =  json.loads(content)
			elif method == 'POST':
				response, content = http.request(url, method, json.dumps(data), headers=headers)
				print "Response:"
				print response
				print "Content:"
				print content
				result = {}
			host_down = False
			logging.debug('CONNECT:' + url + ',' + method + ',OK')
			return result
		except:
			status = 'Error'
			print "Error Connecting ..."
			logging.debug('CONNECT:' + url + ',' + method + ',Error')
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
