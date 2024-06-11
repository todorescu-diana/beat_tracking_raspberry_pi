import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time

GPIO.setmode(GPIO.BCM) # Use physical pin numbering
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

try:
    while True:
        button_state_26 = GPIO.input(26)
        button_state_19 = GPIO.input(19)
        button_state_13 = GPIO.input(13)
        
        if button_state_26 == GPIO.HIGH:
            print("26")
        
        if button_state_19 == GPIO.HIGH:
            print("19")
            
        if button_state_13 == GPIO.HIGH:
            print("13")
        time.sleep(0.1)
        
except KeyboardInterrupt:
    GPIO.cleanup() # Clean up