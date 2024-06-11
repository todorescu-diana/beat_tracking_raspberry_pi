import smbus

def scan_i2c_devices(bus_number=1):
    # Create an smbus object
    bus = smbus.SMBus(bus_number)

    # List to store found addresses
    found_addresses = []

    # Scan for I2C devices
    for address in range(0, 128):
        try:
            bus.read_byte(address)
            found_addresses.append(address)
        except:
            pass
    
    return found_addresses

if __name__ == "__main__":
    found_devices = scan_i2c_devices()
    print("Found I2C devices at addresses:", found_devices)
