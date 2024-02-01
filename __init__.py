#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ####################################################
    ## Pose2Sim Blender: Companion tool for Pose2Sim  ##
    ####################################################
    
    A Blender addon to visualize Pose2Sim data in Blender.

    OpenSim:
    - addModel: import an .osim model file
    - addMotion: import a .mot (OpenSim API required) or .csv motion file
    - addMarkers: import a .trc marker file
    - addGRF: import a .mot ground reaction force file
    
    Cameras:
    - Import cameras from calibration
    - Export calibration from cameras in scene
    - Show images or videos on each camera
    - Film from cameras
    
    Other tools:
    - View from selected camera
    - Trace line from 3D point to camera
    - Trace line from image point to camera
    
    Scene:
    - Export scene to Alembic
'''


## INIT
import bpy
import bpy_extras.io_utils
from bpy.props import IntProperty, BoolProperty
from Pose2Sim_Blender.Pose2Sim_Blender import model, motion, markers, forces, cameras
from Pose2Sim_Blender.Pose2Sim_Blender.common import ShowMessageBox
import os

rootpath=os.path.dirname(os.path.abspath(__file__))
stlFolder=os.path.join(rootpath,'Pose2Sim_Blender','Geometry')


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2023, BlendOSim & Pose2Sim_Blender"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## CLASSES
bl_info = {
    "name": "Pose2Sim Blender",
    "author": "David Pagnon, Jonathan Camargo",
    "version": (0, 0, 1),
    "blender": (3, 6, 0),
    "location": "VIEW_3D > UI > Sidebar (press N)",
    "category": "Import-Export",
    "description": "visualize OpenSim and Pose2Sim data in Blender",
    "doc_url": "https://github.com/davidpagnon/Pose2Sim_Blender",
    "tracker_url": "https://github.com/davidpagnon/Pose2Sim_Blender/issues"
}


class importCal(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_cam_cal'
    bl_label = 'Import calibration'
    bl_description = "Import cameras from a `.toml` Pose2Sim camera calibration file"
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


class exportCal(bpy.types.Operator,bpy_extras.io_utils.ExportHelper):
    bl_idname = 'mesh.save_cam_cal'
    bl_label = 'Export calibration'
    bl_description = "Export your cameras as a `.toml` Pose2Sim camera calibration file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = '.toml'
    
    filter_glob : bpy.props.StringProperty(
        name='Pose2Sim calibration file',
        default="*.toml",
        options={'HIDDEN'},
        subtype="FILE_PATH")
        
    def invoke(self, context, _event):
        calib_filepath = 'Calib_blender'
        self.filepath = calib_filepath + self.filename_ext
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def execute(self, context):
        toml_path=bpy.path.abspath(self.filepath)
        cameras.export_cameras(toml_path)
        return {'FINISHED'}


class showImages(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.show_img'
    bl_label = 'Show Images/Video'
    bl_description = "Select a camera, then import images or a video"
    bl_options = {'REGISTER', 'UNDO'}
    
    single_image: BoolProperty(
        name="Import single image",
        description="If unchecked, image sequences ot videos will be imported.",
        default=False,
    )
    
    def execute(self, context):
        camera = bpy.context.active_object
        if camera == None:
            ShowMessageBox("Please first select a camera", "No camera selected")
            raise TypeError("Please first select a camera")
        elif camera.type != 'CAMERA':
            ShowMessageBox("Please first select a camera", "No camera selected")
            raise TypeError("Please first select a camera")
        else:
            img_vid_path=bpy.path.abspath(self.filepath)
            cameras.show_images(camera, img_vid_path, single_image = self.single_image)
            return {'FINISHED'}


class filmWithCameras(bpy.types.Operator): #,bpy_extras.io_utils.ExportHelper):
    bl_idname = 'mesh.film_from_cam'
    bl_label = 'Export calibration'
    bl_description = "Export your cameras as a `.toml` Pose2Sim camera calibration file"
    bl_options = {'REGISTER', 'UNDO'}
    
    # filename_ext = '.toml'
    
    # filter_glob : bpy.props.StringProperty(
        # name='Pose2Sim calibration file',
        # default="*.toml",
        # options={'HIDDEN'},
        # subtype="FILE_PATH")
        
    # image sequences or video
    # framerate
        
    # def invoke(self, context, _event):
        # calib_filepath = 'Calib_blender'
        # self.filepath = calib_filepath + self.filename_ext
        # context.window_manager.fileselect_add(self)
        # return {'RUNNING_MODAL'}
        
    # def execute(self, context):
        # toml_path=bpy.path.abspath(self.filepath)
        # cameras.export_cameras(toml_path)
        # return {'FINISHED'}
        
    def execute(self, context):
        ShowMessageBox("Coming soon!", "Almost there...")
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
        max = 500
    )
    
    def execute(self, context):
        trc_path=bpy.path.abspath(self.filepath)
        markers.import_trc(trc_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}


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
        max = 500
    )
    
    def execute(self, context):
        global osim_path
        mot_path=bpy.path.abspath(self.filepath)
        motion.apply_mot_to_model(mot_path, osim_path, direction='zup', target_framerate=self.target_framerate)
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
        max = 500
    )
    
    def execute(self, context):
        grf_path=bpy.path.abspath(self.filepath)
        forces.import_forces(grf_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}


class seeThroughCam(bpy.types.Operator):
    bl_idname = 'mesh.see_through_cam'
    bl_label = 'See through selected camera'
    bl_description = "Select a camera, then click button to see through it"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        camera = bpy.context.active_object
        if camera == None:
            ShowMessageBox("Please first select a camera", "No camera selected")
            raise TypeError("Please first select a camera")
        elif camera.type != 'CAMERA':
            ShowMessageBox("Please first select a camera", "No camera selected")
            raise TypeError("Please first select a camera")
        else:
            cameras.see_through_selected_camera()
            return {'FINISHED'}


class raysFrom3Dpoint(bpy.types.Operator):
    bl_idname = 'mesh.rays_from_3dpoint'
    bl_label = 'See 3D point reprojection on image planes'
    bl_description = "Select one or several objects, then click button to reproject them on all image planes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # points = bpy.context.active_object
        # if points == None:
            # ShowMessageBox("Please first select one or several objects", "No object selected")
            # raise TypeError("Please first select one or several objects")
        # elif points.type == 'CAMERA':
            # ShowMessageBox("Please first select one or several objects", "No object selected")
            # raise TypeError("Please first select one or several objects")
        # else:
            # ShowMessageBox("Coming soon!", "Almost there...")
            # # cameras.reproject_3D_points()
            # return {'FINISHED'}
        ShowMessageBox("Coming soon!", "Almost there...")
        # cameras.reproject_3D_points()
        return {'FINISHED'}


class rayFromImagePoint(bpy.types.Operator):
    bl_idname = 'mesh.ray_from_imgpoint'
    bl_label = 'See epipolar line from camera center to image point'
    bl_description = "Select a point on the image, then click button to trace the epipolar line"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        ShowMessageBox("Coming soon!", "Almost there...")
        return {'FINISHED'}


class alembicExport(bpy.types.Operator):#,bpy_extras.io_utils.ExportHelper):
    bl_idname = 'mesh.export'
    bl_label = 'Export all data to Alembic (.abc) format'
    bl_description = "Alembic format can be read by most other 3D animation softwares"
    bl_options = {'REGISTER', 'UNDO'}
    
    # filename_ext = '.mp4'
    
    def execute(self, context):
        ShowMessageBox("Coming soon!", "Almost there...")
        return {'FINISHED'}


class panel1(bpy.types.Panel):
    bl_idname = "A1_panel.panel1_PT_Pose2Sim_Blenderlel"
    bl_label = "Pose2Sim"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pose2Sim"
    
    def draw(self, context):
        layout=self.layout
        
        layout.label(text='Cameras')
        column_layout = layout.column_flow(columns=2, align=False)
        column_layout.operator("mesh.add_cam_cal",icon='STICKY_UVS_DISABLE', text="Import")
        column_layout.operator("mesh.save_cam_cal",icon='STICKY_UVS_LOC', text="Export")

        layout.label(text='Images/Videos')
        column_layout2 = layout.column_flow(columns=2, align=False)
        column_layout2.operator("mesh.show_img",icon='PASTEDOWN', text="Show")
        column_layout2.operator("mesh.film_from_cam",icon='COPYDOWN', text="Film")
        
        layout.label(text='')
        layout.label(text='Import OpenSim data') 
        layout.operator("mesh.add_osim_markers",icon='MESH_UVSPHERE', text="Add Markers") 
        layout.operator("mesh.add_osim_model",icon='MESH_MONKEY', text="Add Model")
        layout.operator("mesh.add_osim_motion",icon='CURVE_PATH', text="Add Motion")
        layout.operator("mesh.add_osim_forces",icon='EMPTY_SINGLE_ARROW', text="Add Forces") 
        
        layout.label(text='')
        layout.label(text='Other tools') 
        layout.operator("mesh.see_through_cam",icon='IMAGE_RGB_ALPHA', text='See through camera') 
        layout.operator("mesh.rays_from_3dpoint",icon='PARTICLE_DATA', text='Rays from 3D point') 
        layout.operator("mesh.ray_from_imgpoint",icon='CURVE_PATH', text='Ray from image point')
        layout.operator("mesh.export",icon='EXPORT', text='Export to Alembic')


# def enable_external_addon(dummy):
#     bpy.ops.wm.addon_enable(module='io_anim_c3d')


def register():
    print('Addon Registered')
    
    bpy.utils.register_class(importCal)
    bpy.utils.register_class(exportCal)
    bpy.utils.register_class(showImages)
    bpy.utils.register_class(filmWithCameras)
    
    bpy.utils.register_class(addMarkers)
    bpy.utils.register_class(addModel)
    bpy.utils.register_class(addMotion)
    bpy.utils.register_class(addForces)
    
    bpy.utils.register_class(seeThroughCam)
    bpy.utils.register_class(raysFrom3Dpoint)
    bpy.utils.register_class(rayFromImagePoint)
    bpy.utils.register_class(alembicExport)
    
    bpy.utils.register_class(panel1)
    
    # bpy.ops.preferences.addon_enable(module='io_anim_c3d')
    # bpy.ops.wm.addon_enable(module='io_anim_c3d')


def unregister():
    print('Addon Unregistered')
    
    bpy.utils.unregister_class(importCal)
    bpy.utils.unregister_class(exportCal)
    bpy.utils.unregister_class(showImages)
    bpy.utils.unregister_class(filmWithCameras)
    
    bpy.utils.unregister_class(addMarkers)
    bpy.utils.unregister_class(addModel)
    bpy.utils.unregister_class(addMotion)            
    bpy.utils.unregister_class(addForces)
    
    bpy.utils.unregister_class(seeThroughCam)
    bpy.utils.unregister_class(raysFrom3Dpoint)
    bpy.utils.unregister_class(rayFromImagePoint)
    bpy.utils.unregister_class(alembicExport)
    
    bpy.utils.unregister_class(panel1)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    print('test done')
    
    
