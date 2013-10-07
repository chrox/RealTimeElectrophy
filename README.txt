Welcome to the RealTimeElectrophy!

OVERVIEW

The RealTimeElectrophy is a collection of useful programs designed to simplify visual neurophysiology research. The Experimenter package lies in the central position of the routines. An experimenter controls the visual stimulator via StimControl and receives spikes data from SpikeRecord.  Precise frame timing is done by StimControl which sends a sweepstamp trigger to the acquisition system for each screen sweep. Once the visual stimuli is synchronized with the spikes via Experimenter, preliminary data analysis can be performed in real time.

HARDWARE REQUIREMENTS

A recent stand-alone graphics card is required to draw stimuli fast enough for real time control. In our lab, we use an nVIDIA Quadro NVS 440 card in MultiView mode to horizontally span the screen over three or four monitors. And each monitor works at a refresh rate of 120Hz. Any recent nVIDIA GeForce card should be able to run smoothly in DualView mode on two monitors. And we use a Data Translation Digital I/O board to trigger the acquisition device in Windows platform. Compatible Comedi devices should work in Linux platform. But currently only Data Translation DT340
is tested.

INSTALLATION

First, download and install these dependencies:
	- python (version >= 2.6 , but NOT version 3)
	- Pyro (Python remote objects, version >= 3.2, but NOT version 4)
	- PIL (Python Imaging Library, version >= 1.1.6)
	- PyOpenGL (version >= 3.0.1)
	- pygame (version >= 1.8)
	- numpy (version >= 0.9.6)
	- scipy (version >= 0.4.8)
	- matplotlib (version >= 1.01)
	- wxPython (version >= 2.8)
	- VisionEgg (version >= 1.2.1)
	- setuptools (version >= 0.6)
	- pycomedi (version >= 0.5, Linux only)

To install RealTimeElectrophy from source, download the latest source code packages, and extract the files into your home directory. Type this from a command line from the RealTimeElectrophy base directory:

>>>python setup.py install

For windows users binary installers are also provided.

In either case you need a copy of source code to run the demo execuable programs located at each subdirectory with all lowercase letters in their names.

CONFIGURATION

You can edit the configuration file LightStim.cfg with your favorite text editor and make necessary changes to configurable entities including whether the triggering device is installed, dimensional measurements and refresh rates and gamma corrections of each monitor, etc.

LICENSE

The RealTimeElectrophy is Copyright (c) 2010-2011 by the RealTimeElectrophy Authors. It is distributed under the terms of BSD license. See LICENSE.txt for more information. This software is provided "as is" without any warranty of any kind, either expressed or implied.

CREDITS

Much of the behaviour and many of the features of LightStim package are based on Dimstim, a python visual stimulation package written by Martin Spacek and released under BSD license. The Dimstim project page can be found at http://swindale.ecc.ubc.ca/dimstim. StimServer is modified from PyroApps, a demo VisionEgg application shipped with VisonEgg source code. For more information please refer to http://www.visionegg.org .

MISC

Any comments and contributions to this project are welcomed.
See http://vislab.hsc.pku.edu.cn/code/RealTimeElectrophy for more.

_________________________
Manual stimulus controls:

In manbar and mangrating stimulation:
    - mouse cursor controls the bar/grating position, mouse scroll wheel changes 
      bar/grating orientation
    - left and right mouse buttons control stimulus on/off in left and right viewport 
      respectively
    - left/right arrow keys control bar/grating width, up/down arrow keys control 
      bar/grating height
    - ENTER/SPACE keys save current stimulus parameters to disk
    - TAB key alternates currently controlled viewport in turn
    - double-clicking left/right buttons changes currently controlled viewport to 
      the left/right viewport 
    - 'C' sets circular mask for grating
    - 'F' controls stimulus flashing
    - 'G' sets gaussian mask for grating
    - 'H' controls stimulus on/off on all viewports
    - 'I' inverts the bar and background brightness levels
    - 'O' sets the bar orientation orthogonal to motion
    - 'T' add 90 degrees to the bar/grating orientation
    - 'U' reverse the drifting direction of gratings
    - '-'/'+' adjust brightness of bar and contrast of grating
    - '['/']' adjust grating temporal frequency
    - '<'/'>' adjust grating spatial frequency (','/'.' do the same thing)
    - '0' sets 0 deg orientation for bar/grating
    - CTRL+'1' saves stimulus parameters to disk which can be later restored by 
      pressing '1'
    - CTRL+'2' saves stimulus parameters to disk which can be later restored by 
      pressing '2'
    - CTRL+'C' copys stimulus parameters 
    - CTRL+'V' pastes copied stimulus parameters to stimulus being controlled
    - CTRL+'G' groups stimuli on all viewports so that all stimuli are under control
