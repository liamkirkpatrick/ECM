
# Liam Kirkpatrick
# August 17, 2023
# This script makes the GUI used in ecmgui_v26.py (and beyond?)
# incoperates inputs on stick info

# Import packages for GUI
import PySimpleGUI as sg
import datetime
import time
import pandas as pd

#import tkinter
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.patches import Rectangle

#%% make plot
def makeplot(xinput,array,ydim,ACorDC):

    # get dimensions of array
    (h,w) = np.shape(array)
	
	# get colormap
    cmap = matplotlib.colormaps.get_cmap('coolwarm')
	
	#make plot
    fig, ax = plt.subplots(1, 1,figsize=(4, 6), dpi=100)
    
    if ACorDC == 'AC':
        w = sum(array[0,:]>-1)
        print("w = "+str(w))
	
	# loop through array, plot each line
    for i in range(w):
        print(i)
	
		# x vector is the same for all runs with AC, but different for dc
        if ACorDC == 'AC':
            xvec = xinput
        elif ACorDC == 'DC':
            xvec = xinput[:,i]
        else:
            print("ERROR")

			
		# pull out yvector
        yvec = array[:,i]
		
        try:
            ax.plot(yvec,xvec,color=cmap(i/len(ydim)))
        except:
            print(yvec)
            print(xvec)
            print(ydim)
            print(i)
    ax.legend(np.round(ydim[0:w+1]),title='Distance accross core:',fontsize=6)
    ax.set_ylabel('Distance Along Track (mm)',fontsize=6)
    ax.set_xlabel('Conductivity',fontsize=6)
    
    if ACorDC =='DC':
        try:
            ax.set_xlim(0,np.percentile(array,95)+10**(-7))
        except:
            print("Axis label error")
    return(fig)

#%% delete figure
def delete_figure(figure_agg):
    figure_agg.get_tk_widget().forget()
    plt.close('all')
    
#%% draw figure within GUI
def draw_figure(canvas, figure):
   tkcanvas = FigureCanvasTkAgg(figure, canvas)
   tkcanvas.draw()
   tkcanvas.get_tk_widget().pack(side='top', fill='both', expand=1)
   return tkcanvas

#%% make gui
def guibuild():

    # Set Color
    sg.theme('LightGrey')
    # Build first collumn

    # Get current date/time

    today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

    first_col = [
    [sg.Column([[sg.Text('Plotting Window',font=("Helvetica", 12, "bold"))]], justification='c')],
    [sg.Canvas(key='-CANVAS-')],
    [sg.Text("   ",size=(50,1))],
    [sg.Text("")]
    ]
    


    # Build Second Column
    second_col = [
                [sg.Column([[sg.Text('Set Up Window',font=("Helvetica", 12, "bold"))]], justification='c')],
                 [sg.Column([[sg.Text(size=(25, 1), key='SETUP_INSTRUCT')]], justification='c')],
                 #[sg.Checkbox('Collect AC', default=True,key='-AC_SELECT-'), sg.Checkbox('Collect DC', default=False, key='-DC_SELECT-'), sg.Button('Continue',key='-ACDC_CONT-')],
                 [sg.Radio("Collect AC", "acdc", key='-AC_SELECT-', default=True),sg.Radio("Collect DC", "acdc", key='-DC_SELECT-'), sg.Button('Continue',key='-ACDC_CONT-')],
                 [sg.Radio("New Setup", "last", key='new', default=True),sg.Radio("Use Last Values", "last", key='old'),sg.Button('Continue',key='-LAST_CONT-')],
                 [sg.Button('Set Z Down', size=(15,1), key='-Z_SETUP-', disabled=True), sg.Text('     Set At: '), sg.Text('not set', size=(8, 1), key='-Z_SET-')],
                 [sg.Button('Set X0, Y0', size=(15,1), key='-X0Y0_SETUP-', disabled=True), sg.Text('   X Set At: '), sg.Text('not set', size=(8, 1), key='-X0_SET-')],
                 [sg.Text('                                        Y Set At: '), sg.Text('not set', size=(8, 1), key='-Y0_SET-')],
                 [sg.Button('Set X Tiepoint', size=(15,1), key='-XTIE_SETUP-', disabled=True), sg.Text('     Set At: '), sg.Text('not set', size=(8, 1), key='-XTIE_SET-')],
                 [sg.Button('Set X Tiepoint 2', size=(15,1), key='-XTIE2_SETUP-', disabled=True), sg.Text('     Set At: '), sg.Text('not set', size=(8, 1), key='-XTIE2_SET-')],
                 [sg.Button('Set X Tiepoint 3', size=(15,1), key='-XTIE3_SETUP-', disabled=True), sg.Text('     Set At: '), sg.Text('not set', size=(8, 1), key='-XTIE3_SET-')],
                 [sg.Button('Set X1,Y1', size=(15,1), key='-X1Y1_SETUP-', disabled=True), sg.Text('   X Set At: '), sg.Text('not set', size=(8, 1), key='-X1_SET-')],
                 [sg.Text('                                        Y Set At: '), sg.Text('not set', size=(8, 1), key='-Y1_SET-')],
                 [sg.Text('Hold Down Button To Move')],
        		 [sg.Text()],
        		 [sg.Text('           '),
         		 sg.RealtimeButton(sg.SYMBOL_UP, key='-X_UP-'),
         		 sg.Text('           '),
    			sg.RealtimeButton(sg.SYMBOL_UP, key='-Z_UP-')],
        		[sg.RealtimeButton(sg.SYMBOL_LEFT, key='-Y_DOWN-'),
         		sg.Text(size=(10, 1), key='-STATUS-', justification='c', pad=(0, 0)),
         		sg.RealtimeButton(sg.SYMBOL_RIGHT, key='-Y_UP-')],
        		[sg.Text('           '),
         		sg.RealtimeButton(sg.SYMBOL_DOWN, key='-X_DOWN-'),
         		sg.Text('           '),
         		sg.RealtimeButton(sg.SYMBOL_DOWN, key='-Z_DOWN-')],
        		[sg.Text()],

        		# Absolute Movement Sections
        		[sg.Text('Enter Relative or Absolute Movements in mm')],
        		[sg.Text()],
        		[sg.Text('Move X Rel', size=(10, 1)), sg.InputText(size=(6, 1), key='X_rel'),
         			sg.Text('Move X Abs', size=(10, 1)), sg.InputText(size=(6, 1), key='X_abs')],
        		[sg.Text('Move Y Rel', size=(10, 1)), sg.InputText(size=(6, 1), key='Y_rel'),
         			sg.Text('Move Y Abs', size=(10, 1)), sg.InputText(size=(6, 1), key='Y_abs')],
        		[sg.Text('Move Z Rel', size=(10, 1)), sg.InputText(size=(6, 1), key='Z_rel'),
         			sg.Text('Move Z Abs', size=(10, 1)), sg.InputText(size=(6, 1), key='Z_abs')],
        		[sg.Text('Press submit to enact move: '), sg.Submit()]]

        # Build Third Column
    third_col = [
    	[sg.Column([[sg.Text('Admin Window',font=("Helvetica", 12, "bold"))]], justification='c')],
    	[sg.Text("")],
        [sg.Text("Enter tube:", size=(23, 1)), sg.InputText('',size=(10,1), key="tube"),
        sg.Button('Submit',key='-SUBMIT_TUBE-', disabled=True)],
        [sg.Text("Enter index mark relative location:", size=(23, 1)), sg.InputText('',size=(10,1), key="tieloc"),
        sg.Button('Submit',key='-SUBMIT_TIELOC-', disabled=True)],
        [sg.Text("Enter index mark depth:", size=(23, 1)), sg.InputText('',size=(10,1), key="depth"),
        sg.Button('Submit',key='-SUBMIT_DEPTH-', disabled=True)],
        [sg.Column([[sg.Text('File Name Input')]],justification='c')],
        [sg.Text("Enter notes:", size=(10, 1)), sg.InputText('',key="note", size=(30,1))],
        [sg.Button('Submit',key='-SUBMIT_NOTE-', disabled=True)],
        [sg.Text("Enter filename:", size=(10, 1)), sg.InputText(default_text=today+'-STICK.txt', key="file", size=(30,1))],
        [sg.Button('Submit',key='-SUBMIT_FILENAME-',disabled=True)],
        [sg.Column([[sg.Text('Run Status')]], justification='c')],
        [sg.Text("Folder Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key='-RUN_STATUS-', justification='c')],
        [sg.Text("MCC Connection Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key = '-MCC_STATUS-', justification='c')],
        [sg.Text("SMU Connection Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key = '-SMU_STATUS-', justification='c')],
        [sg.Text("LCR Connection Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key = '-LCR_STATUS-', justification='c')],
        [sg.Text("Zaber Connection Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key='-CON_STATUS-', justification='c')],
        [sg.Text("Filename Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key='-FILE_STATUS-', justification='c')],
        [sg.Text("Setup Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key='-SETUP_STATUS-', justification='c')],
        [sg.Text("Write Resolution: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key='-WRITE_RES-', justification='c')],
        [sg.Text("AC/DC Status: ",size=(20,1),justification = 'r'),sg.Text(size=(20,1),key='-ACDC_STATUS-',justification = 'c')],
        [sg.Text("Data Collect Status: ",size=(20,1),justification = 'r'), sg.Text(size=(20, 1), key='-READ_STATUS-', justification='c')],
        [sg.Button('Begin AC Run',key='-START_AC-'), sg.Button('Begin DC Run', key='-START_DC-')],
        [sg.Column([[sg.Quit(button_color=(sg.theme_button_color()[1], sg.theme_button_color()[0]), focus=True)]],
            justification='r')]]
    




    # ----- Full layout -----
    layout = [
        [sg.Column(first_col),
         sg.VSeparator(),
         sg.Column(second_col),
         sg.VSeparator(),
         sg.Column(third_col)]
    ]

    return layout
    
    
    
#%% test when run as main



if __name__=="__main__" and False:

	print("Loading window. Will stay until you click \"quit\"")
	layout = guibuild()
	
	# Create the Window
	window = sg.Window('ECM GUI - Version 7', layout, finalize=True)
	
	
	while True:
		event, values = window.read(timeout=15)
		if event in (sg.WIN_CLOSED, 'Quit'):
			break
			
if __name__=="__main__":
    print("Loading window. Will stay until you click \"quit\"")
    layout = guibuild()
    window = sg.Window('ECM GUI - Version 7', layout, finalize=True)
	
	
	
    
    while True:
        event, values = window.read(timeout=15)
    		
        if event in (sg.WIN_CLOSED, 'Quit'):
            break
    window.close()