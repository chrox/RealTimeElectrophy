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
import random
from LightStim.SweepTable import dictattr
from LightStim.SweepSeque import TimingSeque, ParamSeque
from VisionEgg.Gratings import SinGrating2D
from VisionEgg.Textures import Mask2D
from VisionEgg.MoreStimuli import Target2D

from LightStim.Core import Stimulus

from SweepController import StimulusController,SweepSequeStimulusController

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
            
class ParamController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(ParamController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
    def during_go_eval(self):
        self.gp.temporal_freq_hz = 0.0
        next_param = self.next_param()
        if next_param is not None:
            orientation, spatial_freq, phase_at_t0 = next_param
            self.gp.phase_at_t0 = phase_at_t0
            self.gp.orientation = (orientation + 90) % 360.0
            self.gp.spatial_freq = self.viewport.cycDeg2cycPix(spatial_freq)

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
        if isinstance(self.sweepseq, ParamSeque):
            logger.info('Register ParamController.')
            self.controllers.append(ParamController(self))
        #self.controllers.append(DTSweepStampController(self))
            
    def load_params(self, index=0):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('Lightstim.Grating')
        logger.info('Load preference for ' + info)
        with open('Manbar_preference.pkl','rb') as pkl_input:
            preference = pickle.load(pkl_input)[name][index]
            self.set_parameters(self.parameters, preference)