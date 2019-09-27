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
from api_tools import getDelay, getDelays, getAverageDelay, getUrl, storeService

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
from flask import Flask, render_template

from pytz import timezone

from datetime import datetime, time
from dateutil import tz
import pygal
from google.cloud import datastore
import requests
from time import sleep

datastore_client = datastore.Client()

localtz = timezone("Australia/Melbourne")


app = Flask(__name__)


@app.route('/')
def hello():
	stops = datastore_client.query(kind='stop').fetch()
	return render_template("index.html", stops=stops)

@app.route('/stop/<stopid>')
def viewStop(stopid):
	stopid = int(stopid)
	print(stopid)
	
	data = datastore_client.query(kind="stop")
	data.add_filter("id", "=", stopid)
	data = list(data.fetch(1))
	
	if not data:
		return "Error 404 - Not found."
	
	print(data)
	
	station_name = data[0]["name"]
	
	services = datastore_client.query(kind='past_service')
	services.add_filter("stopid", "=", stopid)
	stopinfo = list(services.fetch())
	
	if not stopinfo:
		return "No services found for " + station_name
	
	hours = {}
		
	for i in stopinfo:
		departure = datetime.fromtimestamp(i["scheduled"])
		departure = departure.replace(tzinfo=tz.tzutc())
		departure = departure.astimezone(localtz)
		departure_time = time(departure.hour)
		print(departure_time)
		try:
			hours[departure_time].append(getDelay(i))
		except KeyError:
			hours[departure_time] = []
			hours[departure_time].append(getDelay(i))
		
	
	for i in hours.keys():
		hours[i] = sum(hours[i])/len(hours[i])
			
	dateline = pygal.TimeLine(x_label_rotation=45, width=1024, height=768, explicit_size=True)
	dateline.add("Delays logged", sorted(hours.items()))
	dateline = dateline.render()
	
	return render_template("stop.html", station_name=station_name, dateline=dateline)

@app.route("/monitor_services")
def monitor_services():
	query = datastore_client.query(kind='stop')
	query.order=['last_updated']
	stops = list(query.fetch(10))
	for i in stops:
		try:
			r = requests.get(getUrl("/v3/departures/route_type/0/stop/"+str(i["id"])+"?max_results=1")).json()
			for j in r["departures"]:			
				scheduled = datetime.strptime(j["scheduled_departure_utc"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
				estimated = datetime.strptime(j["estimated_departure_utc"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
				
				s = storeService(i["id"], j["route_id"], int(scheduled), int(estimated))
		except:
			pass
		
		sleep(5)
	return "monitoring complete!"

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
	
	#getStops()
	
	#print(getAverageDelay(1057))
	#monitorServices()
	
	app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
