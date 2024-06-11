import pyudev
context = pyudev.Context()
for device in context.list_devices(subsystem='block', DEVTYPE='disk'):
    for props in device.properties:
        if device.get("ID_BUS") == "usb":
            print(props, device.get(props))