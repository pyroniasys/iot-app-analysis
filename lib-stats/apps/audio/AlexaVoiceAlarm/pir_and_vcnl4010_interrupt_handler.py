#!/usr/bin/python
  
import sys
import smbus
from Queue import Queue
import threading 
import datetime
import time

import RPi.GPIO as GPIO
from Adafruit_I2C import Adafruit_I2C
import VCNL4010

# ===========================================================================
# AVAC HW Class
# =========================================================================== 
    
class AVAC_HW(object):
  
    def __init__(self):
        #define 3 queues - log entries, send and receive messages
        self.pirQueue = Queue()
        self.vcnlQueue = Queue()
        self.interruptQueue = Queue()
        self.vcnl4010 = VCNL4010.VCNL4010()
        self.vcnl4010.calibrate()
        self.ambient = 0
        self.newEvent = time.time()
        self.lastEvent = time.time()
        # setup the GPIO bus and 2 interrupts
        GPIO.setmode(GPIO.BCM) 
        GPIO.setup(24, GPIO.IN,pull_up_down=GPIO.PUD_UP)  # GPIO pin 24 is the PIR interrupt
        GPIO.setup(23, GPIO.IN)  # GPIO pin 23 is the VCNL4010 interrupt
        GPIO.add_event_detect(24, GPIO.FALLING, callback=self.pirInterruptHandler) 
        GPIO.add_event_detect(23, GPIO.FALLING, callback=self.vcnlInterruptHandler)
 
    def pirWorkAround(self,):
        self.newEvent = time.time()
        self.elapsed = self.newEvent - self.lastEvent
        # print "seconds=",self.elapsed
        self.lastEvent = self.newEvent
        
    def interruptHelper(self,iQ,pQ,vQ):
        # print "interruptHandler running"
        while True:
            event = self.interruptQueue.get()
            if event == "PIR":
                m = time.strftime("PIR %y-%m-%d %H:%M:%S")
                self.pirQueue.put(m)
                # print m
            else:
                m = time.strftime("VCNL %y-%m-%d %H:%M:%S")
                self.vcnlQueue.put(m)
                # print m
                
    # define threaded callback function for the atmega328pu interrupt 
    def pirInterruptHandler(self,channel):  
        self.interruptQueue.put("PIR")
        print "PIR INT"
    
     # define threaded callback function for the atmega328pu interrupt 
    def vcnlInterruptHandler(self,channel): 
        val = self.vcnl4010.getInterruptStatus()
        self.vcnl4010.setInterruptStatus(val)
        self.interruptQueue.put("VCNL")
        # print "VCNL INT"
        
    def pirWait(self,blocking):
        if blocking:
            print "1 pirWait: blocking"
            data = self.pirQueue.get(blocking)
            # print "2 pirWait: data=",data
            self.pirWorkAround()
            return data
        else:
            if self.pirQueue.empty():
                print "3 pirWait non block: EMPTY"
                return ""
            else:
                data = self.pirQueue.get(False)
                print "4 pirWait non block: data=",data
                self.pirWorkAround()
                return data
        
    def vcnlWait(self,blocking):
        if blocking:
            data = self.vcnlQueue.get(True)
            return data
        else:
            if self.vcnlQueue.empty():
                return ""
            else:
                data = self.vcnlQueue.get(False)
                return data

    def run(self,):
        hwThread = threading.Thread(target=self.interruptHelper,args=(self.interruptQueue,self.pirQueue,self.vcnlQueue))
        hwThread.start()
        
    def exitCleanUp(self):
        self.running = False
        GPIO.cleanup()           # clean up GPIO on normal exit  

if __name__ == '__main__':
  print "AVAC HW Main Running"
  hw = AVAC_HW()
  hw.run()
  while True:
    # time.sleep(0.5)
    m = hw.pirWait(True)
    print m
    if len(m) > 0:
        m = hw.pirWait(False)
        
