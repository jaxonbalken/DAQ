# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 13:53:45 2019
connects to rigol electronic load,
sets current, reads voltage, makes plot, saves data.
http://alexforencich.com/wiki/en/python-vxi11/readme
Add command line inputs for filenames etc
@author: Pain
"""

import vxi11
import numpy as np
import time
import matplotlib
import matplotlib.pyplot as plt
import csv
import os
from tkinter import *
default_params={}
default_params['Imin']=0
default_params['Imax']=4
default_params['Nsteps']=30
default_params['Laser_power']=1.7
default_params['TXT_prefix']='SP1'
default_params['Folder']='L:\EXPT\DEEP-IN - interstellar\Lab Testing\PV Testing\sunpower_cell_tests'
default_params['Wavelength']=1064
paramstxt=['Imin','Imax','Nsteps','Laser_power','TXT_prefix','Folder','Wavelength']
paramskeys=paramstxt

from daq import daqDevice
import daqh
db3031_byststr= bytes('DaqBoard3031USB', 'ascii')  #workaround to make daq.py work in py3, open the A/D as dev
dev=daqDevice(db3031_byststr)

def read_chans(dev):
    #get all 16, 2 tranches because MCC needs +256 to refer to upper 8 when differential
    #read n times and average them
    n=20
  #  flags=[daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
#        daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
  #         daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
   #        daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
    #       daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
     #      daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
    #       daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us,
     #      daqh.DafBipolar|daqh.DafDifferential|daqh.DafSettle10us]
    flags=[daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us,
           daqh.DafBipolar|daqh.DafSingleEnded|daqh.DafSettle10us]
    gain=daqh.DgainX1
    adcs=np.zeros(16,int)
    for i in range(n):
        adcs1=np.array(dev.AdcRdScan(0,7,gain,flags))
        adcs2=np.array(dev.AdcRdScan(256,256+7,gain,flags))
        adcs = adcs+np.append(adcs1,adcs2)
    adcvs = np.array([(float(adc)/n-2**15)*20./2**16 for adc in adcs])
    return (adcvs)

def get_diffs(adcvs):
    adcvlist=list(adcvs)
    adcvlist.insert(8,0.0)
    diffs=np.array(adcvlist[1:])-np.array(adcvlist[:-1])
    return (diffs)


def get_date_filename(text_string):
    '''default filename using date and time. 
    creates a directory for each day and returns the file string to be used'''    
    now=time.localtime()[0:6]
    dirfmt = "%4d_%02d_%02d"
    dirname = dirfmt % now[0:3]
    filefmt = "%02d_%02d_%02d.csv"
    filename= text_string+filefmt % now[3:6]
    ffilename=os.path.join(dirname,filename)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return(ffilename) 

def get_time_filename(folder,text_string):
    '''default filename using date and time. 
    creates a directory for each day and returns the file string to be used'''    
    now=time.localtime()[0:6]
    filefmt = "%02d_%02d_%02d.csv"
    filename= text_string+filefmt % now[3:6]
    ffilename=os.path.join(folder,filename)
    print(ffilename)
    return(ffilename) 

def get_date_dirname():
    '''default directory using date and time. 
    creates a directory for each day and returns '''    
    now=time.localtime()[0:6]
    dirfmt = "%4d_%02d_%02d"
    dirname = dirfmt % now[0:3]
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return(dirname)     

def start_monitor_callback():
    #this starts a loop reading all the cell voltages and printing to the array of boxes
    #exits on hitting start_measurment button to avoid conflict, since now we'll measure these 
    #during the sweep as well
    #read 16 a/d
    cell_index=[13,12,5,4,14,11,6,3,15,10,7,2,16,9,8,1]
    if var1.get()==1:
        adcvals=read_chans(dev)
        adcdiffs=get_diffs(adcvals)
        for i in range(16):
            ci=cell_index[i]
            entries[i].delete(0,END)
            entries[i].insert(0,str(adcdiffs[ci-1])[:5])  #a/d mapping of the entry layout: for example lower right is 16th entry but first a/d== 0
        window.after(200,start_monitor_callback)

def start_measurement_callback():
        ftext=entry_prefix.get()
        low=float(entry_i_min.get())
        high=float(entry_i_max.get())
        steps=int(entry_n_steps.get())
        input_power_W=float(entry_power.get())
        delay_time=1.0 #float(input('Delay between steps, seconds '))

        #currents to sweep:

        decimals = 4 
        instr =  vxi11.Instrument("192.168.1.128")
        #instr.write("*RST")
        IDN = instr.ask("*IDN?")
        print(IDN)
        if "00.01.01.00.09" not in IDN:
            print('This is not the right unit')
        else:
            print('correct device found')
            print(instr.ask("*TST?"))
            
            instr.write(":SOUR:FUNC:CURR")  
            instr.write(":SOUR:FUNC:MODE FIX") 
            print( "mode set to: " , instr.ask(":SOUR:FUNC?")  ) 
            instr.write(":SOUR:CURR:RANG max")
            print( "range set to: " , instr.ask(":SOUR:CURR:RANG?")  )  
            
            currents = np.round( np.linspace(low, high, steps), decimals)
            voltages = np.zeros(steps,float)
            m_currents=np.zeros(steps,float)  #measured currents as different from set
            cell_diff_vs=np.zeros([steps,16],float)
            if currents[0] == 0:
                instr.write(":SOUR:INP:STAT 0")
                time.sleep(delay_time)
                voltages[0] = instr.ask( ":MEAS:VOLT?" )
                m_currents[0] = instr.ask( ":MEAS:CURR?" )
                print("--------------------------")
                print( "current set to: disabled" )
                print( "Voltage: " , voltages[0] )
            instr.write(":SOUR:INP:STAT 1") 
            for step, current in enumerate(currents):
                if current != 0:
                    print(step, "--------------------------")
                    command = ":SOUR:CURR:LEV:IMM " + str(current)
                    instr.write(command)
                    print( "current set to: " , instr.ask(":SOUR:CURR:LEV:IMM?") )
                    time.sleep(delay_time)
                    voltages[step] = instr.ask( ":MEAS:VOLT?" )
                    m_currents[step] = instr.ask( ":MEAS:CURR?" )
                    node_vs=read_chans(dev)
                    cell_diff_vs[step,:]=get_diffs(node_vs)
                    print( "Voltage: " , voltages[step] )
                    print("Measured current:",m_currents[step])

            instr.write(":SOUR:CURR:LEV:IMM 0") 
            instr.write(":SOUR:INP:STAT 0") 
            print( "current set to: " , instr.ask(":SOUR:CURR:LEV:IMM?") )
            
            power = m_currents*voltages
            max_power=np.max(power)
            max_power_current=m_currents[np.argmax(power)]
            #save to file
            dirname=get_date_dirname()
            save_data(m_currents,voltages,power,cell_diff_vs)
            #now plot also
            fig, ax = plt.subplots()
            ax.plot(m_currents, voltages)
            ax.set(xlabel='Measured Current [A]', ylabel='Measured Voltage [V]', title='Laser IV %s' %ftext)
            ax.legend([], loc='best', title='Max power %s W at  %s A' %(str(max_power),str(max_power_current)))
            ax.grid()
            dirname=get_date_dirname()
            plt.show()
            figname=os.path.join(dirname,"%s_IV.png" %ftext)
            fig.savefig(figname)
            plt.close()
            
            fig, ax = plt.subplots()
            ax.plot(m_currents, power)
            ax.set(xlabel='Measured Current [A]', ylabel='Output Power [W]', title='Laser IV %s' %ftext)
            
            ax.grid()
            plt.show()
            figname=os.path.join(dirname,"%s_W.png" %ftext)
            fig.savefig(figname)
            plt.close()
            
            #try overplotting all individual cell IV
            fig, ax = plt.subplots()
            for c in range(16):
                ax.plot(m_currents, cell_diff_vs[:,c],label='Cell '+str(c))
                
            ax.set(xlabel='Measured Current [A]', ylabel='Measured Voltage [V]', title='Laser IV %s' %ftext)
            ax.legend()
            ax.grid()
            dirname=get_date_dirname()
            plt.show()
            figname=os.path.join(dirname,"%s__Cell_IVs.png" %ftext)
            fig.savefig(figname)
            plt.close()

    
def save_data(m_currents,voltages,power,cell_diff_vs):
        folder=entry_folder.get()
        prefix=entry_prefix.get()
        laser_power=float(entry_power.get())
        wavelength=float(entry_wavelength.get())
        filename=get_date_filename(prefix)
        with open(filename, mode='w') as out_file:   
                file_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,lineterminator='\n')
                file_writer.writerow(['Current [A]', 'Voltage [V]','Power [W]','Laser Power [W]','Wavelength [nm]',
                                      'Cell 1[V]','Cell 2[V]','Cell 3[V]','Cell 4[V]','Cell 5[V]','Cell 6[V]','Cell 7[V]',
                                     'Cell 8[V]','Cell 9[V]','Cell 10[V]','Cell 11[V]','Cell 12[V]','Cell 13[V]','Cell 14[V]',
                                     'Cell 15[V]','Cell 16[V]'])
                for i in range(len(m_currents)):
                    outlist=[m_currents[i],voltages[i],power[i],laser_power,wavelength]+list(cell_diff_vs[i,:])    
                    file_writer.writerow(outlist)
                


window = Tk()
window.title("Solar cell load test")
window.geometry('500x500')   
poweramplabel=Label(window,text='Rigol electronic load DL3021A',font = "Helvetica 14 bold")
poweramplabel.pack(side=TOP)
pwlbls=[]
pwtxts=[]

monitor=True

paramstxt=['Imin','Imax','Nsteps','Laser_power','TXT_prefix','Folder','Wavelength']
paramskeys=paramstxt        

fi_min=Frame(window)
labeli_min=Label(fi_min,text='Min current [A]')
labeli_min.pack(side="left")
entry_i_min=Entry(fi_min)
entry_i_min.insert(END,'0')
entry_i_min.configure(width=10)
entry_i_min.pack(side="left")
fi_min.pack(side=TOP)

fi_max=Frame(window)
labeli_max=Label(fi_max,text='Max current [A]')
labeli_max.pack(side="left")
entry_i_max=Entry(fi_max)
entry_i_max.insert(END,'4')
entry_i_max.configure(width=10)
entry_i_max.pack(side="left")
fi_max.pack(side=TOP)

fn_steps=Frame(window)
labeln_steps=Label(fn_steps,text='number of steps]')
labeln_steps.pack(side="left")
entry_n_steps=Entry(fn_steps)
entry_n_steps.insert(END,'30')
entry_n_steps.configure(width=10)
entry_n_steps.pack(side="left")
fn_steps.pack(side=TOP)

fpower=Frame(window)
labelpower=Label(fpower,text='Laser power [W]')
labelpower.pack(side="left")
entry_power=Entry(fpower)
entry_power.insert(END,'1.1')
entry_power.configure(width=10)
entry_power.pack(side="left")
fpower.pack(side=TOP)

fprefix=Frame(window)
labelprefix=Label(fprefix,text='File prefix')
labelprefix.pack(side="left")
entry_prefix=Entry(fprefix)
entry_prefix.insert(END,'SP')
entry_prefix.configure(width=10)
entry_prefix.pack(side="left")
fprefix.pack(side=TOP)

ffolder=Frame(window)
labelfolder=Label(ffolder,text='Folder')
labelfolder.pack(side="left")
entry_folder=Entry(ffolder)
entry_folder.insert(END,'C:\Starshot\PV Testing\Supower_characterization')
entry_folder.configure(width=50)
entry_folder.pack(side="left")
ffolder.pack(side=TOP)

fwavelength=Frame(window)
labelwavelength=Label(fwavelength,text='Wavelength')
labelwavelength.pack(side="left")
entry_wavelength=Entry(fwavelength)
entry_wavelength.insert(END,'888')
entry_wavelength.configure(width=10)
entry_wavelength.pack(side="left")
fwavelength.pack(side=TOP)

start_measurement_button=Button(window,command=start_measurement_callback)
start_measurement_button.configure(text='Start acquisition',background='Green',padx=50)
start_measurement_button.pack(side=TOP) 

#stop_monitor_button=Button(window,command=stop_monitor_callback)
#stop_monitor_button.configure(text='Stop Monitoring',background='Red',padx=50)
#stop_monitor_button.pack(side=TOP)
var1=IntVar()
stop_monitor_check=Checkbutton(window,text='Live Monitoring',variable=var1,onvalue=1)
stop_monitor_check.pack(side=TOP)

start_monitor_button=Button(window,command=start_monitor_callback)
start_monitor_button.configure(text='Monitor V_cells',background='Yellow',padx=50)
start_monitor_button.pack(side=TOP)

entries = []
f_ol_voltages=Frame(window)
cell_index=[13,12,5,4,14,11,6,3,15,10,7,2,16,9,8,1]
for i in range(4):
    for j in range(4):
        n=j+4*i
        # create entries list
        entries.append(Entry(f_ol_voltages, bg='yellow', width=10))
        # grid layout the entries
        entries[n].grid(row=i, column=j)
f_ol_voltages.pack()

window.mainloop()
