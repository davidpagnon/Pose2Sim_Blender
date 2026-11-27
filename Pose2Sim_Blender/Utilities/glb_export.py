#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Export the scene to glTF binary (.glb)       ##
    ##################################################

    Exports skeletons, markers, forces, and/or cameras to .glb.
    Videos, images, camera distortion and principal point are not exported.
    Each kind can be included or left out.
    Bakes it all in one single clip.
'''


## INIT
import math
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
def descendants(obj):
    '''
    All children, grand-children, etc. of an object
    '''

    out = []
    for child in obj.children:
        out.append(child)
        out.extend(descendants(child))
    return out


def is_exported(obj, view_layer):
    '''
    Objects that are in the view layer and not hidden
    '''

    return obj.name in view_layer.objects and not obj.hide_get() and not obj.hide_viewport


def animation_range(context):
    '''
    First and last frame where something visible is animated (union of the visible
    objects' actions), or None if nothing is animated.
    The scene range is often longer than the data (e.g., default 0-250 for a 98-frame motion).
    '''

    view_layer = context.view_layer
    starts, ends = [], []
    for obj in context.scene.objects:
        if not is_exported(obj, view_layer):
            continue
        for anim in (obj.animation_data, getattr(obj.data, 'animation_data', None)):
            if anim and anim.action:
                start, end = anim.action.frame_range
                starts.append(start)
                ends.append(end)
    if not starts:
        return None
    return math.floor(min(starts)), math.ceil(max(ends))


def classify(obj):
    '''
    Kind of an object: 'cameras', 'skeletons', 'markers', 'forces', 'images',
    or None (unknown, e.g. lights).

    The "pose2sim_type" custom property is used when present.
    Otherwise, heuristic: an armature, or anything parented under one, is a skeleton;
    any other empty or mesh is a marker.
    '''

    tag = obj.get("pose2sim_type")
    if tag in ('marker', 'skeleton', 'force'):
        return tag + 's'
    if obj.type == 'CAMERA':
        return 'cameras'
    if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        return 'images'
    if obj.type == 'ARMATURE':
        return 'skeletons'
    parent = obj.parent
    while parent:
        if parent.type == 'ARMATURE':
            return 'skeletons'
        parent = parent.parent
    if obj.type in ('EMPTY', 'MESH'):
        return 'markers'
    return None


def armature_root(obj):
    '''
    Nearest armature among the ancestors of an object, or None
    '''

    parent = obj.parent
    while parent:
        if parent.type == 'ARMATURE':
            return parent
        parent = parent.parent
    return None


def export_to_glb(filepath, skeletons=True, markers=True, forces=True, cameras=True):
    '''
    Export the selected kinds of objects to a .glb file.
    Images/videos are never exported.

    INPUTS:
    - filepath: output .glb path
    - skeletons, markers, forces, cameras: whether to export each kind
    '''

    context = bpy.context
    view_layer = context.view_layer
    scene = context.scene
    scene_range = (scene.frame_start, scene.frame_end)
    wanted = {'skeletons': skeletons, 'markers': markers, 'forces': forces, 'cameras': cameras}
    hidden_by_us = []
    moved = []   # (object, original collections, target collections)
    # Move skeleton meshes into the armature collection for glb export and move it back afterwards
    # Otherwise the export duplicates the skeleton meshes, because it reaches it both through its parent bone and its collection
    try:
        if skeletons:
            for obj in list(scene.objects):
                # Skip armature and non-skeleton objects (markers, cameras, forces)
                if obj.type == 'ARMATURE' or classify(obj) != 'skeletons':
                    continue
                armature = armature_root(obj)
                if armature is None:
                    continue
                # Move from original to target
                original = list(obj.users_collection)
                target = list(armature.users_collection)
                if set(original) == set(target):
                    continue
                for col in target:
                    if obj.name not in col.objects:
                        col.objects.link(obj)
                for col in original:
                    if col not in target:
                        col.objects.unlink(obj)
                moved.append((obj, original, target))

        # Hide image/video planes (not exportable by gltf) and unselected object kinds
        for obj in scene.objects:
            kind = classify(obj)
            if is_exported(obj, view_layer) and (kind == 'images' or wanted.get(kind) is False):
                obj.hide_set(True)
                hidden_by_us.append(obj)

        # Skip hidden objects and their children
        for obj in list(view_layer.objects):
            if obj.hide_get() or obj.hide_viewport:
                for child in descendants(obj):
                    if child.name in view_layer.objects and not child.hide_get():
                        child.hide_set(True)
                        hidden_by_us.append(child)

        # Only bake frame range with visible animations
        anim_range = animation_range(context)
        if anim_range:
            scene.frame_start, scene.frame_end = anim_range

        view_layer.update()
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',
            use_visible=True,
            use_selection=False,
            export_cameras=cameras,
            export_skins=skeletons,
            export_animations=True,
            export_animation_mode='SCENE',           # bake what is seen, including constraint-driven skeletons
            export_anim_scene_split_object=False,    # in one single clip
            export_force_sampling=True,              # bake every frame
            export_hierarchy_full_collections=True,  # keep collections
            export_apply=False,
        )

    # Relink each object to its original collections and unlink it from the target ones
    # and restores frame rage
    finally:
        scene.frame_start, scene.frame_end = scene_range
        for obj, original, target in moved:
            if obj.name not in bpy.data.objects:
                continue
            for col in original:
                if obj.name not in col.objects:
                    col.objects.link(obj)
            for col in target:
                if col not in original and obj.name in col.objects:
                    col.objects.unlink(obj)
        for obj in hidden_by_us:
            if obj.name in bpy.data.objects:
                obj.hide_set(False)