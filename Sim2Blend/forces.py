#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import OpenSim .mot forces into Blender      ##
    ##################################################
    
    Import a .mot force file into Blender.
    OpenSim API is not required.

    INPUTS: 
    - grf_path: path to a .mot force file
    - direction: 'zup' or 'yup' (default: 'zup')

    OUTPUTS:
    - Animated forces
'''


## INIT
import bpy
from mathutils import Vector
import numpy as np
import os

direction = 'zup'
SIZE = 1/1000
COLOR =  (0, 1, 0, 0.8)
rootpath=os.path.dirname(os.path.abspath(__file__))
arrowFile=os.path.join(rootpath,'Geometry','arrow.stl')


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2023, BlendOSim & Sim2Blend"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## FUNCTIONS
def load_grf(grf_path):
    '''
    Retrieve data and header from .mot force file

    INPUT: 
    - grf_path: path to the force .mot file

    OUTPUT:
    - grf_data_np: 2D numpy array with forces at each time step
    - grf_header: time and force names (v: 3*value, p: 3*position, m: 3*moment)
    '''

    # read data
    grf_data_np = np.loadtxt(grf_path, skiprows=7)
    
    # read marker names
    with open(grf_path) as f:
        for i, line in enumerate(f):
            if i == 5:
                grf_header = f.readline().strip().split('\t')
            elif i > 5:
                break
    grf_header = [g.strip() for g in grf_header]
    
    return grf_data_np, grf_header


def addForce(force_collection, forceName='', text="FORCE", color=COLOR):        
    '''
    Add one force vector to the scene

    INPUTS:
    - force_collection: collection to add the force to
    - text: force name (default: "MARKER")
    - color: marker color (default: COLOR)

    OUTPUTS:
    - Created new force
    '''

    # Color
    matg = bpy.data.materials.new("Green")
    matg.use_nodes = True
    tree = matg.node_tree
    nodes = tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    matg.diffuse_color = color

    #Add arrow    
    arrow = bpy.data.objects.new(forceName,None)
    force_collection.objects.link(arrow)
    for obj in bpy.data.objects:
        obj.select_set(False)
    bpy.ops.import_mesh.stl(filepath=arrowFile)
    selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
    obj=selected_objects[0]
    obj.scale=(1,.5,.5)
    obj.parent=arrow
    obj.users_collection[0].objects.unlink(obj)
    obj.active_material = matg
    force_collection.objects.link(obj)
    

def import_forces(grf_path, direction='zup'):    
    '''
    Import a .mot force file into Blender.
    OpenSim API is not required.
    
    INPUTS: 
    - grf_path: path to a .mot force file
    - direction: 'zup' or 'yup' (default: 'zu
    
    OUTPUTS:
    - Animated forces
    '''
    
    # import grf
    grf_data_np, grf_header = load_grf(grf_path)
    grfNames = [g[:-3] for g in grf_header if g.endswith('vx')]

    # set framerate
    times = grf_data_np[:,0]
    fps = int(len(times) / (times[-1] - times[0]))
    bpy.data.scenes['Scene'].render.fps = fps
        
    # create forces
    force_collection = bpy.data.collections.new('Forces')
    bpy.context.scene.collection.children.link(force_collection)
    for forceName in grfNames:        
        addForce(force_collection, forceName=forceName, text=forceName)

    # create arrows
    x_unit_arrow=Vector([1,0,0])
    H_zup = np.array([[1,0,0,0], [0,0,-1,0], [0,1,0,0], [0,0,0,1]])
    for n in range(len(times)):
        for i, f in enumerate(grfNames):
            T = grf_data_np[n, 1+3+9*i : 1+3+9*i+3]
            grf_vec = grf_data_np[n, 1+9*i : 1+9*i+3]
            R = (x_unit_arrow.rotation_difference( Vector(grf_vec).normalized() )).to_matrix()
            H = np.block([ [R,T.reshape(3,1)], [np.zeros(3), 1] ])
            if direction=='zup':
                H = H_zup @ H
            scale_arrow = [Vector(grf_vec).magnitude*SIZE, 1, 1]
            obj = force_collection.objects[f]
            obj.matrix_world = H.T
            obj.scale = scale_arrow
            obj.keyframe_insert('location', frame=n+1)
            obj.keyframe_insert('rotation_euler', frame=n+1)
            obj.keyframe_insert('scale', frame=n+1)

    # hide axes
    bpy.ops.object.select_by_type(extend=False, type='EMPTY')
    empties = bpy.context.selected_objects
    [empt.hide_set(True) for empt in empties]
            