#!local/bin/python
import httplib2
import json
import time
import datetime

if __name__ == '__main__':

    httplib2.debuglevel     = 0
    http                    = httplib2.Http()
    content_type_header     = "application/json"

    url = "http://localhost:5000/test"

    data = {    'room':         "Living Room",
                'temp':         23.45,
                'humidity':     50.00,
                'timestamp':    str(datetime.datetime.now())
           }

    headers = {'Content-Type': content_type_header}
    print ("Posting %s" % data)

    while True:
        response, content = http.request( url,
                                          'POST',
                                          json.dumps(data),
                                          headers=headers)
	print "Response:"
        print (response)
	print "Content:"
        print (content)
        time.sleep(3)
