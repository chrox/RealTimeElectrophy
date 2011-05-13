# This module contains the base class of SweepTableController.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import itertools
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types
    
class StimulusController(VisionEgg.FlowControl.Controller):
    """ Base class for real time stimulus parameter controller.
        Assume that all stimulus parameters come from the sweep table. 
    """
    def __init__(self,stimulus):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.stimulus = stimulus
        self.st = stimulus.sweeptable.data
        self.static = stimulus.sweeptable.static #shorthand
        self.viewport = stimulus.viewport
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
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass

class SaveParamsController(StimulusController):
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

class QuitSweepController(VisionEgg.FlowControl.Controller):
    """ Quit the frame sweep loop if there is no viewports in the screen
    """
    def __init__(self, framesweep):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.framesweep = framesweep
    def during_go_eval(self):
        if self.framesweep.parameters.viewports == []:
            self.framesweep.parameters.go_duration = (0, 'frames')
    def between_go_eval(self):
        pass

class CheckViewportController(VisionEgg.FlowControl.Controller):
    """ Quit the frame sweep loop if there is no viewports in the screen
    """
    def __init__(self, framesweep):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.framesweep = framesweep
    def during_go_eval(self):
        viewports_cleaned = True
        p = self.framesweep.parameters
        for viewport in p.viewports:
            for stimulus in viewport.parameters.stimuli:
                viewports_cleaned &= stimulus.sweep_completed
        if viewports_cleaned:
            self.framesweep.parameters.viewports = []
            
    def between_go_eval(self):
        pass
    