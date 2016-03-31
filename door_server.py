#!local/bin/python
#
# File: door_server.py
#
#	Receives opening and closing messages for garage doors over socket and sends notifications
#

from config_door import *
import datetime
import threading
import logging
import smtplib
import httplib2
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from flask import Flask, request, json, jsonify

sec_conf_file = "/var/log/doors/.sec_data"

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

	timestamp = datetime.datetime.now()

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

	global door_info

	door_info[door]['severity'] = severity
	door_info[door]['timestamp'] = event_time

	asc_time = event_time.strftime("%c")
	prefix = '[' + door.upper() + ']'

	# log event and send email
	log_str = 'Open since ' + asc_time + ' (> ' + str(limit) + 's)'
	mail_str = 'Door has been open more than ' + str(limit) + 's.\nSince ' + asc_time
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
	full_log_str = prefix + severity.upper() + log_str + ': '
	logging.debug(full_log_str)

	# send email
	mail_addr = 'djerome@gmail.com'
	msg = MIMEMultipart()
	msg['From'] = mail_addr
	msg['To'] = mail_addr
	msg['Subject'] = prefix + ' ' + severity.upper() + ': Door Open'
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

	global sec_mode, sec_params

	# stop timers
	prefix = '[' + door.upper() + ']'
	if sec_mode == TIMER:
		for severity in timer_severities:
			if timer[door][severity]:
				print "Stopping " + severity + " timer for " + door
				timer[door][severity].cancel()
				stop_str = prefix + 'Stopping ' + severity + ' timer'
				logging.debug(stop_str)

	asc_time = timestamp.strftime("%c")

	# if a door has been opened, take appropriate action depending on security mode
	if event == OPEN:

		if sec_mode == OFF:

			alarm = NONE

		elif sec_mode == TIMER:

			# start timers
			print "TIMER - Starting timers"
			prefix = '[' + door.upper() + ']'
			open_str = prefix + 'Open - Starting timers'
			logging.debug(open_str)

			# Setup and start alarm timers
			for severity in timer_severities:
				limit = int(sec_params[severity])
				timer[door][severity] = threading.Timer(limit, timer_notify, args=(door,timestamp,severity,limit,))
				timer[door][severity].name = severity
				timer[door][severity].start()

			alarm = INFO

		elif sec_mode == NIGHT:

			print "NIGHT - Checking night alarm"
			one_day = datetime.timedelta(days=1)
			day_today_date = datetime.date.today()

			dusk_time = datetime.strptime(sec_params['dusk'], "%H:%M")
			dusk = datetime.datetime.combine(day_today_date, dusk_time)
			print "dusk today"
			print dusk
			dawn_time = datetime.strptime(sec_params['dawn'], "%H:%M")
			dawn = datetime.datetime.combine(day_today_date, dawn_time)
			print "dawn today"
			print dawn

			if dusk < dawn:
				print "dusk and dawn on same day"
			else:
				print "dusk is on previous day"
				dawn = dawn + one_day
				print "New dawn"
				print dawn

			if (timestamp > dusk) and (timestamp < dawn):
				print "Night Alarm"
				alarm = CRITICAL
				asc_dusk = dusk.strftime("%c")
				asc_dawn = dawn.strftime("%c")

				# log event and send email
				log_str = 'Open at night: ' + asc_time + ' (' + asc_dusk + ' - ' + asc_dawn + ')'
				mail_str = 'Door was opened at night at ' + asc_time + ' (between ' + asc_dusk + ' and ' + asc_dawn + ').'
				notify(door, alarm, mail_str, log_str)
			else:
				print"NO Night Alarm"
				alarm = NONE

		elif sec_mode == VACATION:

			# check time of event and send alarm if during defined vacation period
			print "VACATION - Checking time of event and comparing with vacation time"

			vac_start_date = datetime.date(int(sec_params['syr']), int(sec_params['smon']), int(sec_params['sday']))
			vac_start_time = datetime.time(int(sec_params['shr']), int(sec_params['smin']), 0)
			vac_start = datetime.datetime.combine(vac_start_date, vac_start_time)
			print "vac_start"
			print vac_start
			vac_end_date = datetime.date(int(sec_params['eyr']), int(sec_params['emon']), int(sec_params['eday']))
			vac_end_time = datetime.time(int(sec_params['ehr']), int(sec_params['emin']), 0)
			vac_end = datetime.datetime.combine(vac_end_date, vac_end_time)
			print "vac_end"
			print vac_end

			if (timestamp > vac_start) and (timestamp < vac_end):
				print "Vacation Alarm"
				alarm = CRITICAL
				asc_start = vac_start.strftime("%c")
				asc_end = vac_end.strftime("%c")

				# log event and send email
				log_str = 'Open during vacation: ' + asc_time + ' (' + asc_start + ' - ' + asc_end + ')'
				mail_str = 'Door was opened during vacation at ' + asc_time + ' (between ' + asc_start + ' and ' + asc_end + ').'
				notify(door, alarm, mail_str, log_str)
			else:
				print"NO Vacation Alarm"
				alarm = NONE

		# if a door has been closed, cancel the timers if necessary

	elif event == CLOSED:

		alarm = NONE

	return alarm

# Function that handles POST for changing security mode
@app.route("/api/sec_change", methods=['POST'])
def api_sec_mode():

	global door_info, sec_mode, sec_params

	if request.headers['Content-Type'] == 'application/json':

		# retrieve data from JSON
		sec_data = request.json

		# write new security data to file
		print "Got security mode change"
		sec_mode = sec_data['mode']
		sec_params = sec_data['params']
		print sec_mode
		print sec_params
		with open(sec_conf_file, 'w') as outfile:
			json.dump(sec_data, outfile)
			outfile.close()

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
		timestamp = datetime.datetime.now()
		print "Got event " + event

		# log the received event with a prefix for the appropriate door
		prefix = '[' + door.upper() + ']'
		raw_str = prefix + timestamp.strftime("%c") + ',' + door + ',' + event
		logging.debug(raw_str)

		# update dictionary of info about door
		door_info[door]['state'] = event
		door_info[door]['severity'] = check_alarm(door, event, timestamp)
		door_info[door]['timestamp'] = timestamp

		return "OK", 200
	else:
		return "Unsupported Media Type", 415

# Function that handles GET from web server for security mode, info for all doors and part of log
@app.route("/api/get_info", methods=['GET'])
def api_get_info():

	global sec_mode, sec_pararms, door_info

	print "Got request for data"

	sec_data = {'mode': sec_mode, 'params': sec_params}

	# get last 50 lines in log file
	garage_log_file = open(log_file, 'r')
	lines = garage_log_file.readlines()
	garage_log_file.close()
	last50 = lines[-50:]

	return jsonify({'door_info': door_info, 'sec_data': sec_data, 'last50': last50})


#
# Main
#

# initializations
door_info = {}
for door in doors:
	door_info[door] = {}

# Configure log file
logging.basicConfig(filename=log_file, level=logging.DEBUG, format=log_format, datefmt=date_format)
logging.debug('RESTART DOORS-'+os.path.basename(__file__))	# log program restart

# get the security mode information from the security config file
# includes the security mode (OFF, TIMER, NIGHT, VACATION) and the appropriate parameters for that mode
with open(sec_conf_file, 'r') as json_data:
	sec_data = json.load(json_data)
	json_data.close()
sec_mode = sec_data['mode']
sec_params = sec_data['params']
print "sec_mode: ", sec_mode
print "sec_params: ", sec_params

# get information about each door
# includes the state (OPEN or CLOSED), alarm severity (INFO, WARNING, CRITICAL) and timestamp for the last event
door_info = get_door_info()
print "door_info: ", door_info

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = True)
