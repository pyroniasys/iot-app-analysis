#!/usr/bin/python

# ===========================================================================
# Rotating Logger Class
# ===========================================================================

import logging
from logging.handlers import RotatingFileHandler

class MyLogger(object):

  def __init__(self, fileName='logging.log', fileSize=1024*1024, fileCopies=5):
    self.logger = logging.getLogger(fileName)
    self.logger.setLevel(logging.INFO)
    self.handler = RotatingFileHandler(filename=fileName,maxBytes=fileSize,backupCount=fileCopies)
    self.formatter = logging.Formatter('%(asctime)s :  %(message)s')
    self.handler.setFormatter(self.formatter)
    self.logger.addHandler(self.handler)
    
  def write(self,msg):
    self.logger.info(msg)

if __name__ == '__main__':
  print "Logging from main"
