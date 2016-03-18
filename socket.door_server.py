#!local/bin/python
#
# File: door_server.py
#
#	Receives opening and closing messages for garage doors over socket and sends notifications
#

import socket
import time
import threading
import logging
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def notify(door, event_time, severity):
	"""Send notification when a timer event occurs."""

	### Inputs ###
	#
	#	door: the door that the event is coming from
	#	event_time: the time when the event originally occurred
	#	severity: the severity of the event
	#
	### Outputs ###
	#
	#	None
	#
	###

	asc_time = time.ctime(float(event_time))
	prefix = '[' + door.upper() + ']'

	# prepare severity and time threshold strings
	if severity == 'warn':
		sev = 'WARNING:'
		time_threshold = warn_limit[door]
	elif severity == 'crit':
		sev = 'CRITICAL:'
		time_threshold = crit_limit[door]

	# log the event
	log_str = prefix + sev + ' Open since ' + asc_time + ' (> ' + str(time_threshold) + 's)'
	logging.debug(log_str)

        # send email
	mail_addr = 'djerome@gmail.com'
        msg = MIMEMultipart()
        msg['From'] = mail_addr
        msg['To'] = mail_addr
        msg['Subject'] = prefix + ' ' + sev + ' Door Open'
	mail_str = 'Door has been open more than ' + str(time_threshold) + 's.\nSince ' + asc_time
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

# Main

# Constants used on server and client
doors = ["garage", "man"]
OPEN = "0"
CLOSED = "1"
TEST = "99"
OFF = "0"
ON = "1"

# flag for each door to indicate whether door is already open (so a message can be sent when it is closed)
open_already = {}
for door in doors:
	open_already[door] = 0

# Warning level timers and limits initialization
warn_timer = {}	# Warning level timer thread dictionary for each door
warn_limit = {}
warn_limit["man"] = 10		# Warning time limit for man door in s
warn_limit["garage"] = 10	# Warning time limit for garage door in s

# Critical level timers and limits initialization
crit_timer = {}	# Critical level timer thread dictionary for each door
crit_limit = {}
crit_limit["man"] = 20		# Critical time limit for man door in s
crit_limit["garage"] = 20	# Critical time limit for garage door in s

# Configure log file
logging.basicConfig(filename='/var/log/doors/garage.log', level=logging.DEBUG,
	format='%(asctime)s: %(message)s',
	datefmt='%m/%d/%Y %I:%M:%S %p',
	)
logging.debug('RESTART')	# log program restart

# setup socket to listen for door events from client
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 12121))
serversocket.listen(5) # become a server socket, maximum 5 connections

# Main loop
while True:

	connection, address = serversocket.accept()
	buf = connection.recv(64)

	# if there is data from the socket
	if buf:
		(event_time, door, event) = buf.split(',')	# extract data from the event
		prefix = '[' + door.upper() + ']'

		# log the received event with a prefix for the appropriate door
		raw_str = prefix + buf
		logging.debug(raw_str)

		# if a door has been opened, start the timers
		if event == OPEN:

			# check if secure mode is ON
			sec_mode_filename = '/var/log/doors/.sec_mode'
			sec_mode_file = open(sec_mode_filename, 'r')
			sec_mode = sec_mode_file.read().rstrip()
			sec_mode_file.close()
			if sec_mode == ON:

				open_str = prefix + 'Open - Starting timers'
				logging.debug(open_str)
				warn_timer[door] = threading.Timer(warn_limit[door], notify, args=(door,event_time,'warn',))
				warn_timer[door].name = 'warn'
				warn_timer[door].start()
				crit_timer[door] = threading.Timer(crit_limit[door], notify, args=(door,event_time,'crit',))
				crit_timer[door].name = 'crit'
				crit_timer[door].start()
				open_already[door] = 1

		# if a door has been closed, cancel the timer
		elif event == CLOSED:

			# only stop timers if the door is already open
			if open_already[door]:
				close_str = prefix + 'Closed - Stopping timers'
				logging.debug(close_str)
				if warn_timer[door].isAlive():
					warn_timer[door].cancel()
				if crit_timer[door].isAlive():
					crit_timer[door].cancel()

				open_already[door] = 0
