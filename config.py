#
# File config.py
#
#	Initializes application
#

import datetime

WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

# create log file for each execution of application
now = datetime.datetime.now()
timeString = now.strftime("%Y-%m-%d_%H:%M")
log_filename = "log/" + timeString + ".log"
log_file = open(log_filename, 'w')
header = "Output logging started: " + timeString + "\n\n"
log_file.write(header)

