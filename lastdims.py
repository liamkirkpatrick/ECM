#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 21:49:27 2024

Save and Load last set of dims


@author: Liam
"""

# import packages

import numpy as np

#%% Save Last

def savelast(yl,yr,xmin,xmax,index1,index2,index3,zdown):
    
    last = np.array([yl,yr,xmin,xmax,index1,index2,index3,zdown])
    
    np.save('lastdims.npy',last)
    
    return()

def loadlast():
    
    last = np.load('lastdims.npy')
    
    return(last[0],last[1],last[2],last[3],last[4],last[5],last[6],last[7])

#%% Test

if __name__=="__main__":
    
    savelast(0,1,2,3,4,5,6,7)
    
    yl,yr,xmin,xmax,index1,index2,index3,zdown = loadlast()
    
    print("yl = "+str(yl))
    print("yr = "+str(yr))