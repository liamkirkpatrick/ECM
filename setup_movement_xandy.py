'''
Liam Kirkpatrick
setup_movement_xandy.py

Built on setup_movement6.py. Allows for simultaneous setup of topleft/bottom right corner
'''

import constants as c
import PySimpleGUI as sg
from zaber_motion import Units
import time
import keyboard

# import XInput for controller
from XInput import *
try:
	import tkinter as tk
except ImportError:
	import TKinter as tk
	

set_deadzone(DEADZONE_TRIGGER,10)

def setup_movxy(window,x_dev,y_dev,z_dev, qt, button, outputy, outputx, des):
    
    window['SETUP_INSTRUCT'].update('*** Set ' + des + ' Location ***')
    window[button].update(disabled=False)
    window['-SETUP_BACK-'].update(disabled=False)
    
    loc = float("NaN")
    locx = float("NaN")
    locy = float("NaN")
    
    break_out_flag = False
    back_out_flag = False
    
    stopX = True
    stopY = True
    stopZ = True
    
    yprior = 0
    xprior = 0
    zprior = 0

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read(timeout=15)

        con_events = get_events()

        for con_event in con_events:
            if con_event.type == EVENT_STICK_MOVED:
                if con_event.stick == LEFT:
                    if abs(con_event.y) > 0.2:
                        try:
                            x_dev.move_velocity(c.x_spd / c.xv_conv * con_event.y)
                        except:
                            print("Error Moving X")
                        stopX = False
                    else:
                        stopX = True

                    if abs(con_event.x) > 0.2:
                        y_dev.move_velocity(8 * con_event.x, Units.VELOCITY_MILLIMETRES_PER_SECOND)
                        stopY = False
                    else:
                        stopY = True

                if con_event.stick == RIGHT:
                    if abs(con_event.y) > 0.2:
                        z_dev.move_velocity(3 * con_event.y * -1, Units.VELOCITY_MILLIMETRES_PER_SECOND)
                        stopZ = False
                    else:
                        stopZ = True

            if con_event.type == EVENT_BUTTON_PRESSED:
                if con_event.button == "X" or con_event.button == "B":
                    locy = y_dev.get_position(unit=Units.LENGTH_MILLIMETRES)
                    locx = x_dev.get_position(unit=Units.NATIVE)

                    window[outputx].update(str(round(locx * c.x_conv, 2)) + ' mm')
                    window[outputy].update(str(round(locy, 2)) + ' mm')

                    break_out_flag = True

                    time.sleep(0.5)
                    break
                elif con_event.button == "DPAD_UP":
                    x_dev.move_relative(1 / c.x_conv)
                elif con_event.button == "DPAD_DOWN":
                    x_dev.move_relative(-1 / c.x_conv)
                elif con_event.button == "DPAD_RIGHT":
                    y_dev.move_relative(1, Units.LENGTH_MILLIMETRES)
                elif con_event.button == "DPAD_LEFT":
                    y_dev.move_relative(-1, Units.LENGTH_MILLIMETRES)
                elif con_event.button == "Y":
                    z_dev.move_relative(-1, Units.LENGTH_MILLIMETRES)
                elif con_event.button == "A":
                    z_dev.move_relative(1, Units.LENGTH_MILLIMETRES)

        if break_out_flag:
            break

        if event in (sg.WIN_CLOSED, 'Quit'):
            qt = False
            break
        elif event == '-SETUP_BACK-' or keyboard.is_pressed('b'):
            back_out_flag = True
            break
        elif event == button or keyboard.is_pressed('Enter'):
            locy = y_dev.get_position(unit=Units.LENGTH_MILLIMETRES)
            locx = x_dev.get_position(unit=Units.NATIVE)

            window[outputx].update(str(round(locx * c.x_conv, 2)) + ' mm')
            window[outputy].update(str(round(locy, 2)) + ' mm')

            break
        elif event == '-X_UP-':
            window['-STATUS-'].update(event)
            x_dev.move_velocity(c.x_spd / c.xv_conv)
        elif event == '-X_DOWN-':
            window['-STATUS-'].update(event)
            x_dev.move_velocity(-c.x_spd / c.xv_conv)
        elif event == '-Y_UP-':
            window['-STATUS-'].update(event)
            y_dev.move_velocity(8, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        elif event == '-Y_DOWN-':
            window['-STATUS-'].update(event)
            y_dev.move_velocity(-8, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        elif event == '-Z_UP-':
            window['-STATUS-'].update(event)
            z_dev.move_velocity(-2, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        elif event == '-Z_DOWN-':
            window['-STATUS-'].update(event)
            z_dev.move_velocity(2, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        elif event == 'Submit':
            if bool(window['X_abs'].get()):
                x_dev.move_absolute(float(window['X_abs'].get()) / c.x_conv, timeout=120)
            if bool(window['Y_abs'].get()):
                y_dev.move_absolute(float(window['Y_abs'].get()), Units.LENGTH_MILLIMETRES)
            if bool(window['Z_abs'].get()):
                z_dev.move_absolute(float(window['Z_abs'].get()), Units.LENGTH_MILLIMETRES)
            if bool(window['X_rel'].get()):
                x_dev.move_relative(float(window['X_rel'].get()) / c.x_conv, timeout=120)
            if bool(window['Y_rel'].get()):
                y_dev.move_relative(float(window['Y_rel'].get()), Units.LENGTH_MILLIMETRES)
            if bool(window['Z_rel'].get()):
                z_dev.move_relative(float(window['Z_rel'].get()), Units.LENGTH_MILLIMETRES)

            keys_to_clear = ['X_abs', 'X_rel', 'Y_abs', 'Y_rel', 'Z_abs', 'Z_rel']
            for key in keys_to_clear:
                window[key]('')
        elif keyboard.is_pressed('left'):
            window['-STATUS-'].update('Left Arrow')
            y_dev.move_velocity(-8, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        elif keyboard.is_pressed('right'):
            window['-STATUS-'].update('Right Arrow')
            y_dev.move_velocity(8, Units.VELOCITY_MILLIMETRES_PER_SECOND)
        elif keyboard.is_pressed('up'):
            window['-STATUS-'].update('Up Arrow')
            x_dev.move_velocity(c.x_spd / c.xv_conv)
        elif keyboard.is_pressed('down'):
            window['-STATUS-'].update('Down Arrow')
            x_dev.move_velocity(-c.x_spd / c.xv_conv)
        else:
            window['-STATUS-'].update('READY')
            try:
                if stopX:
                    x_dev.stop()
                if stopY:
                    y_dev.stop()
                if stopZ:
                    z_dev.stop()
            except:
                print('Error Stopping')
    # read one more time to print out last value
    event, values = window.read(timeout=15)
    
    # disable button
    window[button].update(disabled=True)
    window['-SETUP_BACK-'].update(disabled=True)
    
    while keyboard.is_pressed('Enter'):
        time.sleep(0.5)
    while keyboard.is_pressed('b'):
        time.sleep(0.5)
    
    #return position value, and quit T/F
    return locx,locy, qt, back_out_flag
