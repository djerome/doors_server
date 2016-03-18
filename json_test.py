#!local/bin/python

from config_door import *
import httplib2
from flask import Flask, request, json, jsonify

sec_conf_file = "/var/log/doors/.sec_mode"

with open(sec_conf_file, 'r') as json_data:
	data = json.load(json_data)
	json_data.close()

print data['mode'], data['params']

sec_data = {}
sec_data['mode'] = TIMER
sec_data['params'] = {WARNING: 60, CRITICAL: 300}

#with open(sec_conf_file, 'w') as outfile:
with open("/var/log/doors/.sec_data", 'w') as outfile:
	json.dump(sec_data, outfile)
	outfile.close()
