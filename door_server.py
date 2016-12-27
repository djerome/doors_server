#!local/bin/python
#
# File: door_server.py
#
#	Receives opening and closing messages for garage doors over socket and sends notifications
#
#	Data structures used:
#
#	door_info:
#	door_info[door]['state'] = OPEN|CLOSED
#	door_info[door]['severity'] = CRITICAL|WARNING|INFO|NONE
#	door_info[door]['timestamp'] = <seconds since epoch> of last event
#
#	notify_data:
#	notify_data['mode'] = ALL|VACATION|NIGHT|TIMER|OFF
#	notify_data['params'] =	{}|
#				{"v_start" = <timestamp>, "v_end" = <timestamp>}|
#				{"dawn" = <timestamp>, "dusk" = <timestamp>}|
#				{"Critical" = <seconds>, "Warning" = <seconds>}
#	notify_data['method'] = EMAIL|TEXT <or both>
#
# pseudocode
# at startup or when mode is changed
#   if mode == NIGHT or mode == VACATION
#     if start_time > time_now
#       start start_time timer
#     else
#       { start_time has already passed }
#       if event == OPEN
#         alarm
#     if end_time > time_now
#       start end_time timer
#     else
#       { end_time has already passed }
#
#     if event == OPEN
#       if timestamp > start_time and timestamp < end_time
#         alarm
#       else
#         no alarm
#     else
#       no alarm
#
# when start_time timer fires
#   if event == OPEN
#     alarm
#   if mode == NIGHT
#     start a new start_timer for next day
# when end_time timer fires
#   if event == OPEN
#     no alarm
#   if mode == NIGHT
#     start a new end_timer for next day


from config_door_common import *
import datetime
import time
import threading
import smtplib
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from flask import Flask, request, json, jsonify

app = Flask(__name__)

#
# Function Definitions
#


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

	asc_time = time.ctime(event_time)
	asc_limit = str(limit)

	# log event and send email
	log_str = 'Timer (' + asc_limit + 's) expired'
	mail_str = door + ' door has been open more than ' + asc_limit + 's.  Since:\n\t' + asc_time
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

	global notify_methods, logger

	prefix = '[' + door.upper() + ']'
	if log_str != "":
		full_log_str = prefix + severity.upper() + ': ' + log_str
		logger.info(full_log_str)

	if mail_str != "":
		for method in notify_methods:

			# send email
			msg = MIMEMultipart()
			from_addr = 'djerome@gmail.com'
			msg['From'] = from_addr
			if method == EMAIL:
				to_addr = 'djerome@gmail.com'
				msg['Subject'] = '[GARAGE] ' + door + ' door ' + severity.upper() + ' Alarm'
			if method == TEXT:
				to_addr = '4163589017@pcs.rogers.com'
			msg['To'] = to_addr
			msg.attach(MIMEText(mail_str))
			mailserver = smtplib.SMTP('smtp.gmail.com', 587)
			# identify ourselves to smtp gmail client
			mailserver.ehlo()
			# secure our email with tls encryption
			mailserver.starttls()
			# re-identify ourselves as an encrypted connection
			mailserver.ehlo()
			mailserver.login(from_addr, 'criznartfpjlyhme')
			mailserver.sendmail(from_addr, to_addr, msg.as_string())
			mailserver.quit()

	return

# Function that stops timer
def stop_timers(door, mode):
	"""Stops door timers"""

	### Inputs ###
	#
	#	door: door to stop timers for
	#	mode: notifcation mode
	#
	### Outputs ###
	#
	#	None.
	#
	###

	global timer

	# stop Timer mode timers
	if mode == TIMER:

		# stop all timers
		for severity in timer_severities:

			if timer[door][severity]:
				timer[door][severity].cancel()

			# Loop until timer is cancelled
			timer_running = True
			while timer_running:
				if timer[door][severity]:
					time.sleep(1)
				else:
					timer_running = False

		notify(door, INFO, "", 'Stopping Timers')

	# stop period (Night or Vacation) mode timers
	elif (mode == NIGHT) or (mode == VACATION):

		# stop the start and end timers for this mode
		for type in ("start", "end"):
			if timer[door][mode][type]:
				timer[door][mode][type].cancel()

		notify(door, INFO, "", 'Stopping Timers')

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
	if (dt_timestamp >= start) and (dt_timestamp < end):
		alarm = CRITICAL
		asc_start = start.strftime("%c")
		asc_end = end.strftime("%c")
		asc_time = time.ctime(timestamp)

		# log event and send email
		log_str = notify_mode + ' Alarm: Open between ' + asc_start + ' - ' + asc_end
		mail_str = door + ' door was opened during ' + notify_mode + ' at:\n\t' + asc_time + '\n' + notify_mode + ' is:\n\t' + asc_start + ' - ' + asc_end
		notify(door, alarm, mail_str, log_str)
	else:
		alarm = NONE

	return alarm

# Function that sets timers for Night and Vacation notification modes
def start_timer(mode, door, type):
	"""Starts timers for Night and Vacation notification modes"""

	### Inputs ###
	#
	#	mode: notification mode (either 'Night' or 'Vacation')
	#	door: door to set timer for
	#	type: either "start" or "end" timer
	#
	#	Note that times are formatted according to the mode:
	#		Vacation string format: "%d/%m/%y %H:%M"
	#		Night string format: "%H:%M"
	#
	### Outputs ###
	#
	#	None
	#
	###

	global timer, notify_params

	one_day_secs = datetime.timedelta(days=1).total_seconds()

	# get time now in seconds
	now_time = time.time()

	# Convert  time setting into a timestamp in seconds
	if mode == NIGHT:
		if type == "start":
			time_setting = notify_params["dusk"]
		else:
			time_setting = notify_params["dawn"]

		day_today_date = datetime.date.today()
		time_setting = datetime.datetime.time(datetime.datetime.strptime(time_setting, time_format[NIGHT]))
		fire_time = datetime.datetime.combine(day_today_date, time_setting)
		fire_time = time.mktime(fire_time.timetuple())
	else:
		if type == "start":
			time_setting = notify_params["v_start"]
		else:
			time_setting = notify_params["v_end"]

		fire_time = time.mktime(time.strptime(time_setting, time_format[VACATION]))

	# calculate delta in seconds between now and fire time 
	fire_delta = fire_time - now_time

	# if the fire_time has already passed, set new fire_time to tomorrow for NIGHT mode
	if mode == NIGHT:
		if fire_delta < 0:
			fire_delta = fire_delta + one_day_secs

	# if time that timer should fire is in the future
	if fire_delta > 0:

		# start the timer
		timer[door][mode][type] = threading.Timer(fire_delta, update_severity, args=(door,mode,type,))
		timer[door][mode][type].name = door + '_' + mode + '_' + type
		timer[door][mode][type].start()


# Function that updates alarm severity when a timer fires
def update_severity(door, mode, type):
	"""Updates alarm severity when a timer fires"""

	### Inputs ###
	#
	#	door: door that has generated event
	#	mode: notification mode
	#	type: start or end of interval
	#
	### Outputs ###
	#
	#	None
	#
	###

	global door_info, timer, notify_params

	# get current door state and use that as event
	current_state = door_info[door]['state']

	# Set timestamp to current time
	current_time = time.time()

    # update the alarm severity for the door
	door_info[door]['severity'] = check_alarm(door, current_state, current_time)

	# if NIGHT mode, start a new timer for the next day
	if mode == NIGHT:
		start_timer(NIGHT, door, type)


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

	global notify_mode, notify_params, door_info, timer

	# default alarm condition
	alarm = NONE

	if event == OPEN:

		if notify_mode == TIMER:

			# Setup and start TIMER alarm timers
			for severity in timer_severities:
				limit = int(notify_params[severity])
				timer[door][severity] = threading.Timer(limit, timer_notify, args=(door,timestamp,severity,limit,))
				timer[door][severity].name = severity
				timer[door][severity].start()

			# Send out notification that timers have been started
			notify(door, INFO, "", "Starting Timers")

		elif notify_mode == NIGHT:

			dusk_setting = notify_params['dusk']
			dawn_setting = notify_params['dawn']

			one_day = datetime.timedelta(days=1)
			day_today_date = datetime.date.today()

			# convert dusk and dawn into timestamps
			dusk_time = datetime.datetime.time(datetime.datetime.strptime(dusk_setting, time_format[NIGHT]))
			dusk = datetime.datetime.combine(day_today_date, dusk_time)
			dawn_time = datetime.datetime.time(datetime.datetime.strptime(dawn_setting, time_format[NIGHT]))
			dawn = datetime.datetime.combine(day_today_date, dawn_time)

			# adjust dawn to be the next day
			if dusk > dawn:
				dawn = dawn + one_day

			# check time of event and send alarm if timestamp is between dusk and dawn
			alarm = check_period(door, dusk, dawn, timestamp, NIGHT)

		elif notify_mode == VACATION:

			vac_start = datetime.datetime.strptime(notify_params['v_start'], time_format[VACATION])
			vac_end = datetime.datetime.strptime(notify_params['v_end'], time_format[VACATION])

			# check time of event and send alarm if timestamp is during vacation period
			alarm = check_period(door, vac_start, vac_end, timestamp, VACATION)

		elif notify_mode == ALL:

			# notify door was opened
			alarm = INFO
			mail_str = door + ' door was opened at:\n\t' + time.ctime(timestamp)
			notify(door, alarm, mail_str, "")

	elif event == CLOSED:

		if notify_mode == TIMER:

			# stop timers
			stop_timers(door, TIMER)

		elif notify_mode == ALL:

			# notify door was closed
			alarm = INFO
			mail_str = door + ' door was closed at:\n\t' + time.ctime(timestamp)
			notify(door, alarm, mail_str, "")

		# if door was in alarm, send notification that door was closed
		if (door_info[door]['severity'] == CRITICAL) or (door_info[door]['severity'] == WARNING):

			log_str = 'Alarm Cleared'
			mail_str = door + ' door was closed at:\n\t' + time.ctime(timestamp)
			notify(door, alarm, mail_str, log_str)

	return alarm


# Function that handles POST for changing notification mode or methods
@app.route("/api/notify_change", methods=['POST'])
def api_notify_mode():

	global door_info, notify_mode, notify_params, notify_methods, logger

	if request.headers['Content-Type'] == 'application/json':

		# stop any timers if they are already running
		for door in doors:
			stop_timers(door, notify_mode)

		# retrieve data from JSON
		notify_data = request.json

		# write new notification data to file
		notify_mode = notify_data['mode']
		notify_params = notify_data['params']
		notify_methods = notify_data['methods']
		with open(notify_conf_file, 'w') as outfile:
			json.dump(notify_data, outfile)
			outfile.close()

		# start timers if notification mode is Night or Vacation
		if notify_mode == NIGHT:
			for door in doors:
				start_timer(NIGHT, door, "start")
				start_timer(NIGHT, door, "end")
		elif notify_mode == VACATION:
			for door in doors:
				start_timer(VACATION, door, "start")
				start_timer(VACATION, door, "end")

		log_str = 'Notification Changes: Mode = ' + notify_mode + '; Params = ' + str(notify_params) + '; Methods = ' + str(notify_methods)
		logger.info(log_str)

		# Set timestamp to current time
		current_time = time.time()

		# Check to see if either door is now in alarm
		for door in doors:

			# get current door state and use that as event
			current_state = door_info[door]['state']

			door_info[door]['severity'] = check_alarm(door, current_state, current_time)

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

	global notify_mode, notify_params, door_info, notify_methods, restart_time

	notify_data = {'mode': notify_mode, 'params': notify_params, 'methods': notify_methods, 'restart': restart_time}

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
# time format strings
time_format = {NIGHT: "%H:%M", VACATION: "%d/%m/%y %H:%M"}

# TIMER mode severities
timer_severities = [WARNING, CRITICAL]

# dictionary that holds all information about doors
door_info = {}
for door in doors:
	door_info[door] = {}
	door_info[door]['severity'] = NONE

# configuration file where notification settings are stored
notify_conf_file = "/home/pi/doors/conf/notify.conf"

# Alarm timer initializations
timer = {}
for door in doors:
	timer[door] = {}
	for severity in timer_severities:
		timer[door][severity] = {}
	for mode in (NIGHT, VACATION):
		timer[door][mode] = {}
		for type in ("start", "end"):
			timer[door][mode][type] = {}

# Setup logger log program restart
logger = log_setup(os.path.basename(__file__))

# get the security mode information from the security config file
# includes the security mode (OFF, TIMER, NIGHT, VACATION) and the appropriate parameters for that mode
with open(notify_conf_file, 'r') as json_data:
	notify_data = json.load(json_data)
	json_data.close()
notify_mode = notify_data['mode']
notify_params = notify_data['params']
notify_methods = notify_data['methods']

# start timers for start and end of period if notification mode is Night or Vacation
if notify_mode == NIGHT:
	for door in doors:
		start_timer(NIGHT, door, "start")
		start_timer(NIGHT, door, "end")
elif notify_mode == VACATION:
	for door in doors:
		start_timer(VACATION, door, "start")
		start_timer(VACATION, door, "end")

# On startup we don't know when door state changed so set the event timestamp to the current time
restart_time = time.time()

# get the state of both doors
print "Getting door state"
door_state = rest_conn(detect_server, "5000", "/api/get_doors", "GET", "",
logger)

# initialize info for each door
for door in doors:
	state = door_state[door]

	# populate dictionary of info about door and check if door is in alarm
	door_info[door]['state'] = state
	door_info[door]['severity'] = check_alarm(door, state, restart_time)
	door_info[door]['timestamp'] = restart_time

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = True, use_reloader=False)
