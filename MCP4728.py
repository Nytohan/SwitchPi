#!/usr/bin/env python
"""
================================================
MCP4728 DAC

Marko Pinteric 2018
http://www.pinteric.com/raspberry.html

Requires python smbus to be installed
================================================

NOTES:
- includes only methods for (a) writing to a single channel or (a) writing to
  all four channels
- (a) no-eeprom methods use multiple write command, (b) eeprom methods use?
  sequential write and single write command
- the same voltage reference is assumed for writing to all four channels
- no pull-down resistors on output channels are assumed (PD1=PD0=0)
- immediate voltage update assumed (UDAC=0) 
"""

try:
    import smbus
except ImportError:
    raise ImportError("python-smbus not found")

import RPi.GPIO as GPIO
import re
import platform
import time

"""
Control the MCP4728 DAC
"""
class MCP4728:
    # internal variables
    __dac_address = 0x60
    __bus = None

    # LOCAL METHODS

    # internal method for getting an instance of the i2c bus
    # copied from ABElectronics ADC Differential Pi 8-Channel ADC
    @staticmethod
    def __get_smbus():
        i2c__bus = 1
        # detect the device that is being used
        device = platform.uname()[1]

        if device == "orangepione":  # running on orange pi one
            i2c__bus = 0

        elif device == "orangepiplus":  # running on orange pi one
            i2c__bus = 0

        elif device == "linaro-alip":  # running on Asus Tinker Board
            i2c__bus = 1

        elif device == "raspberrypi":  # running on raspberry pi
            # detect i2C port number and assign to i2c__bus
            for line in open('/proc/cpuinfo').readlines():
                model = re.match('(.*?)\\s*\\s*(.*)', line)
                if model:
                    (name, value) = (model.group(1), model.group(2))
                    if name == "Revision":
                        if value[-4:] in ('0002', '0003'):
                            i2c__bus = 0
                        else:
                            i2c__bus = 1
                        break
        try:
            return smbus.SMBus(i2c__bus)
        except IOError:
            raise 'Could not open the i2c bus'

    # logical function: byte = (byte AND mask) OR value
    def __updatebyte(self, byte, mask, value):
        byte &= mask
        byte |= value
        return byte

    # init object with i2caddress, default is 0x60 for MCP4728
    def __init__(self, address=0x60):
        self.__bus = self.__get_smbus()
        self.__dac_address = address
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    # GLOBAL METHODS

    # writes multiple raw values to the specified DAC channels - channels 1 to 4, EEPROM not affected
    def multiple_raw(self, channels, reference, gains, values):
        bytes=[]
        for i in range(len(channels)):
            # first byte is 01000XXU, where XX is channel address (0-3)
            first=self.__updatebyte(0x40,0xFF,(channels[i]-1) << 1)
            bytes.append(first)
            # second word is XPPYDDDD DDDDDDDD, where X is reference, Y is gain and D is data
            second = list(divmod(values[i], 0x100))
            second[0] =self.__updatebyte(second[0],0x0F,reference << 7 | gains[i] << 4)
            bytes.extend(second)
        self.__bus.write_i2c_block_data(self.__dac_address,bytes[0],bytes[1:])
        return

    # writes sequential raw values to the all DAC channels - channels 1 to 4, EEPROM affected
    def sequential_raw(self, reference, gains, values):
        # first byte is 0101000U for writing starting at channel 0
        first=0x50
        # second word is XPPYDDDD DDDDDDDD, where X is reference, Y is gain and D is data
        seconds=[]
        for i in range(4):
            second = list(divmod(values[i], 0x100))
            second[0] =self.__updatebyte(second[0],0x0F,reference << 7 | gains[i] << 4)
            seconds.extend(second)
        self.__bus.write_i2c_block_data(self.__dac_address,first,seconds)
        return

    # writes single raw value to the selected DAC channel - channels 1 to 4, EEPROM affected
    def single_raw(self, channel, reference, gain, value):
        # first byte is 01011XXU, where XX is channel address (0-3)
        first=self.__updatebyte(0x58,0xFF,(channel-1) << 1)
        # second word is XPPYDDDD DDDDDDDD, where X is reference, Y is gain and D is data
        second = list(divmod(value, 0x100))
        second[0] =self.__updatebyte(second[0],0x0F,reference << 7 | gain << 4)
        self.__bus.write_i2c_block_data(self.__dac_address,first,second)
        return

    # writes single value to the selected DAC channel using internal reference - channels 1 to 4
    def single_internal(self, channel, volt, eeprom):
        if volt>2: gain=2
        else: gain=1
        value=int(0x1000 * volt/2.048/gain)
        if eeprom: self.single_raw(channel,1,gain-1,value)
        else: self.multiple_raw([channel],1,[gain-1],[value])

    # writes single value to the selected DAC channel using external reference - channels 1 to 4
    def single_external(self, channel, rel, eeprom):
        value=int(0x1000 * rel)
        if eeprom: self.single_raw(channel,0,0,value)
        else: self.multiple_raw([channel],0,[0],[value])

    # writes multiple values to the selected DAC channel using internal reference - channels 1 to 4
    def multiple_internal(self, volts, eeprom):
        values=[]
        gains=[]
        for i in range(4):
            if volts[i]>2: gain=2
            else: gain=1
            values.append(int(0x1000 * volts[i]/2.048/gain))
            gains.append(gain-1)
        if eeprom: self.sequential_raw(1,gains,values)
        else: self.multiple_raw([1,2,3,4],1,gains,values)

    # writes multiple values to the selected DAC channel using external reference - channels 1 to 4
    def multiple_external(self, rels, eeprom):
        values=[]
        for i in range(4):
            values.append(int(0x1000 * rels[i]))
        if eeprom: self.sequential_raw(0,[0,0,0,0],values)
        else: self.multiple_raw([1,2,3,4],0,[0,0,0,0],values)

"""
Gets and sets the MCP4728 DAC address
"""
class MCP4728_address:

    # LOCAL METHODS
    # all assume and leave SCL low, except when specified differently
    
    # following methods assume SCL and SDA high
    def __i2cstart(self):
        GPIO.setup(self.__sda_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)

    def __i2crestart(self):
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__sda_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)

    # following methods leave SCL and SDA high
    def __i2cstop(self):
        GPIO.setup(self.__sda_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__sda_gpio, GPIO.IN)

    def __i2cgetbyte(self):
        num=0x00
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        for i in range(8):
            GPIO.setup(self.__scl_gpio, GPIO.IN)
            # I2C clock stretching
            while(GPIO.input(self.__scl_gpio)==False): time.sleep(0.000001)
            num = num << 1
            if(GPIO.input(self.__sda_gpio)==True): num = num | 0x01
            GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)
        return(num)

    def __i2csendbyte(self,num):
        for i in range(8):
            if num & 0x80 == 0:
                GPIO.setup(self.__sda_gpio, GPIO.OUT, initial=GPIO.LOW)
            else:
                GPIO.setup(self.__sda_gpio, GPIO.IN)
            num = num << 1
            GPIO.setup(self.__scl_gpio, GPIO.IN)
            GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)

    def __i2cgetack(self):
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        res=GPIO.input(self.__sda_gpio)
        GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)
        return(not res)

    def __i2csendack(self):
        GPIO.setup(self.__sda_gpio, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)

    def __i2csendnack(self):
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__scl_gpio, GPIO.OUT, initial=GPIO.LOW)

    # GLOBAL METHODS

    # init object with GPIO addresses
    def __init__(self, scl, sda, ldac):
        self.__scl_gpio=scl
        self.__sda_gpio=sda
        self.__ldac_gpio=ldac
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    # gets the DAC address
    def getaddress(self):
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        GPIO.setup(self.__ldac_gpio, GPIO.IN)

        self.__i2cstart()
        self.__i2csendbyte(0)
        if(self.__i2cgetack()==False): print('No ACK G1')
        self.__i2csendbyte(0x0C)
        GPIO.setup(self.__ldac_gpio, GPIO.OUT, initial=GPIO.LOW)
        if(self.__i2cgetack()==False): print('No ACK G2')
        self.__i2crestart()
        self.__i2csendbyte(0xC1)
        GPIO.setup(self.__ldac_gpio, GPIO.IN)
        if(self.__i2cgetack()==False): print('No ACK G3')
        val = self.__i2cgetbyte()
        self.__i2csendnack()
        self.__i2cstop()
        adr1 = (val & 0xE0) >> 5
        adr2 = (val & 0x0E) >> 1
        if ((adr1 != adr2) or ((val & 0x11) != 0x10)):
            print('Error: returned {0:08b}'.format(val))
        return(0x60 | adr1)

    # sets the DAC address
    def setaddress(self,cur,new):
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        GPIO.setup(self.__ldac_gpio, GPIO.IN)
        cur &= 0x07
        new &= 0x07

        self.__i2cstart()
        self.__i2csendbyte(0xC0 | (cur << 1))
        if(self.__i2cgetack()==False): print('No ACK S1')
        self.__i2csendbyte(0x61 | (cur << 2))
        GPIO.setup(self.__ldac_gpio, GPIO.OUT, initial=GPIO.LOW)
        if(self.__i2cgetack()==False): print('No ACK S2')
        self.__i2csendbyte(0x62 | (new << 2))
        if(self.__i2cgetack()==False): print('No ACK S3')
        self.__i2csendbyte(0x63 | (new << 2))
        GPIO.setup(self.__ldac_gpio, GPIO.IN)
        if(self.__i2cgetack()==False): print('No ACK S4')
        self.__i2cstop()

    # resets the DAC
    def reset(self):
        GPIO.setup(self.__scl_gpio, GPIO.IN)
        GPIO.setup(self.__sda_gpio, GPIO.IN)
        GPIO.setup(self.__ldac_gpio, GPIO.IN)

        self.__i2cstart()
        self.__i2csendbyte(0x00)
        if(self.__i2cgetack()==False): print('No ACK R1')
        self.__i2csendbyte(0x06)
        if(self.__i2cgetack()==False): print('No ACK R2')
        self.__i2cstop()
