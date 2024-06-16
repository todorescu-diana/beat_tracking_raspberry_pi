import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import RPi.GPIO as GPIO
import time
from constants import pins

GPIO.setmode(GPIO.BCM) # use physical pin numbering
GPIO.setup(pins.BUTTON_PREV, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pins.BUTTON_NEXT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pins.BUTTON_SELECT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pins.BUTTON_STOP_SCRIPT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pins.BUTTON_STOP_AUDIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        BUTTON_PREV = GPIO.input(pins.BUTTON_PREV)
        BUTTON_NEXT = GPIO.input(pins.BUTTON_NEXT)
        BUTTON_SELECT = GPIO.input(pins.BUTTON_SELECT)
        BUTTON_STOP_SCRIPT = GPIO.input(pins.BUTTON_STOP_SCRIPT)
        BUTTON_STOP_AUDIO = GPIO.input(pins.BUTTON_STOP_AUDIO)
        
        if BUTTON_PREV == GPIO.HIGH:
            print("BUTTON_PREV")
        if BUTTON_NEXT == GPIO.HIGH:
            print("BUTTON_NEXT")
        if BUTTON_SELECT == GPIO.HIGH:
            print("BUTTON_SELECT")
        if BUTTON_STOP_SCRIPT == GPIO.HIGH:
            print("BUTTON_STOP_SCRIPT")
        if BUTTON_STOP_AUDIO == GPIO.HIGH:
            print("BUTTON_STOP_AUDIO")
        time.sleep(0.1)
        
except KeyboardInterrupt:
    GPIO.cleanup() # clean up