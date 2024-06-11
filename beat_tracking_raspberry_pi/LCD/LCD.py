import smbus
import time

class LCD:
    def __init__(self, pi_rev = 2, i2c_addr = 0x3F, backlight = True):

        # device constants
        self.I2C_ADDR  = i2c_addr
        self.LCD_WIDTH = 16   # Max. characters per line

        self.LCD_CHR = 1 # Mode - Sending data
        self.LCD_CMD = 0 # Mode - Sending command

        self.LCD_LINE_1 = 0x80 # LCD RAM addr for line one
        self.LCD_LINE_2 = 0xC0 # LCD RAM addr for line two

        if backlight:
            # on
            self.LCD_BACKLIGHT  = 0x08
        else:
            # off
            self.LCD_BACKLIGHT = 0x00

        self.ENABLE = 0b00000100 # Enable bit

        # Timing constants
        self.E_PULSE = 0.0005
        self.E_DELAY = 0.0005

        # Open I2C interface
        if pi_rev == 2:
            # Rev 2 Pi uses 1
            self.bus = smbus.SMBus(1)
        elif pi_rev == 1:
            # Rev 1 Pi uses 0
            self.bus = smbus.SMBus(0)
        else:
            raise ValueError('pi_rev param must be 1 or 2')

        # Initialise display
        self.lcd_byte(0x33, self.LCD_CMD) # 110011 Initialise
        self.lcd_byte(0x32, self.LCD_CMD) # 110010 Initialise
        self.lcd_byte(0x06, self.LCD_CMD) # 000110 Cursor move direction
        self.lcd_byte(0x0C, self.LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28, self.LCD_CMD) # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, self.LCD_CMD) # 000001 Clear display

    def lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = 1 for data, 0 for command

        bits_high = mode | (bits & 0xF0) | self.LCD_BACKLIGHT
        bits_low = mode | ((bits<<4) & 0xF0) | self.LCD_BACKLIGHT

        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.toggle_enable(bits_high)

        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.toggle_enable(bits_low)

    def toggle_enable(self, bits):
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR,(bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)

    def message(self, string, scroll_speed=0.5, line_speed=0.25):
        # Display message string on LCD with automatic text wrapping and scrolling

        # Split the string into lines of appropriate length
        lines = [string[i:i+self.LCD_WIDTH] for i in range(0, len(string), self.LCD_WIDTH)]

        # Clear both lines
        self.clear()

        # If text fits in both lines, display it
        if len(lines) <= 2:
            for i, line in enumerate(lines, start=1):
                lcd_line = self.LCD_LINE_1 if i == 1 else self.LCD_LINE_2
                line = line.ljust(self.LCD_WIDTH, " ")
                self.lcd_byte(lcd_line, self.LCD_CMD)
                for char in line:
                    self.lcd_byte(ord(char), self.LCD_CHR)
                time.sleep(line_speed)
        else:
            # Combine lines for scrolling
            combined_text = ''.join(lines)
            remaining_text = combined_text

            # While there's text remaining, scroll it
            while remaining_text:
                # Clear the first line before displaying new text
                self.clear_line(self.LCD_LINE_1)

                # Display text on the first line
                display_text_1 = remaining_text[:self.LCD_WIDTH]
                self.lcd_byte(self.LCD_LINE_1, self.LCD_CMD)
                for char in display_text_1:
                    self.lcd_byte(ord(char), self.LCD_CHR)

                # Scroll remaining text on the second line
                display_text_2 = remaining_text[self.LCD_WIDTH:self.LCD_WIDTH * 2]
                if len(display_text_2) < self.LCD_WIDTH:
                    display_text_2 = display_text_2.ljust(self.LCD_WIDTH, " ")
                self.lcd_byte(self.LCD_LINE_2, self.LCD_CMD)
                for char in display_text_2:
                    self.lcd_byte(ord(char), self.LCD_CHR)

                # Update remaining text for next iteration
                if len(remaining_text) > self.LCD_WIDTH:  # Check if remaining text is longer than LCD width
                    remaining_text = remaining_text[self.LCD_WIDTH:]
                else:
                    if len(remaining_text) > 0:  # Check if there's remaining text to display
                        for char in remaining_text[:self.LCD_WIDTH]:
                            self.lcd_byte(ord(char), self.LCD_CHR)
                    remaining_text = ''  # Set remaining_text to empty string when there's no more text left to display

                # Sleep for scroll speed
                time.sleep(scroll_speed)

        # If the text is shorter than the LCD's capacity, clear the remaining lines
        if len(string) < self.LCD_WIDTH * 2:
            for i in range(len(string), self.LCD_WIDTH * 2):
                self.lcd_byte(0x80 + i, self.LCD_CMD)
                self.lcd_byte(0x20, self.LCD_CHR)

    def clear_line(self, line):
        # Clear a specific line on the LCD
        self.lcd_byte(line, self.LCD_CMD)
        for _ in range(self.LCD_WIDTH):
            self.lcd_byte(0x20, self.LCD_CHR)

    def clear(self):
        # clear LCD display
        self.lcd_byte(0x01, self.LCD_CMD)
