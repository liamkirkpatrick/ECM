# Liam Kirkpatrick
# ECM System
# This file stores all the constants for the program
# Ideally, this will be the only file to tweak before a run

#%% Import packages

import numpy as np

#%% Choices in how the system runs

# Write Resolution (mm)
write_res = 1

# Spacing between tracks (on y-axis)
y_space = 8.5

# data collection speed (mm/s)
col_spd_DC = 25
col_spd_AC = 10

# axis default speeds (mm/s)
x_spd = 50
y_spd = 15
z_spd = 15

#%% Spacing Variables

#AC/DC offset, new electrodes, measured at ICF (best measurement))
#acdc_offset = 239.5
# old electrodes
acdc_offset = 305

# DC to laser offset, in mm, measured at ICF
laser_offset = -10         

# temp, w/ broken motor
z_offset = 0 

# edge_to_electrode offset, AC, mm
ac_edgespace = 16

# edge_to_electrode offset, DC, mm
dc_edgespace = 10

# Laser center to electrode center (horizontal), AC, mm
ac_ylaseroffset = 0

# Laser center to electrode center (horizontal), DC, mm
dc_ylaseroffset = 0

#%% SMU Variables

voltage = 1000
#cur_range = 0.0000001
cur_range = 0.00005
if voltage > 200:
    if cur_range < 0.0001:
        print('WARNING - MEASURE RANGE MAY BE TOO LOW')

SMU_sample_time = 0.0169444
#SMU_sample_time = 0.0172

#%% plot variables
pltmin = 0
pltmax = 8 * 10**(-6)
ACpltmin = 0
ACpltmax = 0.00001/100

#%% Motor control constants

# Ball screw
mm_per_rotation = 20                    # mm per rotation of screw drive

# motor speed/location
x_conv = 0.028125/360 * mm_per_rotation # convert x native units to mm
y_conv = 0.00049609374                  # convert y native units to mm
z2_conv = 0.09921875 * 10**(-3)         # convert z1 native units to mm
z1_conv = 0.49609375 * 10**(-3)         # convert z2 native units to mm
xv_conv = x_conv * 9.375                # convert x native units to mm/s

# motor ports
xport = 4
z1port = 3
y1port = 0
y2port = 1 
z2port = 2
# xport = 0
# z1port = 2
# y1port = 1
# y2port = 3
# z2port = 4


# encoder
change_per_cycle = 4
cycles_per_rotation = 20 * change_per_cycle # encoder resolution, cycles per rotation
mm_per_step = mm_per_rotation / cycles_per_rotation

# AC/DC offset
#acdc_offset = 332           # AC/DC electrode x-axis offset, in mm, old electrode
#acdc_offset = 267           # AC/DC offset, w/ new electrodes



#%% MCC DAQ

button_channel = 3

# Establish relevant channels for encoder
encode_channel = np.array([4, 5])

#%% SMU constants



#%% Other Constants

