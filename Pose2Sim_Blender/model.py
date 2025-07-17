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
from xml.dom import minidom
import os
from Pose2Sim_Blender.Pose2Sim_Blender.common import createMaterial
try:
    import vtk
except ImportError:
    pass

COLOR = (0.8, 0.8, 0.8, 1)


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
        print(f'{vtp_path} file converted')


def import_model(osim_path, modelRoot='',stlRoot='.',collection='', color = COLOR):
    '''osim_path
    Reads an .osim model file, lists bodies and corresponding meshes
    Searches the meshes (stl, ply, vtp) on the computer, 
    converts them to .stl if only defined as .vtp
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
        collection = bpy.data.collections.new(os.path.basename(osim_path))
        bpy.context.scene.collection.children.link(collection)
    if isinstance(collection,str):
        collection = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(collection)
    if modelRoot=='':
        modelRoot=os.path.dirname(osim_path)
    
    geometry_directories = [os.path.join(modelRoot,'Geometry'), stlRoot, 'C:\\OpenSim 4.5\\Geometry']
    try:
        import opensim as osim
        geometry_directories.append(os.path.join('C:\\', f'OpenSim {osim.__version__[:3]}', 'Geometry'))
    except ImportError:
        pass
    
    xmldoc = minidom.parse(osim_path)
    bodySet = xmldoc.getElementsByTagName('BodySet')[0]
    bodies=bodySet.getElementsByTagName('Body')
    obj = []
    for i,body in enumerate(bodies): 
        # add object to collection
        bodyName=body.getAttribute('name')

        try:
            physicalOffset_translation = body.getElementsByTagName('components')[0].getElementsByTagName('PhysicalOffsetFrame')[0].getElementsByTagName('translation')[0].firstChild.nodeValue
            physicalOffset_translation = [float(x) for x in physicalOffset_translation.split()]
        except: 
            physicalOffset_translation = [0., 0., 0.]
        
        obj += [bpy.data.objects.new(bodyName,None)]
        collection.objects.link(obj[i])
    
        # an object can be composed of several meshes
        print('\nImporting ',bodyName)
        meshes=body.getElementsByTagName('Mesh')  
        for mesh in meshes:
            # import mesh file
            files=mesh.getElementsByTagName('mesh_file')
            # print([file.firstChild.nodeValue for file in files])
            scaleFactorElems=mesh.getElementsByTagName('scale_factors')
            scaleFactorStr=scaleFactorElems[0].firstChild.nodeValue
            scaleFactor=[float(x) for x in scaleFactorStr.split()]
            file=files[0]
            filename_vtp=file.firstChild.nodeValue
            filename_stl=str.replace(filename_vtp,'.vtp','.stl')
            filename_ply=str.replace(filename_vtp,'.vtp','.vtp.ply')
            bpy.ops.object.select_all(action='DESELECT')
            
            for dir in geometry_directories:
                fullFile_stl = os.path.join(dir, filename_stl)
                fullFile_ply = os.path.join(dir, filename_ply)
                fullFile_vtp = os.path.join(dir, filename_vtp)
                # print(f'{fullFile_ply} exists: {os.path.exists(fullFile_ply)}')
                if os.path.exists(fullFile_stl):
                    bpy.ops.wm.stl_import(filepath=fullFile_stl)
                    # bpy.ops.import_mesh.stl(filepath=fullFile_stl)
                    break
                elif os.path.exists(fullFile_ply):
                    bpy.ops.wm.ply_import(filepath=fullFile_ply)
                    break
                elif os.path.exists(fullFile_vtp):
                    try:
                        vtp2stl(fullFile_vtp)
                        bpy.ops.wm.stl_import(filepath=fullFile_stl)
                    except:
                        print('VTK not installed on Blender. Try Pose2Sim_Blender Full install instead')
                    break
            else:
                print(f'File {filename_stl} or {filename_ply} or {filename_vtp} not found on system')
                # raise Exception(f'File {filename_stl} or {filename_ply} or {filename_vtp} not found on system')
            
            # Scale meshes
            selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
            mesh_obj=selected_objects[0]
            mesh_obj.scale=scaleFactor
            
            # Translation and rotation of PhysicalOffsetFrame if exists
            translation_nodes = [node for node in mesh.parentNode.parentNode.childNodes if node.nodeName == "translation"]
            if translation_nodes:
                translation_text = translation_nodes[0].firstChild.nodeValue
                mesh_obj.location = [float(t) for t in translation_text.split()]
            rotation_nodes = [node for node in mesh.parentNode.parentNode.childNodes if node.nodeName == "orientation"]
            if rotation_nodes:
                rotation_text = rotation_nodes[0].firstChild.nodeValue
                mesh_obj.rotation_euler = [float(t) for t in rotation_text.split()]
        
            # Parent meshes to object in collection
            mesh_obj.parent=obj[i]
            mesh_obj.users_collection[0].objects.unlink(mesh_obj)
            collection.objects.link(mesh_obj)

    # hide axes, add material, add smooth shading
    objects = collection.objects
    for obj in objects:
        matg = createMaterial(color=COLOR, metallic = 0., roughness = 0.5)
        obj.active_material = matg
        for mesh in obj.children:
            for polygon in mesh.data.polygons:
                polygon.use_smooth = True
    for obj in objects:
        obj.select_set(obj.type == "EMPTY")
    empties = bpy.context.selected_objects
    [empt.hide_set(True) for empt in empties]
    
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
    
    print(f'OpenSim model imported from {osim_path}')
            

