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
from bpy.props import IntProperty, BoolProperty, EnumProperty, StringProperty, CollectionProperty
from .Pose2Sim_Blender import model, motion, markers, forces, cameras
from .Pose2Sim_Blender.common import ShowMessageBox
import os
import subprocess
import sys

def install_package(package):
    python_exe = sys.executable
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([python_exe, "-m", "pip", "install", package])

rootpath=os.path.dirname(os.path.abspath(__file__))
stlFolder=os.path.join(rootpath,'Pose2Sim_Blender','Geometry')

install_package("anytree")


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2023, BlendOSim & Pose2Sim_Blender"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.7.0"
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
    
    filter_glob : StringProperty(
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
    
    filter_glob : StringProperty(
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


class showImages(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
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


class filmWithCameras(bpy.types.Operator, bpy_extras.io_utils.ImportHelper): #,bpy_extras.io_utils.ExportHelper):
    bl_idname = 'mesh.film_from_cam'
    bl_label = 'Film from cameras'
    bl_description = "Render videos from selected cameras in chosen directory"
    bl_options = {'REGISTER', 'UNDO'}
    
    directory: StringProperty(
        name="Output directory",
        description="Root directory of saved films/image sequences"
        )
        
    filter_folder: BoolProperty(
        default=True,
        options={"HIDDEN"}
        )
    
    all_cams: BoolProperty(
        name="Film with all cameras",
        description="If checked, all cameras will film the scene",
        default=False,
    )
    
    movie_or_sequence: EnumProperty(
        name="Save as",
        description="Save as movie or image sequence",
        items=[ ('movie',"Movie","Save as movie"),
                ('images',"Image sequence","Save as image sequence")],
        default = 'movie'
    )
    
    target_framerate: IntProperty(
        name="Output framerate [fps]",
        description="Framerate of the output movie. Ignored if image_sequence",
        default=30,
        min = 1
    )
    
    first_frame: IntProperty(
        name="First frame",
        description="First frame to render",
        default=0,
        min = 0
    )
    
    last_frame: IntProperty(
        name="Last frame",
        description="Last frame to render",
        default=100,
        min = 1
    )
    
    render_quality: IntProperty(
        name="Render quality (%)",
        description="Best quality is nicer but slower to render",
        default=100,
        min = 0, 
        max = 100
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def execute(self, context):
        dir_path = bpy.path.abspath(self.directory)  
        cams = bpy.context.selected_objects
        if len(cams) == 0 and self.all_cams == False:
            ShowMessageBox("Please first select one or several cameras", "No camera selected")
            raise TypeError("Please first select one or several cameras")
        for i, cam in enumerate(cams):
            if cam.type != 'CAMERA':
                ShowMessageBox(f"{cam.name} is not a camera", "Not a camera")
                raise TypeError(f"{cam.name} is not a camera")
                    
        cameras.film_from_cams( dir_path, 
                                cams,
                                all_cameras=self.all_cams, 
                                movie_or_sequence=self.movie_or_sequence, 
                                target_framerate=self.target_framerate, 
                                first_frame = self.first_frame, 
                                last_frame = self.last_frame, 
                                render_quality=self.render_quality)
        
        return {'FINISHED'}


class addMarkers(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_markers'
    bl_label = 'Markers'
    bl_description = "Import a `.trc` or a `.c3d` marker file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(
        name="Markers file",
        default="*.trc;*.c3d",
        options={'HIDDEN'},
        subtype="FILE_PATH"
    )

    target_framerate: StringProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default='auto',
    )

    armature_type: EnumProperty(
        name="Armature",
        description="Create an armature to animate a rigged skeleton or character.",
        items=[
            ('none', "None", "Do not create an armature"),
            ('halpe_26', "Body with feet", "BodyWithFeet (Halpe_26) skeleton"),
            ('coco_133_wrist', "Body with feet and hands", "WholeBody (Coco_133) skeleton, without face and fingers"),
            ('coco_133', "Body with feet, fingers, face", "WholeBody (Coco_133_wrist) skeleton, without face and fingers"),
            ('coco_17', "Body", "Body (Coco_17) skeleton"),
            ('hand_21', "Hand", "Hand (Hand_21) skeleton"),
            ('face_106', "Face", "Face (face_106) skeleton"),
            ('animal2d_17', "Animal", "Animal (Animal2d_17) skeleton"),
        ],
        default='none'
    )

    # File picker properties
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        for file in self.files:
            trc_path = os.path.join(self.directory, file.name)
            markers.import_trc(trc_path, direction='zup', target_framerate=self.target_framerate, armature_type=self.armature_type)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_framerate")
        layout.prop(self, "armature_type")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class addModel(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_model'
    bl_label = 'Model'
    bl_description ="Import the 'bodies' of an `.osim` model"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : StringProperty(
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
    bl_label = 'Motion'
    bl_description = "Import a `.mot` or a `.csv` motion file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : StringProperty(
        name='Motion file',
        default="*.mot;*.csv",
        options={'HIDDEN'},
        subtype="FILE_PATH")
    
    target_framerate: StringProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default='auto',
    )
    
    def execute(self, context):
        global osim_path
        mot_path=bpy.path.abspath(self.filepath)
        motion.apply_mot_to_model(mot_path, osim_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}
    

class addForces(bpy.types.Operator,bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mesh.add_osim_forces'
    bl_label = 'Forces'
    bl_description = "Import a `.mot` force file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob : StringProperty(
        name='Force file',
        default="*.mot",
        options={'HIDDEN'},
        subtype="FILE_PATH")
    
    target_framerate: IntProperty(
        name="Target framerate [fps]",
        description="Target framerate for animation in frames-per-second. Lower values will speed up import time.",
        default=30,
        min = 1
    )
    
    def execute(self, context):
        grf_path=bpy.path.abspath(self.filepath)
        forces.import_forces(grf_path, direction='zup', target_framerate=self.target_framerate)
        return {'FINISHED'}


class frameRange(bpy.types.PropertyGroup):
    frame_before: bpy.props.IntProperty(
        name="Frame Before",
        max = 0,
        default = -20
    )
    frame_after: bpy.props.IntProperty(
        name="Frame After",
        min = 0,
        default = 50
    )
    

class trackPoints(bpy.types.Operator):
    bl_idname = 'mesh.track_points'
    bl_label = 'See 3D point motion path'
    bl_description = "Select one or several objects, then click button to see their motion path"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.before_after_frames
        
        # Get selected objects
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}
        
        for obj in selected_objects:
            obj.animation_visualization.motion_path.frame_before = - props.frame_before
            obj.animation_visualization.motion_path.frame_after = props.frame_after
            bpy.ops.object.paths_calculate(display_type='CURRENT_FRAME')
            obj.motion_path.line_thickness = 2
            obj.motion_path.use_custom_color = True
            obj.animation_visualization.motion_path.show_frame_numbers = False
            obj.animation_visualization.motion_path.show_keyframe_highlight = False
            obj.animation_visualization.motion_path.show_keyframe_numbers = False
            obj.animation_visualization.motion_path.show_keyframe_highlight = False
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
        points = bpy.context.active_object
        if points == None:
            ShowMessageBox("Please first select one or several objects", "No object selected")
            raise TypeError("Please first select one or several objects")
        elif points.type == 'CAMERA':
            ShowMessageBox("Selected objects cannot be cameras", "No object selected")
            raise TypeError("Selected objects cannot be cameras")
        else:
            cameras.reproject_3D_points()
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
    
    
    def execute(self, context):
        bpy.ops.wm.alembic_export('INVOKE_DEFAULT')
        return {'FINISHED'}


class panel1(bpy.types.Panel):
    bl_idname = "PANEL1_PT_Pose2Sim_Blender"
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
        layout.operator("mesh.add_osim_markers",icon='MESH_UVSPHERE', text="Markers") 
        layout.operator("mesh.add_osim_model",icon='MESH_MONKEY', text="Model")
        layout.operator("mesh.add_osim_motion",icon='IPO_BACK', text="Motion")
        layout.operator("mesh.add_osim_forces",icon='EMPTY_SINGLE_ARROW', text="Forces") 
        
        layout.label(text='')
        layout.label(text='Other tools')

        layout.operator("mesh.track_points",icon='TRACKING', text='3D point motion path')
        # props = layout.operator("mesh.track_points", text="See 3D Point Motion Path")
        props = context.scene.before_after_frames
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text="Current frame")
        row.prop(props, "frame_before", text="")
        row.label(text="to")
        row.prop(props, "frame_after", text="")
        layout.label(text='')
        
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
    
    bpy.utils.register_class(frameRange)
    bpy.types.Scene.before_after_frames = bpy.props.PointerProperty(type=frameRange)
    bpy.utils.register_class(trackPoints)
    
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
    
    bpy.utils.unregister_class(frameRange)
    bpy.utils.unregister_class(trackPoints)
    del bpy.types.Scene.before_after_frames

    bpy.utils.unregister_class(seeThroughCam)
    bpy.utils.unregister_class(raysFrom3Dpoint)
    bpy.utils.unregister_class(rayFromImagePoint)
    bpy.utils.unregister_class(alembicExport)
    
    bpy.utils.unregister_class(panel1)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    
    
