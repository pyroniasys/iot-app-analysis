#!/usr/bin/python

# ===========================================================================
# DisplayOLED
# ===========================================================================

import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import socket

hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)

from threading import Thread

class OLED_Display(object):

    def __init__(self,):
        # Raspberry Pi pin configuration:
        RST = 24
        # 128x64 display with hardware I2C:
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
        self.disp.begin()
        self.disp.clear()
        self.disp.display()
        # Create image buffer. Make sure to create image with mode '1' for 1-bit color.
        self.image = Image.new('1', (self.disp.width, self.disp.height))
        self.font = ImageFont.truetype("/home/pi/Fonts/Tahoma.ttf",12)
        # self.font = ImageFont.load_default()
        # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as this python script!
        # Some nice fonts to try: http://www.dafont.com/bitmap.php
        self.draw = ImageDraw.Draw( self.image )
        self.hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #connect to any target website
        s.connect(('google.com', 0))
        self.ipAddress = s.getsockname()[0]
        s.close()
        self.oledUpdateRunning = False
        self.sleepingOled = False
        self.line3 = ""
        self.line4 = ""
        self.wakeUpImage = Image.open('/home/pi/Projects/wakeUpImage.jpg').convert('1')
        self.speakImage = Image.open('/home/pi/Projects/speakImage.jpg').convert('1')
        self.mode = 'text'

    def updateDisplay(self,):
        self.disp.clear()
        # Clear image buffer by drawing a black filled box.
        self.draw.rectangle((0,0,self.disp.width,self.disp.height), outline=0, fill=0)
        if not self.sleepingOled:
            if self.mode == 'speakImage':
                self.disp.image(self.speakImage)
            elif self.mode == 'wakeUpImage':
                self.disp.image(self.wakeUpImage)
            else:
                dayOfWeekString = time.strftime("%A %b %-d")
                self.draw.text((4,1), dayOfWeekString, font=self.font, fill=255)
                self.draw.text((2,16), self.ipAddress, font=self.font, fill=255)
                self.draw.text((2,32), self.line3, font=self.font, fill=255)
                self.draw.text((2,48), self.line4, font=self.font, fill=255)
                self.disp.image(self.image)
        self.disp.display()

    def oledUpdateThread(self,):
        # print "started oledeUpdateThread"
        while self.oledUpdateRunning:
            self.updateDisplay()
            time.sleep(0.5)

    def setImageMode(self,newMode='text'):
        self.mode = newMode
        self.updateDisplay()

    def setLine3(self,val=""):
        self.line3 = val
        self.updateDisplay()

    def setLine4(self,val=""):
        self.line4 = val
        self.updateDisplay()

    def setSleepMode(self,sleep):
        # print("set sleep mode="+str(sleep))
        self.sleepingOled = sleep
        self.updateDisplay()

    def run(self):
        self.oledUpdateRunning = True
        self.oThread = Thread(target=self.oledUpdateThread )
        self.oThread.daemon = True
        self.oThread.start()

if __name__ == '__main__':
    # print "DisplayOLED"
    oled = OLED_Display()
    oled.run()
    while True:
        time.sleep(5.0)
        oled.setImageMode('speakImage')
        time.sleep(5.0)
        oled.setImageMode('text')
        time.sleep(5.0)
        oled.setImageMode('wakeUpImage')
        time.sleep(5.0)
        oled.setImageMode('text')





