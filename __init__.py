#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ####################################################
    ## Sim2Blend: import data from OpenSim to Blender ##
    ####################################################
    
    A Blender addon to import data from OpenSim to Blender.

    - addModel: import an .osim model file
    - addMotion: import a .mot (OpenSim API required) or .csv motion file
    - addMarkers: import a .trc marker file
    - addGRF: import a .mot ground reaction force file
'''


## INIT
import bpy
import bpy_extras.io_utils
from Sim2Blend.Sim2Blend import model, motion, markers, forces
import os

rootpath=os.path.dirname(os.path.abspath(__file__))
stlFolder=os.path.join(rootpath,'Sim2Blend','Geometry')


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2023, BlendOSim & Sim2Blend"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## CLASSES
bl_info = {
    "name": "Sim2Blend",
    "author": "David Pagnon, Jonathan Camargo",
    "version": (0, 0, 1),
    "blender": (3, 6, 0),
    "location": "VIEW_3D > UI > Sidebar (press N)",
    "category": "Import-Export",
    "description": "Import OpenSim results",
    "doc_url": "https://github.com/davidpagnon/Sim2Blend",
    "tracker_url": "https://github.com/davidpagnon/Sim2Blend/issues"
}


class addModel(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_model'
    bl_label = 'Add Model'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Model file',
        default="*.osim",
        options={'HIDDEN'},
        subtype="FILE_PATH")
      
    def execute(self, context):
        global osim_path
        osim_path= bpy.path.abspath(self.filepath)
        model.import_model(osim_path,stlRoot=stlFolder)
        return {'FINISHED'}
    

class addMotion(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_motion'
    bl_label = 'Add Motion'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Motion file',
        default="*.mot;*.csv",
        options={'HIDDEN'},
        subtype="FILE_PATH")
      
    def execute(self, context):
        global osim_path
        mot_path=bpy.path.abspath(self.filepath)
        motion.apply_mot_to_model(mot_path, osim_path, direction='zup')
        return {'FINISHED'}
    

class addMarkers(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_markers'
    bl_label = 'Add Markers'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Markers file',
        default="*.trc",
        options={'HIDDEN'},
        subtype="FILE_PATH")
  
    def execute(self, context):
        trc_path=bpy.path.abspath(self.filepath)
        markers.import_trc(trc_path, direction='zup')
        return {'FINISHED'}


class addForces(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_forces'
    bl_label = 'Add Forces'
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Force file',
        default="*.mot",
        options={'HIDDEN'},
        subtype="FILE_PATH")
  
    def execute(self, context):
        grf_path=bpy.path.abspath(self.filepath)
        forces.import_forces(grf_path, direction='zup')
        return {'FINISHED'}


class panel1(bpy.types.Panel):
    bl_idname = "A1_panel.panel1_PT_Sim2Blendlel"
    bl_label = "Sim2Blend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sim2Blend"
    
    def draw(self, context):
        layout=self.layout
        layout.label(text='Import OpenSim data') 
        layout.operator("mesh.add_osim_model",icon='MESH_MONKEY', text="Add Model")      
        layout.operator("mesh.add_osim_motion",icon='CURVE_PATH', text="Add Motion")     
        layout.operator("mesh.add_osim_markers",icon='MESH_UVSPHERE', text="Add Markers") 
        layout.operator("mesh.add_osim_forces",icon='EMPTY_SINGLE_ARROW', text="Add Forces") 
        

def register():
    print('Addon Registered')
    bpy.utils.register_class(addModel)
    bpy.utils.register_class(addMotion)            
    bpy.utils.register_class(addMarkers)
    bpy.utils.register_class(addForces)
    bpy.utils.register_class(panel1)

def unregister():
    print('bye')
    bpy.utils.unregister_class(addModel)
    bpy.utils.unregister_class(addMotion)            
    bpy.utils.unregister_class(addMarkers)
    bpy.utils.unregister_class(addForces)
    bpy.utils.unregister_class(panel1)

        
# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    print('test done')
    
    