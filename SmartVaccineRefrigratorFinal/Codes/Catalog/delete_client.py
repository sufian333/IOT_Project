import requests
import time
import json

f=open("data/WSCatalog_config.json")
conf=json.loads(f.read())
f.close()

# init root
ADMIN=conf["administrator"]["user"]
PSW=conf["administrator"]["password"]

age=conf["refresh"]["age"]
dt=conf["refresh"]["dt"]

s=requests.Session()

OK=False
while not OK:
	try:
		r=s.post("http://192.168.137.40:8080/login",data=json.dumps({"user":ADMIN,"password":PSW}))
		OK=True
	except:
		time.sleep(10)
while 1:
	try:
		r=s.delete("http://192.168.137.40:8080/clean",params={"age":age})
	except:
		try:
			r=s.post("http://192.168.137.40:8080/login",data=json.dumps({"user":ADMIN,"password":PSW}))
		except:
			pass
	time.sleep(dt)
