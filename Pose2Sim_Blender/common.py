#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## OTHER SHARED UTILITIES                       ##
    ##################################################
    
    Functions shared between modules, and other utilities
    
'''

## INIT
import bpy


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon"
__copyright__ = "Copyright 2023, Pose2Sim_Blender"
__credits__ = ["David Pagnon"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## FUNCTIONS
def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    '''
    Popup message box.
    See https://blender.stackexchange.com/a/110112/174689
    '''
    
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

