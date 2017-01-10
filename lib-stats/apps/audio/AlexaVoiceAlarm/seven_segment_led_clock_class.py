#!/usr/bin/python

# ===========================================================================
# ClockLED
# ===========================================================================

import time
from Adafruit_LED_Backpack import SevenSegment
from threading import Thread

class LED_Clock(object):

    def __init__(self,):
        # Create display instance on default I2C address (0x70) and bus number.
        self.display = SevenSegment.SevenSegment()
        # Initialize the display. Must be called once before using the display.
        self.display.begin()
        self.brightness = 7
        self.display.set_brightness(self.brightness)
        self.colon = False
        self.alarm = False
        self.timeUpdateRunning = False
        self.timeFormat = "%l%M"

    def timeUpdateThread(self,):
        # print "started timeUpdateThread"
        while self.timeUpdateRunning:
            time.sleep(1.0)
            digitString = time.strftime(self.timeFormat)
            self.display.clear()
            self.display.print_number_str(digitString)
            self.display.set_colon(self.colon)
            if (self.colon):
                self.colon = False
            else:
                self.colon = True
            self.display.set_decimal(3, self.alarm)
            self.display.write_display()

    def setTime24(self,Time24=True):
        if Time24:
            self.timeFormat = "%I%M"
        else:
            self.timeFormat = "%l%M"

    def setAlarm(self,val):
        self.alarm = val

    def setBrightness(self,val):
        # print("set brightness="+str(val))
        self.brightness = val
        self.display.set_brightness(self.brightness)

    def increaseBrightness(self,):
        self.brightness = self.brightness + 1
        if self.brightness > 15:
            self.brightness = 15
        self.display.set_brightness(self.brightness)

    def decreaseBrightness(self,):
        self.brightness = self.brightness - 1
        if self.brightness < 0:
            self.brightness = 0
        self.display.set_brightness(self.brightness)

    def run(self):
        self.timeUpdateRunning = True
        self.tuThread = Thread(target=self.timeUpdateThread )
        self.tuThread.daemon = True
        self.tuThread.start()

if __name__ == '__main__':
    # print "ClockLED"
    clock = LED_Clock()
    clock.run()
    while True:
        # simple input driver
        choice = raw_input("> ")

        if choice == 'x' :
            print "exiting"
            clock.timeUpdateRunning = False
            time.sleep(2.0)
            break
        elif choice == 'a':
            if clock.alarm:
                clock.alarm = False
            else:
                clock.alarm = True
        elif choice == '+':
            clock.increaseBrightness()
            print "brightness=",clock.brightness
        elif choice == '-':
            clock.decreaseBrightness()
            print "brightness=",clock.brightness
        else:
            print ("e)xit or a)larm or + or -")

