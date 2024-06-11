from LCD.LCD import LCD
from utils.i2c_scan import scan_i2c_devices
import time

lcd = None

def init_lcd():
    global lcd
    
    found_devices = scan_i2c_devices()
    print("Found I2C devices at addresses:", found_devices)

    if len(found_devices):
        lcd = LCD(2, found_devices[0], True)
        time.sleep(0.5)
        lcd.clear()
        
    else:
        print("No found devices.")
    
def get_lcd():
    return lcd

def clear_lcd_content():
    lcd = get_lcd()
    lcd.clear()
    
def display_lcd_content(content):
    lcd = get_lcd()
    lcd.clear()
    lcd.message(content)
    time.sleep(0.5)