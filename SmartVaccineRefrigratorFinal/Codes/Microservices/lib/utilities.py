import paho.mqtt.client as MQTT
import requests
import telepot
import time
import json
import os
import datetime


class DoSomething(object):
	
	def __init__(self):
		#self.clientID=None
		#self.msg=None
		self.fifo=None
		self.timer=None
			 
	def temperature(self,clientID,msg,flags):
		# Obtain user and payload
		user,payload=self.user_payload(msg)
		
		
		flags,self.timer,msg=self.common(clientID,flags,msg)
		
		if user not in list(self.fifo.keys()):
			self.fifo[user]=FIFO(8)
		
		if payload['e'][0]['v']>payload['e'][0]['tr']:
			self.fifo[user].insert(1)
		else:
			self.fifo[user].insert(0)
			
		
		if self.fifo[user].check():
			flags['allarm']=True
		
		return msg,flags
		
	def humidity(self,clientID,msg,flags):
		flags,self.timer,msg=self.common(clientID,flags,msg)
		return msg,flags
		
	def user_payload(self,msg):
		user=msg.topic.split('/')[1].encode() 
		payload=json.loads(msg.payload)
		return user,payload
		
	def common(self,clientID,flags,msg):
		user,payload=self.user_payload(msg)
		resource=payload['e'][0]['n']
		if user not in list(self.timer.keys()):
			self.timer[user]={}
			if resource not in list(self.timer[user].keys()):
				self.timer[user][resource]=time.time()
		if time.time()-self.timer[user][resource]>15:
			self.timer[user][resource]=time.time()
			topic_l=msg.topic.split('/')
			topic_l[0]='MicroServices/'+resource+'/'+clientID
			msg.topic='/'.join(topic_l)
			payload['e'][0]['user']=user
			payload['bn']=msg.topic
			msg.payload=json.dumps(payload)
			flags["timer"]=True
		else:
			flags["timer"]=False
		return flags,self.timer,msg
		
class MicroServicePubSub:
	def __init__(self,clientID,TOKEN=None,WSC_URL=None,ADMIN=None,PASSWORD=None):
		
		self.clientID=clientID
		#self.resource=resource
		if TOKEN is not None:
			self.bot = telepot.Bot(token=TOKEN)
		if None not in [WSC_URL,ADMIN,PASSWORD]:
			self.clientSession=WebServiceClient(WSC_URL,ADMIN,PASSWORD)
			self.clientSession.start()
		else:
			self.clientSession=None
		self.doSomething=DoSomething()
		self._paho_mqtt=MQTT.Client(self.clientID,clean_session=True)
		
		self._paho_mqtt.on_connect=self.myOnConnect
		self._paho_mqtt.on_message=self.myOnMessageReceived
		
		# initalize Data 

		self.doSomething.timer={}
		self.doSomething.fifo={}
		self.QoS=2
		
	def start(self, url, port, sub_topic=None):
		# connection to broker
		self._paho_mqtt.connect(url,port)
		self._paho_mqtt.loop_start()
		
		# if it's also subscriber, subscribe to a topic
		if sub_topic is not None:
			self.mySubscribe(sub_topic)
	
	def stop(self, sub_topic=None):

		# if it's also subscriber, subscribe to a topic		
		if sub_topic is not None:
			self.myUnsubscribe(sub_topics)
		
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()
	
	def myPublish(self,topic,message,QoS):
		
		# publish a message on a certain topic
		self._paho_mqtt.publish(topic, message, QoS,retain=False)

	def mySubscribe(self,sub_topics):
		self._paho_mqtt.subscribe(sub_topics)
	
	def myUnsubscribe(self,sub_topics):
		self._paho_mqtt.unsubscribe(sub_topics)
		
	def myUpdate(self,new_sub_topics,old_sub_topics):
		topics_to_add=[]
		topics_to_remove=[]
		for topic in new_sub_topics:
			if topic not in old_sub_topics:
				for o in old_sub_topics:
					if o[0] == topic[0] or (o not in new_sub_topics):
						topics_to_remove.append(o[0])
				topics_to_add.append(topic)
		topics_to_remove=self.unique(topics_to_remove)
		
		if topics_to_remove!=[]:
			self.myUnsubscribe(topics_to_remove)
		if topics_to_add!=[]:
			self.mySubscribe(topics_to_add)
		
	def unique(self,duplicate):
		final_list = []
		for num in duplicate:
			if num not in final_list:
				final_list.append(num)
		return final_list
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"connected to message broker with rc" + str(rc))
	
	def myOnMessageReceived(self, paho_mqtt, userdata, msg):
		print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Received from Topic: " + msg.topic + " QoS: "+ str(msg.qos))
		
		# initialize timer and allarm flags
		flags={"timer":False,"allarm":False}
		
		# get the type of resource
		resource=json.loads(msg.payload)['e'][0]['n']
		
		user=msg.topic.split('/')[1]
		action=getattr(self.doSomething,resource)
		msg,flags=action(self.clientID,msg,flags)

		if flags['timer']:
			self.myPublish(msg.topic,msg.payload,self.QoS)
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Publishing subsampled data to Topic: " + msg.topic + " QoS: "+ str(self.QoS))
			
		if flags['allarm']:	
			contacts=self.clientSession.get_contacts()
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+user+": sending allarm to user by RefrigeratorAllarm_bot")
			try:
				chat_id=contacts[user]['telegramID']
				tmsg='WARNING: '+resource+' is over threshold!!!'
				self.bot.sendMessage(chat_id=chat_id, text=tmsg)
			except:
				print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Missing telegram contact for "+user)
			
			
class WebServiceClient(object):
	def __init__(self,urlWebService,user,password):
		self.url=urlWebService
		self.user=user
		self.password=password
		self.loggedin=False
	
	def start(self):
		r=self.login()
		if r.status_code==200:
			self.loggedin=True
		else:
			print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"- "+"Authentication Error")
		return r.status_code
	
	def login(self):
		self.s=requests.Session()
		r=self.s.post(self.url+'/login',data=json.dumps({'user':self.user,'password':self.password}))
		return r
			
	def get_msgbroker(self):
		IP_msgbroker=None
		PORT_msgbroker=None
		if self.loggedin:
			r=self.s.get(self.url+'/msgbroker')
			msgbroker=json.loads(r.text)['msgbroker']
			IP_msgbroker=msgbroker["IP"]
			PORT_msgbroker=msgbroker["PORT"]
		return IP_msgbroker,PORT_msgbroker
	
	def get_topics(self,resource):
		if self.loggedin:
			r=self.s.get(self.url+'/devices',params={'resources':resource})
			topics=[]
			devices=json.loads(r.text)['devices']
			users=list(devices.keys())
			for user in users:
				for dev in devices[user]:
					if dev["resources"]==resource:
						topics.append(dev['endpoints'])
			return topics
		else:
			return None
		
	def get_contacts(self):
		contacts=None
		if self.loggedin:
			r=self.s.get(self.url+'/contacts')
			contacts=json.loads(r.text)['contacts']
		return contacts
	
	def put_microservice(self,data):
		if self.loggedin:
			r=self.s.put(self.url+'/newmicroservice',data=json.dumps(data))
			return r.status_code
		else:
			return 401
		
	
class FIFO:
	def __init__(self,nbit=8):
		self.array=[0]*nbit
		self.nbit=nbit
		
	def insert(self,bit):
		self.array.pop(0)
		self.array.append(bit)
		
	def check(self):
		return sum(self.array)==self.nbit
		
	def reset(self):
		self.array=[0]*self.nbit
