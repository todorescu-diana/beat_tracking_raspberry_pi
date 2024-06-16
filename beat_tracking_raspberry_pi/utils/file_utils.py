import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import os
import pyudev
import subprocess
import time
import RPi.GPIO as GPIO 
from utils.gpio_setup import init_gpio, cleanup_gpio
from utils.lcd_utils import init_lcd, get_lcd, display_lcd_content
import constants.pins as pins
import os
from pydub.utils import mediainfo

def is_wav_or_mp3(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower() in ['.wav', '.mp3']

def is_audio_file(filepath):
    if not os.path.isfile(filepath):
        return False
    try:
        info = mediainfo(filepath)
        return 'audio' in info['codec_type']
    except:
        return False

def explore_folder(folder_path, lcd, audio_callback, root_dir_name):
    counter = 0
    display_lcd_content("Current location:" + folder_path)
    items = os.listdir(folder_path)
    if len(items):
        display_lcd_content(f'{counter+1}/{len(items)}: ' + items[counter])

        while True:
            sel = GPIO.input(pins.BUTTON_SELECT)
            prv = GPIO.input(pins.BUTTON_PREV)
            nxt = GPIO.input(pins.BUTTON_NEXT)
            time.sleep(0.1)
            while sel == GPIO.LOW and prv == GPIO.LOW and nxt == GPIO.LOW:
                sel = GPIO.input(pins.BUTTON_SELECT)
                prv = GPIO.input(pins.BUTTON_PREV)
                nxt = GPIO.input(pins.BUTTON_NEXT)
                time.sleep(0.1)
            if sel == GPIO.HIGH:
                while GPIO.input(pins.BUTTON_SELECT) == GPIO.HIGH:
                    pass
                selected_item = items[counter]
                new_path = os.path.join(folder_path, selected_item)
                if os.path.isdir(new_path):
                    counter = 0
                    explore_folder(new_path, lcd, audio_callback, root_dir_name)
                    break
                else:
                    display_lcd_content("Selected file:" + new_path)
                    if is_audio_file(new_path):
                        audio_callback(lcd, new_path)
                    print("RETURNED IN EXPLORE FOLDER 2")
                    explore_folder(folder_path, lcd, audio_callback, root_dir_name)

            elif prv == GPIO.HIGH:
                while GPIO.input(pins.BUTTON_PREV) == GPIO.HIGH:
                    pass
                if counter == 0 and folder_path != root_dir_name:
                    # navigate to the prev folder
                    folder_path = os.path.dirname(folder_path)
                    explore_folder(folder_path, lcd, audio_callback, root_dir_name)
                    break
                else:
                    counter = (counter - 1) % len(items)
                    display_lcd_content(f'{counter+1}/{len(items)}: ' + items[counter])

            elif nxt == GPIO.HIGH:
                while GPIO.input(pins.BUTTON_NEXT) == GPIO.HIGH:
                    pass
                counter = (counter + 1) % len(items)
                display_lcd_content(f'{counter+1}/{len(items)}: ' + items[counter])
            
            time.sleep(0.1) 
    else:
        display_lcd_content("No content available on USB.")

def access_usb_storage(audio_callback):
    lcd = get_lcd()
    
    sel = GPIO.input(pins.BUTTON_SELECT)
    prv = GPIO.input(pins.BUTTON_PREV)
    nxt = GPIO.input(pins.BUTTON_NEXT)
    
    # check for currently mounted USB storage devices
    context = pyudev.Context()
    mounted_devices = [device for device in context.list_devices(subsystem='block', DEVTYPE='partition') if 'ID_BUS' in device.properties and device.properties['ID_BUS'] == 'usb']
            
    if len(mounted_devices): # usb device(s) already inserted
        display_lcd_content(f"Found {len(mounted_devices)} USB storage device(s) already inserted: ")
        counter = 0
        display_lcd_content(f"Device {counter+1}/{len(mounted_devices)}")
        while True:
            sel = GPIO.input(pins.BUTTON_SELECT)
            prv = GPIO.input(pins.BUTTON_PREV)
            nxt = GPIO.input(pins.BUTTON_NEXT)
            time.sleep(0.1)
            while sel == GPIO.LOW and prv == GPIO.LOW and nxt == GPIO.LOW:
                sel = GPIO.input(pins.BUTTON_SELECT)
                prv = GPIO.input(pins.BUTTON_PREV)
                nxt = GPIO.input(pins.BUTTON_NEXT)
                time.sleep(0.1)
            if prv == GPIO.HIGH:
                while GPIO.input(pins.BUTTON_PREV) == GPIO.HIGH:
                    pass
                print("PREV")
                if counter > 0:
                    counter -= 1
                    lcd.clear()
                    display_lcd_content(f"Device {counter-1}/{len(mounted_devices)}")
            elif nxt == GPIO.HIGH:
                while GPIO.input(pins.BUTTON_NEXT) == GPIO.HIGH:
                    pass
                print("NEXT")
                if counter < len(mounted_devices) - 1:
                    counter += 1
                    lcd.clear()
                    display_lcd_content(f"Device {counter+1}/{len(mounted_devices)}")
            elif sel == GPIO.HIGH:
                while GPIO.input(pins.BUTTON_SELECT) == GPIO.HIGH:
                    pass
                print("SEL")
                device = mounted_devices[counter]
                    
                mount_point = '/mnt/usb'
                subprocess.run(['sudo', 'mkdir', '-p', mount_point])
                subprocess.run(['sudo', 'mount', device.device_node, mount_point])
                print("MOUNTED!")
                
                selected_mount_point = mount_point
                explore_folder(selected_mount_point, lcd, audio_callback, root_dir_name=selected_mount_point)
        time.sleep(0.1)
    else:
        display_lcd_content("Listening for USB input...")
        # check what happens for multiple inputs
     
        monitor = pyudev.Monitor.from_netlink(pyudev.Context())
        monitor.filter_by(subsystem='block', device_type='partition')
        for device in iter(monitor.poll, None):
            if device.action == 'add':
                if 'ID_BUS' in device.properties and device.properties['ID_BUS'] == 'usb':
                    display_lcd_content("USB storage device inserted:" + device.device_node)
                    
                    while True:
                        sel = GPIO.input(pins.BUTTON_SELECT)
                        prv = GPIO.input(pins.BUTTON_PREV)
                        nxt = GPIO.input(pins.BUTTON_NEXT)
                        time.sleep(0.1)
                        
                        while sel == GPIO.LOW and prv == GPIO.LOW and nxt == GPIO.LOW:
                            sel = GPIO.input(pins.BUTTON_SELECT)
                            prv = GPIO.input(pins.BUTTON_PREV)
                            nxt = GPIO.input(pins.BUTTON_NEXT)
                            time.sleep(0.1)
                        if prv == GPIO.HIGH:
                            while GPIO.input(pins.BUTTON_PREV) == GPIO.HIGH:
                                pass
                            print("PREV")
#                             if counter > 0:
#                                 counter -= 1
#                                 lcd.clear()
#                                 display_lcd_content(f"Device {counter+1}/{len(mounted_devices)}")
                        elif nxt == GPIO.HIGH:
                            while GPIO.input(pins.BUTTON_NEXT) == GPIO.HIGH:
                                pass
                            print("NEXT")
#                             if counter < len(mounted_devices) - 1:
#                                 counter += 1
#                                 lcd.clear()
#                                 display_lcd_content(f"Device {counter+1}/{len(mounted_devices)}")
                        elif sel == GPIO.HIGH:
                            while GPIO.input(pins.BUTTON_SELECT) == GPIO.HIGH:
                                pass
                            print("SEL")
#                             device = mounted_devices[counter]
                                
                            mount_point = '/mnt/usb'
                            subprocess.run(['sudo', 'mkdir', '-p', mount_point])
                            subprocess.run(['sudo', 'mount', device.device_node, mount_point])
                            print("MOUNTED!")
                            
                            selected_mount_point = mount_point
                            explore_folder(selected_mount_point, lcd, audio_callback, root_dir_name=selected_mount_point)
                    time.sleep(0.1)
