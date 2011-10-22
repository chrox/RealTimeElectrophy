# This module contains the base class of SweepTableController.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import logging
import itertools
import Pyro.core
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types
from SweepStamp import DT,DTBOARDINSTALLED
from LightUtil import ISOTimeFormat

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
        SEE Lightstim.ManStimulus
    """
    def __init__(self,stimulus,viewport=None):
        super(ViewportController,self).__init__(stimulus)
        if viewport:
            self.set_viewport(viewport)

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
        # runtime control will be achived by pyro parameter pass.
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

class SweepSequeStimulusController(StimulusController):
    def __init__(self,stimulus):
        logger = logging.getLogger('Lightstim.SweepController')
        super(SweepSequeStimulusController,self).__init__(stimulus)
        self.sweepseq = stimulus.sweepseq
        repeat = int(self.sweepseq.sweep_duration * self.viewport.refresh_rate) 
        # frame and sweep are confusing names sometimes. Most of the time a sweep corresponse a vsync in screen sweeping.
        # but in this line sweep means a frame defined in sweepseque.
        self.vsyncseque = [vsync for sweep in self.sweepseq.sequence_list for vsync in itertools.repeat(sweep,repeat)]
        self.sequence_iter = itertools.chain.from_iterable(self.vsyncseque)
        estemated_duration = self.get_estemated_duration()
        logger.info('Estimated stimulus duration: %s' %str(ISOTimeFormat(estemated_duration)))
    def next_param(self):
        try:
            return self.sequence_iter.next()
        except StopIteration:
            self.stimulus.sweep_completed = True
            return None
    def get_vsyncs(self):
        return len(list(itertools.chain.from_iterable(self.vsyncseque)))
    def get_estemated_duration(self):
        return self.get_vsyncs() / self.viewport.refresh_rate

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


class DTSweepStampController(SweepTableStimulusController):
    """ Digital output for triggering and frame timing verification
    """
    def __init__(self,*args,**kwargs):
        super(DTSweepStampController, self).__init__(*args,**kwargs)
        if DTBOARDINSTALLED: DT.initBoard()
    def set_stamp(self,bits):
        if DTBOARDINSTALLED: DT.setBitsNoDelay(bits)
    def post_stamp(self,postval):
        if DTBOARDINSTALLED: 
            DT.postInt16NoDelay(postval)
            DT.clearBitsNoDelay(postval)

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
