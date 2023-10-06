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
    - addGRF: import a .mot or .csv ground reaction force file

'''


## INIT
import bpy
import Sim2Blend
import os

rootpath=os.path.dirname(os.path.abspath(__file__))
stlFolder=os.path.join(rootpath,'Sim2Blend','Geometry')


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2021, BlendOSim & Sim2Blend"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## CLASSES
bl_info = {
    "name": "Sim2Blend",
    "category": "Import",
    "version": (0, 0, 1),
    "blender": (3, 6, 0),
}


class MyProperties(bpy.types.PropertyGroup):
    modelfile : bpy.props.StringProperty(
        name='Model file',
        subtype="FILE_PATH")
    motionfile : bpy.props.StringProperty(
        name='Motion file',
        subtype="FILE_PATH")
    markersfile : bpy.props.StringProperty(
        name='Markers file',
        subtype="FILE_PATH")
    forcesfile : bpy.props.StringProperty(
        name='Forces file',
        subtype="FILE_PATH")            
    momentsfile : bpy.props.StringProperty(
        name='Moments file',
        subtype="FILE_PATH")   

    
class addModel(bpy.types.Operator):
    bl_idname = 'mesh.add_osim_model'
    bl_label = 'Add Model'
    bl_options = {'REGISTER', 'UNDO'}
      
    def execute(self, context):
        scene=context.scene
        mytool=scene.my_tool
        osim_path = bpy.path.abspath(mytool.modelfile)
        Sim2Blend.model.import_model(osim_path,stlRoot=stlFolder)
        return {'FINISHED'}
    

class addMotion(bpy.types.Operator):
    bl_idname = 'motion.add_osim_motion'
    bl_label = 'Add Motion'
    bl_options = {'REGISTER', 'UNDO'}
      
    def execute(self, context):
        scene=context.scene
        mytool=scene.my_tool  
        osim_path = bpy.path.abspath(mytool.modelfile)
        mot_path=bpy.path.abspath(mytool.motionfile)
        Sim2Blend.motion.apply_mot_to_model(mot_path, osim_path, direction='zup')
        return {'FINISHED'}
    

class addMarkers(bpy.types.Operator):
    bl_idname = 'mesh.add_osim_markers'
    bl_label = 'Add Markers'
    bl_options = {'REGISTER', 'UNDO'}
  
    def execute(self, context):
        scene=context.scene
        mytool=scene.my_tool  
        trc_path=bpy.path.abspath(mytool.markersfile)
        Sim2Blend.markers.import_trc(trc_path, direction='zup')
        #bpy.context.scene.update()        
        return {'FINISHED'}


class addForces(bpy.types.Operator):
    bl_idname = 'mesh.add_osim_forces'
    bl_label = 'Add Forces'
    bl_options = {'REGISTER', 'UNDO'}
  
    def execute(self, context):
        scene=context.scene
        mytool=scene.my_tool  
        force_path=bpy.path.abspath(mytool.forcesfile)
        Sim2Blend.forces.loadForces(force_path)
        #bpy.context.scene.update()        
        return {'FINISHED'}


class addMoments(bpy.types.Operator):
    bl_idname = 'mesh.add_osim_moments'
    bl_label = 'Add Moments'
    bl_options = {'REGISTER', 'UNDO'}
  
    def execute(self, context):
        scene=context.scene
        mytool=scene.my_tool  
        force_path=bpy.path.abspath(mytool.momentsfile)
        Sim2Blend.moments.loadMoments(force_path)
        #bpy.context.scene.update()        
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
        scene=context.scene
        mytool=scene.my_tool  
        layout.prop(mytool,"modelfile")
        layout.operator("mesh.add_osim_model",icon='MESH_MONKEY', text="Add Model")      
        layout.prop(mytool,"motionfile")   
        layout.operator("motion.add_osim_motion",icon='CURVE_PATH', text="Add Motion")     
        layout.prop(mytool,"markersfile")            
        layout.operator("mesh.add_osim_markers",icon='MESH_UVSPHERE', text="Add Markers") 
        layout.prop(mytool,"forcesfile")            
        layout.operator("mesh.add_osim_forces",icon='EMPTY_SINGLE_ARROW', text="Add Forces") 
        layout.prop(mytool,"momentsfile")            
        layout.operator("mesh.add_osim_moments",icon='EMPTY_SINGLE_ARROW', text="Add Moments") 
        
def register():
    print('Addon Registered')
    bpy.utils.register_class(addModel)
    bpy.utils.register_class(addMotion)            
    bpy.utils.register_class(addMarkers)
    bpy.utils.register_class(addForces)
    bpy.utils.register_class(addMoments)
    bpy.utils.register_class(panel1)
    bpy.utils.register_class(MyProperties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)

def unregister():
    print('bye')
    bpy.utils.unregister_class(addModel)
    bpy.utils.unregister_class(addMotion)            
    bpy.utils.unregister_class(addMarkers)
    bpy.utils.unregister_class(addForces)
    bpy.utils.unregister_class(addMoments)
    bpy.utils.unregister_class(panel1)
    bpy.utils.unregister_class(MyProperties)

        
# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    print('test done')
    
    