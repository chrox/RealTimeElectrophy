# Demo for pyro usage
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division
from LightStim.FrameControl import FrameSweep
from LightStim.Core import Dummy_Stimulus
from LightStim.SweepController import StimulusPoolController
from VisionEgg.PyroHelpers import PyroServer
import Pyro
Pyro.config.PYRO_MOBILE_CODE = True
Pyro.config.PYRO_TRACELEVEL = 3
Pyro.config.PYRO_PICKLE_FORMAT = 1

sweep = FrameSweep()
dummy_stimulus = Dummy_Stimulus()
sweep.add_stimulus(dummy_stimulus)

pyro_server = PyroServer()

#quit_controller = PyroConstantController(during_go_value=0)
#pyro_server.connect(quit_controller,'quit_controller')
#sweep.add_controller(sweep,'quit', quit_controller)
#sweep.add_controller(None,None, pyro_server.create_listener_controller())

stimulus_pool = StimulusPoolController(framesweep=sweep)
pyro_server.connect(stimulus_pool,'stimulus_pool')
sweep.add_controller(None,None, stimulus_pool)
sweep.add_controller(None,None, pyro_server.create_listener_controller())

sweep.go()