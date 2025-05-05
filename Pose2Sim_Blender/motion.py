#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import OpenSim .mot motion into Blender      ##
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
from .common import ShowMessageBox

direction = 'zup'
export_to_csv = True


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
def apply_mot_to_model(mot_path, osim_path, direction='zup', target_framerate='auto'):
    '''
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

    # Retrieve previously loaded model
    collection = bpy.context.collection
    if collection == None or collection == bpy.data.scenes['Scene'].collection:
        ShowMessageBox("First select a model in the outliner", "No OpenSim model found")
        raise('First select a model in the outliner.')
    
    # If chosen file is .mot (joint angles)
    if os.path.splitext(mot_path)[1] == '.mot':
        # read model and motion files
        try:
            import opensim as osim
        except:
            ShowMessageBox("OpenSim API required: Please proceed to Pose2Sim_Blender full install", "OpenSim API required")
            raise('OpenSim API required: Please proceed to Pose2Sim_Blender full install.')
            
        model = osim.Model(osim_path)
        motion_data = osim.TimeSeriesTable(mot_path)

        # set framerate
        times = motion_data.getIndependentColumn()
        fps = round((len(times)-1) / (times[-1] - times[0]))
        first_frame = round(times[0]*fps)
        if target_framerate == 'auto':
            target_framerate = fps
        target_framerate = round(target_framerate)
        bpy.context.scene.render.fps = target_framerate
        conv_fac_frame_rate = fps // target_framerate
        if conv_fac_frame_rate == 0:
            conv_fac_frame_rate = 1
        # bpy.data.scenes['Scene'].render.fps = fps

        # model: get model coordinates and bodies
        model_coordSet = model.getCoordinateSet()
        model_bodySet = model.getBodySet()
        bodies = [model_bodySet.get(i) for i in range(model_bodySet.getSize())]
        bodyNames = [b.getName() for b in bodies]

        # motion: read coordinates and convert rotations to radians
        # coordinateNames = [c.getName() for c in coordinates]
        # coordinates = [model_coordSet.get(i) for i in range(model_coordSet.getSize())]
        coordinateNames = motion_data.getColumnLabels()
        motion_data_np = motion_data.getMatrix().to_numpy()
        for i, c in enumerate(coordinateNames):
            try:
                if model_coordSet.get(c).getMotionType() == 1: # 1: rotation, 2: translation, 3: coupled
                    if  motion_data.getTableMetaDataAsString('inDegrees') == 'yes':
                        motion_data_np[:,i] = motion_data_np[:,i] * np.pi/180 # if rotation, convert to radians
            except:
                pass
        
        # animate model
        state = model.initSystem()
        loc_rot_frame_all = []
        # H_zup = np.array([[0,0,1,0], [1,0,0,0], [0,1,0,0], [0,0,0,1]])
        H_zup = np.array([[1,0,0,0], [0,0,-1,0], [0,1,0,0], [0,0,0,1]])
        
        # print('Time frame:')
        for n in range(0, len(times), conv_fac_frame_rate):
            # print(times[n], 's')
            # set model struct in each time state
            for c, coord in enumerate(coordinateNames): ## PROBLEME QUAND HEADERS DE MOTION_DATA_NP ET COORDINATENAMES SONT PAS DANS LE MEME ORDRE
                try:
                    model.getCoordinateSet().get(coord).setValue(state, motion_data_np[n,c], enforceContraints=False)
                except:
                    pass
            # model.assemble(state)
            model.realizePosition(state) # much faster (IK already done, no need to compute it again)
            
            # use state of model to get body coordinates in ground
            loc_rot_frame = []
            for b in bodies:
                H_swig = b.getTransformInGround(state)
                T = H_swig.T().to_numpy()
                R_swig = H_swig.R()
                R = np.array([[R_swig.get(0,0), R_swig.get(0,1), R_swig.get(0,2)],
                    [R_swig.get(1,0), R_swig.get(1,1), R_swig.get(1,2)],
                    [R_swig.get(2,0), R_swig.get(2,1), R_swig.get(2,2)]])
                H = np.block([ [R,T.reshape(3,1)], [np.zeros(3), 1] ])
                
                # y-up to z-up
                if direction=='zup':
                    H = H_zup @ H
                
                # convert matrix to loc and rot, and export to csv
                if export_to_csv:
                    loc_x, loc_y, loc_z = H[0:3,3]
                    R_mat = H[0:3,0:3]
                    sy = np.sqrt(R_mat[1,0]**2 +  R_mat[0,0]**2) # singularity when y angle is +/- pi/2
                    if sy>1e-6:
                        rot_x = np.arctan2(R_mat[2,1], R_mat[2,2])
                        rot_y = np.arctan2(-R_mat[2,0], sy)
                        rot_z = np.arctan2(R_mat[1,0], R_mat[0,0])
                    else: # to be verified
                        rot_x = np.arctan2(-R_mat[1,2], R_mat[1,1])
                        rot_y = np.arctan2(-R[2,0], sy)
                        rot_z = 0
                    loc_rot_frame.extend([loc_x, loc_y, loc_z, rot_x, rot_y, rot_z])
            
                # set coordinates of blender bodies to this state
                b_iterated = [o.name for o in collection.objects if o.name.startswith(b.getName())][0]
                obj=collection.objects[b_iterated]
                obj.matrix_world = H.T
                obj.keyframe_insert('location',frame=first_frame+round(n/conv_fac_frame_rate))
                obj.keyframe_insert('rotation_euler',frame=first_frame+round(n/conv_fac_frame_rate))
            
            if export_to_csv:
                loc_rot_frame_all.append(loc_rot_frame)

        # export to csv
        if export_to_csv:
            loc_rot_frame_all_np = np.array(loc_rot_frame_all)
            loc_rot_frame_all_np = np.insert(loc_rot_frame_all_np, 0, times[::conv_fac_frame_rate], axis=1) # insert time column
            bodyHeader = 'times, ' + ''.join([f'{b}_x, {b}_y, {b}_z, {b}_rotx, {b}_roty, {b}_rotz, ' for b in bodyNames])[:-2]
            np.savetxt(os.path.splitext(mot_path)[0]+'.csv', loc_rot_frame_all_np, delimiter=',', header=bodyHeader)
        

    # If chosen file is .csv (body positions and rotations)
    elif os.path.splitext(mot_path)[1] == '.csv':
        # read csv motion file
        loc_rot_frame_all_np = np.loadtxt(mot_path, delimiter=",", dtype=float, skiprows=1)
        with open(mot_path) as f:
            csv_header = f.readline()
        bodyNames = csv_header.split(',')[1::6]
        bodyNames = [b[1:-2] for b in bodyNames]

        # set framerate
        times = loc_rot_frame_all_np[:,0]
        fps = round((len(times)-1) / (times[-1] - times[0]))
        first_frame = round(times[0]*fps)
        if target_framerate == 'auto':
            target_framerate = fps
        target_framerate = round(target_framerate)
        bpy.context.scene.render.fps = target_framerate
        conv_fac_frame_rate = fps // target_framerate
        if conv_fac_frame_rate == 0:
            conv_fac_frame_rate = 1
        
        # animate model
        for n in range(0, len(times), conv_fac_frame_rate):
            for i, b in enumerate(bodyNames):
                loc_x = loc_rot_frame_all_np[n,6*i+1]
                loc_y = loc_rot_frame_all_np[n,6*i+2]
                loc_z = loc_rot_frame_all_np[n,6*i+3]
                rot_x = loc_rot_frame_all_np[n,6*i+4]
                rot_y = loc_rot_frame_all_np[n,6*i+5]
                rot_z = loc_rot_frame_all_np[n,6*i+6]

                b_nameiterated = [o.name for o in collection.objects if o.name.startswith(b)][0]
                obj=collection.objects[b_nameiterated]
                obj.location=loc_x,loc_y,loc_z
                obj.rotation_euler=rot_x,rot_y,rot_z
                obj.keyframe_insert('location',frame=first_frame+round(n/conv_fac_frame_rate)+1)
                obj.keyframe_insert('rotation_euler',frame=first_frame+round(n/conv_fac_frame_rate)+1)

    print(f'OpenSim motion imported from {mot_path}')
