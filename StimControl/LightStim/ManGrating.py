# -*- coding: utf-8 -*-
# ManGrating Stimulus
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise')
import logging

import pygame
from pygame.locals import K_COMMA,K_PERIOD,K_LEFTBRACKET,K_RIGHTBRACKET,K_m,K_c,K_f,K_g,KMOD_CTRL
from VisionEgg.Core import FixationSpot
from VisionEgg.Gratings import SinGrating2D
from VisionEgg.Textures import Mask2D

from SweepController import StimulusController
from ManStimulus import ManStimulus
from ManBar import SizeController,OrientationController,FlashController

class ManGratingController(StimulusController):
    """ update mangrating parameters """
    def __init__(self,*args,**kwargs):
        super(ManGratingController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
        if self.p.mask:
            self.gmp = self.stimulus.gmp
        self.bgp = self.stimulus.bgp
        self.cp = self.stimulus.cp
        self.fp = self.stimulus.fp
    def during_go_eval(self):
        self.cp.on = self.p.on
        self.cp.position = self.viewport.deg2pix(self.p.xorigDeg) + self.viewport.xorig ,\
                           self.viewport.deg2pix(self.p.yorigDeg) + self.viewport.yorig # update center spot position
        
        self.fp.on = True
        self.gp.on = self.p.on
        self.gp.position = self.cp.position
        
        if self.p.mask and self.stimulus.mask_on:
            radius = self.viewport.deg2pix(self.p.maskDiameterDeg) / 2.0
            if self.p.mask == 'gaussian':
                self.gp.size = [max(self.viewport.width_pix,self.viewport.height_pix) * 1.415] * 2
            else:
                self.gp.size = [radius * 2] * 2
            samplesperpix = self.stimulus.nmasksamples / self.gp.size[0]
            if self.gp.mask: # mask is on in last sweep 
                old_params = self.gp.mask.constant_parameters
                if not radius*samplesperpix == old_params.radius_parameter or not self.p.mask == old_params.function:
                    new_mask = Mask2D(function=self.p.mask,
                                      radius_parameter=radius*samplesperpix,
                                      num_samples=old_params.num_samples)
                    self.gp.mask = new_mask
            # mask is not on in last sweep find last mask
            elif self.p.mask == 'circle' and hasattr(self.stimulus,'last_circle_mask'):
                self.gp.mask = self.stimulus.last_circle_mask
            elif self.p.mask == 'gaussian' and hasattr(self.stimulus,'last_gaussian_mask'):
                self.gp.mask = self.stimulus.last_gaussian_mask 
            else: # first sweep
                new_mask = Mask2D(function=self.p.mask,
                                  radius_parameter=radius*samplesperpix,
                                  num_samples=self.stimulus.grating_mask.constant_parameters.num_samples)
                self.gp.mask = new_mask
            if self.p.mask == 'circle':
                self.stimulus.last_circle_mask = self.gp.mask
            if self.p.mask == 'gaussian':
                self.stimulus.last_gaussian_mask = self.gp.mask
        else:
            self.gp.size = self.viewport.deg2pix(self.p.gheightDeg), self.viewport.deg2pix(self.p.widthDeg) # convert to pix
            self.gp.mask = None
        self.gp.spatial_freq = self.viewport.cycDeg2cycPix(self.p.sfreqCycDeg)
        self.gp.temporal_freq_hz = self.p.tfreqCycSec
        
        # customize the drifting process so that when changing the grating size the drifting keeps smooth
        # have some hacks to rectify phase_at_t0
        try:
            self.last_heightDeg
        except AttributeError:
            self.last_heightDeg = self.p.gheightDeg
        delta_height = max((self.p.gheightDeg - self.last_heightDeg) / 2, 0)
        phase_rect = (delta_height / self.p.sfreqCycDeg * 360.0 / self.viewport.refresh_rate ) % 360.0
        self.last_heightDeg = self.p.gheightDeg
        deltaphase = self.viewport.cycSec2cycVsync(self.p.tfreqCycSec) * 360
        self.p.phase0 = (self.p.phase0 - phase_rect - deltaphase) % 360.0
        self.gp.phase_at_t0 = self.p.phase0
        
        self.gp.orientation = (self.p.ori + 90) % 360.0
        self.gp.contrast = self.p.contrast
        self.bgp.color = (self.p.bgbrightness, self.p.bgbrightness, self.p.bgbrightness, 1.0)                         

class GratingInfoController(StimulusController):
    """ update stimulus info """
    def __init__(self,*args,**kwargs):
        super(GratingInfoController, self).__init__(*args,**kwargs)
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):
        if not self.stimulus.mask_on:                     
            self.sptp.text = u'pos:(%5.1f,%5.1f)º| size:(%4.1f,%4.1f)º| ori:%5.1fº| tfreq:%.2fcyc/s| sfreq:%.2f cyc/º| contrast:%.2f' \
                            % ( self.p.xorigDeg, self.p.yorigDeg,
                                self.p.widthDeg, self.p.gheightDeg,
                                self.p.ori, self.p.tfreqCycSec, self.p.sfreqCycDeg, self.p.contrast)
        else:
            self.sptp.text = u'pos:(%5.1f,%5.1f)º | diameter:%5.1fº | ori:%5.1fº| tfreq:%.2fcyc/s| sfreq:%.2f cyc/º| contrast:%.2f' \
                            % ( self.p.xorigDeg, self.p.yorigDeg,
                                self.p.maskDiameterDeg,
                                self.p.ori, self.p.tfreqCycSec, self.p.sfreqCycDeg, self.p.contrast)
                 
class SpatialFrequencyController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(SpatialFrequencyController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.COMMA:
            self.p.sfreqCycDeg /= self.p.sfreqmultiplier
        elif self.stimulus.PERIOD:
            self.p.sfreqCycDeg *= self.p.sfreqmultiplier
            
class TemporalFrequencyController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(TemporalFrequencyController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.LEFTBRACKET:
            self.p.tfreqCycSec /= self.p.tfreqmultiplier
        elif self.stimulus.RIGHTBRACKET:
            self.p.tfreqCycSec *= self.p.tfreqmultiplier

class ContrastController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(ContrastController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.PLUS:
            self.p.contrast *= self.p.contrastmultiplier
        elif self.stimulus.MINUS:
            self.p.contrast /= self.p.contrastmultiplier
#        self.stimulus.contrast = max(self.stimulus.contrast, 0) # keep it >= 0
#        self.stimulus.contrast = min(self.stimulus.contrast, 1) # keep it <= 1

class GratingSizeController(SizeController):
    def __init__(self,*args,**kwargs):
        super(GratingSizeController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.p.mask and self.stimulus.mask_on:
            if self.stimulus.UP or self.stimulus.RIGHT:
                self.p.maskDiameterDeg += self.p.maskSizeStepDeg
                self.p.widthDeg = self.p.maskDiameterDeg
            elif self.stimulus.DOWN or self.stimulus.LEFT:
                self.p.maskDiameterDeg = max(self.p.maskDiameterDeg - self.p.maskSizeStepDeg, 0.1)
                self.p.widthDeg = self.p.maskDiameterDeg
            if self.p.widthDeg < self.p.gheightDeg: # set smaller value of grating width and height to maskDiameter 
                self.p.widthDeg = self.p.maskDiameterDeg
            else:
                self.p.gheightDeg = self.p.maskDiameterDeg
        else:
            super(GratingSizeController, self).during_go_eval()

class GratingOriController(OrientationController):
    def __init__(self,*args,**kwargs):
        super(GratingOriController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        super(GratingOriController, self).during_go_eval()
        self.p.ori += self.stimulus.reverse_direction * 180.0
        self.p.reverse_direction = False
        self.p.ori = self.p.ori % 360 # keep it in [0, 360)

class ManGrating(ManStimulus):
    def __init__(self, params, disp_info=False, **kwargs):
        super(ManGrating, self).__init__(params=params, disp_info=disp_info, **kwargs)
        """ Class specific data """
        self.name = 'mangrating'
        self.logger = logging.getLogger('LightStim.ManGrating')
        self.param_names = ['xorigDeg','yorigDeg','widthDeg','gheightDeg','ori','mask',\
                            'maskDiameterDeg','sfreqCycDeg','tfreqCycSec']
        self.defalut_parameters = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':5.0,
                                   'gheightDeg':5.0, # gheightDeg for grating stimulus
                                   'ori': 0.0,
                                   'mask':'circle',
                                   'maskDiameterDeg':5.0,
                                   'sfreqCycDeg':0.3,
                                   'tfreqCycSec':2.0,}
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        
        """ set special parameters """
        self.restored_on = self.parameters.on
        
        """ set special states """
        self.COMMA, self.PERIOD = False,False
        self.LEFTBRACKET, self.RIGHTBRACKET = False,False
        
        self.make_stimuli()
        self.stimuli = self.complete_stimuli if disp_info else self.essential_stimuli
        """ register controllers """
        self.register_controllers()
        
        self.restore_pos()
        
    def make_stimuli(self):
        super(ManGrating, self).make_stimuli()
        nsinsamples = 512
        self.grating = SinGrating2D(anchor='center',
                                    pedestal=self.parameters.ml,
                                    ignore_time=True,
                                    num_samples=nsinsamples,
                                    max_alpha=1.0,
                                    on=False) # opaque
        self.gp = self.grating.parameters
        self.nmasksamples = 256
        self.grating_mask = Mask2D(function='circle', num_samples=(self.nmasksamples, self.nmasksamples)) # size of mask texture data (# of texels)
        self.gmp = self.grating_mask.parameters
        if self.parameters.mask:
            self.mask_on = True
        else:
            self.mask_on = False
        self.fixationspot = FixationSpot(anchor='center',
                                                 color=(1.0, 0.0, 0.0, 0.0),
                                                 size=(5, 5),
                                                 on=False)
        self.fp = self.fixationspot.parameters
        self.centerspot = FixationSpot(anchor='center',
                                                 color=(0.0, 1.0, 0.0, 0.0),
                                                 size=(3, 3),
                                                 on=False)
        self.cp = self.centerspot.parameters
        self.complete_stimuli = (self.background, self.grating, self.fixationspot, self.centerspot) + self.info
        self.essential_stimuli = (self.background, self.grating)
    
    def register_stimulus_controller(self):
        self.controllers.append(GratingSizeController(self))
        self.controllers.append(SpatialFrequencyController(self))
        self.controllers.append(TemporalFrequencyController(self))
        self.controllers.append(GratingOriController(self))
        self.controllers.append(ContrastController(self))
        self.controllers.append(FlashController(self))
        self.controllers.append(ManGratingController(self))
        
    def register_info_controller(self):
        super(ManGrating,self).register_info_controller()
        self.controllers.append(GratingInfoController(self))
    
    def restore_pos(self):
        # changes only after load/save a new preference
        self.x  = int(round(self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig))
        self.y  = int(round(self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig))
        self.fp.position = self.x, self.y
        self.viewport.save_mouse_pos((self.x, self.viewport.height_pix - self.y))
    
    def load_params(self, index=0):
        super(ManGrating,self).load_params(index)
        self.parameters.maskDiameterDeg = self.parameters['widthDeg']
        if self.parameters.mask:
            self.mask_on = True
        
    def save_params(self, index):
        super(ManGrating,self).save_params(index)
        self.fp.position = self.x, self.y
        self.brightenText = "Index" + str(index)  # brighten the text for feedback
        
    def keydown_callback(self,event):
        super(ManGrating,self).keydown_callback(event)
        mods = pygame.key.get_mods()
        key = event.key
        if key == K_COMMA:
            self.COMMA = True
        elif key == K_PERIOD:
            self.PERIOD = True
        elif key == K_LEFTBRACKET:
            self.LEFTBRACKET = True
        elif key == K_RIGHTBRACKET:
            self.RIGHTBRACKET = True
        elif key == K_m:
            self.mask_on = not self.mask_on
        elif key == K_c and not mods & KMOD_CTRL:
            self.parameters.mask = 'circle'
            self.mask_on = True
        elif key == K_f:
            self.parameters.flash = not self.parameters.flash
        elif key == K_g and not mods & KMOD_CTRL:
            self.parameters.mask = 'gaussian'
            self.mask_on = True
            
    def keyup_callback(self,event):
        super(ManGrating,self).keyup_callback(event)
        key = event.key
        if key == K_COMMA:
            self.COMMA = False
        elif key == K_PERIOD:
            self.PERIOD = False
        elif key == K_LEFTBRACKET:
            self.LEFTBRACKET = False
        elif key == K_RIGHTBRACKET:
            self.RIGHTBRACKET = False
        