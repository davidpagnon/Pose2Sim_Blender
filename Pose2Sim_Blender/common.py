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
__version__ = '0.6.0'
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


def createMaterial(color=(0.8, 0.8, 0.8, 1), metallic = 0.5, roughness = 0.5):
    '''
    Create a material
    '''
    
    color_count = [m.name for m in bpy.data.materials].count(str(color))
    if color_count > 0:
        color_index = [m.name for m in bpy.data.materials].index(str(color))
        matg = bpy.data.materials[color_index]
    else:
        matg = bpy.data.materials.new(str(color))
        matg.use_nodes = True
        tree = matg.node_tree
        nodes = tree.nodes
        bsdf = nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = color
        matg.diffuse_color = color
        matg.metallic = metallic
        matg.roughness = roughness
    
    return matg