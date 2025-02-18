#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import OpenSim .trc markers into Blender     ##
    ##################################################
    
    Import a .trc marker file into Blender.
    OpenSim API is not required.

    INPUTS: 
    - trc_path: path to a .trc marker file
                or to a a .c3d marker file
    - direction: 'zup' or 'yup' (default: 'zup')

    OUTPUTS:
    - Animated markers
'''


## INIT
import os
import numpy as np
import bpy
import bmesh
from .common import ShowMessageBox, createMaterial
from .skeletons import *
from anytree import  PreOrderIter


direction = 'zup'
RADIUS = 20/1000 # 12
COLOR =  (0, 1, 0, 0.8)


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2023, BlendOSim & Pose2Sim_Blender"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.7.0"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## FUNCTIONS
def find_first_children_with_id(armature_tree):
    '''
    Recursively find the first children of an anytree tree that have an id
    
    INPUTS:
    - armature_tree: AnyTree tree
    
    OUTPUTS:
    - first_children: the first children of the tree that have an ID
    '''

    first_children = []
    for child in armature_tree.children:
        if child.id is not None:
            first_children.append(child.name)
        else:
            # Recursively check the child's descendants
            first_children.extend(find_first_children_with_id(child))
    return first_children


def load_trc(trc_path):
    '''
    Retrieve data and marker names from trc

    INPUT: 
    - trc_path: path to the .trc file

    OUTPUT:
    - trc_data_np: 2D numpy array with marker coordinates at each time step
    - markerNames: list of marker names
    '''

    # read data
    trc_data_np = np.genfromtxt(trc_path, skip_header=5, delimiter = '\t')
    
    # read marker names
    with open(trc_path) as f:
        for i, line in enumerate(f):
            if i == 2:
                trc_header = f.readline()[12:-3]
            elif i > 2:
                break
    markerNames = trc_header.split('\t\t\t')
    
    return trc_data_np, markerNames


def addMarker(marker_collection, position=(0,0,0), text="MARKER", material=bpy.types.Material):
    '''
    Add one marker to the scene

    INPUTS:
    - marker_collection: collection to add the marker to
    - position: marker position (default: (0,0,0))
    - text: marker name (default: "MARKER")
    - color: marker color (default: COLOR)

    OUTPUTS:
    - Created new marker
    '''

    mySphere=bpy.data.meshes.new('sphere')
    sphere = bpy.data.objects.new(text, mySphere)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=RADIUS)
    bm.to_mesh(mySphere)
    bm.free()
    sphere.location=position
    sphere.active_material = material
    marker_collection.objects.link(sphere)
           

def create_armature_trc(armature_tree, armature_name):
    '''
    Creates an armature and sets up the bone hierarchy based on the given tree.
    Constrain armature to marker spheres.

    INPUTS:
    - armature_tree: anytree hierarchy of bones
    - armature_name: name of the armature object

    OUTPUTS:
    - Created armature with bones and constraints
    '''
    
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # Create armature object
    armature_data = bpy.data.armatures.new(armature_name)
    armature_object = bpy.data.objects.new(armature_name, armature_data)
    bpy.context.collection.objects.link(armature_object)
    bpy.context.view_layer.objects.active = armature_object
    armature_object.display_type = 'WIRE'
    armature_data.display_type = 'OCTAHEDRAL'

    # Set the current frame to the middle of the animation (points are sometimes not well detected at the end of the animation)
    marker_collection = bpy.data.collections[armature_name+'.trc']
    first_marker = marker_collection.objects[0]
    frame_start, frame_end = first_marker.animation_data.action.frame_range
    bpy.context.scene.frame_set(int((frame_start + frame_end) / 2))    

    # Create bones (Edit mode)
    bpy.ops.object.mode_set(mode='EDIT')
    bones = {}
    for node in PreOrderIter(armature_tree):
        bone = armature_data.edit_bones.new(node.name)
        bones[node.name] = bone
        if node.parent:
            # tail (child)
            try:
                child_name = node.name
                tail_marker = [o for o in marker_collection.objects if o.name.strip()==child_name][0]
            except:
                print(f'Could not find {child_name} in the TRC file.')
                continue
            # head (parent)
            try:
                parent_name = node.parent.name
                head_marker = [o for o in marker_collection.objects if o.name.strip()==parent_name][0]
            except:
                print(f'Could not find {parent_name} in the TRC file.')
                continue
            bone.tail = tail_marker.location
            bone.head = head_marker.location
            bone.parent = bones[node.parent.name]
            

    # Create IK rig (pose mode)
    bpy.ops.object.mode_set(mode='POSE')
    first_children = find_first_children_with_id(armature_tree)
    for node in PreOrderIter(armature_tree):
        bone_name = node.name
        bone = armature_object.pose.bones.get(bone_name)
        if bone and node.parent:
            # Constrain bone to sphere animation
            head_marker = [o for o in marker_collection.objects if o.name.strip()==node.name][0]
            armature_object.data.bones.active = armature_object.data.bones.get(bone_name)
            # IK from child to parent
            ik_constraint = bone.constraints.new(type='IK')
            ik_constraint.target = head_marker
            ik_constraint.chain_count = 1
            # Copy location of root bone
            if node.parent.name in first_children:
                copy_loc_constraint = bone.constraints.new(type='COPY_LOCATION')
                copy_loc_constraint.target = [o for o in marker_collection.objects if o.name.strip()==node.parent.name][0]
        
    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')


def create_armature_c3d(armature_tree):
    '''
    /!\ DOES NOT WORK!
    Left if for future reference in case me or anyone else find time to fix it.
    
    Edit the armature from c3d_importer (bones created without a hierarchy)
    to give it a hierarchy, with the head of each bones at the tail of its parents.

    Creates an armature and sets up the bone hierarchy based on the given tree.
    Sets the head of each bone to its parent's tail and the tail to its world coordinates.
    '''

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # Select last created armature
    for obj in reversed(bpy.context.scene.objects):
        if obj.type == 'ARMATURE':
            armature_object = obj
            break
    armature_data = armature_object.data
    bpy.context.view_layer.objects.active = armature_object
    armature_object.display_type = 'WIRE'
    armature_data.display_type = 'OCTAHEDRAL'
    
    # Set the current frame to the middle of the animation
    frame_range = armature_object.animation_data.action.frame_range
    frame_start, frame_end = frame_range
    bpy.context.scene.frame_set(int((frame_start + frame_end) / 2))

    # THIS LOOKS OKAY IN POSE MODE (ONE SINGLE FRAME, WITH NO CONNECTION BETWEEN JOINTS)
    # bone.use_connect = True LEADS TO NO CREATION OF BONE OTHER THAN ROOT (DELETED BECAUSE HEAD == TAIL?)
    # Bone hierarchy (Edit mode)  
    bpy.ops.object.mode_set(mode='EDIT')
    bones = {}
    for node in PreOrderIter(armature_tree):
        bone_name = node.name
        bone = armature_data.edit_bones[bone_name]
        bones[bone_name] = bone
        if node.parent:
            parent_name = node.parent.name
            parent_bone = armature_data.edit_bones[parent_name]
            if parent_bone:
                bone.parent = parent_bone
    
    # Reset all the poses to zero
    bpy.ops.object.mode_set(mode='POSE')
    bone_world_locs = {}
    for bone in armature_object.pose.bones:
        bone_world_locs[bone.name] = bone.location.copy()
    for node in PreOrderIter(armature_tree):
        bone_name = node.name
        bone = armature_object.pose.bones[bone_name]
        bone_prev_loc = bone_world_locs[bone_name]
        if node.parent:
            parent_bone_name = node.parent.name
            parent_bone = armature_object.pose.bones[parent_bone_name]
            parent_bone_prev_loc = bone_world_locs[parent_bone_name]
            bone.location = bone_prev_loc - parent_bone_prev_loc
            

    # # THIS LOOKS OKAY IN EDIT MODE, ONE SINGLE FRAME
    # # Bone hierarchy (Edit mode)
    # bone_world_locs = {}
    # for bone in armature_object.pose.bones:
        # bone_world_locs[bone.name] = bone.matrix.translation.copy()    
    # bpy.ops.object.mode_set(mode='EDIT')
    # bones = {}
    # for node in PreOrderIter(armature_tree):
        # bone_name = node.name
        # bone = armature_data.edit_bones[bone_name]
        # bones[bone_name] = bone
        # bone_world_loc = bone_world_locs.get(bone_name)
        # if node.parent:
            # parent_name = node.parent.name
            # parent_bone = bones.get(parent_name)
            # parent_bone_world_loc = bone_world_locs.get(parent_name)
            # if parent_bone:
                # bone.parent = parent_bone
                # # bone.use_connect = True
                # bone.head = parent_bone_world_loc
                # bone.tail = bone_world_loc

    bpy.ops.object.mode_set(mode='OBJECT')

 
def import_trc(trc_path, direction='zup', target_framerate=30, armature_type=None):
    '''
    Import a .trc marker file into Blender.
    OpenSim API is not required.

    INPUTS: 
    - trc_path: path to a .trc marker file
    - direction: 'zup' or 'yup' (default: 'zup')
    - armature_type: None or string (name of the model from skeletons.py, 'halpe_26' for example)

    OUTPUTS:
    - Animated markers
    '''

    # TRC file
    if trc_path.endswith('.trc'):
        # import trc    
        trc_data_np, markerNames = load_trc(trc_path)

        # set framerate
        bpy.context.scene.render.fps = target_framerate
        
        times = trc_data_np[:,1]
        first_frame = int(trc_data_np[0,0])
        fps = round((len(times)-1) / (times[-1] - times[0]))
        conv_fac_frame_rate = int(np.round(fps / target_framerate))
        if conv_fac_frame_rate == 0:
            conv_fac_frame_rate = 1
        # bpy.data.scenes['Scene'].render.fps = fps
            
        # create markers
        marker_collection = bpy.data.collections.new(os.path.basename(trc_path))
        bpy.context.scene.collection.children.link(marker_collection)
        for markerName in markerNames:
            matg = createMaterial(color=COLOR, metallic = 0.5, roughness = 0.5)
            addMarker(marker_collection,text=markerName, material=matg)

        # animate markers
        for i, m in enumerate(markerNames):
            coll_marker_names = [ob.name for ob in marker_collection.objects]
            m = [coll_m for coll_m in coll_marker_names if m == coll_m][0]
            for n in range(0, len(times), conv_fac_frame_rate):
                # y-up to z-up
                if direction=='zup':
                    # loc_x = trc_data_np[n,3*i+4]
                    # loc_y = trc_data_np[n,3*i+2]
                    # loc_z = trc_data_np[n,3*i+3]
                    loc_x = trc_data_np[n,3*i+2]
                    loc_y = -trc_data_np[n,3*i+4]
                    loc_z = trc_data_np[n,3*i+3]
                else:
                    loc_x = trc_data_np[n,3*i+2]
                    loc_y = trc_data_np[n,3*i+4]
                    loc_z = trc_data_np[n,3*i+3]                    
                obj=marker_collection.objects[m]
                obj.location=loc_x,loc_y,loc_z
                obj.keyframe_insert('location',frame=first_frame+int(n/conv_fac_frame_rate))
        [ob.select_set(True) for ob in marker_collection.objects]
                
        # create armature
        armature_name = os.path.splitext(os.path.basename(trc_path))[0]
        if armature_type.upper() != 'NONE':
            armature_tree = eval(armature_type.upper())
            create_armature_trc(armature_tree, armature_name)
        
    
    # C3D file
    elif trc_path.endswith('.c3d'):
        bpy.ops.preferences.addon_enable(module='io_anim_c3d')
        from io_anim_c3d import c3d_importer
        operator = bpy.types.Operator
        c3d_importer.load(operator, bpy.context, \
                          filepath = trc_path, \
                          use_manual_orientation=True, axis_forward='Y', axis_up='Z')
                          
        # Shift animation one frame back
        for obj in reversed(bpy.context.scene.objects): # last created armature
            if obj.type == 'ARMATURE':
                armature_object = obj
                break
        action = armature_object.animation_data.action
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.co.x -= 1

        # create armature
        # Rigged armature not supported for c3d files. Feel free to contribute!
        armature_name = os.path.splitext(os.path.basename(trc_path))[0]
        if armature_type.upper() != 'NONE':
            ShowMessageBox("Rigged armature not supported for c3d files. Feel free to contribute!", "Not supported")
            
            # armature_tree = eval(armature_type.upper())
            # create_armature_c3d(armature_tree)
        
    print(f'Marker data imported from {trc_path}')
