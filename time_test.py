#!local/bin/python
import datetime

nparams = {'duskh': "18", 'duskm': "04", 'dawnh': "17", 'dawnm': "30"}
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
