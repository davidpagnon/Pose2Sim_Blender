#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import/export Cameras, show/film images      ##
    ##################################################
    
    OpenCV or OpenSim not needed
    Reads a .toml calibration file and imports cameras

'''


## INIT
import bpy
import mathutils
import numpy as np
import os
import toml
import sys


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon"
__copyright__ = "Copyright 2023, Sim2Blend"
__credits__ = ["David Pagnon"]
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


def world_to_camera_persp(r, t):
    '''
    Converts rotation R and translation T 
    from Qualisys world centered perspective
    to OpenCV camera centered perspective
    and inversely.

    Qc = RQ+T --> Q = R-1.Qc - R-1.T
    '''

    r = r.T
    t = - r @ t

    return r, t
    

def set_loc_rotation(obj, value):
    '''
    Rotate object around local axis
    See https://blender.stackexchange.com/a/255375/174689
    '''
    
    rot = mathutils.Euler(value, 'ZYX')
    obj.rotation_euler = (obj.rotation_euler.to_matrix() @ rot.to_matrix()).to_euler(obj.rotation_mode)
    
    
def retrieveCal(toml_path):
    '''
    Retrieve calibration parameters from toml file.
    Output a dialog window to choose calibration file.
    '''
    S, D, K, R, T, P = {}, {}, {}, {}, {}, {}
    Kh, H = [], []
    cal = toml.load(toml_path)
    cal_keys = [i for i in cal.keys() if 'metadata' not in i] # exclude metadata key
    for i, cam in enumerate(cal_keys):
        S[cam] = np.array(cal[cam]['size'])
        D[cam] = np.array(cal[cam]['distortions'])
        
        K[cam] = np.array(cal[cam]['matrix'])
        Kh = np.block([K[cam], np.zeros(3).reshape(3,1)])
        
        R[cam] = rod_to_mat(np.array(cal[cam]['rotation']))
        T[cam] = np.array(cal[cam]['translation'])
        H = np.block([[R[cam],T[cam].reshape(3,1)], [np.zeros(3), 1 ]])
        
        P[cam] = Kh.dot(H)
        
    return S, D, K, R, T, P


def setCamsfromCal_callback(*args):
    '''
    Set cameras from calibration file.
    Create cameras according to the calibration file chosen from dialog window.
    '''
    px_size = float(cmds.textFieldGrp(pxsize_field, query=1, text=1)) * 1e-6
    binning_factor = float(cmds.textFieldGrp(binning_field, query=1, text=1))
    
    # open file dialog (fm = 0 pour sauver plutot qu'ouvrir)
    singleFilter = "Toml calibration files (*.toml)"
    path = cmds.fileDialog2(fileFilter=singleFilter, dialogStyle=2, cap="Open Calibration File", fm=1)[0]
    # retrieve calibration
    S, D, K, R, T, P = maya_utils.retrieveCal(path)
    
    # set cameras
    cams=[]
    for c in range(len(R)): # Pour chaque cam
        Rc =  R['cam_%02d' %(c+1)].T
        Tc = -R['cam_%02d' %(c+1)].T . dot(T['cam_%02d' %(c+1)])# / 1000 # Pour l'avoir en m
        M = np.block([[Rc,Tc.reshape(3,1)], [np.zeros(3), 1 ]])
        Mlist = M.T.reshape(1,-1)[0].tolist()
        
        fm = K['cam_%02d' %(c+1)][0, 0] * px_size * 1000 # fp*px*1000 [mm]
        
        W, H = S['cam_%02d' %(c+1)]        
        
        cam, camShape = cmds.camera(n='cam_%02d' %(c+1), focalLength=fm, horizontalFilmAperture = W*px_size*39.3701*binning_factor, verticalFilmAperture = H*px_size*39.3701*binning_factor)  # m->inch : *39.3701
        cams.append(cam) 

        cmds.setAttr(camShape + '.aiRadialDistortion', float(-D['cam_%02d' %(c+1)][0]*4)) # Cuisine pour passer de la distorsion de maya (fisheye?) a celle de opencv (pinhole?)
        cmds.xform(cam, m=Mlist)
        cmds.setAttr("defaultResolution.width", float(W)) 
        cmds.setAttr("defaultResolution.height", float(H)) 
        cmds.select(cam)
        cmds.rotate(180,0,0, objectSpace=1, relative=1)

    cmds.select(cams)
    cmds.group(n='cameras')


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
    
    if os.path.isfile(toml_path):
        outfile = os.path.splitext(toml_path)[0]+".toml"
        S, D, K, R, T, P = retrieveCal(toml_path)
        
        cam_collection = bpy.data.collections.new('importedCameras')
        bpy.context.scene.collection.children.link(cam_collection)
        
        for i, c in enumerate(S.keys()):
            bpy.ops.object.camera_add()
            camera = bpy.context.active_object
            camera.name = c
            
            # image dimensions
            w, h = [int(i) for i in S[c]]
            
            # field of view
            fx, fy = K[c][0,0], K[c][1,1]
            fov_x = 2 * np.arctan2(w, 2 * fx)
            fov_y = 2 * np.arctan2(h, 2 * fy)
            
            camera.data.type = 'PERSP'
            camera.data.lens_unit = 'FOV'
            camera.data.angle = np.max([fov_x, fov_y])
            
            # rotation and translation
            r, t = world_to_camera_persp(R[c], T[c])
            homog_matrix = np.block([[r,t.reshape(3,1)], 
                                    [np.zeros(3), 1 ]])
            camera.matrix_world = mathutils.Matrix(homog_matrix)
            set_loc_rotation(camera, np.radians([180,0,0]))
            
            # principal point # see https://blender.stackexchange.com/a/58236/174689
            principal_point =  K[c][0,2],  K[c][1,2]
            max_wh = np.max([w,h])
            
            camera.data.shift_x = -2/max_wh*(w/2 - principal_point[0])
            camera.data.shift_y = 2/max_wh*(h/2 - principal_point[1])

            # render settings
            render_settings = bpy.context.scene.render
            render_settings.resolution_x = w
            render_settings.resolution_y = h
            
            
            cam_collection.objects.link(camera)
        
        scene = bpy.context.scene
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.length_unit = 'METERS'
        scene.unit_settings.scale_length = 1.0
            
        
        print(f'Cameras imported from {toml_path} calibration file.')



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
            

