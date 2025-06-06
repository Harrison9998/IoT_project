# SSD1306 OLED Display Driver

class SSD1306_I2C:
    def __init__(self, width, height, i2c):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.buffer = bytearray((width * height // 8))
        self.init_display()

    def init_display(self):
        # Initialization sequence for the SSD1306
        self.command(0xAE)  # Display off
        self.command(0xD5)  # Set display clock divide ratio/oscillator frequency
        self.command(0x80)  # Set divide ratio
        self.command(0xA8)  # Set multiplex ratio
        self.command(self.height - 1)
        self.command(0xD3)  # Set display offset
        self.command(0x0)    # No offset
        self.command(0x40)   # Set start line
        self.command(0x8D)   # Charge pump
        self.command(0x14)   # Enable charge pump
        self.command(0x20)   # Set memory addressing mode
        self.command(0x00)   # Horizontal addressing mode
        self.command(0xA1)   # Set segment re-map
        self.command(0xC8)   # Set COM output scan direction
        self.command(0xDA)   # Set COM pins hardware configuration
        self.command(0x12)
        self.command(0x81)   # Set contrast control
        self.command(0x7F)
        self.command(0xD9)   # Set pre-charge period
        self.command(0xF1)
        self.command(0xDB)   # Set VCOMH deselect level
        self.command(0x40)
        self.command(0xA4)   # Entire display on
        self.command(0xA6)   # Set normal display
        self.command(0xAF)   # Display on

    def command(self, cmd):
        # Send a command to the display
        self.i2c.writeto(0x3C, bytearray([0x00, cmd]))

    def show(self):
        # Update the display with the current buffer
        for page in range(0, self.height // 8):
            self.command(0xB0 + page)  # Set page address
            self.command(0x00)          # Set lower column address
            self.command(0x10)          # Set higher column address
            self.i2c.writeto(0x3C, self.buffer[page * self.width:(page + 1) * self.width])

    def fill(self, color):
        # Fill the display with a color
        if color:
            self.buffer = bytearray((self.width * self.height // 8) - 1)
            for i in range(len(self.buffer)):
                self.buffer[i] = 0xFF
        else:
            self.buffer = bytearray((self.width * self.height // 8))

    def pixel(self, x, y, color):
        # Set a pixel in the buffer
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        if color:
            self.buffer[x + (y // 8) * self.width] |= (1 << (y % 8))
        else:
            self.buffer[x + (y // 8) * self.width] &= ~(1 << (y % 8))