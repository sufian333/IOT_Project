import time
from lib.utilities import WebServiceClient,MicroServicePubSub
import json

f=open("data/TemperatureService_config.json")
config=json.loads(f.read())
QoS=config["QoS"]
name=config["name"]
resource=config["resource"]
endpoints=config["endpoints"]
TOKEN=config["TOKEN"] # @RefrigeratorAllarm_bot

WSC_URL=config["WSCatalog"]["url"]
ADMIN=config["WSCatalog"]["credentials"]["user"]
PASSWORD=config["WSCatalog"]["credentials"]["password"]

	

OK=False
while not OK:
	wsc=WebServiceClient(WSC_URL,ADMIN,PASSWORD)
	ans=wsc.start()
	if ans==200:
		OK=True
	else:
		time.sleep(10)

IP_msgbroker, PORT_msgbroker=wsc.get_msgbroker()

OK=False
while not OK:
	try:
		topics=wsc.get_topics(resource)
		sub_topics=[('/'.join(topic.split('/')[1:]),QoS) for topic in topics]
		OK=True
	except:
		pass
	
test=MicroServicePubSub(name,TOKEN,WSC_URL,ADMIN,PASSWORD)
test.QoS=QoS
test.start(IP_msgbroker, PORT_msgbroker, sub_topic=sub_topics)

endpoints=IP_msgbroker+':'+str(PORT_msgbroker)+endpoints
data={'microserviceID':name,'category':resource,'endpoints':endpoints,'protocol':'mqtt'}


while 1:
	time.sleep(5)
	wsc.put_microservice(data)
	try:	
		new_topics=wsc.get_topics(resource)
		new_sub_topics=[('/'.join(topic.split('/')[1:]),QoS) for topic in new_topics]
		test.myUpdate(new_sub_topics,sub_topics)
		sub_topics=new_sub_topics
	except:
		pass
