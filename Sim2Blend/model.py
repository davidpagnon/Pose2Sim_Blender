#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import OpenSim .osim model into Blender      ##
    ##################################################
    
    Reads an .osim model file, lists bodies and corresponding meshes
    Searches the meshes on the computer, converts them to .stl if only defined as .vtp
    Adds meshes and their parent bodies to the scene and scale them.

    OpenSim API is not required.
    
    INPUTS: 
    - osim_path: path to the .osim model file
    - modelRoot, stlRoot: optional paths
    - collection: optional collection name

    OUTPUTS:
    - Imported .osim model
'''


## INIT
import bpy
import vtk
from xml.dom import minidom
import os


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
def vtp2stl(vtp_path):
    '''
    Convert a .vtp file to .stl
    Save it under the same name in the same folder
    
    OpenSim .vtp file needs vtkXMLPolyDataReader
    Other vtp formats may need vtkGenericDataObjectReader

    INPUT:
    - vtp_path: path to the .vtp file

    OUTPUT:
    - .stl file: same name, same folder
    '''

    if os.path.isfile(vtp_path):
        outfile = os.path.splitext(vtp_path)[0]+".stl"
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(vtp_path)
        reader.Update()
        writer = vtk.vtkSTLWriter()
        writer.SetInputConnection(reader.GetOutputPort())
        writer.SetFileName(outfile)
        writer.Write()


def import_model(osim_path,modelRoot='',stlRoot='.',collection=''):
    '''
    Reads an .osim model file, lists bodies and corresponding meshes
    Searches the meshes on the computer, converts them to .stl if only defined as .vtp
    Adds meshes and their parent bodies to the scene and scale them.

    OpenSim API is not required.
    
    INPUTS: 
    - osim_path: path to the .osim model file
    - modelRoot, stlRoot: optional paths
    - collection: optional collection name

    OUTPUTS:
    - Imported .osim model
    '''

    if collection=='':
        collection = bpy.data.collections.new('osimModel')
        bpy.context.scene.collection.children.link(collection)
    if isinstance(collection,str):
        collection = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(collection)
    if modelRoot=='':
        modelRoot=os.path.dirname(osim_path)
    print('collection:')
    print(collection)
    xmldoc = minidom.parse(osim_path)
    bodySet = xmldoc.getElementsByTagName('BodySet')[0]
    
    bodies=bodySet.getElementsByTagName('Body')
    obj = []
    for i,body in enumerate(bodies): 
    
        # add object to collection
        bodyName=body.getAttribute('name')
        obj += [bpy.data.objects.new(bodyName,None)]
        collection.objects.link(obj[i])
    
        # an object can be composed of several meshes
        meshes=body.getElementsByTagName('Mesh')  
        for mesh in meshes:
            # mesh file and scale factors
            files=mesh.getElementsByTagName('mesh_file')
            scaleFactorElems=mesh.getElementsByTagName('scale_factors')
            scaleFactorStr=scaleFactorElems[0].firstChild.nodeValue
            scaleFactor=[float(x) for x in scaleFactorStr.split()]
            file=files[0]
            filename_vtp=file.firstChild.nodeValue
            filename=str.replace(filename_vtp,'.vtp','.stl')
    
            # Check in different directories if stl or vtp file exists. If only vtp file, convert to stl
            fullFile=os.path.join(modelRoot,'Geometry',filename)    # in model directory?
            if not os.path.exists(fullFile):
                fullFile_vtp=os.path.join(modelRoot,filename_vtp)
                if os.path.exists(fullFile_vtp):
                    vtp2stl(fullFile_vtp)
                else:                                               # in add-on\Sim2Blend\Geometry directory?
                    fullFile=os.path.join(stlRoot,filename)
                    if not os.path.exists(fullFile):
                        fullFile_vtp=os.path.join(stlRoot,filename_vtp)
                        if os.path.exists(fullFile_vtp):
                            vtp2stl(fullFile_vtp)
                        else:                                       # in OpenSim 4.4 Geometry directory?
                            fullFile=os.path.join('C:\\OpenSim 4.4\\Geometry',filename)
                            if not os.path.exists(fullFile): #
                                fullFile_vtp=os.path.join('C:\\OpenSim 4.4\\Geometry',filename_vtp)
                                if os.path.exists(fullFile_vtp):
                                    vtp2stl(fullFile_vtp)
                                else:                       # in other OpenSim Geometry directory?
                                    try:
                                        import opensim
                                        fullFile=os.path.join(f'C:\\OpenSim {opensim.__version__[:3]}\\Geometry',filename)
                                        if not os.path.exists(fullFile):
                                            fullFile_vtp=os.path.join('C:\\OpenSim 4.4\\Geometry',filename_vtp)
                                            if os.path.exists(fullFile_vtp):
                                                vtp2stl(fullFile_vtp)
                                    except:
                                        pass
            
            # import all meshes for each object
            [obj.select_set(False) for obj in bpy.data.objects] # first deselect all
            bpy.ops.import_mesh.stl(filepath=fullFile)
    
            # scale meshes and parent to object
            selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
            mesh_obj=selected_objects[0]
            mesh_obj.scale=scaleFactor
            mesh_obj.parent=obj[i]
            mesh_obj.users_collection[0].objects.unlink(mesh_obj)
            collection.objects.link(mesh_obj)

    # hide axes
    bpy.ops.object.select_by_type(extend=False, type='EMPTY')
    empties = bpy.context.selected_objects
    [empt.hide_set(True) for empt in empties]
            

