import json
import time
from lib.TSAutils import GetDataFromWSCatalog,ThingSpeakAdaptor,ms2topic

f=open('data/ThingSpeakAdaptor_config.json')
config=json.loads(f.read())
f.close()

Name=config["name"]
QoS=config["QoS"]
categories=config["categories"]
dictionary=config["vocabulary"]
topics_update_interval=config["topics_update_interval"]

WSC_URL=config["WebServiceCatalog"]["endpoints"]
ADMIN=config["WebServiceCatalog"]["credentials"]["user"]
PASSWORD=config["WebServiceCatalog"]["credentials"]["password"]

url_thingspeak=config["ThingSpeak"]["url"]

client=GetDataFromWSCatalog(WSC_URL,ADMIN,PASSWORD)
client.start()

msgbrIP,msgbrPORT=client.get_msgbroker()

OK=False
while not OK:
	try:
		microservices=client.get_microservices()
		sub_topics=ms2topic(microservices,categories)
		sub_topics=(sub_topics,QoS)
		OK=True
	except:
		pass

tsa=ThingSpeakAdaptor(Name,url_thingspeak,dictionary)
tsa.start(msgbrIP,msgbrPORT,sub_topics)

while 1:
	tsa.contacts=client.get_contacts()
	time.sleep(topics_update_interval)
	try:
		new_topics=ms2topic(client.get_microservices(),categories)
		new_sub_topics=(new_topics,QoS)
		tsa.myUpdate(new_sub_topics,sub_topics)
		sub_topics=new_sub_topics
	except:
		pass
