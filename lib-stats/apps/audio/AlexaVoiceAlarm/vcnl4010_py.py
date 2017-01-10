# The MIT License (MIT)
#
# Modern Art Electronics Project
#
# Vishay Proximity/Ambient Light Sensor VCNL4010 Class
#
# David Wilson
# Word derived from the Vishay and Adafruit library.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time

VCNL4010_ADDRESS               = 0x13   # 001 0011 shifted left 1 bit = 0x26
 
# registers 
REGISTER_COMMAND               = 0x80
REGISTER_ID                    = 0x81
REGISTER_PROX_RATE             = 0x82
REGISTER_PROX_CURRENT          = 0x83
REGISTER_AMBI_PARAMETER        = 0x84
REGISTER_AMBI_VALUE            = 0x85
REGISTER_PROX_VALUE            = 0x87
REGISTER_INTERRUPT_CONTROL     = 0x89
REGISTER_INTERRUPT_LOW_THRES   = 0x8a
REGISTER_INTERRUPT_HIGH_THRES  = 0x8c
REGISTER_INTERRUPT_STATUS      = 0x8e
REGISTER_PROX_TIMING           = 0x8f
REGISTER_AMBI_IR_LIGHT_LEVEL   = 0x90   # This register is not intended to be use by customer
 
# Bits in Command register = 0x80

COMMAND_ALL_DISABLE            = 0x00
COMMAND_SELFTIMED_MODE_ENABLE  = 0x01
COMMAND_PROX_ENABLE            = 0x02
COMMAND_AMBI_ENABLE            = 0x04
COMMAND_PROX_ON_DEMAND         = 0x08
COMMAND_AMBI_ON_DEMAND         = 0x10
COMMAND_MASK_PROX_DATA_READY   = 0x20
COMMAND_MASK_AMBI_DATA_READY   = 0x40
COMMAND_MASK_LOCK              = 0x80
 
# Bits in Product ID Revision Register = 0x81

PRODUCT_MASK_REVISION_ID       = 0x0f
PRODUCT_MASK_PRODUCT_ID        = 0xf0
 
# Bits in Prox Measurement Rate register = 0x82

PROX_MEASUREMENT_RATE_2        = 0x00   # DEFAULT
PROX_MEASUREMENT_RATE_4        = 0x01
PROX_MEASUREMENT_RATE_8        = 0x02
PROX_MEASUREMENT_RATE_16       = 0x03
PROX_MEASUREMENT_RATE_31       = 0x04
PROX_MEASUREMENT_RATE_62       = 0x05
PROX_MEASUREMENT_RATE_125      = 0x06
PROX_MEASUREMENT_RATE_250      = 0x07
PROX_MASK_MEASUREMENT_RATE     = 0x07
 
# Bits in Procimity LED current setting = 0x83

PROX_MASK_LED_CURRENT          = 0x3f   # DEFAULT = 2
PROX_MASK_FUSE_PROG_ID         = 0xc0
 
# Bits in Ambient Light Parameter register = 0x84

AMBI_PARA_AVERAGE_1            = 0x00
AMBI_PARA_AVERAGE_2            = 0x01
AMBI_PARA_AVERAGE_4            = 0x02
AMBI_PARA_AVERAGE_8            = 0x03
AMBI_PARA_AVERAGE_16           = 0x04
AMBI_PARA_AVERAGE_32           = 0x05   # DEFAULT
AMBI_PARA_AVERAGE_64           = 0x06
AMBI_PARA_AVERAGE_128          = 0x07
AMBI_MASK_PARA_AVERAGE         = 0x07
 
AMBI_PARA_AUTO_OFFSET_ENABLE   = 0x08   # DEFAULT enable
AMBI_MASK_PARA_AUTO_OFFSET     = 0x08
 
AMBI_PARA_MEAS_RATE_1          = 0x00
AMBI_PARA_MEAS_RATE_2          = 0x10   # DEFAULT
AMBI_PARA_MEAS_RATE_3          = 0x20
AMBI_PARA_MEAS_RATE_4          = 0x30
AMBI_PARA_MEAS_RATE_5          = 0x40
AMBI_PARA_MEAS_RATE_6          = 0x50
AMBI_PARA_MEAS_RATE_8          = 0x60
AMBI_PARA_MEAS_RATE_10         = 0x70
AMBI_MASK_PARA_MEAS_RATE       = 0x70
 
AMBI_PARA_CONT_CONV_ENABLE     = 0x80
AMBI_MASK_PARA_CONT_CONV       = 0x80   # DEFAULT disable
 
# Bits in Interrupt Control Register = x89

INTERRUPT_THRES_SEL_PROX       = 0x00
INTERRUPT_THRES_SEL_ALS        = 0x01
 
INTERRUPT_THRES_ENABLE         = 0x02
 
INTERRUPT_ALS_READY_ENABLE     = 0x04
 
INTERRUPT_PROX_READY_ENABLE    = 0x08
 
INTERRUPT_COUNT_EXCEED_1       = 0x00   # DEFAULT
INTERRUPT_COUNT_EXCEED_2       = 0x20
INTERRUPT_COUNT_EXCEED_4       = 0x40
INTERRUPT_COUNT_EXCEED_8       = 0x60
INTERRUPT_COUNT_EXCEED_16      = 0x80
INTERRUPT_COUNT_EXCEED_32      = 0xa0
INTERRUPT_COUNT_EXCEED_64      = 0xc0
INTERRUPT_COUNT_EXCEED_128     = 0xe0
INTERRUPT_MASK_COUNT_EXCEED    = 0xe0 
 
# Bits in Interrupt Status Register = x8e

INTERRUPT_STATUS_THRES_HI      = 0x01
INTERRUPT_STATUS_THRES_LO      = 0x02
INTERRUPT_STATUS_ALS_READY     = 0x04
INTERRUPT_STATUS_PROX_READY    = 0x08
INTERRUPT_MASK_STATUS_THRES_HI = 0x01
INTERRUPT_MASK_THRES_LO        = 0x02
INTERRUPT_MASK_ALS_READY       = 0x04
INTERRUPT_MASK_PROX_READY      = 0x08
 

class VCNL4010(object):
    """VCNL40xx proximity sensors."""

    def __init__(self, address=VCNL4010_ADDRESS, i2c=None, **kwargs):
        """Initialize the VCNL40xx sensor."""
        # Setup I2C interface for the device.
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)
        self.reset()
        
    def reset(self,):
        byte = self.getProductIDRegister()
        # print "Product ID=",byte
        self.setCommandRegister(COMMAND_ALL_DISABLE);
        self.setProximityRate (PROX_MEASUREMENT_RATE_31);
        # enable proximity and ambiant in selftimed mode
        self.setCommandRegister(COMMAND_PROX_ENABLE|COMMAND_AMBI_ENABLE|COMMAND_SELFTIMED_MODE_ENABLE)
        # set interrupt control for threshold
        self.setInterruptControl(INTERRUPT_THRES_SEL_PROX|INTERRUPT_THRES_ENABLE|INTERRUPT_COUNT_EXCEED_1)
        #set ambient light measurement parameter
        self.setAmbientConfiguration(AMBI_PARA_AVERAGE_32|AMBI_PARA_AUTO_OFFSET_ENABLE|AMBI_PARA_MEAS_RATE_2)
        
    def calibrate(self,):
        sum = 0
        for x in xrange(1, 30):
            sum = sum + self.getProximityOnDemand()
        sum = sum / 30
        offset = sum + 100
        self.reset()
        self.setHighThreshold(offset)
        # print('Proximity={0}, Threshold={1}'.format(sum, offset))
        # enable proximity and ambiant in selftimed mode
        self.setCommandRegister(COMMAND_PROX_ENABLE|COMMAND_AMBI_ENABLE|COMMAND_SELFTIMED_MODE_ENABLE)

    def getProductIDRegister(self,):
        result = self._device.readU8(REGISTER_ID)
        return result
         
    def setCommandRegister(self, command):
        self._device.write8(REGISTER_COMMAND,command)
        
    def getCommandRegister(self, ):
        return self._device.readU8(REGISTER_COMMAND)
        
    def setProximityRate(self, command):
        self._device.write8(REGISTER_PROX_RATE,command)     
        
    def setProximityCurrent(self, command):
        self._device.write8(REGISTER_PROX_CURRENT,command)  
    
    def setInterruptControl(self, command):
        self._device.write8(REGISTER_INTERRUPT_CONTROL,command)
        
    def getInterruptControl(self,):
        result = self._device.readU8(REGISTER_INTERRUPT_CONTROL)
        return result
        
    def setInterruptStatus (self, command):
        self._device.write8(REGISTER_INTERRUPT_STATUS,command)
        
    def getInterruptStatus (self,):
        result = self._device.readU8(REGISTER_INTERRUPT_STATUS)
        return result
        
    def setAmbientConfiguration (self, command):
        self._device.write8(REGISTER_AMBI_PARAMETER,command)
        
    def setLowThreshold (self, command):
        loByte = (command & 0xff)
        hiByte = ((command >> 8) & 0xff)
        self._device.write8(REGISTER_INTERRUPT_LOW_THRES,hiByte)
        self._device.write8(REGISTER_INTERRUPT_LOW_THRES+1,loByte)
        
    def setHighThreshold (self, command):
        loByte = (command & 0xff)
        hiByte = ((command >> 8) & 0xff)
        self._device.write8(REGISTER_INTERRUPT_HIGH_THRES,hiByte)
        self._device.write8(REGISTER_INTERRUPT_HIGH_THRES+1,loByte)
    
    def setModulatorTimingAdjustment (self, command):  
        self._device.write8(REGISTER_PROX_TIMING,command)
        
    def getProximityValue (self,):
        return self._device.readU16BE(REGISTER_PROX_VALUE); 
        
    def getAmbientValue (self,):
        return self._device.readU16BE(REGISTER_AMBI_VALUE); 

    def getProximityOnDemand (self,):
        self.setCommandRegister (COMMAND_PROX_ENABLE | COMMAND_PROX_ON_DEMAND)
        command = self.getCommandRegister ()   
        while ( (command & COMMAND_MASK_PROX_DATA_READY) == 0 ):
            command = self.getCommandRegister ()  
        result = self._device.readU16BE(REGISTER_PROX_VALUE)                        
        # self.reset() 
        return result
        
    def getAmbientOnDemand (self,):
        self.setCommandRegister (COMMAND_AMBI_ENABLE | COMMAND_AMBI_ON_DEMAND)
        command = self.getCommandRegister ()   
        while ( (command & COMMAND_MASK_AMBI_DATA_READY) == 0 ):
            command = self.getCommandRegister ()  
        result = self._device.readU16BE(REGISTER_AMBI_VALUE)                        
        # self.reset()
        return result
    

if __name__ == '__main__':
  print "VCNL4010 Driver Running"
  vcnl = VCNL4010()
  vcnl.calibrate()
  print "modes a,b,i,p"
  mode=raw_input()
  if mode.lower()=='a':
    while True:
      val = vcnl.getAmbientValue()
      print "Ambient=",val
      time.sleep(1.0)
  elif mode.lower()=='p':
    while True:
      val = vcnl.getProximityValue()
      print "proximity=",val
      time.sleep(1.0)
  else:
    while True:
      proximity = vcnl.getProximityOnDemand()
      ambient = vcnl.getAmbientOnDemand()
      print('Proximity={0}, Ambient light={1}'.format(proximity, ambient))
      time.sleep(1.0)
 
