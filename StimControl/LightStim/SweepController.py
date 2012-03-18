# This module contains the base class of StimulusController.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

import itertools
import Pyro.core
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types
from SweepStamp import DT,DTBOARDINSTALLED,RSTART_EVT

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
    def set_viewport(self, viewport):
        self.viewport = viewport
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass
        
class ViewportController(StimulusController):
    """ Dummy class used to show that the controller is viewport sensitive.
        SEE LightStim.ManStimulus
    """
    def __init__(self,stimulus,viewport=None):
        super(ViewportController,self).__init__(stimulus)
        if viewport:
            self.set_viewport(viewport)

class SweepSequeStimulusController(StimulusController):
    def __init__(self,stimulus):
        super(SweepSequeStimulusController,self).__init__(stimulus)
        self.sweepseq = stimulus.sweepseq
        repeat = int(self.sweepseq.sweep_duration * self.viewport.refresh_rate) 
        # frame and sweep are confusing names sometimes. Most of the time a sweep corresponse a vsync in screen sweeping.
        # but in this line sweep means a frame defined in sweepseque.
        vsyncseque = [vsync for sweep in self.sweepseq.sequence_list for vsync in itertools.repeat(sweep,repeat)]
        self.vsync_list = list(itertools.chain.from_iterable(vsyncseque))
        self.sequence_iter = itertools.chain.from_iterable(vsyncseque)
        self.sequence_indices = iter(range(len(self.vsync_list)))
    def next_param(self):
        try:
            return self.sequence_iter.next()
        except StopIteration:
            self.stimulus.sweep_completed = True
            return None
    def next_index(self):
        try:
            return self.sequence_indices.next()
        except StopIteration:
            return None
    def get_sweeps_num(self):
        return len(self.vsync_list)
    def get_estimated_duration(self):
        return len(self.vsync_list) / self.viewport.refresh_rate

class DTSweepStampController:
    """ Digital output for triggering and frame timing verification
    """
    def __init__(self):
        if DTBOARDINSTALLED: DT.initBoard()
    def set_stamp(self,bits):
        if DTBOARDINSTALLED: DT.setBitsNoDelay(bits)
    def post_stamp(self,postval):
        if DTBOARDINSTALLED: 
            DT.postInt16NoDelay(postval)
            DT.clearBitsNoDelay(postval)
    def set_bits(self,setval):
        #print 'set bits: %d' %setval
        if DTBOARDINSTALLED:
            DT.setBits(setval)
    def clear_bits(self,clearval):
        #print 'clear bits: %d' %clearval
        if DTBOARDINSTALLED:
            DT.clearBits(clearval)
        
class DTSweepSequeController(DTSweepStampController, SweepSequeStimulusController):
    """ DTSweepStampController for SweepSeque stimulus
    """
    def __init__(self,*args,**kwargs):
        DTSweepStampController.__init__(self)
        SweepSequeStimulusController.__init__(self,*args,**kwargs)

class DTRemoteStartController(DTSweepStampController, VisionEgg.FlowControl.Controller):
    def __init__(self):
        DTSweepStampController.__init__(self)
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.ONCE)
    def during_go_eval(self):
        self.set_bits(RSTART_EVT)
    def between_go_eval(self):
        pass

class DTRemoteStopController(DTSweepStampController, VisionEgg.FlowControl.Controller):
    def __init__(self):
        DTSweepStampController.__init__(self)
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.ONCE)
    def during_go_eval(self):
        self.clear_bits(RSTART_EVT)
    def between_go_eval(self):
        pass

class SaveParamsController(SweepSequeStimulusController):
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
