from LCD.LCD import LCD
import time
from i2c_scan import scan_i2c_devices
# Now you can use found_devices list in your program

def main():
    found_devices = scan_i2c_devices()
    print("Found I2C devices at addresses:", found_devices)

    if len(found_devices):
        lcd = LCD(2, found_devices[0], True)
        lcd.message("TEST")
        time.sleep(5)
        lcd.clear()
        
    else:
        print("No found devices.")


if __name__ == '__main__':
    main()
