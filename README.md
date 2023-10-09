[![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8421820.svg)](https://doi.org/10.5281/zenodo.8421820)


# Sim2Blend

**`Sim2Blend` is a Blender add-on for importing OpenSim data:** model, motion, markers, and forces.

[OpenSim](https://simtk.org/projects/opensim) is an open-source software for research in biomechanics, widely used in motion capture (MoCap). [Blender](https://www.blender.org) is an open-source software used for 3D modeling, animation, and rendering. 

Feel free to try [Pose2Sim](https://github.com/perfanalytics/pose2sim), an open-source pipeline for obtaining research-grade OpenSim results from consumer-grade cameras.

<img src='Content/Demo_Sim2Blend.gif' title='Sim2Blend demonstration. An OpenSim model imported in Blender, along with its motion, markers, and force results.'  width="760">

> N.B.: Sim2Blend is inspired from [BlendOsim](https://github.com/JonathanCamargo/BlendOsim). Unlike BlendOsim, Sim2Blend does not require using Matlab as an intermediary (and expensive) software between two open-source ones.


## Contents
1. [Installation](#installation)
2. [Demonstration](#demonstration)
3. [How to cite and how to contribute](#how-to-cite-and-how-to-contribute)


## Installation

Installation is a little tricky, but the following steps should do it smoothly. If you encounter any issue, please [submit an issue](https://github.com/davidpagnon/Sim2Blend/issues).

#### Prerequisites

- Install [Blender](https://www.blender.org/download/) (haven't tried with versions other than 3.6)
- Install [OpenSim](https://simtk.org/projects/opensim) (haven't tried with versions other than 4.4)
- Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Download [Sim2Blend.zip](https://github.com/davidpagnon/Sim2Blend/raw/main/Sim2Blend.zip)

#### Find your Blender Python version

Open Blender, press Shift+F4, type the following lines:

```
import sys
sys.version
```

#### Install Sim2Blend libraries

Open Miniconda, and copy-paste these lines. Replace with the Python version you just found:
```
conda create -n Sim2Blend python=3.10.12 -y 
conda activate Sim2Blend
conda install -c opensim-org opensim -y
pip uninstall numpy
pip install numpy bpy vtk
```

#### Install Sim2Blend add-on

You will need admin rights for the next steps:
- Rename `python` in `C:\Program Files\Blender Foundation\Blender 3.6\3.6\python` to `python_old`
- Copy-paste there your `Sim2Blend` environment folder (to find its location, type `conda env list` in Anaconda prompt). Rename it to `python`
- Open `C:\Program Files\Blender Foundation\Blender 3.6\3.6\python\Lib\opensim\__init__.py` 
  - comment out the line `# from .moco import *`
  - line 4, add the path to your OpenSim bin folder: `os.add_dll_directory(r"C:/OpenSim 4.4/bin")`

#### Install Sim2Blend add-on in Blender

- Blender -> Edit -> Preferences -> Add-ons -> Install -> Choose Sim2Blend.py
- Check `Sim2Blend` to enable it
- Click on the tiny arrow on the upper-right corner of the 3D viewport to open it

![Where to find Sim2Blend add-on](Content/Show_Sim2Blend.png)

<br>

## Demonstration

Find example files in the `Examples` folder, or use it with you own OpenSim data.

- **Add Model**: Import a `.osim` model. 
- **Add Motion**: Import a `.mot` or a `.csv` motion file. Calculating all body segment positions may take a while if the model is complex or the motion long. Creates a .csv file for faster loading next time.
- **Add Markers**: Import a `.trc` marker file.
- **Add Forces**: Import a `.mot` GRF force file.

`Warning:` All files must be sampled at the same framerate.

<br>

## How to cite and how to contribute

### How to cite

If you use Sim2Blend, please cite [Pagnon and Camargo, 2023].

     @misc{Pagnon2023,
       author = {Pagnon, David and Camargo, Jonathan},
       title = {Sim2Blend - OpenSim results in Blender},
       year = {2023},
       doi= {10.5281/zenodo.8421820},
       publisher = {GitHub},
       journal = {GitHub repository},
       howpublished = {\url{https://github.com/davidpagnon/Sim2Blend}},
     }

### How to contribute

I would happily welcome any proposal for new features, code improvement, and more!\
If you want to contribute to Sports2D, please follow [this guide](https://docs.github.com/en/get-started/quickstart/contributing-to-projects) on how to fork, modify and push code, and submit a pull request. I would appreciate it if you provided as much useful information as possible about how you modified the code, and a rationale for why you're making this pull request. Please also specify on which operating system, as well as which Python, Blender, OpenSim versions you have tested the code.

*Here is a to-do list. Feel free to complete it:*
- [x] Import data from standard OpenSim data files (.osim, .mot, .trc, grf.mot)
- [x] Convert .vtp files to .stl if .stl not found on disk
- [x] Save segment angles to .csv files for faster loading of motion next time
- [x] Import multiple persons in the same scene
- [x] Create Example data
- [ ] Rig model
- [ ] Add other tool for importing or exporting cameras, and for importing videos or filming (see [Maya-Mocap](https://github.com/davidpagnon/Maya-Mocap/))
- [ ] Tutorial for Mac/Linux
