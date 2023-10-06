#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import OpenSim .trc markers into Blender     ##
    ##################################################
    
    Computes the coordinates of each opensim bodies in the ground plane
    from a .mot motion file (joint angles) and a .osim model file,
    saves to a .csv file (body positions and orientations).
    Animates a previously loaded .osim model.
    Requires OpenSim API to be installed in Blender (see Readme.md).

    Can also import the resulting csv file,
    in which case OpenSim API is not required.
    
    INPUTS: 
    - mot_path: path to a .mot motion file (joint angles) 
                or to a .csv file (body positions and orientations)
    - osim_path: path to the .osim model file
    - direction: 'zup' or 'yup' (default: 'zup')

    OUTPUTS:
    - mot_path.csv (file with body positions and orientations)
    - Animated .osim model
'''


## INIT
import os
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix

direction = 'zup'
RADIUS=24/1000
FONTSIZE=0.05
OFFSET=(-0.1,0.1,0.1)

## AUTHORSHIP INFORMATION
__author__ = "David Pagnon, Jonathan Camargo"
__copyright__ = "Copyright 2021, BlendOSim & Sim2Blend"
__credits__ = ["David Pagnon", "Jonathan Camargo"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## FUNCTIONS
def import_trc(trc_path):
    '''
    Retrieve data and marker names from trc

    INPUT: 
    - trc_path: path to the .trc file

    OUTPUT:
    - trc_data: 2D numpy array with marker coordinates at each time step
    - markerNames: list of marker names
    '''

    # read data
    trc_data_np = np.loadtxt(trc_path, delimiter="\t", skiprows=5)[:,1:] 
    
    # read marker names
    with open(trc_path) as f:
        for i, line in enumerate(f):
            if i == 2:
                trc_header = f.readline()[12:-3]
            elif i > 4:
                break
    markerNames = trc_header.split('\t\t\t')
    
    return trc_data_np, markerNames


def addMarker(collection,position=(0,0,0),rotation=(0,0,0),text="MARKER"):        
    '''
    
    '''
    
    #Add sphere
    mySphere=bpy.data.meshes.new('sphere')
    sphere = bpy.data.objects.new(text, mySphere)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=RADIUS)
    bm.to_mesh(mySphere)
    bm.free()
    sphere.location=position
    collection.objects.link(sphere)
    
    #Add text
    myFontCurve = bpy.data.curves.new(type="FONT",name="myFontcurve")
    myFontObj = bpy.data.objects.new(text,myFontCurve)
    myFontObj.data.body = text
    myFontObj.data.size=FONTSIZE
    myFontObj.location=np.asarray(position)+np.asarray(OFFSET)
    myFontObj.rotation_euler=(1,0,3.1416)
    myFontObj.parent=sphere
    collection.objects.link(myFontObj)
           
 
def loadMarkers(trc_path):	 
    '''
    
    '''

    # import trc    
    trc_data_np, markerNames = import_trc(trc_path)

    # set framerate
    times = trc_data_np[:,0]
    fps = int(len(times) / (times[-1] - times[0]))
    bpy.data.scenes['Scene'].render.fps = fps
        
    # create markers
    marker_collection = bpy.data.collections.new('markers')
    bpy.context.scene.collection.children.link(marker_collection)
    for markerName in markerNames:
        addMarker(marker_collection,text=markerName)
	
	# animate markers
    for n in range(len(times)):
        for i, m in enumerate(markerNames):
            loc_x = trc_data_np[n,3*i+1]
            loc_y = trc_data_np[n,3*i+2]
            loc_z = trc_data_np[n,3*i+3]
            obj=marker_collection.objects[m]
            obj.location=loc_x,loc_y,loc_z
            obj.keyframe_insert('location',frame=n+1)
            
	

    

''' 
#Example
trc_path = r'D:\softs\github_david\Openpose-to-Opensim\temp\Moco\to_martin_jake\0.Balancing.trc'

'''

