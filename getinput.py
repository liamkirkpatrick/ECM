
"""
Liam Kirkpatrick
Inputs
May 24, 2023
ICF VERSION
Gets inputs (ie filename, etc)

Used in ecmgui_v21 and later


"""


#%% Imports

import PySimpleGUI as sg
import keyboard
import time

#%% Define Function

def getinput(window,button_key,box_key,status,back_key='-ADMIN_BACK-'):

    window[button_key].update(disabled=False)
    if back_key is not None:
        window[back_key].update(disabled=False)
    window[box_key].set_focus()

    back = False

    while True:

        # update status
        window['-FILE_STATUS-'].update('*** WAITING FOR '+status+' ***')
	
		# read
        event, values = window.read(timeout=50)
        txtinput = window[box_key].get()
		
        if event == button_key or keyboard.is_pressed('Enter'):
            qt = True
            break
        elif event == back_key:
            back = True
            qt = True
            window[box_key]('')
            break
        elif event in (sg.WIN_CLOSED, 'Quit'):
            qt = False
            break
		
    window[button_key].update(disabled=True)
    if back_key is not None:
        window[back_key].update(disabled=True)
    
    while keyboard.is_pressed('Enter'):
        time.sleep(0.25)
	
    return txtinput, qt, back