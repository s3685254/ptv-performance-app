# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask, render_template

from google.cloud import datastore

from time import sleep

import requests
from datetime import datetime
from dateutil import tz
from hashlib import sha1
import hmac
import binascii
import threading


datastore_client = datastore.Client()




# PTV API STUFF
def getUrl(request):
	devId = 3001331
	key = 'e5f81663-60ed-477a-be3c-dc3a7c9706c9'
	request = request + ('&' if ('?' in request) else '?')
	raw = request+'devid={0}'.format(devId)
	hashed = hmac.new(key.encode('utf-8'), raw.encode('utf-8'), sha1)
	signature = hashed.hexdigest().upper()
	return 'http://timetableapi.ptv.vic.gov.au'+raw+'&signature={1}'.format(devId, signature)

from_zone = tz.gettz('UTC')
to_zone = tz.gettz('Australia/Melbourne')


def store_stop(id, name):
	entity = datastore.Entity(key=datastore_client.key('stop'))
	entity.update({
		'id': id,
		'name': name
	})
	datastore_client.put(entity)
	
def fetch_stops(limit):
	query = datastore_client.query(kind='stop')
	stops = query.fetch(limit=limit)
	return stops

def getStops():
	for i in range(1001, 1228):
		try:
			r = requests.get(getUrl("/v3/stops/"+str(i)+"/route_type/0"))
			print(r.json())
			store_stop(i, r.json()["stop"]["stop_name"])
			sleep(1)
		except:
			pass

# class PastService(ndb.Model):
	# stopid = ndb.IntegerProperty()
	# routeid = ndb.IntegerProperty()
	# scheduled = ndb.DateTimeProperty()
	# expected = ndb.DateTimeProperty()
	
	# # Get delay in minutes.
	# def getDelay():
		# expectedArrival = datetime.datetime.combine(datetime.date.today(), expected)
		# scheduledArrival = datetime.datetime.combine(datetime.date.today(), scheduled)
		# delay = expectedArrival - scheduledArrival
		# return delay.total_seconds() / 60

def storeService(stopid, routeid, scheduled, expected):
	entity = datastore.Entity(key=datastore_client.key('past_service'))
	entity.update({
		'stopid': stopid,
		'routeid': routeid,
		'scheduled': scheduled,
		'expected': expected
	})
	print(datastore_client.put(entity))
	return entity

#def extractTime(string):
	

def getNextServices(stopid):
	for i in r.json["departures"]:
		routeid = i["route_id"]
		scheduled = i["scheduled_departure_utc"]
		expected = i["estimated_departure_utc"]
		storeService(stopid, routeid, scheduled, expected)

def getDelay(service):
	return int((service["expected"]-service["scheduled"])/60)

def getDelays(stopid):
	data = datastore_client.query(kind="past_service")
	data.add_filter("stopid", "=", stopid)
	return data.fetch()
	
def getAverageDelay(stopid):
	sumd = 0
	num = 0
	delays = getDelays(stopid)
	for i in delays:
		sumd += getDelay(i)
		num += 1
	if num != 0:
		return int(sumd/num)
	return 0

def monitorServices():
	stops = datastore_client.query(kind='stop').fetch()
	
	while True:
		for i in stops:
			try:
				r = requests.get(getUrl("/v3/departures/route_type/0/stop/"+str(i["id"])+"?max_results=1")).json()
				for j in r["departures"]:
					print(j["estimated_departure_utc"])
					
					scheduled = datetime.strptime(j["scheduled_departure_utc"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
					estimated = datetime.strptime(j["estimated_departure_utc"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
					
					s = storeService(i["id"], j["route_id"], int(scheduled), int(estimated))
					
					print(getDelay(s))
			except:
				pass
			sleep(5)

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


@app.route('/')
def hello():
	stops = datastore_client.query(kind='stop').fetch()
	avg_delays = {}
	for i in stops:
		avg_delays[i["name"]] = getAverageDelay(i["id"])
	return render_template("index.html", stops=stops, avg_delays=avg_delays)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
	
	#getStops()
	
	#print(getAverageDelay(1057))
	#monitorServices()
	
	app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
