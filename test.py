import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

Motor1 = 22 # Enable Pin
Motor2 = 27 # Input Pin
Motor3 = 19 # Input Pin
print("Hello")

GPIO.setup(Motor1,GPIO.OUT)
GPIO.setup(Motor2,GPIO.OUT)
GPIO.setup(Motor3,GPIO.OUT)

GPIO.output(Motor1,GPIO.LOW)

GPIO.output(Motor1,GPIO.HIGH)
GPIO.output(Motor2,GPIO.LOW)
GPIO.output(Motor3,GPIO.HIGH)
sleep(1)

GPIO.output(Motor1,GPIO.HIGH)
GPIO.output(Motor2,GPIO.HIGH)
GPIO.output(Motor3,GPIO.LOW)

sleep(5)
GPIO.output(Motor1,GPIO.LOW)
print("done")

GPIO.cleanup() 