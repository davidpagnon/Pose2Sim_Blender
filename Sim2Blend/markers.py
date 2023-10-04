import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector

import bmesh

import numpy as np

import math

from blendosim.common import data2keyframes, loadAnimation, readNames

def addMarker(collection,position=(0,0,0),rotation=(0,0,0),text="MARKER"):        
    #Add a marker to 3d space    

    # Constants
    DIAMETER=12/1000    
    FONTSIZE=0.05
    OFFSET=(-0.1,0.1,0.1)
    
    #Add sphere
    mySphere=bpy.data.meshes.new('sphere')
    sphere = bpy.data.objects.new(text, mySphere)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16,diameter=DIAMETER)
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
           
 
def loadMarkers(csvFileName):	 
	data = np.genfromtxt(csvFileName, dtype=float, delimiter=',', names=True,skip_header=0) 
	markerNames=readNames(data.dtype.names[1:])	
	####Create markers
	newCol = bpy.data.collections.new('markers')
	bpy.context.scene.collection.children.link(newCol)
	for markerName in markerNames:
		addMarker(newCol,text=markerName)
	#bpy.context.scene.update()
	a=bpy.data.collections['markers']
	loadAnimation(a,data,markerNames)

    

''' 
#Example
fileName='G:\\Dropbox (GaTech)\\PvA\\TestScaling\\test.csv' 
loadMarkers(fileName)
'''