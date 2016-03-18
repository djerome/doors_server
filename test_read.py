#!local/bin/python
log_file = open('/var/log/doors/garage.log', 'r')
lines = log_file.readlines()
log_file.close()
last50 = lines[-50:]
for line in last50:
	print line
print "\n\n############\n\n"
prev50 = lines[-100:-50]
for line in prev50:
	print line
