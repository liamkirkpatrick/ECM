"""

Liam Kirkpatrick
ECM GUI system - 28th iteration (builds on ecmgui_28.py)
August, 2023

records true depth. Integrates inline plotting. Calls new settup script.
Compadible with xbox controller

This new version integrates:
- ability to skip re-entering setup info for repeat runs
- AC/DC as radio toggle

Requires functions:
  -laser_v2
  -makegui_v10
  -setup_movement_v3
"""


#%% Import Packages

# Import relevant packages - SCPI
import pyvisa

# Settup for plot
import matplotlib
matplotlib.use('TkAgg')

# Import relevant Packages - GUI
import PySimpleGUI as sg
import datetime
import time

# Import relevant Packages - Zaber
from zaber_motion.binary import Connection, CommandCode
from zaber_motion import Units

# Import Packages - Other
import os
from os import listdir
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt
import keyboard

# Import functions
from make_gui_v10 import guibuild, delete_figure, draw_figure, makeplot
from setup_movement_v6 import setup_mov
from setup_movement_xandy import setup_movxy
from getinput import getinput
from lastdims import loadlast, savelast

# Import packages - MCC
from mcculw import ul
from mcculw.enums import ULRange, DigitalIODirection
from mcculw.device_info import DaqDeviceInfo

# Import constants
import constants as c
import glob

#%%  Basic settup
# ==========================================================================================================
# Get time on stareup
today = datetime.datetime.now().strftime("%Y-%m-%d-%h-%m")

# Set quit variable to True (means don't quit)
qt = True

#%%  Open GUI
# ==========================================================================================================

# run make_gui function to build the GUI layout
layout = guibuild()

# Create the Window
window = sg.Window('ECM GUI - Version 7', layout, finalize=True)

#%% Set default Status reports, lock buttons
# ==========================================================================================================

window['-RUN_STATUS-'].update('')
window['-CON_STATUS-'].update('')
window['-MCC_STATUS-'].update('')
window['-READ_STATUS-'].update('')
window['-STATUS-'].update('')
window['-WRITE_RES-'].update('')
window['-SETUP_STATUS-'].update('')

# Lock Move Buttons
window['-Z_UP-'].update(disabled=True)
window['-Z_DOWN-'].update(disabled=True)
window['-X_UP-'].update(disabled=True)
window['-X_DOWN-'].update(disabled=True)
window['-Y_UP-'].update(disabled=True)
window['-Y_DOWN-'].update(disabled=True)
window['Submit'].update(disabled=True)
window['-ACDC_CONT-'].update(disabled=True)
window['-START_DC-'].update(disabled=True)
window['-START_AC-'].update(disabled=True)

#%% Create a folder for today
# ==========================================================================================================

fldr = datetime.datetime.now().strftime("%Y-%m-%d")
#parent = "/Users/Liam/Desktop/UW/ECM/run_outputs/"
parent = r"\Users\agu\Desktop\run_outputs"
path = os.path.join(parent, fldr)

try:
    os.mkdir(path)
    window['-RUN_STATUS-'].update('Created Folder')
except:
    print("*********************************************************************************")
    print('              Folder Already Exists (or other error creating file)               ')
    print("*********************************************************************************")
    window['-RUN_STATUS-'].update('Folder Already Exists')

#%% attempt to connect to MCC
# ==========================================================================================================

try:
    board_num = 0
    channel = 0
    ai_range = ULRange.BIP5VOLTS
    dev_id_list=[]
    
    daq_dev_info = DaqDeviceInfo(board_num)
    dio_info = daq_dev_info.get_dio_info()
    
    # Configure digital output
    # If I'm being fully honest, I don't know exactly what each of these lines
    # does, but I copied it from the mcculw examples on GitHub and it seems 
    # to work OK. 
    daq_dev_info = DaqDeviceInfo(board_num)
    port = next((port for port in dio_info.port_info if port.supports_output),None)
    ul.d_config_port(board_num, port.type, DigitalIODirection.OUT)
    
    # configure analog input
    ai_info = daq_dev_info.get_ai_info()
    #ai_range = ULRange.BIP5VOLTS
    ai_range = ai_info.supported_ranges[1]
    
    # print confirmation
    print('\nActive DAQ Device: ', daq_dev_info.product_name,'(,',daq_dev_info.unique_id,')\n',sep='')
    
    # turn digital output off to start
    ul.d_out(board_num, port.type, 0)
    
    
    print("*********************************************************************************")
    print("                           Connection to MCC Successful                          ")
    print("*********************************************************************************")
    
    window['-MCC_STATUS-'].update('MCC Connected')
    
except:
    print("*********************************************************************************")
    print("                        Error : Failed to Connect to MCC                         ")
    print("*********************************************************************************")
    qt = 0;

#%% attempt to connect to zaber. If there is no connection, return an error message
# ==========================================================================================================

try:
    # if True:
    connection = Connection.open_serial_port("COM3")
    
    print("connection = true")
    #connection = Connection.open_serial_port("COM7")
    device_list = connection.detect_devices()
    
    print("*********************************************************************************")
    print("                          Zaber Connection Successful                            ")
    print("                             Found {} devices            ".format(len(device_list)))
    print("*********************************************************************************")
    window['-CON_STATUS-'].update("Connected to {} devices".format(len(device_list)))
    
    if len(device_list) < 4:
        print('Not Enough Devices Connected')
        qt = False
    else:
        
        print("Attempting to Home Z2")
        z2_dev = device_list[c.z2port]
        z2_dev.generic_command(CommandCode.SET_HOME_SPEED, 1100)
        # z2_dev.generic_command_with_unit(CommandCode.SET_HOME_SPEED,
        #                                  15,Units.VELOCITY_MILLIMETRES_PER_SECOND)
        z2_dev.home()
        z2_dev.generic_command(CommandCode.SET_TARGET_SPEED,1100)
        #z2_dev.generic_command_with_unit(CommandCode.SET_TARGET_SPEED,
        #                                 15,Units.VELOCITY_MILLIMETRES_PER_SECOND)
        print("Finished Homing Z2")
        
        print("Attempting to Home Z1")
        z1_dev = device_list[c.z1port]
        z1_dev.generic_command(CommandCode.SET_HOME_SPEED, 3300)
        #z1_dev.generic_command_with_unit(CommandCode.SET_HOME_SPEED,5,Units.VELOCITY_MILLIMETRES_PER_SECOND)
        z1_dev.home()
        print("Finished Homing Z1")
        z1_dev.generic_command(CommandCode.SET_TARGET_SPEED, 3300)
        #z1_dev.generic_command_with_unit(CommandCode.SET_TARGET_SPEED,5,Units.VELOCITY_MILLIMETRES_PER_SECOND)
        
        print("Attempting to Home Y1")
        y1_dev = device_list[c.y1port]
        y1_dev.generic_command_with_units(CommandCode.SET_HOME_SPEED, 20, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        y1_dev.home()
        print("Finished Homing Y1")
        y1_dev.generic_command_with_units(CommandCode.SET_TARGET_SPEED, 20, Units.VELOCITY_MILLIMETRES_PER_SECOND)

        print("Attempting to Home Y2")
        y2_dev = device_list[c.y2port]
        y2_dev.generic_command_with_units(CommandCode.SET_HOME_SPEED, 20, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        y2_dev.home()
        print("Finished Homing Y2")
        y2_dev.generic_command_with_units(CommandCode.SET_TARGET_SPEED, 20, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        

        # Assign devices
        print("Attempting to Home X")      
        x_dev = device_list[c.xport]
        #x_dev.generic_command(CommandCode.SET_HOME_SPEED, 7000)
        x_dev.home()
        x_dev.generic_command(CommandCode.SET_HOME_SPEED, 2000)
        x_dev.generic_command(CommandCode.SET_TARGET_SPEED, round(c.x_spd / c.xv_conv))
        x_dev.generic_command(CommandCode.SET_MICROSTEP_RESOLUTION, 64)
        print("Finished Homing X")        
except Exception:

    # if False (connection fails):
    print("*********************************************************************************")
    print("       There is no Zaber connection or the Zaber connection has failed.")
    print("*********************************************************************************")
    window['-CON_STATUS-'].update('Connection Failed')
    
    qt = False

#%% Select Run Style
# ==========================================================================================================

if qt:

    window['-NEW-'].update(disabled=True)
    window['-FLIP-'].update(disabled=True)
    window['-SAME-'].update(disabled=True)

    while True:
        event, values = window.read(timeout=50)
        if event == '-NEW-' or keyboard.is_pressed('Enter'):
            set_new = True
            break
        elif event == '-SAME-' or keyboard.is_pressed('s'):
            set_new = False
            flip = False
            repeat = True
            break
        elif event == '-FLIP-' or keyboard.is_pressed('f'):
            set_new = False
            flip = True
            repeat = True
            break
        elif event in (sg.WIN_CLOSED, 'Quit'):
            qt = False
            break

    window['-NEW-'].update(disabled=True)
    window['-FLIP-'].update(disabled=True)
    window['-SAME-'].update(disabled=True)

#%% Get Basic info - (if setup = repeat)
# ==========================================================================================================

if qt and repeat:

    # set run_last to true
    run_last = True

    # find the most recent .txt file in the output folder
    txt_files = glob.glob(os.path.join(path, '*.txt'))
    latest_file = max(txt_files, key=os.path.getmtime)

    # extract tube from the filename (assumes "YYYY-MM-DD-HH-MM-tube.txt")
    basename = os.path.basename(latest_file)
    tube = os.path.splitext(basename)[0].split('-', 5)[-1]

    # initialize holders
    tieloc = None
    depth  = None
    note   = None

    # parse the header lines for the values
    with open(latest_file, 'r') as fh:
        for line in fh:
            if line.startswith('Note:'):
                note = line.split('Note:')[1].split(',')[0].strip()
            elif 'Index Mark Relative Depth:' in line:
                tieloc = line.split('Index Mark Relative Depth:')[1].split(',')[0].strip()
            elif '(first) Index Mark Absolute Depth:' in line:
                depth = line.split('(first) Index Mark Absolute Depth:')[1].split(',')[0].strip()
    
    # pull out the last run AC or DC
    splitline = line.split(',')
    if splitline[3] == '--':
        run_AC = False
        run_DC = True
    else:
        run_AC = True
        run_DC = False

    # if flip is true, flip the run style
    if flip:
        if run_AC:
            AC_run = False
            DC_run = True
        else:
            AC_run = True
            DC_run = False

    # if run_DC is true, set the radio button to DC (should be AC by default)
    if run_DC:
        window['-DC_SELECT-'].update(True)

    # convert to numbers if desired
    try:
        tieloc = float(tieloc)
    except:
        pass
    try:
        depth = float(depth)
    except:
        pass

    # update GUI with loaded values
    window['tube'].update(tube)
    window['tieloc'].update(tieloc)
    window['depth'].update(depth)
    window['note'].update(note)


#%% Get Basic info - (if setup = new)
# ==========================================================================================================

# Get Tube:
if qt and set_new:
	[tube, qt] = getinput(window,'-SUBMIT_TUBE-','tube','TUBE')

# Get Index Mark (relative):
if qt and set_new:
	[tieloc, qt] = getinput(window,'-SUBMIT_TIELOC-','tieloc','INDEX MARK (RELATIVE)')

# Get Index Mark (depth):
if qt and set_new:
	[depth, qt] = getinput(window,'-SUBMIT_DEPTH-','depth','INDEX MARK (DEPTH)')

# Get Note:
if qt and set_new:
	[note, qt] = getinput(window,'-SUBMIT_NOTE-','note','NOTE')

# Check setup (repeat or new)
if qt and set_new:
    window['-SETUP_STATUS-'].update('Select AC, DC, or Both')
    window['-LAST_CONT-'].update(disabled=False)
    # loop until user enters to run last or not
    while True:
        # read
        event, values = window.read(timeout=50)
        # check if quit
        if event == '-ACDC_CONT-' or keyboard.is_pressed('Enter'):
            if values['-AC_SELECT-'] == True:
                AC_run = True
                DC_run = False
            else:
                AC_run = False
                DC_run = True
            break
        elif event in (sg.WIN_CLOSED, 'Quit'):
                qt = False
                break
    window['-ACDC_CONT-'].update(disabled=True)
    time.sleep(0.25)

# Check setup (repeat or new)
if qt and set_new:
    window['-SETUP_STATUS-'].update('Decide if we want to run last or new values')
    window['-LAST_CONT-'].update(disabled=False)
    # loop until user enters to run last or not
    while True:
        # read
        event, values = window.read(timeout=50)
        # check if quit
        if event == '-LAST_CONT-' or keyboard.is_pressed('Enter'):
            if values['new'] == True:
                run_last = False
            else:
                run_last = True
            break
        elif event in (sg.WIN_CLOSED, 'Quit'):
                qt = False
                break
    window['-LAST_CONT-'].update(disabled=True)
    time.sleep(0.25)

#%% get filename
#===================================================================================

if qt:

    today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    filename = today+'-'+tube+'.txt'
    # check if file already exists, if so modify name
    if any(ext in filename for ext in cur_files):
        window['-FILE_STATUS-'].update('*** FILE ALREADY EXISTS - MODIFYING ***')
        filename = today+'-'+tube+'-TRY2.txt'
    window['file'].update(filename)
    f_path = r"/Users/agu/Desktop/run_outputs/" +fldr+'/'+filename
    file_object = open(f_path,'a')


#%% Connect to SMU
# ==========================================================================================================

if qt and DC_run:
    try:
    
        rm = pyvisa.ResourceManager()
        rm.list_resources()
        keithley = rm.open_resource('USB0::0x05E6::0x2470::04567382::INSTR')
        
        keithley.write("*rst; status:preset; *cls")
        keithley.write(":SOUR:FUNC VOLT")
        vol_str = ":SOUR:VOLT " + str(int(c.voltage))
        keithley.write(vol_str)
        keithley.write(":SOUR:VOLT:ILIMIT 0.001")
        keithley.write(":SENSE:FUNC  \"CURR\"")
        keithley.write(":ROUT:TERM FRONT")
        keithley.write(":SOUR:VOLT:READ:BACK OFF") #off gets 50 S/s, on get 30S/s, std 2.8 on, 3.4 off
        keithley.write(":SENS:CURR:AZERO OFF") #off gets 50 S/s, on gets 15 S/s, std improves from 3 to 2.1  
        keithley.write(":SENSE:CURR:NPLC 1") #1 gives std 3, 0.1 gives .46 
        #keithley.write(":SENS:CURR:UNIT OHM")
        #keithley.write(":FORM:DATA REAL") # attempt at binary, don't use
        
        # turn autorange on/off
        if False: # on
            wait_after = 10 # wait time after run, in s
            extra_cycles = 450 # extra aquisitions beyodn calculated 
            keithley.write(":CURR:RANG:AUTO On") #off gets 50 S/s, on gets 30 S/s, std improves from 3 to 2.5
        else: # off
            wait_after = 1 # wait time after run, in s
            extra_cycles = 120 # extra aquisitions beyond calculated
            keithley.write(":CURR:RANG:AUTO OFF") #off gets 50 S/s, on gets 30 S/s, std improves from 3 to 2.5
            lim_str = ":CURR:RANG:UPP " + str(c.cur_range)
            keithley.write(lim_str)
            
        print("*********************************************************************************")
        print("                           Connection to SMU Successful                          ")
        print("*********************************************************************************")
        window['-SMU_STATUS-'].update('Connection Successful')
    
    except:
        print("*********************************************************************************")
        print("                        Error : Failed to Connect to SMU                         ")
        print("*********************************************************************************")
        window['-SMU_STATUS-'].update('Connection Failed')
        qt = 0; 
    
#%% Connect to LCR
# ==========================================================================================================

if qt and AC_run:
    try:
        lcr = rm.open_resource("USB0::0x0957::0x0909::MY46100776::INSTR")
        lcr.write("*rst; *cls")
        lcr.write("VOLT 2.000")
        lcr.write("SOUR:CURR MAX")
        # lcr.write("CURR .000001")
        lcr.write("CORR:OPEN:STAT OFF")
        lcr.write("CORR:SHOR:STAT OFF")
        lcr.write("CORR:LOAD:STAT OFF")
        lcr.write("FUNC:IMP GB")
        lcr.write("APER SHOR")
        lcr.write("FREQ 100000")
        lcr.write("FROM ASC")
        lcr.write("TRIG:SOUR BUS")
        lcr.write("INIT:CONT OFF")
        lcr.write("INIT:IMM")
        
        print("*********************************************************************************")
        print("                           Connection to LCR Successful                          ")
        print("*********************************************************************************")
        window['-LCR_STATUS-'].update('Connection Successful')
    except:
        print("*********************************************************************************")
        print("                        Error : Failed to Connect to LCR                         ")
        print("*********************************************************************************")
        qt = 0; 
        window['-LCR_STATUS-'].update('Connection Failed')


#%% Setup - find the size of the ice sample
# ==========================================================================================================

if qt:

    # if run_last is true, load the values from the last run
    if run_last:
        yl,yr,xmin,xmax,xtie,xtie2,xtie3,zup = loadlast()

        # update values on GUI
        window['-Z_SET-'].update(zup)
        window['-Y0_SET-'].update(yl)
        window['-Y1_SET-'].update(yr)
        window['-X0_SET-'].update(xmin)
        window['-X1_SET-'].update(xmax)
        window['-XTIE_SET-'].update(xtie)
        window['-XTIE2_SET-'].update(xtie2)
        window['-XTIE3_SET-'].update(xtie3)

    # else, get new ice position information
    else:

        # Unlock Move Buttons
        window['-Z_UP-'].update(disabled=False)
        window['-Z_DOWN-'].update(disabled=False)
        window['-X_UP-'].update(disabled=False)
        window['-X_DOWN-'].update(disabled=False)
        window['-Y_UP-'].update(disabled=False)
        window['-Y_DOWN-'].update(disabled=False)
        window['Submit'].update(disabled=False)

        # update status
        window['-SETUP_STATUS-'].update('*** SETUP STARTED ***')

        # Turn laser on
        ul.d_out(board_num, port.type, 128)

        # set motors for setup runs
        if DC_run:
            y_setup = y1_dev
            z_setup = z1_dev
        else:
            #y_setup = y2_dev
            #z_setup = z2_dev
            y_setup = y1_dev
            z_setup = z1_dev
            
        # move y-axis so there are no length issues
        y2_dev.move_absolute(80,Units.LENGTH_MILLIMETRES)
        
        # bottom left (X0Y0)
        if qt:
            [xmin,yl,qt] = setup_movxy(window, x_dev,y1_dev,z_setup, qt, '-X0Y0_SETUP-', '-X0_SET-','-Y0_SET-', 'X0Y0')
        if qt:
            [xtie, qt] = setup_mov(window, x_dev, y_setup, z_setup, x_dev, qt, '-XTIE_SETUP-', '-XTIE_SET-', 'X Tiepoint', c.x_conv) 
        
        #toggle tiepoints 2 and 3
        if False:
            if qt:
                [xtie2, qt] = setup_mov(window, x_dev, y_setup, z_setup, x_dev, qt, '-XTIE2_SETUP-', '-XTIE2_SET-', 'X Tiepoint 2', c.x_conv) 
            if qt:
                [xtie3, qt] = setup_mov(window, x_dev, y_setup, z_setup, x_dev, qt, '-XTIE3_SETUP-', '-XTIE3_SET-', 'X Tiepoint 3', c.x_conv) 
        else:
            xtie2 = 0
            xtie3 = 0
        
        # top right (X1Y1)
        if qt:
            [xmax,yr,qt] = setup_movxy(window, x_dev,y1_dev,z_setup, qt, '-X1Y1_SETUP-', '-X1_SET-','-Y1_SET-', 'X1Y1')
            
        # set up z axis 
        if qt:
            #[zup, qt] = setup_mov(window, x_dev, y_setup, z_setup, z_setup, qt, '-Z_SETUP-', '-Z_SET-', 'Z Up Height', 1)
            zup=71
    
        if qt:
            z1_dev.home()
            z2_dev.home()  
            
        # save values
        savelast(yl,yr,xmin,xmax,xtie,xtie2,xtie3,zup)
        
        # home z axis
        if qt:
            z1_dev.home()
            z2_dev.home()

        # Turn off laser
        #mcc_digital(dio_device, port_to_write, 0)
        ul.d_out(board_num, port.type, 0)

        # Lock Move Buttons
        window['-Z_UP-'].update(disabled=True)
        window['-Z_DOWN-'].update(disabled=True)
        window['-X_UP-'].update(disabled=True)
        window['-X_DOWN-'].update(disabled=True)
        window['-Y_UP-'].update(disabled=True)
        window['-Y_DOWN-'].update(disabled=True)
        window['Submit'].update(disabled=True)

# update status
window['-SETUP_STATUS-'].update('Setup Complete')
event, values = window.read(timeout=15)

# Move to xmax positions
if qt:
    if AC_run:
        x_dev.move_absolute(xmax + (c.acdc_offset - c.laser_offset)/c.x_conv)
    else:
        x_dev.move_absolute(xmax - (c.laser_offset)/c.x_conv)

#%% Calculate y-axis section and count threxhold
#==========================================================================================================

# First up is to decide which y-axis dimensions to use.
if qt:
    
    if DC_run:
        edgespace = c.dc_edgespace
    else:
        edgespace = c.ac_edgespace
        
    ydim = np.array([yl+edgespace])
    
    if yl != yr:
        while ydim[-1] < yr-edgespace:
            ydim = np.append(ydim,ydim[-1]+round(c.y_space))
        ydim[-1] = yr-edgespace
        
        
    # Turn on digital output to provide power to button
    ul.d_out(board_num, port.type, 1)
        
    # calculate count threshold (to know when the run is complete)
    cnt_threshold = round(c.cycles_per_rotation / c.mm_per_rotation / c.write_res)
    window['-WRITE_RES-'].update("Writing Every "+str(cnt_threshold)+" Cycles")
    
    
#calculate total number of counts
if qt:
    countmax = np.floor((xmax-xmin) * c.x_conv * c.cycles_per_rotation / c.mm_per_rotation)

#%% Write File Header
# ==========================================================================================================

if qt:
    file_object.write('ECM File Output,,,,,'+'\n')
    file_object.write('Filename (includes date): '+filename+ ',,,,,\n' )
    file_object.write('AC Collect Speed: '+str(c.col_spd_AC)+ ',,,,,\n')
    file_object.write('DC Collect Speed: '+str(c.col_spd_DC)+ ',,,,,\n')
    file_object.write('DC Voltage: '+str(c.voltage)+ ',,,,,\n')
    file_object.write('Note: '+str(note)+ ',,,,,\n')
    file_object.write('mm per encode step: '+str(c.mm_per_step)+ ',,,,,\n')
    file_object.write('Number of Expected tracks: '+str(len(ydim)+1)+ ',,,,,\n')
    file_object.write('ACDC offset: '+str(c.acdc_offset)+ ',,,,,\n')
    file_object.write('Laser offset: '+str(c.laser_offset)+ ',,,,,\n')
    file_object.write('Y Left: '+str(yl)+ ',,,,,\n')
    file_object.write('Y Right: '+str(yr)+ ',,,,,\n')
    file_object.write('AC edgespace '+str(c.ac_edgespace)+ ',,,,,\n')
    file_object.write('DC edgespace '+str(c.dc_edgespace)+ ',,,,,\n')
    file_object.write('Index Mark (raw - not laser corrected): '+str(xtie*c.x_conv)+ ',,,,,\n')
    file_object.write('Index Mark Relative Depth: '+str(tieloc)+ ',,,,,\n')
    file_object.write('Index Mark 2 Relative Depth: '+str(xtie2 * c.x_conv)+',,,,,\n')
    file_object.write('Index Mark 3 Relative Depth: '+str(xtie3 * c.x_conv)+',,,,,\n')
    file_object.write('(first) Index Mark Absolute Depth: '+str(depth)+ ',,,,,\n')
    file_object.write('X min Position (raw - not laser corrected): '+str(xmin*c.x_conv)+',,,,,\n')
    file_object.write('X max Position (raw - not laser corrected): '+str(xmax*c.x_conv)+',,,,,\n')
    file_object.write('Y_dimension(mm),X_dimension(mm),Button,AC,DC,True_depth(m)\n')

#%% Setup the Plot

# make colormap
cmap = matplotlib.colormaps.get_cmap('coolwarm')

#%% Collect DC Data
# ==========================================================================================================

# Wait for button to start DC run
if qt and DC_run:
    
    # update window
    window['-START_DC-'].update(disabled=False)
    window['-ACDC_STATUS-'].update('Waiting to start DC Run')
    
    while True:
        
        # read to wait for start DC (or quit)
        event, values = window.read(timeout=50)
        
        if event == '-START_DC-' or keyboard.is_pressed('Enter'):
            
            # move AC y-axis to ensure no cable length issues
            y2_dev.move_absolute(80,Units.LENGTH_MILLIMETRES)
            
            #EVENTUALlY, RUN FUNCTION WILL LIVE HERE
            window['-START_DC-'].update(disabled=True)
            window['-ACDC_STATUS-'].update('Collecting DC Data')
            
            # calculate how many measurements the SMU needs to make
            SMU_num = round( (xmax-xmin) * c.x_conv / c.col_spd_DC / c.SMU_sample_time + extra_cycles)
            SMU_num_string = ":TRIG:LOAD \"SimpleLoop\", "+str(SMU_num)+", 0"
            SMU_query_string = ":TRAC:DATA? 1,"+str(SMU_num)+", \"defbuffer1\", READ, SOUR, REL"
            
            #make arrays
            timer = np.zeros([int(countmax),int(len(ydim))])
            timer_relative = np.zeros([int(countmax),int(len(ydim))])
            button = np.zeros([int(countmax),int(len(ydim))])
            c_smu = np.empty([SMU_num,int(len(ydim))])
            c_smu.fill(np.NaN)
            v_smu = np.empty([SMU_num,int(len(ydim))])
            v_smu.fill(np.NaN)
            t_smu = np.empty([SMU_num,int(len(ydim))])
            t_smu.fill(np.NaN)
            
            # loop through all y dimensions for the run
            for y in np.arange(0,len(ydim)):
                
                # update status
                window['-READ_STATUS-'].update('Reading Row at y = '+str(round(ydim[y],3))+' mm')
                event, values = window.read(timeout=15)
                
                # go to starting position
                y1_dev.move_absolute(ydim[y]+c.dc_ylaseroffset, Units.LENGTH_MILLIMETRES)
                x_dev.move_absolute(xmax- (c.laser_offset)/c.x_conv)
                if zup > 0:
                    z1_dev.move_absolute(zup, Units.LENGTH_MILLIMETRES)
                else:
                    print("ERROR, Z IS SET TOO LOW")
                
                # set counter to 0, set prior to true
                cnt = 0
                
                # set current encoder state
                if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[0], ai_range))) > 1:
                    if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                        state = 3;
                    else:
                        state = 2;
                else:
                    if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                        state = 1;
                    else:
                        state = 0;
                
                #get x starting location
                xstart = x_dev.get_position(unit=Units.NATIVE) #SLOW - 2cm/s max
                
                # start moving
                x_dev.move_velocity(- c.col_spd_DC /c.xv_conv)
                
                # Tell SMU to record data
                #keithley.write(":TRIG:LOAD \"SimpleLoop\", 100, 0")
                keithley.write(SMU_num_string)
                keithley.write(":OUTP ON")
                keithley.write(":INIT")
                keithley.write("*WAI")
                keithley.write(":OUTP OFF")
                
                # set a timer zero. This seems to happen so fast it's actually not 100%
                # neccissary
                timer_zero = time.time()
            
                while cnt < countmax:
                    
                    #cntprior=cnt
                    
                    stateprior = state;
                    
                    # here we check to see if the encoder sees movement. Start
                    # by getting the current state of the encoder (2 channels,
                    # each at high or low voltage)
                    if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[0], ai_range))) > 1:
                        if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                            state = 3
                        else:
                            state = 2
                    else:
                        if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                            state = 1
                        else:
                            state = 0
                                        
                    # When we have reached (1/20) rotations, then we write to the file.
                    # 1 should be every 1 mm
                    if state != stateprior:
                        
                        cnt += 1
                        #print(str(cnt))
                        
                        # check button
                        button[cnt-1,y] = abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.button_channel, ai_range))) < 1

                        
                        timer[cnt-1,y] = time.time()
                        
                # check for quit
                event, values = window.read(timeout=1) 
                if event in (sg.WIN_CLOSED, 'Quit'):
                    qt = False
                    break
                
                # Stop movement, lift electrodes
                x_dev.stop()
                time.sleep(0.5)
                try:
                    z1_dev.move_relative(-30,Units.LENGTH_MILLIMETRES)
                except:
                    z1_dev.home() 
                
                # pause in case SMU is still recording
                time.sleep(wait_after)

                #read from smu and seperate values
                vals = keithley.query(SMU_query_string)
                vs = vals.split(',')
                for i in range(0,SMU_num,1):
                    c_smu[i,y] = float(vs[i*3])
                    v_smu[i,y] = float(vs[i*3+1])
                    t_smu[i,y] = float(vs[i*3+2])
                
                # stitch times together        
                # first step - turn encoder time into relative time
                timer_relative[:,y] = timer[:,y] - timer_zero
                ind = t_smu[:,y] <= np.max(timer_relative[:,y])
                if y==0:
                    t_corr_smu = np.empty([sum(ind==True),int(len(ydim))])
                    c_corr_smu = np.empty([sum(ind==True),int(len(ydim))])
                    v_corr_smu = np.empty([sum(ind==True),int(len(ydim))])
                else:
                    if sum(ind==True) > len(t_corr_smu):
                        addition = np.empty([sum(ind==True)-len(t_corr_smu),int(len(ydim))])
                        addition.fill(np.NaN)
                        t_corr_smu = np.append(t_corr_smu,addition)
                        c_corr_smu = np.append(c_corr_smu,addition)
                        v_corr_smu = np.append(v_corr_smu,addition)
                        t_corr_smu= t_corr_smu.reshape([sum(ind==True),len(ydim)])
                        c_corr_smu = c_corr_smu.reshape([sum(ind==True),len(ydim)])
                        v_corr_smu = v_corr_smu.reshape([sum(ind==True),len(ydim)])
                t_corr_smu[0:sum(ind==True),y] = t_smu[ind,y]
                c_corr_smu[0:sum(ind==True),y] = c_smu[ind,y]
                v_corr_smu[0:sum(ind==True),y] = v_smu[ind,y]
                #idx = x_smu!=np.NaN
                
                # make arrays
                if y==0:
                    button_smu = np.empty([int(len(t_corr_smu)),int(len(ydim))])
                    button_smu.fill(np.NaN)
                    x_smu = np.empty([int(len(t_corr_smu)),int(len(ydim))])
                    x_smu.fill(np.NaN)
                else:
                    if sum(ind==True) > len(button_smu):
                        addition = np.empty([sum(ind==True)-len(button_smu),int(len(ydim))])
                        addition.fill(np.NaN)
                        button_smu = np.append(button_smu,addition)
                        x_smu = np.append(x_smu,addition)
                        button_smu = button_smu.reshape([sum(ind==True),len(ydim)])
                        x_smu =  x_smu.reshape([sum(ind==True),len(ydim)])
                
                for i in np.arange(0,len(t_corr_smu)):
                    x_smu[i,y] = np.interp(t_corr_smu[i,y],timer_relative[:,y],np.arange(0,cnt*c.mm_per_step,c.mm_per_step))
                    button_smu[i,y] = round(np.interp(t_corr_smu[i,y],timer_relative[:,y],button[:,y]))
                
                for i in np.arange(0,len(t_corr_smu)-2):
                    try:
                        f_tieloc = float(tieloc)
                    except:
                        f_tieloc = 0
                        print("Error - Tiepoint depth not valid number")
                    true_depth = f_tieloc + (xmax-xtie)*c.x_conv/1000 - x_smu[i,y]/1000
                    true_depth = 'na'
                    file_object.write(str(round(ydim[y],3)) + ',' + str(x_smu[i,y]) + ',' + str(button_smu[i,y]) + ',' + '--,'+ str(c_corr_smu[i,y])+','+str(true_depth)+'\n')
                
                # Plot
                #plt.plot(x_smu[30:,y],c_corr_smu[30:,y],color=cmap(y/len(ydim)))
                #plt.draw()
                
                if y > 0:
                    delete_figure(tkcanvas)
                fig = makeplot(x_smu,c_corr_smu,ydim,'DC')
                tkcanvas = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                plt.close(fig)
                
                #get x finishing location
                xend = x_dev.get_position(unit=Units.NATIVE)
                if abs((xstart-xend) - (xmax-xmin)) > 0.01 * (xmax-xmin):
                    print("*********************************************************************************")
                    print("    WARNING - THE ENCODER DOES NOT SEEM TO BE KEEPING UP WITH DEVICE MOVEMENT    ")
                    print("Run should be "+str((xmax-xmin)*c.x_conv)+" mm, but was actually  "+str((xstart-xend)*c.x_conv)+" mm")
                    print("*********************************************************************************")
                else:
                    print(" Endoder is within 1% of expected distance covered")

            # break out of loop to continue with program
            break
            
            
        elif event in (sg.WIN_CLOSED, 'Quit'):
            qt = False
            break
        
    if qt:
        print("Attempting to Home Z2")
        z2_dev.home()
        print("Finished Homing Z2")
        
        print("Attempting to Home Z1")
        z1_dev.home()
        print("Finished Homing Z1")
        
        # Assign devices
        print("Attempting to Home X")      
        x_dev.home()
        print("Finished Homing X")
        
        print("Attempting to Home Y1")
        y1_dev.home()
        print("Finished Homing Y1")
    
        print("Attempting to Home Y2")
        y2_dev.home()
        print("Finished Homing Y2")


if qt:
    # make summary plot
    if qt and DC_run:
        plt.figure(2)
        plt.clf()
        for y in range(0,len(ydim)):
            plt.plot(x_smu[30:,y],c_corr_smu[30:,y],color=cmap(y/len(ydim)))
        plt.title('DC Runs')
        plt.show()  

#%% Collect AC Data
# ==========================================================================================================

# Wait for button to start run
if qt and AC_run:
    window['-START_AC-'].update(disabled=False)
    window['-ACDC_STATUS-'].update('Waiting to start AC Run')
    
    while True:
    
        # read
        event, values = window.read(timeout=50)
        
        if event == '-START_AC-' or keyboard.is_pressed('Enter'):
            
            # move opposite axis so there are no length issues
            y1_dev.move_absolute(80,Units.LENGTH_MILLIMETRES)
            
            # Update GUI
            window['-START_AC-'].update(disabled=True)
            window['-ACDC_STATUS-'].update('Collecting AC Data')
            
            button_AC = np.empty([int(countmax),int(len(ydim))])
            button_AC.fill(np.NaN)
            
            G_AC = np.empty([int(countmax),int(len(ydim))])
            G_AC.fill(np.NaN)
            
            # loop through all y dimensions for the run
            for y in np.arange(0,len(ydim)):
                
                # update status
                window['-READ_STATUS-'].update('Reading Row at y = '+str(round(ydim[y],3))+' mm')
                event, values = window.read(timeout=15)
                
                # go to starting position
                y2_dev.move_absolute(ydim[y] + c.ac_ylaseroffset, Units.LENGTH_MILLIMETRES)
                x_dev.move_absolute(xmax + (c.acdc_offset - c.laser_offset)/c.x_conv)
                if zup+c.z_offset > 0:
                    z2_dev.move_absolute(zup+c.z_offset, Units.LENGTH_MILLIMETRES)
                else:
                    print("ERROR, Z IS SET TOO LOW")
                    
                # set counter to 0, set prior to true
                cnt = 0
                
                # set the array of measurements to blank
                G_raw = np.empty(5)
                G_raw.fill(np.NaN)
                raw_cnt = 0;
                
                # set current encoder state
                if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[0], ai_range))) > 1:
                    if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                        state = 3;
                    else:
                        state = 2;
                else:
                    if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                        state = 1;
                    else:
                        state = 0;
                        
                #get x starting location
                xstart = x_dev.get_position(unit=Units.NATIVE) #SLOW - 2cm/s max
                
                # start moving
                x_dev.move_velocity(- c.col_spd_AC /c.xv_conv)
                
                # loop until desired distance is reached
                while cnt < countmax:
                    
                    #cntprior=cnt
                    
                    # Every loop, we make a measurement
                    lcr.write("TRIG:IMM")
                    vals = lcr.query("FETC?")
                    vs = vals.split(',')
                    G_raw[raw_cnt] = vs[0]
                    raw_cnt += 1
                    
                    stateprior = state;
                    
                    # here we check to see if the encoder sees movement
                    if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[0], ai_range))) > 1:
                        if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                            state = 3
                        else:
                            state = 2
                    else:
                        if abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.encode_channel[1], ai_range))) > 1:
                            state = 1
                        else:
                            state = 0
                    
                    # When we have reached (1/20) rotations, then we check the
                    # button, average measurements, 
                    if state != stateprior:
                        
                        cnt += 1
                        #print(str(cnt))
                        
                        # check button
                        button_AC[cnt-1,y] = abs(ul.to_eng_units(0, ai_range, ul.a_in(board_num, c.button_channel, ai_range))) < 1

                        # save value
                        G_AC[cnt-1,y] = np.nanmean(G_raw)
                        
                        # re-empty c_raw vector (ready for next round)
                        G_raw.fill(np.NaN)
                        raw_cnt = 0;
                
                # Stop movement, lift electrodes
                x_dev.stop()
                time.sleep(0.5)
                try:
                    z2_dev.move_relative(-50,Units.LENGTH_MILLIMETRES)
                except:
                    z2_dev.home() 
            
                #get x finishing location
                xend = x_dev.get_position(unit=Units.NATIVE)
                if abs((xstart-xend) - (xmax-xmin)) > 0.01 * (xmax-xmin):
                    print("*********************************************************************************")
                    print("    WARNING - THE ENCODER DOES NOT SEEM TO BE KEEPING UP WITH DEVICE MOVEMENT    ")
                    print("Run should be "+str((xmax-xmin)*c.x_conv)+" mm, but was actually  "+str((xstart-xend)*c.x_conv)+" mm")
                    print("*********************************************************************************")
                else:
                    print(" Endoder is within 1% of expected distance covered")
                
                # write values to file
                for i in range(0,int(countmax)):
                    try:
                        f_tieloc = float(tieloc)
                    except:
                        f_tieloc = 0
                        print("Error - Tiepoint depth not valid number")
                    true_depth = f_tieloc + (xmax-xtie)/1000 - i *c.mm_per_step/1000
                    true_depth = 'na'
                    file_object.write(str(round(ydim[y],3)) + ',' + str(i * c.mm_per_step) + ',' + str(button_AC[i,y]) + ',' + str(G_AC[i,y])+',--,' +str(true_depth)+'\n')
                    
             
                # Plot
                #plt.plot(np.arange(0,countmax) * c.mm_per_step,G_AC[:,y],color=cmap(y/len(ydim)))
                #plt.draw()
                if y > 0:
                    delete_figure(tkcanvas)
                fig = makeplot(np.arange(0,countmax) * c.mm_per_step,G_AC,ydim,'AC')
                tkcanvas = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                
                # check for quit
                event, values = window.read(timeout=1) 
                if event in (sg.WIN_CLOSED, 'Quit'):
                    qt = False
                    break
                
            # # add legend
            # if qt:
            #     plt.legend(np.round(ydim),title='Distance accross core:')
            #     plt.draw()
                
            # break out of loop to continue with code
            break
            
        elif event in (sg.WIN_CLOSED, 'Quit'):
            qt = False
            break     
    
    if qt:
        print("Attempting to Home Z2")
        z2_dev.home()
        print("Finished Homing Z2")
        
        print("Attempting to Home Z1")
        z1_dev.home()
        print("Finished Homing Z1")
        
        # Assign devices
        print("Attempting to Home X")      
        x_dev.home()
        print("Finished Homing X")
        
        print("Attempting to Home Y1")
        y1_dev.home()
        print("Finished Homing Y1")
    
        print("Attempting to Home Y2")
        y2_dev.home()
        print("Finished Homing Y2")

if qt:
    # make summary plot
    if qt and AC_run:
        plt.figure(3)
        plt.clf()
        for y in range(0,len(ydim)):
            plt.plot(range(0,int(countmax)),G_AC[:,y],color=cmap(y/len(ydim)))
        plt.title('AC Runs')
        plt.show()        

# update status
window['-READ_STATUS-'].update('Done Reading')
        
# Turn button off
#mcc_digital(dio_device, port_to_write, 0)
ul.d_out(board_num, port.type, 0)

#%% End Session
# ==========================================================================================================


# close the window - waiting for quit
while True:
    event, values = window.read(timeout=15)
    if event in (sg.WIN_CLOSED, 'Quit'):
        break
window.close()

# close file
try:
    file_object.close()
except:
    print("Failed to close file (may have quit before opening)")

#close the connection (essential to prevent error on next run)
try:
    Connection.close(connection)
except:
    print("Failed to close Zaber connection (may have quit before connecting")
    
# close the 
try:
    rm.close()
except:
    print("Failed to close SMU/LCR connection (may have quit before connecting")

# print ending information
print("*********************************************************************************")
print("                                      Session Over                               ")
print("*********************************************************************************")


# ==========================================================================================================
# ==========================================================================================================
# ==========================================================================================================



