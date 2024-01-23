ECM Control Programs

The code in this folder runs the ECM machine at the NSF Ice Core Facility.

Programs include:

#######################################
quickplot.py

This program can be run on it's own to plot data.
It quickly produces and saves figures.
Enter "last" to plot the most recent run


#######################################
constants.py

This file holds all constants for the ECM system. Use this to change base settings for
each run.


#######################################
setup_movement_v6.py

This script holds a function called by ecmgui during the setup stage.
It takes input from the xbox controller, keyboard, or gui to move motors and read in ice
locations.

#######################################
make_gui_v9.py

This script, called by ecmgui, builds the GUI. 

#######################################
get_input.py

This simple function waits for a key to be pressed. Used in setup

#######################################
ecmgui_v28.py

The master control program. If it's not somewhere else, it's here.
Future work will try to push more features to functions to shorten this script.