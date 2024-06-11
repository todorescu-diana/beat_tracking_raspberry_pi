import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import os
import pyudev
import subprocess
import time
import RPi.GPIO as GPIO 
from utils.gpio_setup import init_gpio, cleanup_gpio
from utils.lcd_utils import init_lcd, get_lcd
import constants.pins as pins

def is_wav_or_mp3(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower() in ['.wav', '.mp3']

def display_content(content):
    lcd = get_lcd()
    lcd.clear()
    lcd.message(content)
    time.sleep(0.5)

def explore_folder(folder_path, lcd, audio_callback, root_dir_name):
    current_index = 0
    display_content("Current location:" + folder_path)
    items = os.listdir(folder_path)
    if len(items):
        display_content(f'{current_index+1}/{len(items)}: ' + items[current_index])

        while True:
            time.sleep(0.1) 

            if GPIO.input(pins.BUTTON_SELECT) == GPIO.HIGH:
                selected_item = items[current_index]
                new_path = os.path.join(folder_path, selected_item)
                if os.path.isdir(new_path):
                    current_index = 0
                    explore_folder(new_path, lcd, audio_callback, root_dir_name)
                    break
                else:
                    display_content("Selected file:" + new_path)
                    if is_wav_or_mp3(new_path):
                        audio_callback(lcd, new_path)

            elif GPIO.input(pins.BUTTON_PREV) == GPIO.HIGH:
                if current_index == 0 and folder_path != root_dir_name:
                    # navigate to the prev folder
                    folder_path = os.path.dirname(folder_path)
                    explore_folder(folder_path, lcd, audio_callback, root_dir_name)
                    break
                else:
                    current_index -= 1
                    display_content(items[current_index])

            elif GPIO.input(pins.BUTTON_NEXT) == GPIO.HIGH:
                current_index = (current_index + 1) % len(items)
                display_content(items[current_index])
    else:
        display_content("No content available on USB.")

def access_usb_storage(audio_callback):
    lcd = get_lcd()
    
    # check for currently mounted USB storage devices
    context = pyudev.Context()
    mounted_devices = [device for device in context.list_devices(subsystem='block', DEVTYPE='partition') if 'ID_BUS' in device.properties and device.properties['ID_BUS'] == 'usb']
    print("MOUNTED DEVICES: ", mounted_devices)
    
#     for root, dirs, files in os.walk(mount_point):
#         for file in files:
#             print(f'Found file: {os.path.join(root, file)}')
            
    if len(mounted_devices):
        display_content(f"Found {len(mounted_devices)} USB storage device(s) already inserted: ")
        for device in mounted_devices:
            display_content("Device node:" + device.device_node)
            
            mount_point = '/mnt/usb'
            subprocess.run(['sudo', 'mkdir', '-p', mount_point])
            subprocess.run(['sudo', 'mount', device.device_node, mount_point])
            print("MOUNTED!")

#             # List mount points
#             mount_points = [os.path.join("/media", entry) for entry in os.listdir("/media")]
# 
#             lcd.message(f"Found {len(mount_points)} mount points.")
#             lcd.message("Available mount points:")
#             
#             if len(mount_points):
            counter = 0
            selected = GPIO.input(pins.BUTTON_SELECT)
            
            while selected == GPIO.LOW:
                display_content(f"Device {counter+1}/{len(mounted_devices)}")
                prv = GPIO.input(pins.BUTTON_PREV)
                nxt = GPIO.input(pins.BUTTON_NEXT)
                
                while selected == GPIO.LOW and prv == GPIO.LOW and nxt == GPIO.LOW:
                    selected = GPIO.input(pins.BUTTON_SELECT)
                    prv = GPIO.input(pins.BUTTON_PREV)
                    nxt = GPIO.input(pins.BUTTON_NEXT)
                    time.sleep(0.1)
                
                if GPIO.input(pins.BUTTON_PREV) == GPIO.HIGH:
                    if counter > 0:
                        counter -= 1
                if GPIO.input(pins.BUTTON_NEXT) == GPIO.HIGH:
                    if counter < len(mount_points) - 1:
                        counter += 1
                lcd.clear()
                
            selected_mount_point = mount_point
            explore_folder(selected_mount_point, lcd, audio_callback, root_dir_name=selected_mount_point)
    else:
        display_content("Listening for USB input...")
        # check what happens for multiple inputs
     
        monitor = pyudev.Monitor.from_netlink(pyudev.Context())
        monitor.filter_by(subsystem='block', device_type='partition')
        for device in iter(monitor.poll, None):
            if device.action == 'add':
                if 'ID_BUS' in device.properties and device.properties['ID_BUS'] == 'usb':
                    lcd.message("USB storage device inserted:" + device.device_node)
                    mount_point = '/mnt/usb'
                    subprocess.run(['sudo', 'mkdir', '-p', mount_point])
                    subprocess.run(['sudo', 'mount', device.device_node, mount_point])
                    print("MOUNTED!")
#                     mount_points = [os.path.join("/media", entry) for entry in os.listdir("/media")]
# 
#                     lcd.message("Available mount points:")
#                 if len(mount_points):
                counter = 0
                selected = GPIO.input(pins.BUTTON_SELECT)
                
                while selected == GPIO.LOW:
#                     lcd.message(f"{counter+1}/{len(. {mount_points[counter - 1]}")
                    prv = GPIO.input(pins.BUTTON_PREV)
                    nxt = GPIO.input(pins.BUTTON_NEXT)
                    
                    while selected == GPIO.LOW and prv == GPIO.LOW and nxt == GPIO.LOW:
                        selected = GPIO.input(pins.BUTTON_SELECT)
                        prv = GPIO.input(pins.BUTTON_PREV)
                        nxt = GPIO.input(pins.BUTTON_NEXT)
                        time.sleep(0.1)
                    
                    if GPIO.input(pins.BUTTON_PREV) == GPIO.HIGH:
                        if counter > 0:
                            counter -= 1
                    if GPIO.input(pins.BUTTON_NEXT) == GPIO.HIGH:
                        if counter < len(mount_points) - 1:
                            counter += 1
                    lcd.clear()
                    
                selected_mount_point = mount_point
                explore_folder(selected_mount_point, lcd, audio_callback, root_dir_name=selected_mount_point)
