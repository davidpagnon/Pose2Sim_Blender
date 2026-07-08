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
__version__ = "0.8.0"
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
    
    hex_color = "".join(f"{int(round(c * 255)):02x}" for c in color)
    material_name = f"Material_{hex_color}"
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]    
   
    matg = bpy.data.materials.new(material_name)
    matg.use_nodes = True
    nodes = matg.node_tree.nodes
    bsdf = nodes["Principled BSDF"]

    bsdf.inputs["Base Color"].default_value = color
    matg.diffuse_color = color
    matg.metallic = metallic
    matg.roughness = roughness
    
    return matg