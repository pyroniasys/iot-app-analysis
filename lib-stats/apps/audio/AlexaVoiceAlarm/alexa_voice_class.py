#!/usr/bin/python

# ===========================================================================
# Alexa Voice Handler
# ===========================================================================

import time
from threading import Thread
from Queue import Queue
import subprocess

import os
#import random
import alsaaudio
import wave
from creds import *
import requests
import json
import re
from memcache import Client

servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))
device = "plughw:1" # Name of your microphone/soundcard in arecord -L

class AlexaVoice(object):

    def __init__(self,):
        # Create display instance on default I2C address (0x70) and bus number.
        self.commandQueue = Queue()
        self.running = False
        self.defaultCommand = "/home/pi/Voices/time.wav"

    def internetAvailable(self,):
        # print "Checking Internet Connection"
        try:
            r =requests.get('https://api.amazon.com/auth/o2/token')
            # print "Connection OK"
            return True
        except:
            # print "Connection Failed"
            return False
        
    def getAmazonToken(self,):
        # print "getAmazonToke"
        token = mc.get("access_token")
        refresh = refresh_token
        if token:
		    return token
        elif refresh:
		    payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
		    url = "https://api.amazon.com/auth/o2/token"
		    r = requests.post(url, data = payload)
		    resp = json.loads(r.text)
		    mc.set("access_token", resp['access_token'], 3570)
		    return resp['access_token']
        else:
            return False
		    
    def getVerbalCommand(self,):
	    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
	    inp.setchannels(1)
	    inp.setrate(16000)
	    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
	    inp.setperiodsize(500)
	    audio = ""
	    t_end = time.time() + 5
	    while time.time() < t_end:
	        l, data = inp.read()
	        if l:
	            audio += data
	    rf = open('/home/pi/Recordings/recording.wav', 'w')
	    rf.write(audio)
	    rf.close()
	    inp = None
	    
    def startVerbalCommand(self,command='/home/pi/Recordings/recording.wav'):
        self.commandQueue.put(command)
        
    def startDialog(self,command='/home/pi/Voices/time.wav'):
       self.commandQueue.put(command)
    
    def alexaVoiceHandler(self,):
        while self.running:
            command = self.commandQueue.get(block=True)
            url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
            headers = {'Authorization' : 'Bearer %s' % self.getAmazonToken()}
            d = {
   	            "messageHeader": {
       		        "deviceContext": [
           		        {
               		        "name": "playbackState",
               		        "namespace": "AudioPlayer",
               		        "payload": {
                   		        "streamId": "",
        			   	        "offsetInMilliseconds": "0",
                                "playerActivity": "IDLE"
                            }
                        }
                    ]
                },
   	            "messageBody": {
                    "profile": "alexa-close-talk",
                    "locale": "en-us",
                    "format": "audio/L16; rate=16000; channels=1"
                }
            }

            with open(command) as inf:
                files = [
                        ('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
                        ('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
                        ]	
                r = requests.post(url, headers=headers, files=files)
            if r.status_code == 200:
                for v in r.headers['content-type'].split(";"):
                    if re.match('.*boundary.*', v):
                        boundary =  v.split("=")[1]
                data = r.content.split(boundary)
                for d in data:
                    if (len(d) >= 1024):
                        audio = d.split('\r\n\r\n')[1].rstrip('--')
                with open(path+"response.mp3", 'wb') as f:
                    f.write(audio)
                os.system('mpg123 -q {}1sec.mp3 {}response.mp3 {}1sec.mp3'.format(path, path, path))
            else:
                print "http status=",r.status_code
            
    def run(self,):
        while self.internetAvailable() == False:
		    print "."
        self.getAmazonToken()
        self.running = True
        self.tuThread = Thread(target=self.alexaVoiceHandler )
        self.tuThread.daemon = True
        self.tuThread.start()  

if __name__ == '__main__':
    # print "ClockLED"
    alexa = AlexaVoice()
    alexa.run()
    while True:
        # simple input driver
        choice = raw_input("> ")

        if choice == 'x' :
            print "exiting"
            alexa.running = False
            time.sleep(2.0)
            break
        elif choice == 't':
            alexa.startDialog("/home/pi/Voices/time.wav")
        
        elif choice == 'w':
            alexa.startDialog("/home/pi/Voices/weather.wav")
            
        else:
            print ("e)xit or a)larm or + or -")

