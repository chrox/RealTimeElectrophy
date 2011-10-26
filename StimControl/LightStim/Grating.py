# -*- coding: utf-8 -*-
# Base class for grating stimulus.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise')
import pickle
import logging
from LightStim.SweepTable import dictattr
from LightStim.SweepSeque import TimingSeque, ParamSeque
from VisionEgg.Gratings import SinGrating2D
from VisionEgg.Textures import Mask2D
from VisionEgg.MoreStimuli import Target2D
from LightUtil import TimeFormat

from LightStim.Core import Stimulus

from SweepController import StimulusController,SweepSequeStimulusController,DTSweepSequeController

class GratingController(StimulusController):
    """ update mangrating parameters """
    def __init__(self,*args,**kwargs):
        super(GratingController, self).__init__(*args,**kwargs)
        
        self.gp = self.stimulus.gp
        if self.stimulus.parameters.mask:
            self.gmp = self.stimulus.gmp
        self.bgp = self.stimulus.bgp
    def during_go_eval(self):
        self.params = self.stimulus.parameters
        self.gp.position  = self.viewport.deg2pix(self.params.xorigDeg) + self.viewport.xorig ,\
                           self.viewport.deg2pix(self.params.yorigDeg) + self.viewport.yorig
        self.gp.spatial_freq = self.viewport.cycDeg2cycPix(self.params.sfreqCycDeg)
        self.gp.temporal_freq_hz = self.params.tfreqCycSec

        deltaphase = self.viewport.cycSec2cycVsync(self.params.tfreqCycSec) * 360
        self.params.phase0 = (self.params.phase0 - deltaphase) % 360.0
        self.gp.phase_at_t0 = self.params.phase0
        
        self.gp.orientation = (self.params.ori + 90) % 360.0
        self.gp.contrast = self.params.contrast
        self.bgp.color = (self.params.bgbrightness, self.params.bgbrightness, self.params.bgbrightness, 1.0)

class TimingController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(TimingController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
    def during_go_eval(self):
        stimulus_on = self.next_param()
        if stimulus_on:
            self.gp.on = True
        else:
            self.gp.on = False

class TimingStampController(DTSweepSequeController):
    def __init__(self,*args,**kwargs):
        super(TimingStampController, self).__init__(*args,**kwargs)
        self.logger = logging.getLogger('Lightstim.Grating')
    def during_go_eval(self):
        stimulus_on = self.next_param()
        if stimulus_on:
            """ 
                16-bits stimulus representation code will be posted to DT port
                     0 1 1 000000000000 1 
                     | | |              |------onset
                     | | |---------------------left viewport
                     | |---------------------- right viewport
                     |------------------------ reserved
            """
            if self.viewport.get_name() == 'left':
                viewport_value = 1<<13
            elif self.viewport.get_name() == 'right':
                viewport_value = 1<<14
            else:
                self.logger.error('Currently TimingStamp can only support left and right viewport.')
            post_val = viewport_value + 1
            self.post_stamp(post_val)
            
class ParamController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(ParamController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
    def during_go_eval(self):
        self.gp.temporal_freq_hz = 0.0
        next_param = self.next_param()
        if next_param is not None:
            self.gp.on = True
            orientation, spatial_freq, phase_at_t0 = next_param
            if orientation is not None and orientation == orientation:
                self.gp.orientation = (orientation + 90) % 360.0
            if spatial_freq is not None and spatial_freq == spatial_freq:
                self.gp.spatial_freq = self.viewport.cycDeg2cycPix(spatial_freq)
            if phase_at_t0 is not None and phase_at_t0 == phase_at_t0:
                self.gp.phase_at_t0 = phase_at_t0
            if any(num != num for num in next_param):  # check has any nan. assume that gp can handle nan parameter.
                self.gp.on = False

class ParamStampController(DTSweepSequeController):
    def __init__(self,*args,**kwargs):
        super(ParamStampController, self).__init__(*args,**kwargs)
        self.ori_range = list(np.linspace(0.0, 180.0, 16))
        self.spf_range = list(np.linspace(0.05, 1.0, 16))
        self.pha_range = list(np.linspace(0.0, 360.0, 16))
        self.logger = logging.getLogger('Lightstim.Grating')
    def during_go_eval(self):
        next_param = self.next_param()
        if next_param is not None and not any(num != num for num in next_param):
            orientation, spatial_freq, phase_at_t0 = next_param
            try:
                ori_index = self.ori_range.index(orientation) if orientation is not None else 0x0F
                spf_index = self.spf_range.index(spatial_freq) if spatial_freq is not None else 0x0F
                pha_index = self.pha_range.index(phase_at_t0) if phase_at_t0 is not None else 0x0F
            except ValueError:
                self.logger.error('Cannot post parameters:(%f,%f,%f)' %(orientation, spatial_freq, phase_at_t0)) 
            """ 
            16-bits stimulus representation code will be posted to DT port
            00 1  1 0101 0001 0011 
               |  |   |    |    |------------orientation index (0.0, 180.0, 16)
               |  |   |    |-----------------spatial_freq index (0.05, 1.0, 16)
               |  |   |----------------------phase_at_t0 index (0.0, 360.0, 16)
               |  |--------------------------stimulus onset
               |-----------------------------stimulus offset
            """
            onset = 1
            post_val = ori_index + (spf_index<<4) + (pha_index<<8) + (onset<<12)
            #print ori_index,spf_index,pha_index,post_val
        else:
            offset = 1
            post_val = offset<<13
        self.post_stamp(post_val)
            
        
class Grating(Stimulus):
    def __init__(self, params, sweepseq, **kwargs):
        super(Grating, self).__init__(**kwargs)
        self.name = 'grating'
        self.parameters = dictattr()
        self.load_params()
        self.set_parameters(self.parameters, params)
        self.sweepseq = sweepseq
        
        self.make_stimuli()
        self.register_controllers()
    def make_stimuli(self):
        size = self.viewport.get_size()
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   on=True)

        self.bgp = self.background.parameters
        #set background color before real sweep
        bgb = self.parameters.bgbrightness
        self.bgp.color = bgb, bgb, bgb, 1.0
        nsinsamples = 1024
        self.grating = SinGrating2D(anchor='center',
                                    pedestal=self.parameters.ml,
                                    ignore_time=True,
                                    num_samples=nsinsamples,
                                    max_alpha=1.0)
        self.gp = self.grating.parameters
        
        nmasksamples = 1024
        radius = self.viewport.deg2pix(self.parameters.maskDiameterDeg) / 2.0
        self.gp.size = [radius * 2] * 2
        samplesperpix = nmasksamples / self.gp.size[0]
        self.grating_mask = Mask2D(function=self.parameters.mask,
                                   radius_parameter=radius*samplesperpix,
                                   num_samples=(nmasksamples,nmasksamples))
        self.gp.mask = self.grating_mask
        self.gmp = self.grating_mask.parameters
        self.stimuli = (self.background, self.grating)

    def get_parameters(self):
        param_names = ['on','xorigDeg','yorigDeg','widthDeg','heightDeg','ori','mask','maskDiameterDeg','sfreqCycDeg','tfreqCycSec']
        return dict((paramname,self.parameters[paramname]) for paramname in param_names)

    def set_parameters(self, dest_params, source_params):
        for paramname, paramval in source_params.items():
            setattr(dest_params, paramname, paramval)
    
    def register_controllers(self):
        logger = logging.getLogger('Lightstim.Grating')
        self.controllers.append(GratingController(self))
        if isinstance(self.sweepseq, TimingSeque):
            logger.info('Register TimingController.')
            self.controllers.append(TimingController(self))
            self.controllers.append(TimingStampController(self))
        if isinstance(self.sweepseq, ParamSeque):
            logger.info('Register ParamController.')
            self.controllers.append(ParamController(self))
            self.controllers.append(ParamStampController(self))
        if isinstance(self.controllers[-1],SweepSequeStimulusController):
            controller = self.controllers[-1]
            estimated_duration = controller.get_estimated_duration()
            sweep_num = controller.get_sweeps_num()
            logger.info('Estimated stimulus duration: %s for %d sweeps.' %(str(TimeFormat(estimated_duration)), sweep_num))
        #self.controllers.append(DTSweepStampController(self))
            
    def load_params(self, index=0):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('Lightstim.Grating')
        logger.info('Load preference for ' + info)
        with open('Manbar_preference.pkl','rb') as pkl_input:
            preference = pickle.load(pkl_input)[name][index]
            self.set_parameters(self.parameters, preference)