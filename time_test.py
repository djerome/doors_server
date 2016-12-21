#!local/bin/python
import datetime
import time

print "time.time() = ", time.time()
print "time.ctime() = ", time.ctime(time.time())
print "time.gmtime() = ", time.gmtime()
print "time.strftime(time.gmtime) = ", time.strftime("%c", time.gmtime())
print "time.strftime(time.localtime) = ", time.strftime("%c", time.localtime())

asc_time = str(time.time())
conv_time = datetime.datetime.fromtimestamp(float(asc_time))
print "conv_time = ", conv_time

nparams = {'duskh': "18", 'duskm': "04", 'dawnh': "17", 'dawnm': "30"}
dusk = "18:04"
dawn = "06:00"
dusk_time = datetime.datetime.strptime(dusk, "%H:%M")

vparams = {'syr': "2015", 'smon': "12", 'sday': "13", 'shr': "18", 'smin': "00", 'eyr': "2016", 'emon': "01", 'eday': "20", 'ehr': "17", 'emin': "30"}

day_today_date = datetime.date.today()

dusk_time = datetime.time(int(nparams['duskh']), int(nparams['duskm']), 0)
dusk_today = datetime.datetime.combine(day_today_date, dusk_time)
print "dusk today"
print dusk_today
dawn_time = datetime.time(int(nparams['dawnh']), int(nparams['dawnm']), 0)
dawn_today = datetime.datetime.combine(day_today_date, dawn_time)
print "dawn today"
print dawn_today

vac_start_date = datetime.date(int(vparams['syr']), int(vparams['smon']), int(vparams['sday']))
vac_start_time = datetime.time(int(vparams['shr']), int(vparams['smin']), 0)
vac_start = datetime.datetime.combine(vac_start_date, vac_start_time)
print "vac_start"
print vac_start
vac_end_date = datetime.date(int(vparams['eyr']), int(vparams['emon']), int(vparams['eday']))
vac_end_time = datetime.time(int(vparams['ehr']), int(vparams['emin']), 0)
vac_end = datetime.datetime.combine(vac_end_date, vac_end_time)
print "vac_end"
print vac_end

time_now = datetime.datetime.now()
asc_time_now = time_now.strftime("%c")
print "time_now"
print time_now
print "As a string: " + asc_time_now

#time_now = datetime.datetime.now().time()
#date_now = datetime.datetime.now().date()

one_day = datetime.timedelta(days=1)
one_day_secs = datetime.timedelta(days=1).total_seconds()
print "one day in seconds: " + str(one_day_secs)

if dusk_today < dawn_today:
	print "dusk and dawn on same day"
else:
	print "dusk is on previous day"
	dawn_today = dawn_today + one_day
	print "New dawn"
	print dawn_today

if (time_now > dusk_today) and (time_now < dawn_today):
	print "Night Alarm"
else:
	print"NO Night Alarm"

if (time_now > vac_start) and (time_now < vac_end):
	print "Vacation Alarm"
else:
	print"NO Vacation Alarm"

# Test setup of night and vacation timers
# Convert start and end times into a timestamp in seconds
start_time = "20/11/16 21:36"
end_time = "20/11/16 23:36"
start_time_s = time.mktime(time.strptime(start_time, "%d/%m/%y %H:%M"))
end_time_s = time.mktime(time.strptime(end_time, "%d/%m/%y %H:%M"))
print "start_time_s = " + str(start_time_s)
print "end_time_s = " + str(end_time_s)

# Compute delay until start_time
# get time now in seconds
now_time_s = time.time()
print "now_time_s = " + str(now_time_s)

# calculate delta in seconds between now and start_time
start_delta = start_time_s - now_time_s
end_delta = end_time_s - now_time_s
print "start_delta = " + str(start_delta)
print "end_delta = " + str(end_delta)

fire_time_v = "25/11/16 21:36"
time_format_v = "%d/%m/%y %H:%M"
fire_time_v = time.mktime(time.strptime(fire_time_v, time_format_v))
print "fire_time_v = " + str(fire_time_v)
fire_time_n = "21:36"
time_format_n = "%H:%M"
day_today_date = datetime.date.today()
fire_time_n = datetime.datetime.time(datetime.datetime.strptime(fire_time_n, time_format_n))
fire_time_n = datetime.datetime.combine(day_today_date, fire_time_n)
fire_time_n = time.mktime(fire_time_n.timetuple())
print "fire_time_n = " + str(fire_time_n)
