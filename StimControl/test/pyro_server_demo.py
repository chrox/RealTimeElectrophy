# Demo for pyro usage
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Core import Dummy_Stimulus
from StimControl.LightStim.SweepController import SweepController
from VisionEgg.PyroHelpers import PyroServer
import Pyro
Pyro.config.PYRO_MOBILE_CODE = True
Pyro.config.PYRO_TRACELEVEL = 3
Pyro.config.PYRO_PICKLE_FORMAT = 1


class StimulusPoolController(SweepController,Pyro.core.ObjBase):
    """ Maintain a stimulus pool and synchronize the pool with sweep viewport
    """
    def __init__(self,*arg,**kw):
        super(StimulusPoolController, self).__init__(*arg,**kw)
        Pyro.core.ObjBase.__init__(self)
    def add_stimulus(self,stimulus):
        self.framesweep.add_stimulus(stimulus)
    def remove_stimulus(self,stimulus):
        pass

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