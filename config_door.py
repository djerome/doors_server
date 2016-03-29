#
#	config_door.py
#
#	Defines constants used in door application
#

import httplib2
from flask import json
import logging
import RPi.GPIO as io

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
wait_time = 1		# initial wait time in seconds
max_wait_time = 8193

# logging constants
log_file = "/var/log/doors/garage.log"
log_format = "%(asctime)s: %(message)s"
date_format = "%m/%d/%Y %I:%M:%S %p"

# GPIO pin for each door
pin = {GARAGE: 23, MAN: 24}

# Alarm timer initializations
timer = {GARAGE: {WARNING: {}, CRITICAL: {}}, MAN: {WARNING: {}, CRITICAL: {}}}

# Servers and Clients
web_server = "blueberry"
door_server = "cranberry"
detect_server = "strawberry"

def rest_get(url):
	"""Get content over REST from another machine"""

	### Inputs ###
	#
	#	url: url to get data from
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
	client_down = True

	# get initial state of both doors
	while client_down:

		try:
			print "Connecting to " + url + " ..."
			response, content = http.request(url, 'GET', headers=headers)
			print "Response:"
			print response
			print "Content:"
			print content
			client_down = False
		except:
			print "Waiting ..."
			time.sleep(wait_time)
			if wait_time < max_wait_time:
				wait_time = wait_time + wait_time

	return json.loads(content)

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

def get_doors_state():
	"""Get state of both doors from GPIO pins"""

	### Inputs ###
	#
	#	None
	#
	### Outputs ###
	#
	#	state: dictionary of doors states
	#
	###

	state = {}
	io.setmode(io.BCM)	# set appropriate mode for reading GPIO
	for door in doors:
		io.setup(pin[door], io.IN, pull_up_down=io.PUD_UP)

	for door in doors:

		# get state of door
		if io.input(pin[door]):	# door open
			state[door] = OPEN
		else:
			state[door] = CLOSED

	return state
