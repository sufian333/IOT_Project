import time
from lib.utilities import WebServiceClient,MicroServicePubSub
import json

f=open("data/HumidityService_config.json")
config=json.loads(f.read())
QoS=config["QoS"]
name=config["name"]
resource=config["resource"]
endpoints=config["endpoints"]
print(endpoints)

WSC_URL=config["WSCatalog"]["url"]
ADMIN=config["WSCatalog"]["credentials"]["user"]
PASSWORD=config["WSCatalog"]["credentials"]["password"]

print(ADMIN)	
print(PASSWORD)

OK=False
while not OK:
	wsc=WebServiceClient(WSC_URL,ADMIN,PASSWORD)
	ans=wsc.start()
	if ans==200:
		OK=True
	else:
		time.sleep(10)

IP_msgbroker, PORT_msgbroker=wsc.get_msgbroker()
print(IP_msgbroker)
print(PORT_msgbroker)
OK=False
while not OK:
	try:
		topics=wsc.get_topics(resource)
		print("topics=",topics)
		print("something=")
		sub_topics=[]
		sub_topics=[('/'.join(topic.encode().split('/')[1:]),QoS) for topic in topics]
		print("sub_topics=",sub_topics)
		print("Nothing=")
		OK=True
	except:
		pass
	
test=MicroServicePubSub(name)
print(test)
test.QoS=QoS
test.start(IP_msgbroker, PORT_msgbroker, sub_topic=sub_topics)

endpoints=IP_msgbroker+':'+str(PORT_msgbroker)+endpoints
print(endpoints)
data={'microserviceID':name,'category':resource,'endpoints':endpoints,'protocol':'mqtt'}
print(data)

while 1:
	time.sleep(5)
	wsc.put_microservice(data)
	try:
		new_topics=wsc.get_topics(resource)
		print(new_topics)
		new_sub_topics=[('/'.join(topic.encode().split('/')[1:]),QoS) for topic in new_topics]
		test.myUpdate(new_sub_topics,sub_topics)
		sub_topics=new_sub_topics
	except:
		pass
