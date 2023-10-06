import numpy as np
import math

    

def readNames(columnNames):
    #For a list of column names get a list of names by 
    #removing the axis suffix eg. MARKERNAME_x => MARKERNAME
    names=list()
    for column in columnNames:
        column=str.replace(column,'moment_','')
        splitName=str.split(column,'_')
        name='_'.join(splitName[:-1])
        if not name in names:
            names.append(name)        
    return names


def data2keyframes(obj,frames,locx=None,locy=None,locz=None,
                    rotx=None,roty=None,rotz=None,
                    scalex=None,scaley=None,scalez=None):
    #For a list of frames and loc or rot data create an animation for object obj        
    if not isinstance(frames,list) and not isinstance(frames,np.ndarray):
        frames=[frames]
    if isinstance(frames,np.ndarray) and frames.size==1:
        frames=[frames.tolist()]        
    if isinstance(locx,np.ndarray) and locx.size==1:
        locx=[locx.tolist()]        
    if isinstance(locy,np.ndarray) and locy.size==1:
        locy=[locy.tolist()]        
    if isinstance(locz,np.ndarray) and locz.size==1:
        locz=[locz.tolist()]        
    if isinstance(rotx,np.ndarray) and rotx.size==1:
        rotx=[rotx.tolist()]        
    if isinstance(roty,np.ndarray) and roty.size==1:
        roty=[roty.tolist()]        
    if isinstance(rotz,np.ndarray) and rotz.size==1:
        rotz=[rotz.tolist()]        
    for i,frame in enumerate(frames):        
        if locx is not None :
            locx=[locx] if not isinstance(locx,list) and  not isinstance(locx,np.ndarray) else locx
            obj.location.x=float(locx[i])            
        if locy is not None:
            locy=[locy] if not isinstance(locy,list) and  not isinstance(locy,np.ndarray) else locy
            obj.location.y=float(locy[i])
        if locz is not None :
            locz=[locz] if not isinstance(locz,list) and  not isinstance(locz,np.ndarray) else locz
            obj.location.z=float(locz[i])
        if rotx is not None :
            rotx=[rotx] if not isinstance(rotx,list) and  not isinstance(rotx,np.ndarray) else rotx
            obj.rotation_euler.x=math.radians(float(rotx[i]))
        if roty is not None :
            roty=[roty] if not isinstance(roty,list) and  not isinstance(roty,np.ndarray) else roty
            obj.rotation_euler.y=math.radians(float(roty[i]))
        if rotz is not None :
            rotz=[rotz] if not isinstance(rotz,list) and  not isinstance(rotz,np.ndarray) else rotz
            obj.rotation_euler.z=math.radians(float(rotz[i]))
        if scalex is not None :
            scalex=[scalex] if not isinstance(scalex,list) and  not isinstance(scalex,np.ndarray) else scalex
            obj.scale.x=float(scalex[i])            
        if scaley is not None:
            scaley=[scaley] if not isinstance(scaley,list) and  not isinstance(scaley,np.ndarray) else scaley
            obj.scale.y=float(scaley[i])
        if scalez is not None :
            scalez=[scalez] if not isinstance(scalez,list) and  not isinstance(scalez,np.ndarray) else scalez
            obj.scale.z=float(scalez[i])
        
        if ((locx is not None) or (locy is not None) or (locz is not None)):
            obj.keyframe_insert('location',frame=frame)
        if ((rotx is not None) or (roty is not None) or (rotz is not None)):
            obj.keyframe_insert('rotation_euler',frame=frame)
        if ((scalex is not None) or (scaley is not None) or (scalez is not None)):
            obj.keyframe_insert('scale',frame=frame)
        
        
def loadAnimation(collection,data,objectNames):
    # For all the objects in a collection retrieve the position 
    # and rotation if it exists and create the frame by frame animation.
    
    #Check that all the objects exist inside the collection first?
    frames=data['Header']
    headerNames=data.dtype.names[1:]
    
    #print(headerNames)
    N=len(objectNames)
    properties=len(headerNames)/N;
        
    if properties==3: #Only location
        headerIdx=0
        for object in objectNames:
            obj=collection.objects[object]
            locx=data[headerNames[headerIdx]]  
            locy=data[headerNames[headerIdx+1]]
            locz=data[headerNames[headerIdx+2]]
            headerIdx=headerIdx+3
            data2keyframes(obj,frames,locx=locx,locy=locy,locz=locz)
    elif properties==6: #Location and rotation
        headerIdx=0
        for object in objectNames:
            obj=collection.objects[object]
            print(headerNames[headerIdx])
            locx=data[headerNames[headerIdx]]            
            locy=data[headerNames[headerIdx+1]]
            locz=data[headerNames[headerIdx+2]]
            rotx=data[headerNames[headerIdx+3]]            
            roty=data[headerNames[headerIdx+4]]
            rotz=data[headerNames[headerIdx+5]]              
            headerIdx=headerIdx+6
            data2keyframes(obj,frames,locx=locx,locy=locy,locz=locz,rotx=rotx,roty=roty,rotz=rotz)
    elif properties==9: #Location and rotation and scale
        headerIdx=0
        for object in objectNames:
            obj=collection.objects[object]
            print(headerNames[headerIdx])
            locx=data[headerNames[headerIdx]]            
            locy=data[headerNames[headerIdx+1]]
            locz=data[headerNames[headerIdx+2]]
            rotx=data[headerNames[headerIdx+3]]            
            roty=data[headerNames[headerIdx+4]]
            rotz=data[headerNames[headerIdx+5]]            
            scalex=data[headerNames[headerIdx+6]]            
            scaley=data[headerNames[headerIdx+7]]
            scalez=data[headerNames[headerIdx+8]]                        
            headerIdx=headerIdx+9
            data2keyframes(obj,frames,locx=locx,locy=locy,locz=locz,
                           rotx=rotx,roty=roty,rotz=rotz,
                           scalex=scalex,scaley=scaley,scalez=scalez)    
    else: 
        #ERROR
        errormsg='Incorrect number of inputs, check data\n'
        errormsg='Objects:\n'+'\n'.join(objectNames)
        errormsg='HeaderNames:\n'+'\n'.join(headerNames)
        raise Exception(errormsg)
