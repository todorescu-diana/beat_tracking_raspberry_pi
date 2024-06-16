import RPi.GPIO as GPIO
import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import constants.pins as pins

def init_gpio():
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(pins.BUTTON_SELECT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pins.BUTTON_PREV, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pins.BUTTON_NEXT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pins.BUTTON_STOP_SCRIPT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pins.BUTTON_STOP_AUDIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    GPIO.setup(pins.SOLENOID_CONTROL, GPIO.OUT, initial=GPIO.LOW)

def cleanup_gpio():
    print("CLEANUP")
    GPIO.cleanup()
