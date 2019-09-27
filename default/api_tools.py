
from pytz import timezone

from itertools import groupby
from operator import attrgetter

from google.cloud import datastore

from time import sleep
import time

import requests
from datetime import datetime
from dateutil import tz
from hashlib import sha1
import hmac
import binascii


datastore_client = datastore.Client()

localtz = timezone("Australia/Melbourne")


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
	key = datastore_client.key('stop', str(id))
	entity = datastore.Entity(key)
	entity.update({
		'id': id,
		'name': name,
		'num_records': 0,
		'average_delay': 0,
		'last_updated': int(time.time())
	})
	print(datastore_client.put(entity))
	
def fetch_stops(limit):
	query = datastore_client.query(kind='stop')
	stops = query.fetch(limit=limit)
	return stops

def getStops():
	for i in range(1001, 1228):
		try:
			r = requests.get(getUrl("/v3/stops/"+str(i)+"/route_type/0"))
			#print(r.json())
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

def updateStopInfo(stopid, service):
	with datastore_client.transaction():
		key = datastore_client.key('stop', str(stopid))
		stop = datastore_client.get(key)
		
		
		stop['average_delay'] = (stop['average_delay']*stop['num_records'] + getDelay(service))/(stop['num_records']+1)
		stop['num_records'] = stop['num_records'] + 1
		stop['last_updated'] = int(time.time())
		print(stop)
		datastore_client.put(stop)


def storeService(stopid, routeid, scheduled, expected):
	entity = datastore.Entity(key=datastore_client.key('past_service'))
	entity.update({
		'stopid': stopid,
		'routeid': routeid,
		'scheduled': scheduled,
		'expected': expected
	})
	
	print(datastore_client.put(entity))
	
	# Update average delay information for the stop.
	updateStopInfo(stopid, entity)
	
	return entity

#def extractTime(string):
	

def getNextServices(stopid):
	for i in r.json["departures"]:
		routeid = i["route_id"]
		scheduled = i["scheduled_departure_utc"]
		expected = i["estimated_departure_utc"]
		storeService(stopid, routeid, scheduled, expected)

def getDelay(service):
	delay = int((service["expected"]-service["scheduled"])/60)
	return delay

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
	stops = list(datastore_client.query(kind='stop').fetch())
	
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

