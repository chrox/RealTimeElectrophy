# This module contains the base class of StimulusController.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

import itertools
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types
from VisionEgg.FlowControl import ONCE,TRANSITIONS,NOT_DURING_GO,NOT_BETWEEN_GO
from SweepStamp import RSTART_EVT,DAQStampTrigger

class StimulusController(VisionEgg.FlowControl.Controller):
    """ Base class for real time stimulus parameter controller.
        For stimulus in viewport.
    """
    def __init__(self,stimulus,
                  return_type=ve_types.NoneType,
                  eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=return_type,
                                           eval_frequency=eval_frequency)
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
    def __init__(self,stimulus,viewport=None,*args,**kwargs):
        super(ViewportController,self).__init__(stimulus,*args,**kwargs)
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
        
class SweepSequeTriggerController(SweepSequeStimulusController):
    """ DAQStampTrigger for SweepSeque stimulus
    """
    def __init__(self,*args,**kwargs):
        SweepSequeStimulusController.__init__(self,*args,**kwargs)
        self.stamp_trigger = DAQStampTrigger()
    def post_stamp(self, postval):
        self.stamp_trigger.post_stamp(postval)

class RemoteStartController(VisionEgg.FlowControl.Controller):
    """ Sending a START event
    """
    def __init__(self):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=ONCE|TRANSITIONS|NOT_BETWEEN_GO)
        self.stamp_trigger = DAQStampTrigger()
    def during_go_eval(self):
        #print 'set bits: %d' %RSTART_EVT
        self.stamp_trigger.post_stamp(RSTART_EVT, event='start')
    def between_go_eval(self):
        pass

class RemoteStopController(VisionEgg.FlowControl.Controller):
    """ Sending a STOP event
    """
    def __init__(self):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=ONCE|TRANSITIONS|NOT_DURING_GO)
        self.stamp_trigger = DAQStampTrigger()
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        #print 'clear bits: %d' %RSTART_EVT
        self.stamp_trigger.post_stamp(RSTART_EVT, event='stop')

class SaveParamsController(SweepSequeStimulusController):
    """ Use Every_Frame evaluation controller in case of real time sweep table modification
    """
    def __init__(self,stimulus,file_prefix):
        super(SaveParamsController, self).__init__(stimulus)
        self.savedpost = []
        self.file_prefix = file_prefix
        import time,os
        (year,month,day,hour24,_min,sec) = time.localtime(time.time())[:6]
        trial_time_str = "%04d%02d%02d_%02d%02d%02d"%(year,month,day,hour24,_min,sec)
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