# function to grab specified data from iotech USB acquisition board.
# simple and not very general, assumes all channels set the same
# for now hardwire to differential

from daq import daqDevice
import daqh
import os

import daq
import ctypes as ct
from ctypes import wintypes as wt
import numpy as np
import time
jnk=np.zeros([2,3],dtype=float)
help,jnk
nseconds=10
def get_date_filename():
    now=time.localtime()[0:6]
    #dirfmt = "c:\\cofe\\ground_data\\testdata\\%4d_%02d_%02d"
    dirfmt = "%4d_%02d_%02d"
    dirname = dirfmt % now[0:3]
    filefmt = "%02d_%02d_%02d.dat"
    filename= filefmt % now[3:6]
    ffilename=os.path.join(dirname,filename)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return(ffilename)

def get_data(nchan=6,freq=100,nseconds=5,comment='None',alerts=[58,59,60,118,119,120,178,179,180,238,239,240,298,299,300]):
    """
    function to simply aquire nchan a/d channels at rate freq
    for nseconds seconds
    """
    
    #outdata=np.zeros([nchan,nscans],dtype=float)
    db3031_byststr= bytes('DaqBoard3031USB', 'ascii')
    dev=daqDevice(db3031_byststr)
    gains=[]
    flags=[]
    chans=[]
    if nchan > 8:
        uchan=nchan-8
        for i in range(8):
            gains.append(daqh.DgainX1)
            flags.append(daqh.DafBipolar|daqh.DafDifferential)
            chans.append(i)
        for i in range(uchan):
            gains.append(daqh.DgainX1)
            flags.append(daqh.DafBipolar|daqh.DafDifferential)
            chans.append(256+i)   #HERE is the famous fix where DaqX refs upper level dif channels!
    elif nchan<9:      
        for i in range(nchan):
            gains.append(daqh.DgainX1)
            flags.append(daqh.DafBipolar|daqh.DafDifferential)
            chans.append(i)
    acqmode = daqh.DaamNShot
    dev.AdcSetAcq(acqmode, postTrigCount = nseconds*freq)
    dev.AdcSetScan(chans,gains,flags)
    dev.AdcSetFreq(freq)
    #use the driver buffer here user buffer was very limited (the way I tried anyway) 
    transMask = daqh.DatmUpdateBlock|daqh.DatmCycleOn|daqh.DatmDriverBuf

    buf=dev.AdcTransferSetBuffer(transMask, np.uint(nseconds*freq*nchan))
    #bufMask is for transferring the buffer
    bufMask = daqh.DabtmOldest | daqh.DabtmRetAvail

    timestart = (time.time())
    timenotify = timestart + 5

    dev.SetTriggerEvent(daqh.DatsImmediate,None, 0, np.array(gains[0],dtype=int), np.array(flags[0],dtype=int), daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStartEvent)
    dev.SetTriggerEvent(daqh.DatsScanCount,None, 0, np.array(gains[0],dtype=int), np.array(flags[0],dtype=int), daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStopEvent)
    dev.AdcTransferStart()
    dev.AdcArm()
    
    while True:
        
        #alertscopy=alerts[:]
        #timenotify = checkAlerts(timenotify, timestart, alerts,alertscopy)        
        stat = dev.AdcTransferGetStat()
        active = stat['active']
        if not (active & daqh.DaafAcqActive):
            break
    dev.AdcDisarm()
    outdata,ret=dev.AdcTransferBufData(nseconds*freq, nchan,bufMask)
    
    outdata=np.array(outdata,dtype=float)
    outdata=(outdata-2**15)*20./2**16
    outdata=np.reshape(outdata,[nseconds*freq,nchan])
    print ("Finished collecting data\n----------------------")
    dev.Close()
    return outdata
        
fname = get_date_filename()
dd=get_data(freq=10000,nseconds=10)
np.savetxt('tst.csv',dd,delimiter =',')


    
    
    
    
    