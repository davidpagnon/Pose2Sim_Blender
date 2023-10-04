# Sim2Blend


Import OpenSim results in Blender.

This add-on is heavily inspired from [BlendOsim](https://github.com/JonathanCamargo/BlendOsim). However, it is end-to-end and does not require using Matlab to export OpenSim files to a .csv format. 





## Installation

To install, download the repository into a zip file and install from Blender->Preferences. Make sure that the zip file that you pass to blender has the repository directly in the first level folder (not in a subfolder).

BlendOsim has been tested in blender from version 2.83 up to 3.0. If you need to use a different version and encounter issues please submit an issue. I will do my best to help.

## Getting started

After installing and enabling the add-on, a new tab will appear at your tools panel: **BlendOsim**. 

![Options added to the tools panel](doc/toolspanel.png)

With this tab you can import:

- **Markers file**: takes a csv file containing the xyz trajectories of the markers in the motion capture recorded in the experiment. This import option inserts mesh spheres, labels, and animates the trajectory location at every keyframe.

- **Forces file**: takes a csv file containing the force, moments and center of pressure for the forceplate data recorded in the experiment.This import option inserts mesh arrows with the tail located at the center of pressure, pointing and scaled in the direction of the force. The location and magnitude of the force is animated at every keyframe provided in the csv file.

- **Model file**: corresponds to the description of the biomechanics model in .osim format. Adding the model will add STL surfaces parented to empty objects that can be later used for animation. 

- **Motion file**: a csv file containing the location and rotation for every segment in the model at each animation keyframe to animate. This option constructs the trajectories for the loaded model file.

Try the files in the example folder!
![This is what you would see](doc/bones.png)










- Remove cube
- Explanation on where to find add-on with screenshot
- Installing OpenSim (for mot files)
- Change file hierarchy (cf Pose2Sim, Sports2D)
- Run when file selected

Pipeline:
- Add cameras, scene, film from cameras, import cameras, import videos
- Pose2Sim: Detection, Calibration/Sync/Identification, Triangulation/Filtering, Scaling/IK
- Import model, mot, markers












```
Install Blender (haven't tried with versions other than 3.6)
Install OpenSim (haven't tried with versions other than 4.4)
Install Miniconda

Find the Python version used in Blender: 
Open Blender
Shift+F4
import sys
sys.version
Write down your Python version, e.g. 3.10.12

Open miniconda, and copy-paste:
conda create -n Sim2Blend python=3.10.12 -y
conda activate Sim2Blend
conda install -c opensim-org opensim -y
# pip install bpy
pip uninstall numpy
pip install numpy bpy

You will need admin rights for the next steps:
Rename python in "C:\Program Files\Blender Foundation\Blender 3.6\3.6\" to python_old. 
Copy-paste there Sim2Blend folder (see location with "conda env list"), rename to python
Open "C:\Program Files\Blender Foundation\Blender 3.6\3.6\python\Lib\opensim\__init__.py" 
- comment out the line # from .moco import *
- line 4, add the path to your OpenSim bin "os.add_dll_directory("C:/OpenSim 4.4/bin")" 

Launch Blender, Shift+F4
import os

Try import sys, import bpy, import numpy, import opensim
```

pip install opencv-python -> ok
pip install pandas -> DLL library issue when importing