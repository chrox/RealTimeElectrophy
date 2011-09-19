# This module contains the base class of SweepTableController.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import itertools
import Pyro.core
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types
from SweepStamp import DT,DTBOARDINSTALLED,SWEEP

class StimulusController(VisionEgg.FlowControl.Controller):
    """ Base class for real time stimulus parameter controller.
        For stimulus in viewport.
    """
    def __init__(self,stimulus):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.stimulus = stimulus
        self.viewport = stimulus.viewport
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass
    
class DTSweepStampController(StimulusController):
    """ Digital output for triggering and frame timing verification
        First 4 bits are used to indicate viewport visibility.
    """
    def __init__(self,*args,**kwargs):
        super(DTSweepStampController, self).__init__(*args,**kwargs)
        if DTBOARDINSTALLED: DT.initBoard()
    def during_go_eval(self):
        if DTBOARDINSTALLED: DT.setBitsNoDelay(SWEEP)
        postval = self.viewport.is_visible() and self.viewport.is_active()
        if self.viewport.name == 'left':
            postval = postval << 2
        if self.viewport.name == 'right':
            postval = postval << 3
        if DTBOARDINSTALLED: DT.postInt16NoDelay(postval) # post value to port, no delay
        
class SweepTableStimulusController(StimulusController):
    """ 
        Assume that all stimulus parameters come from the sweep table. 
    """
    def __init__(self,stimulus):
        super(SweepTableStimulusController,self).__init__(stimulus)
        
        self.st = stimulus.sweeptable.data
        self.static = stimulus.sweeptable.static #shorthand
        # multiply the sweeptable index with n vsync for every frame sweep
        nvsync = self.viewport.sec2intvsync(self.static.sweepSec)
        # TODO: create a global vsynctable so that run time modification could be easier.
        vsynctable = [vsync for sweep in stimulus.sweeptable.i for vsync in itertools.repeat(sweep,nvsync)]
        # iterator for every vsync sweep
        self.tableindex = iter(vsynctable)
    def next_index(self):
        """Return next vsync sweep index
        """
        try:
            return self.tableindex.next()
        except StopIteration:
            self.stimulus.sweep_completed = True
            return None

class SaveParamsController(SweepTableStimulusController):
    """ Use Every_Frame evaluation controller in case of real time sweep table modification
    """
    def __init__(self,stimulus,file_prefix):
        super(SaveParamsController, self).__init__(stimulus)
        self.savedpost = []
        self.file_prefix = file_prefix
        import time,os
        (year,month,day,hour24,min,sec) = time.localtime(time.time())[:6]
        trial_time_str = "%04d%02d%02d_%02d%02d%02d"%(year,month,day,hour24,min,sec)
        save_dir = os.path.abspath(os.curdir)+ os.path.sep + 'params'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.file_name = save_dir + os.path.sep + self.file_prefix + trial_time_str
        
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass

class SweepController(VisionEgg.FlowControl.Controller):
    """ Base sweep controller 
    """
    def __init__(self, framesweep):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.framesweep = framesweep
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass 

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
