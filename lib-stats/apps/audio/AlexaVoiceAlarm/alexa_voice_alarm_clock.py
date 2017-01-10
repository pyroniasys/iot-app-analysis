# Alexa Voice Alarm Clock
# Dave Wilson
# MIT license
# Based on Adafruit exmaples and other great developers

# Derived from - Example of using the MQTT client class to subscribe to and publish feed values.
# Author: Tony DiCola

# Import standard python modules.
import os
import random
import sys
import time
import subprocess
import threading
import alsaaudio

# Import Adafruit IO MQTT client.
from Adafruit_IO import MQTTClient

# Set to your Adafruit IO key & username below.
ADAFRUIT_IO_KEY      = '---'
ADAFRUIT_IO_USERNAME = '---'  # See https://accounts.adafruit.com

import AlexaVoice
import LED_Clock
import OLED_Display
import VCNL4010
import PIR_HW
import VCNL_HW
import MyLogger

global clock
clock = LED_Clock.LED_Clock()
clock.run()

global oled
oled = OLED_Display.OLED_Display()
oled.run()

global vcnl
vcnl = VCNL4010.VCNL4010()
vcnl.calibrate()

global vcnl_interrupt
vcnl_interrupt = VCNL_HW.VCNL_HW()

global pir_interrupt
pir_interrupt = PIR_HW.PIR_HW()

global myprocess
myprocess = None

global alarmTime
alarmTime = ""

global alarmOn
alarmOn = False

global lightOn
lightOn = False

global ID_WAKEUP
ID_WAKEUP = '600509'
global ID_MUSIC
ID_MUSIC = '600620'
global ID_ALARM_TIME
ID_ALARM_TIME = '601507'
global ID_LIGHT_STRIP
ID_LIGHT_STRIP = '601387'
global ID_SLEEP_MODE
ID_SLEEP_MODE = '601554'
global ID_MOTION
ID_MOTION = '600511'


#set up the status logger
global logger
logger = MyLogger.MyLogger(fileName="/home/pi/LogFiles/RotatingLog.log",fileSize=1024*1024)
logger.write("MQTT_AVAC STARTED")


# Define callback functions which will be called when certain events happen.
def connected(client):
    client.subscribe(ID_WAKEUP) # wake up alarm swith
    client.subscribe(ID_MUSIC) # music switch
    client.subscribe(ID_ALARM_TIME) # alarm time
    client.subscribe(ID_LIGHT_STRIP) # light strip
    client.subscribe(ID_SLEEP_MODE) # System sleep mode

def disconnected(client):
    sys.exit(1)

def message(client, feed_id, payload):
    global myprocess
    global alarmTime
    # wake up alarm switch
    if feed_id == ID_WAKEUP:
        alarmOn = False
        if payload == "ON":
            clock.alarm = True
            logger.write("WAKEUP ON")
        else:
            clock.alarm = False
            logger.write("WAKEUP OFF")
    # music switch
    elif feed_id == ID_MUSIC:
        if payload == "ON":
            dirStr = '/home/pi/Music/'
            fileStr = time.strftime("%A")
            pathStr = dirStr + fileStr + '.m4a'
            myprocess = subprocess.Popen(['omxplayer','-b',pathStr],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            oled.setLine3("Music Player")
            logger.write("MUSIC ON")
        else:
            logger.write("MUSIC OFF")
            if myprocess != None:
                try:
                    myprocess.stdin.write('q')
                except IOError as e:
                    logger.write("BROKEN PIPE: OMXPLAYER")
                oled.setLine3("")
    # light switch
    elif feed_id == ID_LIGHT_STRIP:
        if payload == "ON":
            lightOn = True
            logger.write("LIGHT STRIP ON")
            oled.setLine3("Night Light: ON")
        else:
            lightOn = False
            logger.write("LIGHT STRIP OFF")
            oled.setLine3("Night Light: OFF")
    # brighthness controls during sleep
    elif feed_id == ID_SLEEP_MODE:
        if payload == "ON":
            logger.write("SLEEP ON")
            clock.setBrightness(0)
            oled.setSleepMode(True)
        else:
            logger.write("SLEEP OFF")
            clock.setBrightness(7)
            oled.setSleepMode(False)
    # wake up time
    elif feed_id == ID_ALARM_TIME: # alarm time
        logger.write("ALARM TIME: "+payload)
        alarmTime = payload
        oled.setLine4(alarmTime)
    else:
        logger.write("UNDEFINED MESSAGE")
        oled.setLine4("TILT")


### MAIN THREAD ###

global client
# Create an MQTT client instance.
client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

# Setup the callback functions defined above.
client.on_connect    = connected
client.on_disconnect = disconnected
client.on_message    = message

# Connect to the Adafruit IO server.
client.connect()

client.loop_background()

# check for proximity user command
def userMonitor():
    global alarmOn
    global alarmWait
    global vcnl_interrupt
    global logger
    global alexa
    global oled
    logger.write("USER MONITOR THREAD STARTED")
    while True:
        switch = vcnl_interrupt.wait(True)
        while len(switch) > 0:
            switch = vcnl_interrupt.wait(False)
            # time.sleep(0.1)
        if alarmOn:
            alarmOn = False
            logger.write("STOP ALARM PROCESS")
        else:
            oled.setImageMode('speakImage')
            alexa.getVerbalCommand()
            oled.setImageMode('text')
            alexa.startVerbalCommand()


# check for pir movement
def motionMonitor():
    global pir_interrupt
    global logger
    global alexa
    global client
    logger.write("MOTION MONITOR THREAD STARTED")
    # print "motionMonitor"
    lastMotion = 0
    currentMotion = 0
    waitForMotion = True
    #client.publish(ID_MOTION,currentMotion)
    while True:
        time.sleep(0.1)
        motion = pir_interrupt.wait(waitForMotion)
        # logger.write(motion)
        if len(motion) > 0:
            waitForMotion = False
            while len(motion) > 0:
                # logger.write(motion)
                motion = pir_interrupt.wait(waitForMotion)
            currentMotion = 1
            logger.write("MOTION DETECTED")
        else:
            currentMotion = 0
            waitForMotion = True
            logger.write("MOTION NOT DETECTED")
        if not (lastMotion == currentMotion):
            lastMotion = currentMotion
            #client.publish(ID_MOTION,currentMotion)

alexa = AlexaVoice.AlexaVoice()
alexa.run()

# initialize the clock

time.sleep(5.0)
client.publish(ID_SLEEP_MODE, "OFF")
client.publish(ID_LIGHT_STRIP, "OFF")
client.publish(ID_WAKEUP, "OFF")
client.publish(ID_MUSIC, "OFF")
client.publish(ID_ALARM_TIME, "05:00")
time.sleep(5.0)

userThread = threading.Thread(target=userMonitor)
userThread.start()

#motionThread = threading.Thread(target=motionMonitor)
#motionThread.start()

frame = 0

### Loop forever checking for the alarm

alarmOn = False

while True:
    time.sleep(0.1)
    frame = frame + 1

    if clock.alarm:
        digitString = time.strftime("%H:%M")
        if str(alarmTime) == str(digitString):
            alarmOn = True
            logger.write("START ALARM PROCESS")
            oled.setImageMode('wakeUpMode')
            os.system('mpg123 -q /home/pi/Voices/AVAC-Hello-Time-To-Get-Up.mp3')
            time.sleep(5.0)
            if alarmOn:
                alexa.startDialog("/home/pi/Voices/time.wav")
                time.sleep(5.0)
            if alarmOn:
                alexa.startDialog("/home/pi/Voices/weather.wav")
                time.sleep(5.0)
            if alarmOn:
                client.publish(ID_MUSIC, "ON")
                time.sleep(5.0)
            if not alarmOn:
                client.publish(ID_MUSIC, "OFF")
            client.publish(ID_LIGHT_STRIP, "ON")
            alarmOn = False
        while str(alarmTime) == str(digitString):
            time.sleep(10.0)
            digitString = time.strftime("%H:%M")
            oled.setImageMode('text')
            frame = 6

    if frame >= 40:
        value = vcnl.getAmbientOnDemand()
        vcnl.calibrate()
        client.publish(600510, value)
        frame = 1


