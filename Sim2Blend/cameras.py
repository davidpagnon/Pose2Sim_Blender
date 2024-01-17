#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import/export Cameras, show/film images      ##
    ##################################################
    
    OpenCV not needed
    Reads an .osim model file, lists bodies and corresponding meshes
    Searches the meshes on the computer, converts them to .stl if only defined as .vtp
    Adds meshes and their parent bodies to the scene and scale them.

    OpenSim API is not required.

'''


## INIT
import bpy
# from xml.dom import minidom
# import os
# try:
    # import vtk
# except ImportError:
    # pass


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
def rod_to_mat(rodrigues_vec):
    '''
    Transform Rodrigues vector to rotation matrix without cv2
    https://stackoverflow.com/questions/62345076/how-to-convert-a-rodrigues-vector-to-a-rotation-matrix-without-opencv
-using-pyth
    '''
    rodrigues_vec = rodrigues_vec.flatten()
    theta = np.linalg.norm(rodrigues_vec)
    if theta < sys.float_info.epsilon:
        rotation_mat = np.eye(3, dtype=float)
    else:
        r = rodrigues_vec / theta
        I = np.eye(3, dtype=float)
        r_rT = np.array([
            [r[0]*r[0], r[0]*r[1], r[0]*r[2]],
            [r[1]*r[0], r[1]*r[1], r[1]*r[2]],
            [r[2]*r[0], r[2]*r[1], r[2]*r[2]]
        ])
        r_cross = np.array([
            [0, -r[2], r[1]],
            [r[2], 0, -r[0]],
            [-r[1], r[0], 0]
        ])
        rotation_mat = np.cos(theta) * I + (1 - np.cos(theta)) * r_rT + np.sin(theta) * r_cross
    return rotation_mat

def mat_to_rod(rotation_mat):
    '''
    Transform rotation matrix to Rodrigues vector without cv2
    https://docs.opencv.org/4.2.0/d9/d0c/group__calib3d.html#ga61585db663d9da06b68e70cfbf6a1eac
    '''
    tr = np.trace(rotation_mat) # tr=1+2cos(theta)
    if tr == 3.0: # no rotation
        return np.array([0.,0.,0.])
    theta = np.arccos((tr-1)/2)

    r_cross_sin = (rotation_mat - rotation_mat.T) /2
    r_sin = np.array([-r_cross_sin[1][2], r_cross_sin[0][2], -r_cross_sin[0][1]])
    r_vec = r_sin / np.sin(theta)
    r_vec *= theta
    return r_vec

def import_cameras(toml_path):
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


def import_model(osim_path,modelRoot='',stlRoot='.',collection=''):
    '''
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
        collection = bpy.data.collections.new('osimModel')
        bpy.context.scene.collection.children.link(collection)
    if isinstance(collection,str):
        collection = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(collection)
    if modelRoot=='':
        modelRoot=os.path.dirname(osim_path)
    
    geometry_directories = [os.path.join(modelRoot,'Geometry'), stlRoot, 'C:\\OpenSim 4.4\\Geometry']
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
        obj += [bpy.data.objects.new(bodyName,None)]
        collection.objects.link(obj[i])
    
        # an object can be composed of several meshes
        meshes=body.getElementsByTagName('Mesh')  
        for mesh in meshes:
            # import mesh file
            files=mesh.getElementsByTagName('mesh_file')
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
                if os.path.exists(fullFile_stl):
                    bpy.ops.import_mesh.stl(filepath=fullFile_stl)
                    break
                elif os.path.exists(fullFile_ply):
                    bpy.ops.import_mesh.ply(filepath=fullFile_ply)
                    break
                elif os.path.exists(fullFile_vtp):
                    try:
                        vtp2stl(fullFile_vtp)
                        bpy.ops.import_mesh.stl(filepath=fullFile_stl)
                    except:
                        print('VTK not installed on Blender. Try Sim2Blend Full install instead')
                    break
            else:
                print(f'File {filename_stl} or {filename_vtp} not found on system')
                raise Exception(f'File {filename_stl} or {filename_vtp} not found on system')
            
            # scale meshes and parent to object
            selected_objects = [ o for o in bpy.context.scene.objects if o.select_get() ]
            mesh_obj=selected_objects[0]
            mesh_obj.scale=scaleFactor
            try:
                # mesh_obj.location = [float(t) for t in mesh.parentNode.parentNode.getElementsByTagName('translation')[0].firstChild.nodeValue.split()]
                mesh_obj.rotation_euler = [float(t) for t in mesh.parentNode.parentNode.getElementsByTagName('orientation')[0].firstChild.nodeValue.split()]
            except:
                pass
            mesh_obj.parent=obj[i]
            mesh_obj.users_collection[0].objects.unlink(mesh_obj)
            collection.objects.link(mesh_obj)

    # hide axes
    bpy.ops.object.select_by_type(extend=False, type='EMPTY')
    empties = bpy.context.selected_objects
    [empt.hide_set(True) for empt in empties]
            

