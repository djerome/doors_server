#!local/bin/python

# get last 50 lines in log file
garage_log_file = open(log_file, 'r')
lines = garage_log_file.readlines()
garage_log_file.close()
last50 = lines[-50:]
