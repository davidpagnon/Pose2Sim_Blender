import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector

import bmesh

import numpy as np

import math

from xml.dom import minidom

import os.path

from Sim2Blend.common import readNames,loadAnimation

defaultOsimPath='C:\\OpenSim 4.4\\Geometry'

def addModel(osimFile,modelRoot='',stlRoot='.',collection=''):
    if collection=='':
        collection = bpy.data.collections.new('osimModel')  
        bpy.context.scene.collection.children.link(collection)      
    if isinstance(collection,str):
        collection = bpy.data.collections.new(collection)   
        bpy.context.scene.collection.children.link(collection)
    if modelRoot=='':
        modelRoot=os.path.dirname(osimFile)
    print('collection:')
    print(collection)
    xmldoc = minidom.parse(osimFile)
    itemlist = xmldoc.getElementsByTagName('BodySet')
    bodySet=itemlist[0]
    
    bodies=bodySet.getElementsByTagName('Body')
    empties=[0]*len(bodies)
    for i,body in enumerate(bodies): 
        bodyName=body.getAttribute('name')
        #create an empty to be the parent of mesh objects       
        empties[i] = bpy.data.objects.new(bodyName,None)
        collection.objects.link(empties[i])
        #Read meshes that belong to this body
    for i,body in enumerate(bodies): 
        bodyName=body.getAttribute('name')
        meshes=body.getElementsByTagName('Mesh')  
        for mesh in meshes:
            meshName=mesh.getAttribute('name')
            files=mesh.getElementsByTagName('mesh_file')
            scaleFactorElems=mesh.getElementsByTagName('scale_factors')
            scaleFactorStr=scaleFactorElems[0].firstChild.nodeValue
            scaleFactor=[float(x) for x in scaleFactorStr.split()]
            #print(scaleFactor)
            #Create an empty for the mesh to group individual stls into one parent partition        
            #replace filename to stl to import      
            file=files[0]
            filename=file.firstChild.nodeValue
            filename=str.replace(filename,'.vtp','.stl')
            #Check if file exists in modelRoot
            fullFile=os.path.join(modelRoot,filename)
            if not os.path.exists(fullFile):
                fullFile=os.path.join(stlRoot,filename)
                if not os.path.exists(fullFile):
                    fullFile=os.path.join(defaultOsimPath,filename)
                    if not os.path.exists(fullFile):
                        print(filename+' not found, skipping')
                        #TODO Here I could check for just vtp and convert to stl. 
                        continue            
            # rename
            for obj in bpy.data.objects:
                obj.select_set(False)
            bpy.ops.import_mesh.stl(filepath=fullFile)
            print(fullFile)         
            selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
            obj=selected_objects[0]
            obj.scale=scaleFactor
            obj.parent=empties[i]
            obj.users_collection[0].objects.unlink(obj)
            collection.objects.link(obj)            
            
def loadModel(osimFile,csvFile,modelRoot='',stlRoot='.',collection=''):
    if (collection==''):
        collection = bpy.data.collections.new('osimModel')      
        bpy.context.scene.collection.children.link(collection)
    addModel(osimFile,modelRoot=modelRoot,stlRoot=stlRoot,collection=collection)    
    data = np.genfromtxt(csvFile, dtype=float, delimiter=',', names=True,skip_header=0) 
    objectNames=readNames(data.dtype.names[1:])     
    loadAnimation(collection,data,objectNames)
    #bpy.context.scene.update()
    

'''
#Example       
osimFile='G:\\Dropbox (GaTech)\\PvA\\TestScaling\\OsimXML\\EpicLeg13FullBody_L.osim'
osimPath='G:\Dropbox (GaTech)\cursos\8751\CODE\TerrainPark\CAD\STL\Skeleton'
loadModel(osimFile,stlRoot=osimPath)
'''
