Welcome to the RealTimeElectrophy!

OVERVIEW

The RealTimeElectrophy is a collection of useful programs designed to simplify visual 
neurophysiology research. The Experimenter package lies in the central position of the routines. 
A experimenter controls the visual stimulator via StimControl and receives spikes data from 
SpikeRecord.  Precise frame timing is done by StimControl which sends a sweepstamp trigger to 
the acquisition system for each screen sweep. Once the visual stimuli is synchronized with the 
spikes via Experimenter, preliminary data analysis can be performed in real time.

INSTALLATION

First, download and install these dependencies:
	- python (version >= 2.6 , but NOT version 3)
	- PIL (Python Imaging Library, version >= 1.1.6)
	- PyOpenGL (version >= 3.0.1)
	- pygame (version >= 1.8)
	- numpy (version >= 0.9.6)
	- scipy (version >= 0.4.8)
	- matplotlib (version >= 1.01)
	- wxPython (version >= 2.8)
	- VisionEgg (version == 1.2.1)

To install RealTimeElectrophy from source, download the latest source code packages,
and extract the files into your home directory. Type this from a command line 
from the RealTimeElectrophy base directory:

>>>python setup.py install

For windows users binary installers are also provided.

In either case you need a copy of source code to run the demo execuable programs located 
at each subdirectory with all lowercase letters in their names.

LICENSE

The RealTimeElectrophy is Copyright (c) 2010-2011 by the RealTimeElectrophy
Authors. It is distributed under the terms of BSD license. See LICENSE.txt 
for more information. This software is provided "as is" without any warranty 
of any kind, either expressed or implied.

CREDITS

Much of the behaviour and many of the features of LightStim package are based on Dimstim,
a python visual stimulation package written by Martin Spacek and released under BSD license.
The Dimstim project page can be found at http://swindale.ecc.ubc.ca/dimstim

MISC

Any comments and contributions to this project are welcomed.
See http://vislab.hsc.pku.edu.cn/code/RealTimeElectrophy for more.
