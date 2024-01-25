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
from bpy.props import IntProperty
from Sim2Blend.Sim2Blend import model, motion, markers, forces, cameras
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
    bl_description ="Import the 'bodies' of an `.osim` model"
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
    bl_description = "Import a `.mot` or a `.csv` motion file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Motion file',
        default="*.mot;*.csv",
        options={'HIDDEN'},
        subtype="FILE_PATH")
    
    target_framerate: IntProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default=30,
        min = 1,
        max = 120
    )
    
    def execute(self, context):
        global osim_path
        mot_path=bpy.path.abspath(self.filepath)
        motion.apply_mot_to_model(mot_path, osim_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}
    

class addMarkers(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_markers'
    bl_label = 'Add Markers'
    bl_description = "Import a `.trc` or a `.c3d` marker file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Markers file',
        default="*.trc;*.c3d",
        options={'HIDDEN'},
        subtype="FILE_PATH")
    
    target_framerate: IntProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default=30,
        min = 1,
        max = 120
    )
    
    def execute(self, context):
        trc_path=bpy.path.abspath(self.filepath)
        markers.import_trc(trc_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}


class addForces(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_forces'
    bl_label = 'Add Forces'
    bl_description = "Import a `.mot` force file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : bpy.props.StringProperty(
        name='Force file',
        default="*.mot",
        options={'HIDDEN'},
        subtype="FILE_PATH")
    
    target_framerate: IntProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default=30,
        min = 1,
        max = 120
    )
    
    def execute(self, context):
        grf_path=bpy.path.abspath(self.filepath)
        forces.import_forces(grf_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}


class importCal(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_cam_cal'
    bl_label = 'Import calibration'
    bl_description = "Import a `.toml` Pose2Sim camera calibration file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob : bpy.props.StringProperty(
        name='Pose2Sim calibration file',
        default="*.toml",
        options={'HIDDEN'},
        subtype="FILE_PATH")
        
    def execute(self, context):
        toml_path=bpy.path.abspath(self.filepath)
        cameras.import_cameras(toml_path)
        return {'FINISHED'}


# class exportCal

# class showImages

# class filmWithCameras

# class overlaySelection


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
        
        layout.label(text='')
        layout.label(text='Cameras')
        column_layout = layout.column_flow(columns=2, align=False)
        column_layout.operator("mesh.add_cam_cal",icon='STICKY_UVS_DISABLE', text="Import")
        column_layout.operator("mesh.add_osim_model",icon='STICKY_UVS_LOC', text="Export")

        layout.label(text='Images/Videos')
        column_layout2 = layout.column_flow(columns=2, align=False)
        column_layout2.operator("mesh.add_osim_model",icon='PASTEDOWN', text="Show")
        column_layout2.operator("mesh.add_osim_model",icon='COPYDOWN', text="Film")
        
        layout.label(text='')
        layout.label(text='Other tools')
        layout.operator("mesh.add_osim_model",icon='IMAGE_RGB_ALPHA', text='Overlay selected objects') 
        layout.operator("mesh.add_osim_model",icon='TRANSFORM_ORIGINS', text='Camera to image point')
        layout.operator("mesh.add_osim_model",icon='EXPORT', text='Export to Alembic')


# def enable_external_addon(dummy):
#     bpy.ops.wm.addon_enable(module='io_anim_c3d')

def register():
    print('Addon Registered')
    bpy.utils.register_class(addModel)
    bpy.utils.register_class(addMotion)            
    bpy.utils.register_class(addMarkers)
    bpy.utils.register_class(addForces)
    bpy.utils.register_class(importCal)
    
    bpy.utils.register_class(panel1)
    # bpy.ops.preferences.addon_enable(module='io_anim_c3d')
    # bpy.ops.wm.addon_enable(module='io_anim_c3d')


def unregister():
    print('Addon Unregistered')
    bpy.utils.unregister_class(addModel)
    bpy.utils.unregister_class(addMotion)            
    bpy.utils.unregister_class(addMarkers)
    bpy.utils.unregister_class(addForces)
    bpy.utils.unregister_class(importCal)
    
    bpy.utils.unregister_class(panel1)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    print('test done')
    
    
