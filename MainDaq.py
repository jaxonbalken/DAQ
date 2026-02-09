import os
import sys
import time
from time import time
from time import sleep
from daq import daqDevice
import daqh

db3031_byststr= bytes('DaqBoard3031USB', 'ascii')

#workaround to make daq.py work in py3, open the A/D as dev
dev=daqDevice(db3031_byststr)

def read_chan(dev,chan):
    flags=daqh.DafBipolar|daqh.DafDifferential
    gain=daqh.DgainX1
    adc=dev.AdcRd(chan,gain=gain,flags=flags)
    adcv=(adc-2**15)*20./2**16
    return (adcv)

read_chan(dev,0)
pylab auto
