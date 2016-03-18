#!local/bin/python
from flask import Flask, request, json

app = Flask(__name__)

@app.route("/test", methods=['POST'])
def api_temperature():
    if request.headers['Content-Type'] == 'text/plain':
	print "Text"
        print (request.data)
        return 'OK', 200
    elif request.headers['Content-Type'] == 'application/json':
	print "JSON"
	shlop = request.json
	print shlop['room']
	print shlop['timestamp']
	print shlop['temp']
	print shlop['humidity']
#        shlop = json.dumps(request.json)
#	print shlop.keys()
#        print (json.dumps(request.json))
        return "OK", 200
    else:
        return "Unsupported Media Type", 415

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = True)
