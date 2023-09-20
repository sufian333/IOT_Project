import Adafruit_DHT
import RPi.GPIO as GPIO
import numpy as np
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 27

class SensorManager(object):
	""" This object lets to manage different sensors"""
	def __init__(self):
		pass
		
	def Temperature(self,pin=DHT_PIN ,name=DHT_SENSOR):
		""" Temperature sensor """
		_, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
		return temperature
	
	def Humidity(self,pin=DHT_PIN,name=DHT_SENSOR):
		""" Humidity sensor """
		humidity, _ = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
		return humidity
	def Vaccine(self):
		""" Vaccine Counter """
		print("Vaccine")
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(pin,GPIO.IN)
		GPIO.setup(38,GPIO.IN)
		GPIO.setup(36,GPIO.IN)
		GPIO.setup(37,GPIO.IN)
		GPIO.setup(35,GPIO.IN)
		GPIO.setup(33,GPIO.IN)
		Button1 = GPIO.input(40)
		Button2 = GPIO.input(38)
		Button3 = GPIO.input(36)
		Button4 = GPIO.input(37)
		Button5 = GPIO.input(35)
		Button6 = GPIO.input(33)
		b=[Button1,Button2,Button3,Button4,Button5,Button6]
		
		b1=b.astype(int)
		vaccine = np.sum(b1)
		print(vaccine)
		return vaccine