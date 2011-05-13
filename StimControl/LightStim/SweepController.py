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
    
class SweepTableController(VisionEgg.FlowControl.Controller):
    """Base class for realtime stimulus parameter controller.
    All stimulus parameters come from sweeptable. 
    """
    def __init__(self,sweeptable,viewport=None):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.st = sweeptable.data
        self.static = sweeptable.static #shorthand
        self.viewport = viewport
        # multiply the sweeptable index with n vsync for every frame sweep
        nvsync = self.viewport.sec2intvsync(self.static.sweepSec)
        # TODO: create a global vsynctable so that run time modification could be easier.
        vsynctable = [vsync for sweep in sweeptable.i for vsync in itertools.repeat(sweep,nvsync)]
        # iterator for every vsync sweep
        self.tableindex = iter(vsynctable)
    def next_index(self):
        """Return next vsync sweep index
        """
        try:
            return self.tableindex.next()
        except StopIteration:
            return None
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass

class QuitSweepController(SweepTableController):
    def __init__(self,framesweep,*args,**kwargs):
        super(QuitSweepController, self).__init__(*args,**kwargs)
        self.framesweep = framesweep
    def during_go_eval(self):
        index = self.next_index()
        """If vsynctable runs to an end, quit the sweep right away."""
        if index == None:
            self.framesweep.parameters.go_duration = (0,'frames')
    
class SaveParamsController(SweepTableController):
    """ Use Every_Frame evaluation controller in case of real time sweep table modification
    """
    def __init__(self,file_prefix,*args,**kwargs):
        super(SaveParamsController, self).__init__(*args,**kwargs)
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
        
