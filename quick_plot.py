#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 14:21:13 2024

Liam Kirkpatrick
Script to rapidly plot ECM scripts from ECM computer

Inputs:
    filename
Outputs:
    plot of data from file, both conductivity curves and top down.
    
NOTE: MUST UPDATE PATH TO DATA AND FIGURES BEFORE RUNNING

@author: Liam
"""


#%% Import neccisary packages

import numpy as np
import pandas as pd

import glob
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


#%% User Imputs!!!
# update on ecm computer. Needs to be updated each day, to make sure you're
# pointing to the correct folder (will change each day)

# path to data
# path to the folder where the datafile in question is stored
path_to_data = '../../rapid_plotting/2023-08-23'

# path to figures
# path to the folder where figures made by this program will be stored
path_to_figures = '../../rapid_plotting/figures'

# header length in data file (should be constant unless master script is changed)
h=18

#%% Get filenamename

# true/false toggle allows us to manually set the title without having to 
# input anything
if True:

    filename = input('Input filename to plot (or type \'last\' for most recent file: ')
    
    # if user inputs last, get filename of most recently created file in the path
    if filename == 'last' or filename == 'Last' or filename == 'LAST':
        
        # get list of all ifles matching ECM filename format in folder
        flist = glob.glob(path_to_data+'/202*-*.txt')
        #flist = [f for f in listdir('../'+path[i]) if f[0] != "."] 
    
        # get most recent file on list
        fname_withpath = max(flist, key=os.path.getctime)
        filename = os.path.basename(fname_withpath)
        
    # confirm to user
    print("You have selected "+filename)

else:
    filename = '2023-08-23-16-11-DIC1-228D.txt'

#%% Open file, read in data

# read in metadata
commacnt = -6
with open(path_to_data+'/'+filename, 'r') as f:
    
    cnt = 0
    
    for line in f:
        
        if 'Index Mark Relative Depth' in line:
            index_mark = float(line[len('Index Mark Relative Depth: '):-6])
        if 'X max Position (raw - not laser corrected): ' in line:
            xmax = float(line[len('X max Position (raw - not laser corrected): '):-6])   
        if '(first) Index Mark Absolute Depth: ' in line:
            top_depth = float(line[len('(first) Index Mark Absolute Depth: '):-6])
            
    # check if AC or DC on the last line of the file
    splitline = line.split(',')
    if splitline[3] == '--':
        AC = 0
        DC = 1
    else:
        AC = 1
        DC = 0
        
# read in file to pandas dataframe
raw = pd.read_csv(path_to_data+'/'+filename,header=h)

# AC or DC logistics. Definitly a better way to do this but I'm just copying
# from old code.
if AC==1:
    meas_oppstr = 'DC'
    meas_str = 'AC'
if DC==1:
    meas_oppstr = 'AC'
    meas_str = 'DC'

# pull out data
data_array_temp = raw[raw[meas_oppstr]=='--']
data_meas = data_array_temp[meas_str].to_numpy()
data_x = data_array_temp['X_dimension(mm)'].to_numpy()
data_y = data_array_temp['Y_dimension(mm)'].to_numpy()
data_button = data_array_temp['Button']
data_meas = data_meas.astype(float)

# convert x to depth
data_depth = top_depth + (xmax  - index_mark - data_x) / 1000

# assign y vector
y_vec = np.unique(data_y)

#%% Figure 1 - top down view

fig,axs = plt.subplots(1,2,figsize = (14,11))

print("Started plotting - allow up to 30 secconds")

# compute ranges used in graph
pltmin = np.percentile(data_meas,5)
pltmax = np.percentile(data_meas,95)
dmax = max(data_depth)
dmin = min(data_depth)
ystep = y_vec[1] - y_vec[0]

# set up colors
cmap = matplotlib.colormaps.get_cmap('coolwarm')
my_cmap = matplotlib.colormaps['magma']
rescale = lambda k: (k-pltmin) /  (pltmax-pltmin)

# Axis lables and  limits
axs[1].set_title('Conductivity Curves')
axs[0].set_title('Top View')
axs[0].set_ylabel('Depth (m)')
axs[0].set_xlabel('Distance Accross Core (mm)')
axs[1].set_ylabel('Depth (m)')
axs[1].set_xlabel('Conductivity (amps)')

# set axis limits
#axs[1].set_xlim([0.8*10**(-8), 2.3*10**(-8)])
axs[1].set_ylim([dmin, dmax])
axs[0].set_ylim([dmin, dmax])
axs[0].set_xlim([min(y_vec)-5,max(y_vec)+5])

# overall name
fig.suptitle(filename, fontsize=20)



# set legend
for i in range(len(y_vec)):
    ind = data_y==y_vec[i]
    plt.plot(data_meas[ind],data_depth[ind],color='w')
leg = axs[1].legend(y_vec,title='Distance accross core:',loc='lower left')
for k in range(len(leg.legend_handles)):
    leg.legend_handles[k].set_color(cmap(k/len(y_vec)))


for j in range(len(y_vec)):
    meas = data_meas[data_y==y_vec[j]]
    depth = data_depth[data_y==y_vec[j]]
    button = data_button[data_y==y_vec[j]]
        
    for i in range(len(meas)-1):
        
        axs[0].add_patch(Rectangle((y_vec[j]-ystep/2+0.3,depth[i]),ystep-0.6,depth[i+1]-depth[i],facecolor=my_cmap(rescale(meas[i]))))
        
        # if button[i] == 1:
        #     axs[0].add_patch(Rectangle((y_vec[j]-4.7,depth[i]),9.4,depth[i+1]-depth[i],facecolor='w'))    
        # else:
        #     axs[0].add_patch(Rectangle((y_vec[j]-4.7,depth[i]),9.4,depth[i+1]-depth[i],facecolor=my_cmap(rescale(meas[i]))))    
                    
        axs[1].plot([meas[i],meas[i+1]],[depth[i],depth[i+1]],color=cmap(j/len(y_vec)))
        
# invert y axis, so depth increases down
axs[1].invert_yaxis()
axs[0].invert_yaxis()

# invert x axis on top-down plot, so it matches the way data is read in 
# (right side first, with y=0 on right)
axs[0].invert_xaxis()



    
fig.savefig(path_to_figures+'/curves_'+filename+'.png', 
            transparent = False,  
            facecolor = 'white',
            dpi=450
            )


print("Complete. Figure saved to \'figures\' folder")

