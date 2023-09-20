import time
import json
import requests
from lib.MySensors import SensorManager
from lib.MyMQTT import PubSub
import datetime


class SenseSend:
	def __init__(self, WSC_URL, USER_PATH, deviceID, resource, unit='', 
				 QoS=2, dt=1, pin=None,name=None,
                 source=None, threshold=None):
		
		# Initalization
		self.WSC_URL=WSC_URL
		self.USER_PATH=USER_PATH
		self.deviceID=deviceID
		self.resource=resource
		self.unit=unit
		self.QoS=QoS
		self.dt=dt
		self.user=None
		self.typeOfDevice="Raspberry"
		
		# Sensor manager object
		self.sensor=SensorManager()
		
		# Parameters
		self.sensor_config={}
		if pin is not None:
			self.sensor_config["pin"]=pin
		if name is not None:
			self.sensor_config["name"]=name
		if source is not None:
			self.sensor_config["source"]=source
		if threshold is not None:
			self.threshold=threshold
		self.jj={}
		

			
	def start(self):
		""" Start PubSub"""
		
		self.get_credentials()
		
		r=self.login()
		if r.status_code==200:
			
			# Get info about message broker
			self.get_msgBroker()
			
			self.clientID=self.user+"_"+self.deviceID
			self.test = PubSub(self.clientID)
			
			self.test.start(self.IPmsgBroker,self.PORTmsgBroker)
			
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+self.clientID+' Publisher/Subscriber started')
			
			# Define a topic for publishing
			self.pub_Topic=self.typeOfDevice+'/'+self.user+'/'+self.resource+'/'+self.deviceID
			# Generating endpoints
			self.endpoints=self.IPmsgBroker+':'+str(self.PORTmsgBroker)+'/'+self.pub_Topic
			
			# Get the proper function for the selected sensor
			self.function=getattr(self.sensor,self.resource.capitalize())
			
			
			
			if self.resource not in self.jj.keys():
				self.jj[self.resource]=0
			
			try:
				while 1:
					# Get value from sensor, convert data to SenML and 
					# publish to topic
					self.get_value()
					# Add a new device in user devices
					self.put_device()
					# Wait
					self.jj[self.resource]+=1
					time.sleep(self.dt)
			except KeyboardInterrupt:
				self.stop()
				
	def stop(self):
		""" Stop PubSub"""
		self.test.stop()
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+self.ClientID+' Publisher/Subscriber stopped')
		
	def get_credentials(self):
		""" Get credentials of the coupled user from a specific file """
		while self.user is None:
			try:
				# Read authentication parameters
				f=open(self.USER_PATH,'r')
				self.credentials=json.loads(f.read())
				self.user=self.credentials['user']
				f.close()
			except:
				time.sleep(10)
				
	def login(self):
		""" Login to Web Service Catalog"""
		# Start a new session
		self.s=requests.Session()
		# Login to Web Service Catalog
		r=self.s.post(self.WSC_URL+'/login',data=json.dumps(self.credentials))
		return r
		
	def get_msgBroker(self):
		""" Get message broker info"""
		r=self.s.get(self.WSC_URL+'/msgbroker')
		msgBroker=json.loads(r.text)['msgbroker']
		self.IPmsgBroker=msgBroker['IP']
		self.PORTmsgBroker=msgBroker['PORT']
		return r
		
	def get_value(self):
		""" Get a value from the sensor and send it"""
		OK=True
		if OK:
			self.value=self.function(**self.sensor_config)
			
			if self.value is not None:
				self.send_message()
	
	
	def send_message(self):
		""" Convert data to SenML format and publish message to topic"""
		message = {"bn":self.endpoints,"e":[{ "n": self.resource, "u":self.unit, "t": time.time(), "v":self.value }]}
		if self.resource=='temperature'or self.resource=='vaccine' :
			message["e"][0]["tr"]=self.threshold
		message=json.dumps(message)
		self.test.myPublish (self.pub_Topic, message,self.QoS)
		print("")
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+'PUBLISHING: '+self.resource+' ' +str(self.value)+' '+ self.unit)
		print ('on '+self.pub_Topic)
		print ('current message: ') 
		print (message)
		print("")


	def put_device(self):
		""" Update devices list with sensor"""
		print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Putting "+self.user+"'s "+self.deviceID+ " information on WebService Catalog")
		self.s.put(self.WSC_URL+'/newdevice',data=json.dumps({'deviceID':self.deviceID,'resources':self.resource,'endpoints':self.endpoints,"protocol":"MQTT"}))
