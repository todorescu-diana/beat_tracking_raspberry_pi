import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import time
import RPi.GPIO as GPIO
from utils.gpio_setup import init_gpio, cleanup_gpio
import constants.pins as pins

interval = 0.25

init_gpio()

try:
    for i in range(20):
        print("????")
        GPIO.output(pins.SOLENOID_CONTROL, GPIO.HIGH)
        time.sleep(interval)
        GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
        time.sleep(interval)

except:
    print("EXCEPT")
    cleanup_gpio()
finally:
    print("FINALLY")
    cleanup_gpio()