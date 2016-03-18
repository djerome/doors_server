#!local/bin/python

limit = {}
GARAGE = "Garage"
MAN = "Man"
doors = [GARAGE, MAN]
WARNING = "Warning"
CRITICAL = "Critical"
alarms = [WARNING, CRITICAL]

limit[MAN] = {WARNING: 10, CRITICAL: 20}
limit[GARAGE] = {WARNING: 10, CRITICAL: 20}

for door in doors:
	for alarm in alarms:
		print "Limit for " + door + " - " + alarm + ": " + str(limit[door][alarm])
