import os
os.add_dll_directory("C:/OpenSim 4.4/bin")

import numpy as np
import bpy
import opensim as osim

direction='zup'


def apply_mot_to_model(mot_path, osim_path, direction='zup'):
    '''
    Computes the coordinates of each opensim bodies in the ground plane
    from a .mot motion file and a .osim model file.
    Animates a previously loaded .osim model accordingly.
    
    Requires OpenSim API to be installed in Blender (see Readme.md).

    INPUTS: 
    - mot_path: path to the .mot motion file
    - osim_path: path to the .osim model file
    - direction: 'zup' or 'yup' (default: 'zup')

    OUTPUTS:
    Animated .osim model
    '''

    # read model and motion files
    model = osim.Model(osim_path)
    motion_data = osim.TimeSeriesTable(mot_path)
    try:
        collection=bpy.data.collections['osimModel']
    except:
        raise('First import a model.')
    
    # set framerate
    fps = int(motion_data.getNumRows() / (motion_data.getIndependentColumn()[-1]-motion_data.getIndependentColumn()[0]))
    bpy.data.scenes['Scene'].render.fps = fps

    # model: get model coordinates and bodies
    model_coordSet = model.getCoordinateSet()
    coordinates = [model_coordSet.get(i) for i in range(model_coordSet.getSize())]
    coordinateNames = [model_coordSet.get(i).getName() for i in range(model_coordSet.getSize())]
    model_bodySet = model.getBodySet()
    bodies = [model_bodySet.get(i) for i in range(model_bodySet.getSize())]

    # motion: read coordinates and convert to radians
    motion_data_np = motion_data.getMatrix().to_numpy()
    for i in range(len(coordinates)):
        if coordinates[i].getMotionType() == 1: # 1: rotation, 2: translation, 3: coupled
            motion_data_np[:,i] = motion_data_np[:,i] * np.pi/180 # if rotation, convert to radians

    state = model.initSystem()
    for n in range(motion_data.getNumRows()):
        # set model struct in each time state
        for c, coord in enumerate(coordinateNames):
            model.getCoordinateSet().get(coord).setValue(state, motion_data_np[n,c])
        # use state of model to get body coordinates in ground
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
                H_zup = np.array([[1,0,0,0], [0,0,-1,0], [0,1,0,0], [0,0,0,1]])
                H = H_zup @ H
            # set coordinates of blender bodies to this state
            obj=collection.objects[b.getName()]
            obj.matrix_world = H.T
            obj.keyframe_insert('location',frame=n+1)
            obj.keyframe_insert('rotation_euler',frame=n+1)
            
