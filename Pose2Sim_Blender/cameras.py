#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
    ##################################################
    ## Import/export Cameras, show/film images      ##
    ##################################################
    
    N.B.: Distortions not taken into account at the moment
    N.B. 2: OpenCV or OpenSim not needed
    
    - Read a .toml calibration file and imports cameras
    - Find all cameras in the scene and export their properties as a .toml calibration file
    - 

'''


## INIT
import bpy
import mathutils
import numpy as np
import os
import toml
import sys
from .common import ShowMessageBox

RAY_WIDTH = 0/1000
COLOR = (0.8, 0.4, 0.1, 0.8)
IMAGE_QUALITY = 90


## AUTHORSHIP INFORMATION
__author__ = "David Pagnon"
__copyright__ = "Copyright 2023, Pose2Sim_Blender"
__credits__ = ["David Pagnon"]
__license__ = "MIT License"
__version__ = "0.7.0"
__maintainer__ = "David Pagnon"
__email__ = "contact@david-pagnon.com"
__status__ = "Development"


## CLASSES
class ModalOperator(bpy.types.Operator):
    bl_idname = "object.detect_orbit"
    bl_label = "Detect Orbit (Middle mouse click)"

    def __init__(self):
        print("Waiting for orbiting motion")

    def __del__(self):
        print("Orbiting motion done")

    def execute(self, context):
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MIDDLEMOUSE':
            image.empty_image_depth = 'DEFAULT'
            hide(objects, False)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.value = event.mouse_x
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

bpy.utils.register_class(ModalOperator)


## FUNCTIONS
def has_keyframe(ob, attr):
    '''
    Check if an object is animated or not
    https://blender.stackexchange.com/questions/4994/check-if-a-property-is-animated-or-has-a-driver
    '''
    
    anim = ob.animation_data
    if anim is not None and anim.action is not None:
        for fcu in anim.action.fcurves:
            if fcu.data_path == attr:
                return len(fcu.keyframe_points) > 0
    return False
    
    
def rod_to_mat(rodrigues_vec):
    '''
    Transform Rodrigues vector to rotation matrix without cv2
    https://stackoverflow.com/questions/62345076/how-to-convert-a-rodrigues-vector-to-a-rotation-matrix-without-opencv-using-pyth
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
    
    
def f_from_fov(fov):
    '''
    Retrieve focal length from fov and from render_settings, with:
    fov = camera.data.angle
    '''
    
    render_settings = bpy.context.scene.render
    w = render_settings.resolution_x
    h = render_settings.resolution_y
    f_1 = w / ( 2 * np.tan(fov/2) )
    f_2 = h / ( 2 * np.tan(fov/2) )
    f = np.max([f_1, f_2])
    
    return f
    

def set_mesh_origin(ob, pos):
    '''Given a mesh object set it's origin to a given position.
    
    See there: https://blenderartists.org/t/modifying-object-origin-with-python/507305/7
    '''
    
    pos = mathutils.Vector(pos)
    mat = mathutils.Matrix.Translation(pos - ob.location)
    ob.location = pos
    ob.data.transform(mat.inverted())


def add_bezier(v0 , v1, color=COLOR, ray_width=RAY_WIDTH):
    '''
    Add line connecting two points, 
    with a certain width and color.
    
    See there: https://blender.stackexchange.com/a/110211/174689
    '''
    
    if not 'RAY_WIDTH' in globals():
        ray_width = 5/1000
    if not 'COLOR' in globals():
        color = (0.8, 0.4, 0.1, 0.8)
        
    # Color
    matg = bpy.data.materials.new("Orange")
    matg.use_nodes = True
    tree = matg.node_tree
    nodes = tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    matg.diffuse_color = color
    
    # middle point of the Bezier curve
    v0, v1 = mathutils.Vector(v0), mathutils.Vector(v1)  
    o = (v1 + v0) / 2  
    
    # creat nurb with two points
    curve = bpy.data.curves.new('Curve', 'CURVE')
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(count=1)
    
    # first point
    bp0 = spline.bezier_points[0]
    bp0.co = v0 - o
    bp0.handle_left_type = bp0.handle_right_type = 'AUTO'

    # second point
    bp1 = spline.bezier_points[1]
    bp1.co = v1 - o
    bp1.handle_left_type = bp1.handle_right_type = 'AUTO'
    
    # make it an object
    ob = bpy.data.objects.new('Curve', curve)
    ob.matrix_world.translation = o
    curve = ob.data
    curve.dimensions = '3D'
    curve.bevel_depth = ray_width
    curve.bevel_resolution = 3
    
    # Move gizmo from median part of the nurb to its extremity
    set_mesh_origin(ob, v0)
    # bpy.context.scene.cursor.location = v0
    # bpy.ops.object.origin_set(type='ORIGIN_CURSOR') # THIS IS NOT UPDATED WHEN CALLED IN A FUNCTION
    
    return ob
    
    
def hide(objects, state):
    '''
    Hide objects if state = True
    Unhide them if state = False
    '''
    
    for obj in objects:
        obj.hide_set(state)
    
    
def retrieveCal_fromFile(toml_path):
    '''
    Retrieve calibration parameters from toml file.
    Output a dialog window to choose calibration file.
    '''
    N, S, D, K, R, T, P, moving = {}, {}, {}, {}, {}, {}, {}, {}
    Kh, H = {}, {}
    cal = toml.load(toml_path)
    cal_keys = [i for i in cal.keys() if 'metadata' not in i] # exclude metadata key
    for cam in cal_keys:
        try:
            moving[cam] = cal[cam]['moving']
        except:
            moving[cam] = False

        N[cam] = cal[cam]['name']
        S[cam] = np.array(cal[cam]['size'])
        D[cam] = np.array(cal[cam]['distortions'])
        K[cam] = np.array(cal[cam]['matrix'])
        T[cam] = np.array(cal[cam]['translation'])
        
        R[cam], P[cam], Kh[cam], H[cam] = [], [], [], []
        
        if moving[cam]:
            if 'intr' in moving[cam]:
                for i in range(len(K[cam])):
                    Kh[cam].append(np.block([K[cam][i], np.zeros(3).reshape(3,1)]))
            else:
                Kh[cam] = np.block([K[cam], np.zeros(3).reshape(3,1)])
        
            if 'extr' in moving[cam]:
                for i in range(len(T[cam])):
                    R[cam].append(rod_to_mat(np.array(cal[cam]['rotation'][i])))
                    H[cam].append(np.block([[R[cam][i],T[cam][i].reshape(3,1)], [np.zeros(3), 1 ]]))
            else:
                R[cam] = rod_to_mat(np.array(cal[cam]['rotation']))
                H[cam] = np.block([[R[cam],T[cam].reshape(3,1)], [np.zeros(3), 1 ]])
                    
            if 'extr' in moving[cam] and 'intr' in moving[cam]:
                for i in range(len(T[cam])):
                    P[cam].append(Kh[cam][i] @ H[cam][i])
            elif 'extr' in moving[cam] and 'intr' not in moving[cam]:
                for i in range(len(T[cam])):
                    P[cam].append(Kh[cam] @ H[cam][i])
            elif 'intr' in moving[cam] and 'extr' not in moving[cam]:
                for i in range(len(K[cam])):
                    P[cam].append(Kh[cam][i] @ H[cam])
            
        else:
            R[cam] = rod_to_mat(np.array(cal[cam]['rotation']))
            H[cam] = np.block([[R[cam],T[cam].reshape(3,1)], [np.zeros(3), 1 ]])
            Kh[cam] = np.block([K[cam], np.zeros(3).reshape(3,1)])
            P[cam] = Kh[cam] @ H[cam]
        
    return N, S, D, K, R, T, P, moving


def retrieveCal_fromScene(cameras):
    '''
    Retrieve calibration parameters from cameras in the scene.
    '''
    
    # image dimensions (only accurate if all cameras have the same resolution?)
    render_settings = bpy.context.scene.render
    w = render_settings.resolution_x
    h = render_settings.resolution_y
    S = [[w, h]] * len(cameras)
    
    # distortions are neglected at the moment
    distortions = [0.0, 0.0, 0.0, 0.0]
    D = [distortions] * len(cameras)
    
    N, K, R, T, P = [], [], [], [], []
    for camera_obj in cameras:
        # camera name
        name = camera_obj.name
        camera = bpy.data.cameras[camera_obj.name]
        N += [name]
        
        # principal point
        max_wh = np.max([w,h])
        cx = max_wh * camera.shift_x + w/2
        cy = max_wh * camera.shift_y + h/2
        
        # focal distance (px)
        if not has_keyframe(camera, "lens"):
            fov = camera.angle
            f_1 = w / ( 2 * np.tan(fov/2) )
            f_2 = h / ( 2 * np.tan(fov/2) )
            f = np.max([f_1, f_2])
            
            K += [[[f, 0.0, cx], [0.0, f, cy], [0.0, 0.0, 1.0]]]
            
        else:
            K_cam = []
            for fc in camera.animation_data.action.fcurves:
                if 'lens' in fc.data_path:
                    for key in fc.keyframe_points:                      # each frame
                        lens = key.co[1]
                        f = lens * w / camera.sensor_width
                        K_cam.append( [[f, 0.0, cx], [0.0, f, cy], [0.0, 0.0, 1.0]] )
            K += [K_cam]
        
        # rotation, translation
        rot_180 = mathutils.Euler(np.radians([180,0,0]), 'ZYX').to_matrix()
        rot_90 = np.array(mathutils.Euler([0,0,np.radians(90)]).to_matrix())
        if not has_keyframe(camera_obj, "location") and not has_keyframe(camera_obj, "rotation_euler"):
            # flip x
            r = camera_obj.rotation_euler.to_matrix() @ rot_180
            t = camera_obj.location
            # rotate 90
            t_new = rot_90 @ t
            r_new = rot_90 @ r
            
            r_loc, t_loc = world_to_camera_persp(np.array(r_new), t_new)
            
            r_rod = mat_to_rod(r_loc)
        
        else:
            t_loc, r_rod = [], []
            t_idx, r_idx, extr_len = 0, 0, 0
            rotation = [[], [], []]
            translation = [[], [], []]
            for fc in camera_obj.animation_data.action.fcurves:  # each loc and rot
                extr_len = len(fc.keyframe_points) if len(fc.keyframe_points) > extr_len else extr_len
                if 'rotation' in fc.data_path:
                    for key in fc.keyframe_points:                      # each frame
                        rotation[r_idx].append(key.co[1])
                    r_idx += 1
                    
                if 'location' in fc.data_path:
                    for key in fc.keyframe_points:                      # each frame
                        translation[t_idx].append(key.co[1])
                    t_idx += 1
            
            rotation = np.array(rotation).T
            translation = np.array(translation).T
                    
            for i in range(extr_len):
                # flip x
                r = mathutils.Euler(rotation[i]).to_matrix() @ rot_180
                t = translation[i]
                # rotate 90
                t_new = rot_90 @ t
                r_new = rot_90 @ r
                
                r_loc_i, t_loc_i = world_to_camera_persp(np.array(r_new), t_new)
                
                t_loc.append(list(t_loc_i))
                r_rod.append(list(mat_to_rod(r_loc_i)))
        
        R += [list(r_rod)]
        T += [list(t_loc)]
        
    return S, D, N, K, R, T, P


def write_calibration(calib_params, toml_path):
    '''
    Write calibration file from calibration parameters
    '''
    
    S, D, N, K, R, T, P = calib_params
    with open(toml_path, 'w+') as cal_f:
        for c in range(len(S)):
            cam_str = f'[{N[c]}]\n'
            name_str = f'name = "{N[c]}"\n'
            size_str = f'size = {S[c]} \n'
            mat_str = f'matrix = {K[c]} \n'
            dist_str = f'distortions = {D[c]} \n' 
            rot_str = f'rotation = {R[c]} \n'
            tran_str = f'translation = {T[c]} \n'
            fish_str = f'fisheye = false\n\n'
            cal_f.write(cam_str + name_str + size_str + mat_str + dist_str + rot_str + tran_str + fish_str)
        meta = '[metadata]\nadjusted = false\nerror = 0.0\n'
        cal_f.write(meta)


def setup_cams(calib_params, collection=''):
    '''
    Import cameras from their parameters:
    name, field of view, rotation and translation, proncipal point, render settings
    '''
    
    if collection=='':
        collection = bpy.data.collections.new('importedCameras')
        bpy.context.scene.collection.children.link(collection)
    if isinstance(collection,str):
        collection = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(collection)

    N, S, D, K, R, T, P, moving = calib_params
    for i, c in enumerate(S.keys()):
        camera = bpy.data.cameras.new(c)
        camera_obj = bpy.data.objects.new(c, camera)
        # bpy.ops.object.camera_add()
        # camera = bpy.context.active_object
        collection.objects.link(camera_obj)
        # bpy.context.collection.objects.unlink(camera_obj)

        # name
        camera_obj.name = N[c]
        
        # image dimensions
        w, h = [int(i) for i in S[c]]
        
        # field of view
        if moving[c] and 'intr' in moving[c]:
            for n in range(0,len(K[c])):
                fx, fy = K[c][n][0,0], K[c][n][1,1]
                fov_x = 2 * np.arctan2(w, 2 * fx)
                fov_y = 2 * np.arctan2(h, 2 * fy)
                
                camera.type = 'PERSP'
                camera.lens_unit = 'FOV'
                camera.angle = np.max([fov_x, fov_y])
            
                camera.keyframe_insert('lens', frame=n+1)
        else: 
            fx, fy = K[c][0,0], K[c][1,1]
            fov_x = 2 * np.arctan2(w, 2 * fx)
            fov_y = 2 * np.arctan2(h, 2 * fy)
            
            camera.type = 'PERSP'
            camera.lens_unit = 'FOV'
            camera.angle = np.max([fov_x, fov_y])
            
        # rotation and translation
        if moving[c] and 'extr' in moving[c]:
            for n in range(0,len(R[c])):
                r, t = world_to_camera_persp(R[c][n], T[c][n])
                t = np.array([t[1], -t[0], t[2]])
                homog_matrix = np.block([[r,t.reshape(3,1)], 
                                        [np.zeros(3), 1 ]])
                camera_obj.matrix_world = mathutils.Matrix(homog_matrix)
                set_loc_rotation(camera_obj, np.radians([180,0,0]))
                camera_obj.rotation_euler += np.radians([0, 0, -90])
                
                camera_obj.keyframe_insert('location', frame=n+1)
                camera_obj.keyframe_insert('rotation_euler', frame=n+1)
        else:
            r, t = world_to_camera_persp(R[c], T[c])
            t = np.array([t[1], -t[0], t[2]])
            homog_matrix = np.block([[r,t.reshape(3,1)], 
                                    [np.zeros(3), 1 ]])
            camera_obj.matrix_world = mathutils.Matrix(homog_matrix)
            set_loc_rotation(camera_obj, np.radians([180,0,0]))
            camera_obj.rotation_euler += np.radians([0, 0, -90])
        
        # principal point # see https://blender.stackexchange.com/a/58236/174689
        if moving[c] and 'intr' in moving[c]:
            principal_point =  K[c][0][0,2],  K[c][0][1,2]
        else:
            principal_point =  K[c][0,2],  K[c][1,2]
        max_wh = np.max([w,h])
            
        camera.shift_x = 1/max_wh*(principal_point[0] - w/2)
        camera.shift_y = 1/max_wh*(principal_point[1] - h/2)

        # render settings
        render_settings = bpy.context.scene.render
        render_settings.resolution_x = w
        render_settings.resolution_y = h
        

def import_cameras(toml_path):
    '''
    Import cameras from a .toml calibration file
    '''

    if os.path.isfile(toml_path):
        outfile = os.path.splitext(toml_path)[0]+".toml"
        calib_params = retrieveCal_fromFile(toml_path)
        setup_cams(calib_params)
        
        scene = bpy.context.scene
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.length_unit = 'METERS'
        scene.unit_settings.scale_length = 1.0
            
        print(f'Cameras imported from {toml_path} calibration file.')


def export_cameras(toml_path):
    '''
    Export cameras as a .toml calibration file
    
    N.B.: Distortions are neglected at the moment
    N.B. 2: Only accurate if all cameras have the same resolution
    '''
    
    cameras = [ob for ob in list(bpy.context.scene.objects) if ob.type == 'CAMERA']
    
    calib_params = retrieveCal_fromScene(cameras)
    write_calibration(calib_params, toml_path)
        
    print(f'Cameras exported to {toml_path} calibration file.')
            

def show_images(camera, img_vid_path, single_image=False):
    '''
    Show images or a video associated to a selected camera
    '''
    
    # Global to local Gizmo
    bpy.data.scenes['Scene'].transform_orientation_slots[1].type = 'LOCAL'
    
    # load images or video
    bpy.ops.object.load_reference_image(filepath=img_vid_path)
    img = bpy.context.active_object
    img.matrix_world = np.eye(4)
    img.empty_image_depth = 'DEFAULT' # overlaid by skeleton, markers, etc.
    if single_image == False:
        if img.data.source == 'MOVIE':
            # BUG: if select single image, delete, and then reload as movie, does not update source as movie
            img.image_user.frame_duration =  img.data.frame_duration
            img.image_user.frame_start =  1
        elif img.data.source == 'FILE': 
            img.data.source = 'SEQUENCE'
            img.image_user.frame_start =  1
    else: 
        img.data.source = 'FILE'
    
    # parent image to camera
    img.parent = camera
    img.name = img.parent.name + '_img'
    camera.users_collection[0].objects.link(img)
    bpy.context.collection.objects.unlink(img)
    
    # calculate image size in meters
    fov = camera.data.angle
    f = f_from_fov(fov)
    render_settings = bpy.context.scene.render
    w = render_settings.resolution_x
    h = render_settings.resolution_y
    max_wh = np.max([w,h])
    img_size_m = max_wh / f
    
    # calculate scale factor
    img_size_orig = img.empty_display_size
    scale_factor = img_size_m /img_size_orig
    bpy.app.driver_namespace['scale_factor'] = scale_factor
    
    # create driver for scaleX as a function of translation
    d_scalex = img.driver_add('scale', 0) 
    v_scalex = d_scalex.driver.variables.new()
    v_scalex.name = 'scaleX'
    v_scalex.targets[0].id = img
    v_scalex.type = 'TRANSFORMS'
    v_scalex.targets[0].transform_type = 'LOC_Z'
    v_scalex.targets[0].transform_space = 'LOCAL_SPACE'
    d_scalex.driver.expression = '-scaleX * scale_factor'
    
    # create driver for scaleY as a function of translation
    d_scaley = img.driver_add('scale', 1) 
    v_scaley = d_scaley.driver.variables.new()
    v_scaley.name = 'scaleY'
    v_scaley.targets[0].id = img
    v_scaley.type = 'TRANSFORMS'
    v_scaley.targets[0].transform_type = 'LOC_Z'
    v_scaley.targets[0].transform_space = 'LOCAL_SPACE'
    d_scaley.driver.expression = '-scaleY * scale_factor'
    
    # place at Z = 1.5 m
    img.location[0] = -camera.data.shift_x # NOT 100% SURE OF THIS
    img.location[1] = -camera.data.shift_y
    img.location[2] = -1.5
    
    bpy.ops.object.transform_apply(location=False, scale=True)
    
    print(f'Image or video imported from {img_vid_path}')

    
def film_from_cams( dir_path, 
                    cams,
                    all_cameras=False, 
                    movie_or_sequence='images', 
                    target_framerate=30, 
                    first_frame = 0, 
                    last_frame = 100, 
                    render_quality=100):
    '''
    Film from selected cameras
    Quick viewport render
    '''
    
    if all_cameras:
        cams = [ob for ob in list(bpy.context.scene.objects) if ob.type == 'CAMERA']
    
    # remove outline
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    area.spaces[0].shading.show_object_outline = False
    
    # prepare rendering
    scene = bpy.data.scenes['Scene']
    scene.render.resolution_percentage = render_quality
    scene.render.fps = target_framerate
    scene.frame_start = first_frame
    scene.frame_end = last_frame
    scene.frame_step = 1
    scene.cycles.device = 'GPU'
    scene.render.engine = 'CYCLES'
    
    if movie_or_sequence=='movie':
        scene.render.fps = target_framerate
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.image_settings.quality = IMAGE_QUALITY
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.constant_rate_factor = 'MEDIUM' # Output quality
        scene.render.ffmpeg.ffmpeg_preset = 'GOOD' # Encoding speed
        scene.render.ffmpeg.codec = 'H264' # Video codec
        scene.render.ffmpeg.audio_codec = 'NONE' # Audio set to none
        extension = 'mp4'
    else:
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.quality = IMAGE_QUALITY
        extension = 'png'
    
    for cam in cams:
        bpy.context.view_layer.objects.active = cam
        see_through_selected_camera()
        scene.render.filepath = os.path.join(dir_path, cam.name, cam.name+'.'+extension)
        try:
            print('Render with OpenGL')
            bpy.ops.render.opengl(animation=True)
        except:
            print('WARNING: Render with Blender renderer')
            bpy.ops.render.render(animation=True, use_viewport=True)
            
    
def see_through_selected_camera():
    '''
    See through the selected camera
    '''
    
    global objects, image
    
    # Look through camera
    bpy.context.scene.camera = bpy.context.active_object
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    area.spaces[0].region_3d.view_perspective = 'CAMERA'

    # change image depth
    camera =  bpy.context.active_object
    if not len(camera.children) == 0:
        image = camera.children[0]
        image.empty_image_depth = 'BACK'

    # hide curves
    objects = bpy.ops.object.select_by_type(type='CURVE')
    objects = bpy.context.selected_objects
    hide(objects, True)
        
    # # HERE I WANT TO DETECT AN ORBITAL CHANGE TO UNHIDE STUFF AND MAKE IMAGE DEPTH AUTO:
    ## https://blender.stackexchange.com/questions/311024/detect-orbit-events-via-api
    ## MsgBus does not work with ViewPort changes
    # rot = area.spaces.active.region_3d.view_rotation 
    ## ModalOperator prevents the UI from responding to anything until the user pans
    # bpy.ops.object.detect_orbit('INVOKE_DEFAULT')
    
    
def reproject_3D_points(collection=''):
    '''
    Trace rays from an object to the camera
    '''
    
    objects = bpy.context.selected_objects
    cameras = [ob for ob in list(bpy.context.scene.objects) if ob.type == 'CAMERA']
    
    for ob in objects:
        bpy.ops.object.select_all(action='DESELECT')
        
        collection = bpy.data.collections.new(f'rays{ob.name}')
        bpy.context.scene.collection.children.link(collection)
        for cam in cameras:
            # add Bezier curve
            curve_obj = add_bezier(ob.location, cam.location)
            curve_obj.name = f'{collection.name}_{cam.name}'
            collection.objects.link(curve_obj)

            # hook to object 
            ob.select_set(True)
            curve_obj.select_set(True)
            bpy.context.view_layer.objects.active = curve_obj
            bpy.ops.object.mode_set(mode='EDIT')
            curve_obj.data.splines[0].bezier_points[0].select_control_point = True
            bpy.ops.object.hook_add_selob(use_bone=False)
        bpy.ops.object.mode_set(mode='OBJECT')
            
    bpy.ops.object.select_all(action='DESELECT')
        

