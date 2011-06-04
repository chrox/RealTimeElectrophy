# ManGrating Stimulus
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

import pygame
from pygame.locals import K_COMMA,K_PERIOD,K_LEFTBRACKET,K_RIGHTBRACKET,K_m,K_c,K_g
from VisionEgg.Core import FixationSpot
from VisionEgg.Gratings import SinGrating2D
from VisionEgg.Textures import Mask2D

from SweepController import StimulusController
from ManStimulus import ManStimulus
from ManBar import SizeController,OrientationController

class ManGratingController(StimulusController):
    """ update mangrating parameters """
    def __init__(self,*args,**kwargs):
        super(ManGratingController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
        if self.stimulus.mask:
            self.gmp = self.stimulus.gmp
        self.bgp = self.stimulus.bgp
        self.cp = self.stimulus.cp 
    def during_go_eval(self):
        self.cp.position = self.viewport.deg2pix(self.stimulus.xorigDeg) + self.viewport.xorig ,\
                           self.viewport.deg2pix(self.stimulus.yorigDeg) + self.viewport.yorig # update center spot position
        self.gp.position = self.cp.position
        self.gp.on = self.stimulus.on
        if self.stimulus.mask and self.stimulus.mask_on:
            radius = self.viewport.deg2pix(self.stimulus.maskDiameterDeg) / 2.0
            if self.stimulus.mask == 'gaussian':
                self.gp.size = [max(self.viewport.width_pix,self.viewport.height_pix) * 1.415] * 2
            else:
                self.gp.size = [radius * 2] * 2
            samplesperpix = self.stimulus.nmasksamples / self.gp.size[0]
            if self.gp.mask: # mask is on in last sweep 
                old_params = self.gp.mask.constant_parameters
                if not radius*samplesperpix == old_params.radius_parameter or not self.stimulus.mask == old_params.function:
                    new_mask = Mask2D(function=self.stimulus.mask,
                                      radius_parameter=radius*samplesperpix,
                                      num_samples=old_params.num_samples)
                    self.gp.mask = new_mask
            # mask is not on in last sweep find last mask
            elif self.stimulus.mask == 'circle' and hasattr(self.stimulus,'last_circle_mask'):
                self.gp.mask = self.stimulus.last_circle_mask
            elif self.stimulus.mask == 'gaussian' and hasattr(self.stimulus,'last_gaussian_mask'):
                self.gp.mask = self.stimulus.last_gaussian_mask 
            else: # first sweep
                new_mask = Mask2D(function=self.stimulus.mask,
                                  radius_parameter=radius*samplesperpix,
                                  num_samples=self.stimulus.grating_mask.constant_parameters.num_samples)
                self.gp.mask = new_mask
            if self.stimulus.mask == 'circle':
                self.stimulus.last_circle_mask = self.gp.mask
            if self.stimulus.mask == 'gaussian':
                self.stimulus.last_gaussian_mask = self.gp.mask
        else:
            self.gp.size = self.viewport.deg2pix(self.stimulus.heightDeg), self.viewport.deg2pix(self.stimulus.widthDeg) # convert to pix
            self.gp.mask = None
        self.gp.spatial_freq = self.viewport.cycDeg2cycPix(self.stimulus.sfreqCycDeg)
        self.gp.temporal_freq_hz = self.stimulus.tfreqCycSec
        
        # customize the drifting process so that when changing the grating size the drifting keeps smooth
        # have some hacks to rectify phase_at_t0
        try:
            self.last_heightDeg
        except AttributeError:
            self.last_heightDeg = self.stimulus.heightDeg
        delta_height = max((self.stimulus.heightDeg - self.last_heightDeg) / 2, 0)
        phase_rect = (delta_height / self.stimulus.sfreqCycDeg * 360.0 / self.viewport.refresh_rate ) % 360.0
        self.last_heightDeg = self.stimulus.heightDeg
        deltaphase = self.viewport.cycSec2cycVsync(self.stimulus.tfreqCycSec) * 360
        self.stimulus.phase0 = (self.stimulus.phase0 - phase_rect - deltaphase) % 360.0
        self.gp.phase_at_t0 = self.stimulus.phase0
        
        self.gp.orientation = (self.stimulus.ori + 90) % 360.0
        self.gp.contrast = self.stimulus.contrast
        self.bgp.color = (self.stimulus.bgbrightness, self.stimulus.bgbrightness, self.stimulus.bgbrightness, 1.0)                         

class GratingInfoController(StimulusController):
    """ update stimulus info """
    def __init__(self,*args,**kwargs):
        super(GratingInfoController, self).__init__(*args,**kwargs)
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):
        if not self.stimulus.mask_on:                     
            self.sptp.text = 'pos: (%5.1f, %5.1f) deg | size: (%4.1f, %4.1f) deg | ori: %5.1f deg | tfreq: %.2f cyc/sec | sfreq: %.2f cyc/deg | contrast: %.2f' \
                            % ( self.stimulus.xorigDeg, self.stimulus.yorigDeg,
                                self.stimulus.widthDeg, self.stimulus.heightDeg,
                                self.stimulus.ori, self.stimulus.tfreqCycSec, self.stimulus.sfreqCycDeg, self.stimulus.contrast)
        else:
            self.sptp.text = 'pos: (%5.1f, %5.1f) deg | diameter: %5.1f deg | ori: %5.1f deg | tfreq: %.2f cyc/sec | sfreq: %.2f cyc/deg | contrast: %.2f' \
                            % ( self.stimulus.xorigDeg, self.stimulus.yorigDeg,
                                self.stimulus.maskDiameterDeg,
                                self.stimulus.ori, self.stimulus.tfreqCycSec, self.stimulus.sfreqCycDeg, self.stimulus.contrast)
                 
class SpatialFrequencyController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(SpatialFrequencyController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.COMMA:
            self.stimulus.sfreqCycDeg /= self.stimulus.sfreqmultiplier
        elif self.stimulus.PERIOD:
            self.stimulus.sfreqCycDeg *= self.stimulus.sfreqmultiplier
            
class TemporalFrequencyController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(TemporalFrequencyController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.LEFTBRACKET:
            self.stimulus.tfreqCycSec /= self.stimulus.tfreqmultiplier
        elif self.stimulus.RIGHTBRACKET:
            self.stimulus.tfreqCycSec *= self.stimulus.tfreqmultiplier

class ContrastController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(ContrastController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.PLUS:
            self.stimulus.contrast *= self.stimulus.contrastmultiplier
        elif self.stimulus.MINUS:
            self.stimulus.contrast /= self.stimulus.contrastmultiplier
#        self.stimulus.contrast = max(self.stimulus.contrast, 0) # keep it >= 0
#        self.stimulus.contrast = min(self.stimulus.contrast, 1) # keep it <= 1

class GratingSizeController(SizeController):
    def __init__(self,*args,**kwargs):
        super(GratingSizeController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.mask and self.stimulus.mask_on:
            if self.stimulus.UP or self.stimulus.RIGHT:
                self.stimulus.maskDiameterDeg += self.stimulus.maskSizeStepDeg
            elif self.stimulus.DOWN or self.stimulus.LEFT:
                self.stimulus.maskDiameterDeg = max(self.stimulus.maskDiameterDeg - self.stimulus.maskSizeStepDeg, 0.1)
            if self.stimulus.widthDeg < self.stimulus.heightDeg: # set smaller value of grating width and height to maskDiameter 
                self.stimulus.widthDeg = self.stimulus.maskDiameterDeg
            else:
                self.stimulus.heightDeg = self.stimulus.maskDiameterDeg
        else:
            super(GratingSizeController, self).during_go_eval()
    
class ManGrating(ManStimulus):
    def __init__(self, **kwargs):
        super(ManGrating, self).__init__(**kwargs)
        self.name = 'mangrating'
        self.COMMA, self.PERIOD = False,False
        self.LEFTBRACKET, self.RIGHTBRACKET = False,False

        self.register_controllers()
        #self.register_event_handlers()
        # load preference from saved file
        self.load_preference(0)
    def make_stimuli(self):
        nsinsamples = 512
        self.grating = SinGrating2D(anchor='center',
                                    pedestal=self.ml,
                                    ignore_time=True,
                                    num_samples=nsinsamples,
                                    max_alpha=1.0) # opaque
        self.gp = self.grating.parameters
        self.nmasksamples = 512
        self.grating_mask = Mask2D(function='circle', num_samples=(self.nmasksamples, self.nmasksamples)) # size of mask texture data (# of texels)
        self.gmp = self.grating_mask.parameters
        if self.mask:
            self.mask_on = True
        else:
            self.mask_on = False
        self.fixationspot = FixationSpot(anchor='center',
                                                 color=(1.0, 0.0, 0.0, 0.0),
                                                 size=(5, 5),
                                                 on=True)
        self.fp = self.fixationspot.parameters
        self.centerspot = FixationSpot(anchor='center',
                                                 color=(0.0, 1.0, 0.0, 0.0),
                                                 size=(3, 3),
                                                 on=True)
        self.cp = self.centerspot.parameters
        self.complete_stimuli = (self.background, self.grating, self.fixationspot, self.centerspot) + self.info
        self.essential_stimuli = (self.background, self.grating)
    
    def register_stimulus_controller(self):
        self.controllers.append(GratingSizeController(self))
        self.controllers.append(SpatialFrequencyController(self))
        self.controllers.append(TemporalFrequencyController(self))
        self.controllers.append(OrientationController(self))
        self.controllers.append(ContrastController(self))
        self.controllers.append(ManGratingController(self))
        
    def register_info_controller(self):
        super(ManGrating,self).register_info_controller()
        self.controllers.append(GratingInfoController(self))
        
    def register_event_handlers(self):
        super(ManGrating,self).register_event_handlers()
        
    def rebuild_event_handlers(self):
        super(ManGrating,self).rebuild_event_handlers()
        
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
        elif key == K_c and not mods:
            self.mask = 'circle'
            self.mask_on = True
        elif key == K_g and not mods:
            self.mask = 'gaussian'
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
            
    def load_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('VisionEgg')
        logger.info('Load preference for ' + info)
        self.defalut_preference = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':15.0,
                                   'heightDeg':15.0,
                                   'mask':'circle',
                                   'maskDiameterDeg':15.0,
                                   'sfreqCycDeg':0.07,
                                   'tfreqCycSec':0.5,
                                   'ori': 0.0}
        try:
            with open('Manbar_preference.pkl','rb') as pkl_input:
                preferences_dict = pickle.load(pkl_input)
                self.preference = preferences_dict[name][index]
        except:
            logger.warning('Cannot load preference for ' + info + ' Use the default preference.')
            self.preference = self.defalut_preference
        self.xorigDeg = self.preference['xorigDeg']
        self.yorigDeg = self.preference['yorigDeg']
        self.widthDeg = self.preference['widthDeg']
        self.heightDeg = self.preference['widthDeg']
        if 'mask' in self.preference:
            self.mask = self.preference['mask']
            if self.mask:
                self.mask_on = True
        if 'maskDiameterDeg' in self.preference:
            self.maskDiameterDeg = self.preference['maskDiameterDeg']
        if 'sfreqCycDeg' in self.preference:
            self.sfreqCycDeg = self.preference['sfreqCycDeg']
        if 'tfreqCycSec' in self.preference:
            self.tfreqCycSec = self.preference['tfreqCycSec']
        self.ori = self.preference['ori']
        # changes only after load/save a new preference
        self.x  = int(round(self.viewport.deg2pix(self.xorigDeg) + self.viewport.xorig))
        self.y  = int(round(self.viewport.deg2pix(self.yorigDeg) + self.viewport.yorig))
        self.fp.position = self.x, self.y
        if self.viewport.name == 'control':
            pygame.mouse.set_pos([self.x, self.viewport.height_pix - self.y])
            
    def save_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('VisionEgg')
        logger.info('Save preference for ' + info)
        preferences_dict = {}
        try:
            try:
                with open('Manbar_preference.pkl','rb') as pkl_input:
                    preferences_dict = pickle.load(pkl_input)
            except:
                logger.warning('Cannot load previous preferences.'+ ' Use the default preference.')
            if name not in preferences_dict:
                preferences_dict[name] = [self.defalut_preference] * 2
            with open('Manbar_preference.pkl','wb') as pkl_output:
                self.preference['xorigDeg'] = self.xorigDeg
                self.preference['yorigDeg'] = self.yorigDeg
                self.preference['widthDeg'] = self.widthDeg
                #self.preference['heightDeg'] = self.heightDeg
                self.preference['mask'] = self.mask
                self.preference['maskDiameterDeg'] = self.maskDiameterDeg
                self.preference['sfreqCycDeg'] = self.sfreqCycDeg
                self.preference['tfreqCycSec'] = self.tfreqCycSec
                self.preference['ori'] = self.ori
                preferences_dict[name][index] = self.preference
                pickle.dump(preferences_dict, pkl_output)
        except:
            logger.warning('Cannot save preference ' + info)
        self.fp.position = self.x, self.y
        self.brightenText = "Manbar" + str(index)  # brighten the text for feedback
        