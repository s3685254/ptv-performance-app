# [START gae_python37_app]
from api_tools import getDelay, getDelays, getAverageDelay, getUrl, storeService

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
from flask import Flask, render_template

from pytz import timezone

from datetime import datetime, time
from dateutil import tz
import pygal
from pygal.style import Style
from google.cloud import datastore
import requests
from time import sleep

datastore_client = datastore.Client()

localtz = timezone("Australia/Melbourne")


app = Flask(__name__)


@app.route('/')
def hello():
	# Fetch data from GCE Datastore
	db_route_name = datastore_client.query(kind='route_name').fetch()
	db_routes = datastore_client.query(kind='route').fetch()
	db_stops = datastore_client.query(kind='stop').fetch()
	
	route_name = {}
	for route in  db_route_name:
		route_name[route["id"]] = [route["name"], route["colour"]]

	routes = {}
	count = 0
	for item in db_routes:
		routes[count] = [item["routeid"], [item["stopid"],"",0]]
		count += 1
	count = 0

	for stop in db_stops:
		for key, value in routes.items():
			if value[1][0] == stop["id"]:
				value[1][1] = stop["name"]
				value[1][2] = stop["average_delay"]

	return render_template("index.html", routes=routes, route_name=route_name)

def configureLineGraph(routes):
	# Configure chart styling (line colours)
	chart_colours = []
	for i in routes.keys():
		chart_colours.append(routes[i]["colour"])	
	custom_style = Style(
		colors=tuple(chart_colours)
	)
		
	# Create graph + configure labels.
	chart = pygal.TimeLine(x_label_rotation=45, width=1024, height=768, explicit_size=True,
	 style=custom_style, title="Average Delay at this Station by Hour (by line)",
	  x_title='Time of Day', y_title="Average service delay in minutes.",
	  x_value_formatter=lambda dt: dt.strftime('%I:%M %p'))
	  
	 # x-axis labels config
	hours=[]
	for i in range(0,23):
		hour = datetime.today().replace(hour=i, minute=0, second=0)
		hours.append(hour)
	chart.x_labels = hours
	
	return chart

@app.route('/stop/<stopid>')
def viewStop(stopid):
	stopid = int(stopid)
	
	data = datastore_client.query(kind="stop")
	data.add_filter("id", "=", stopid)
	data = list(data.fetch(1))
	
	if not data:
		return "Error 404 - Not found."

	station_name = data[0]["name"]
	
	services = datastore_client.query(kind='past_service')
	services.add_filter("stopid", "=", stopid)
	stopinfo = list(services.fetch())
	
	if not stopinfo:
		return "No services found for " + station_name
	
	#get routes through station
	routes = {}
	
	for i in stopinfo:
		try:
			if i["routeid"] not in routes:
				route_name = datastore_client.query(kind="route_name")
				route_name.add_filter("id", "=", i["routeid"])
				route_name = list(route_name.fetch(1))
				route_name = route_name[0]
				current_route = {}
				current_route["name"] = route_name["name"]				
				current_route["colour"] = route_name["colour"]
				current_route["delays"] = []
				current_route["hour_delays"] = {}
				current_route["hour_avg_delays"] = {}
				routes[i["routeid"]] = current_route
		except IndexError:
			pass

		

	# Get service info for calculating average delays.
	for i in stopinfo:
		try:
			departure = datetime.fromtimestamp(i["scheduled"])
			departure = departure.replace(tzinfo=tz.tzutc())
			departure = departure.astimezone(localtz)
			departure_time = time(departure.hour)
			try:			
				routes[i["routeid"]]["delays"].append(getDelay(i))
				routes[i["routeid"]]["hour_delays"][departure_time].append(getDelay(i))
				
			except KeyError:
				routes[i["routeid"]]["hour_delays"][departure_time] = []
				routes[i["routeid"]]["hour_delays"][departure_time].append(getDelay(i))
		except Exception:
			pass
	

	for i in routes.keys():
		for j in routes[i]["hour_delays"].keys():
			routes[i]["hour_avg_delays"][j] = sum(routes[i]["hour_delays"][j])/len(routes[i]["hour_delays"][j])
	
	# Create graph.
	dateline = configureLineGraph(routes)
	
	# Add data series
	for i in routes.keys():
		dateline.add(routes[i]["name"], sorted(routes[i]["hour_avg_delays"].items()))
	dateline = dateline.render(disable_xml_declaration=True)
	
	# Calculate average delays for table format.
	for i in routes.keys():
		try:
			routes[i]["avg_delay"] = sum(routes[i]["delays"])/len(routes[i]["delays"])
			routes[i].pop('delays', None)
		except ZeroDivisionError:
			routes[i]["avg_delay"]=0
		try:
			routes[i]["current_hour_avg_delay"] = routes[i]["hour_avg_delays"][time(datetime.now().hour)]
			routes[i].pop('hour_delays', None)
		except (ZeroDivisionError, KeyError):
			routes[i]["current_hour_avg_delay"]=0
	
	# Calculate average delay for current period (hour).
	routes = routes.values()
	current_hour_avg_delay=0
	for i in routes:
		current_hour_avg_delay+=i["current_hour_avg_delay"]
	current_hour_avg_delay/=len(routes)
	
	# Render the page as html.
	return render_template("stop.html", station_name=station_name, dateline=dateline, routes=routes, current_hour_avg_delay=int(current_hour_avg_delay))

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
	
	#getStops()
	
	#print(getAverageDelay(1057))
	#monitorServices()
	
	app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
