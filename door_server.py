#!local/bin/python
#
# File: door_server.py
#
#	Receives opening and closing messages for garage doors over socket and sends notifications
#

from config_door import *
#from datetime import datetime, date, time, timedelta
import datetime
import time
import threading
import logging
import smtplib
import httplib2
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from flask import Flask, request, json, jsonify

notify_conf_file = "/home/pi/doors/conf/notify.conf"

# Alarm timer initializations
timer = {GARAGE: {WARNING: {}, CRITICAL: {}}, MAN: {WARNING: {}, CRITICAL: {}}}

app = Flask(__name__)

#
# Function Definitions
#


def get_door_info():
	"""Initializes information about each door"""

	### Inputs ###
	#
	#	None
	#
	### Outputs ###
	#
	#	severity: dictionary of info for each door which includes:
	#				state: state of the door, either OPEN or CLOSED
	#				severity: current alarm severity for the door
	#				timestamp: time of the last change in severity or change in state
	#
	###

	# initialize dictionary of current door states
	door_state = rest_conn(detect_server, "5000", "/api/get_doors", "GET", "")

	timestamp = time.time()
	print "timestamp = ", str(timestamp)

	# initialize info for each door
	for door in doors:
		print door
		state = door_state[door]

		# populate dictionary of info about door
		door_info[door]['state'] = state
		door_info[door]['severity'] = check_alarm(door, state, timestamp)
		door_info[door]['timestamp'] = timestamp

	return door_info


def timer_notify(door, event_time, severity, limit):
	"""Send notification when a timer event occurs."""

	### Inputs ###
	#
	#	door: the door that created the event
	#	event_time: the time when the event originally occurred
	#	severity: the severity of the event
	#	limit: time limit that has expired
	#
	### Outputs ###
	#
	#	None
	#
	###

	global door_info, in_alarm

	door_info[door]['severity'] = severity
	door_info[door]['timestamp'] = event_time

	asc_time = time.ctime(event_time)
	asc_limit = str(limit)

	# log event and send email
	log_str = 'Timer (' + asc_limit + 's) expired'
	mail_str = door + ' door has been open more than ' + asc_limit + 's.\nSince ' + asc_time
	notify(door, severity, mail_str, log_str)

	return

def notify(door, severity, mail_str, log_str):
	"""Send email and log message."""

	### Inputs ###
	#
	#	door: door that has been opened
	#	severity: alarm severity
	#	mail_str: string which is body of mail
	#	log_str: string to be logged
	#
	### Outputs ###
	#
	#	None
	#
	###

	prefix = '[' + door.upper() + ']'
	if log_str != "":
		full_log_str = prefix + severity.upper() + ': ' + log_str
		logging.debug(full_log_str)

	if mail_str != "":
		# send email
		mail_addr = 'djerome@gmail.com'
		msg = MIMEMultipart()
		msg['From'] = mail_addr
		msg['To'] = mail_addr
		msg['Subject'] = '[GARAGE] ' + door + ' door ' + severity.upper() + ' Alarm'
		msg.attach(MIMEText(mail_str))
		mailserver = smtplib.SMTP('smtp.gmail.com', 587)
		# identify ourselves to smtp gmail client
		mailserver.ehlo()
		# secure our email with tls encryption
		mailserver.starttls()
		# re-identify ourselves as an encrypted connection
		mailserver.ehlo()
		mailserver.login(mail_addr, 'criznartfpjlyhme')
		mailserver.sendmail(mail_addr, mail_addr, msg.as_string())
		mailserver.quit()

	return

# Function that stops timers for a door
def stop_timers(door):
	"""Stops door timers"""

	### Inputs ###
	#
	#	door: door to stop timers for
	#
	### Outputs ###
	#
	#	None.
	#
	###

	# stop all timers
	for severity in timer_severities:
		if timer[door][severity]:
			print "Stopping " + severity + " timer for " + door
			timer[door][severity].cancel()

	log_str = 'Stopping Timers'
	notify(door, INFO, "", log_str)

	return

# Function that checks if event occurred during an alarm period like night or vacation
def check_period(door, start, end, timestamp, notify_mode):
	"""Checks if event occurred during alarm period"""

	### Inputs ###
	#
	#	door: door being checked
	#	start: start of time period
	#	end: end of time period
	#	timestamp: time of event
	#	notify_mode: notification mode
	#
	### Outputs ###
	#
	#	alarm: alarm state for the door
	#
	###

	dt_timestamp = datetime.datetime.fromtimestamp(timestamp)
	if (dt_timestamp > start) and (dt_timestamp < end):
		print notify_mode + " Alarm"
		alarm = CRITICAL
		asc_start = start.strftime("%c")
		asc_end = end.strftime("%c")
		asc_time = time.ctime(timestamp)

		# log event and send email
		log_str = notify_mode + ' Alarm: Open between ' + asc_start + ' - ' + asc_end
		mail_str = door + ' door was opened during ' + notify_mode + ' at ' + asc_time + '.\n' + notify_mode + ' is: ' + asc_start + ' - ' + asc_end + '.'
		notify(door, alarm, mail_str, log_str)
	else:
		print"NO " + notify_mode + " Alarm"
		alarm = NONE

	return alarm

# Function that checks if a door is in alarm
def check_alarm(door, event, timestamp):
	"""Checks if door is in alarm"""

	### Inputs ###
	#
	#	door: door that has generated event
	#	event: event that has taken place
	#	timestamp: timestamp for door event
	#
	### Outputs ###
	#
	#	alarm: alarm state for the door
	#
	###

	global notify_mode, notify_params

	print "Checking alarm for " + door + " " + notify_mode

	# if a door has been opened, take appropriate action depending on security mode
	if event == OPEN:

		if notify_mode == OFF:

			alarm = NONE

		elif notify_mode == TIMER:

			# start timers
			print "TIMER - Starting timers"

			# Setup and start alarm timers
			for severity in timer_severities:
				limit = int(notify_params[severity])
				timer[door][severity] = threading.Timer(limit, timer_notify, args=(door,timestamp,severity,limit,))
				timer[door][severity].name = severity
				timer[door][severity].start()

			alarm = INFO
			log_str = 'Starting Timers'
			notify(door, alarm, "", log_str)

		elif notify_mode == NIGHT:

			print "NIGHT - Checking night alarm"
			one_day = datetime.timedelta(days=1)
			day_today_date = datetime.date.today()

			dusk_time = datetime.datetime.time(datetime.datetime.strptime(notify_params['dusk'], "%H:%M"))
			dusk = datetime.datetime.combine(day_today_date, dusk_time)
			print "dusk today"
			print dusk
			dawn_time = datetime.datetime.time(datetime.datetime.strptime(notify_params['dawn'], "%H:%M"))
			dawn = datetime.datetime.combine(day_today_date, dawn_time)
			print "dawn today"
			print dawn

			if dusk < dawn:
				print "dusk and dawn on same day"
			else:
				print "dawn is on next day"
				dawn = dawn + one_day
				print "New dawn"
				print dawn

			alarm = check_period(door, dusk, dawn, timestamp, notify_mode)

		elif notify_mode == VACATION:

			# check time of event and send alarm if during defined vacation period
			print "VACATION - Checking time of event and comparing with vacation time"

#			vac_start_date = date(int(notify_params['syr']), int(notify_params['smon']), int(notify_params['sday']))
#			vac_start_time = time(int(notify_params['shr']), int(notify_params['smin']), 0)
#			vac_start = datetime.datetime.combine(vac_start_date, vac_start_time)
			vac_start = datetime.datetime.strptime(notify_params['v_start'], "%d/%m/%y %H:%M")
			print "vac_start"
			print vac_start
#			vac_end_date = date(int(notify_params['eyr']), int(notify_params['emon']), int(notify_params['eday']))
#			vac_end_time = time(int(notify_params['ehr']), int(notify_params['emin']), 0)
#			vac_end = datetime.datetime.combine(vac_end_date, vac_end_time)
			vac_end = datetime.datetime.strptime(notify_params['v_end'], "%d/%m/%y %H:%M")
			print "vac_end"
			print vac_end

			alarm = check_period(door, vac_start, vac_end, timestamp, notify_mode)

		elif notify_mode == ALL:

			# notify door was opened
			alarm = INFO
			mail_str = door + ' door was opened at ' + time.ctime(timestamp) + '.'
			notify(door, alarm, mail_str, "")

	elif event == CLOSED:

		alarm = INFO

		# stop timers
		if notify_mode == TIMER:
			stop_timers(door)

		elif notify_mode == ALL:

			mail_str = door + ' door was closed at ' + time.ctime(timestamp) + '.'
			notify(door, alarm, mail_str, "")

		# if door was in alarm, send notification that door was closed
		if (door_info[door]['severity'] == CRITICAL) or (door_info[door]['severity'] == WARNING):

			log_str = 'Alarm Cleared'
			mail_str = door + ' door was closed at ' + time.ctime(timestamp) + '.'
			notify(door, alarm, mail_str, log_str)

	return alarm


# Function that handles POST for changing notification mode
@app.route("/api/notify_change", methods=['POST'])
def api_notify_mode():

	global door_info, notify_mode, notify_params

	if request.headers['Content-Type'] == 'application/json':

		# stop timers if they are already running
		if notify_mode == TIMER:
			for door in doors:
				stop_timers(door)

		# retrieve data from JSON
		notify_data = request.json

		# write new notification data to file
		print "Got security mode change"
		notify_mode = notify_data['mode']
		notify_params = notify_data['params']
		print notify_mode
		print notify_params
		with open(notify_conf_file, 'w') as outfile:
			json.dump(notify_data, outfile)
			outfile.close()

		log_str = 'Notification Mode changed to ' + notify_mode
		logging.debug(log_str)

		# Get information about state of doors and alarm if necessary
		door_info = get_door_info()

		return "OK", 200
	else:
		return "Unsupported Media Type", 415

# Function that handles POST for receiving data from door detection client
@app.route("/api/door_event", methods=['POST'])
def api_door_event():
	if request.headers['Content-Type'] == 'application/json':

		# retrieve data from JSON
		event_data = request.json
		door = event_data['door']
		event = event_data['event']
		timestamp = event_data['timestamp']
		asc_timestamp = time.ctime(float(timestamp))

		# log the received event with a prefix for the appropriate door
		print "Got event " + event + "," + door + "," + asc_timestamp
		log_str = event + " event received; Sent " + asc_timestamp
		notify(door, INFO, "", log_str)

		# update dictionary of info about door
		door_info[door]['state'] = event
		door_info[door]['severity'] = check_alarm(door, event, timestamp)
		door_info[door]['timestamp'] = timestamp

		return "OK", 200
	else:
		return "Unsupported Media Type", 415

# Function that handles GET from web server for notification mode, info for all doors and part of log
@app.route("/api/get_info", methods=['GET'])
def api_get_info():

	global notify_mode, notify_params, door_info

	print "Got request for data"

	notify_data = {'mode': notify_mode, 'params': notify_params}

	# get last 50 lines in log file
	garage_log_file = open(log_file, 'r')
	lines = garage_log_file.readlines()
	garage_log_file.close()
	last50 = lines[-50:]

	return jsonify({'door_info': door_info, 'notify_data': notify_data, 'last50': last50})


#
# Main
#

# initializations
door_info = {}
for door in doors:
	door_info[door] = {}
	door_info[door]['severity'] = NONE

# Configure log file and log program restart
log_restart(os.path.basename(__file__))

# get the security mode information from the security config file
# includes the security mode (OFF, TIMER, NIGHT, VACATION) and the appropriate parameters for that mode
with open(notify_conf_file, 'r') as json_data:
	notify_data = json.load(json_data)
	json_data.close()
notify_mode = notify_data['mode']
notify_params = notify_data['params']
print "notify_mode: ", notify_mode
print "notify_params: ", notify_params

# get information about each door
# includes the state (OPEN or CLOSED), alarm severity (INFO, WARNING, CRITICAL) and timestamp for the last event
door_info = get_door_info()
print "door_info: ", door_info

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = True, use_reloader=False)
