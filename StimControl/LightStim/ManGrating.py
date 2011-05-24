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
from pygame.locals import K_COMMA,K_PERIOD,K_LEFTBRACKET,K_RIGHTBRACKET
from VisionEgg.Core import FixationSpot
from VisionEgg.Gratings import SinGrating2D

from SweepController import StimulusController
from ManStimulus import ManStimulus
from ManBar import SizeController,OrientationController

class ManGratingController(StimulusController):
    """ update bar parameters """
    def __init__(self,*args,**kwargs):
        super(ManGratingController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
        self.bgp = self.stimulus.bgp
        self.cp = self.stimulus.cp
        self.sptp = self.stimulus.sptp
        self.stp = self.stimulus.stp
        self.sltp = self.stimulus.sltp 
    def during_go_eval(self):
        self.cp.position = self.stimulus.x, self.stimulus.y # update center spot position
        self.gp.position = self.stimulus.x, self.stimulus.y
        self.gp.on = self.stimulus.on
        self.gp.size = self.viewport.deg2pix(self.stimulus.heightDeg), self.viewport.deg2pix(self.stimulus.widthDeg) # convert to pix
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
        self.sptp.text = 'x, y = (%5.1f, %5.1f) deg | size = (%.1f, %.1f) deg | ori = %5.1f deg | tfreq = %.2f cyc/sec | sfreq = %.2f cyc/deg | contrast = %.2f' \
                         % ( self.viewport.pix2deg(self.stimulus.x - self.viewport.width_pix / 2), 
                             self.viewport.pix2deg(self.stimulus.y - self.viewport.height_pix / 2),
                             self.stimulus.widthDeg, self.stimulus.heightDeg,
                             self.stimulus.ori, self.stimulus.tfreqCycSec, self.stimulus.sfreqCycDeg, self.stimulus.contrast)

        self.stp.text = self.stimulus.screenstring
        if self.stimulus.brightenText == 'Manbar0':
            self.sptp.color = (1.0, 1.0, 0.0, 1.0) # set to yellow
        elif self.stimulus.brightenText == 'Manbar1':
            self.sptp.color = (1.0, 0.0, 0.0, 1.0) # set to red
        else:
            self.stimulus.sptp.color = (0.0, 1.0, 0.0, 1.0) # set it back to green
            self.stimulus.stp.color = (0.0, 1.0, 1.0, 1.0) # set it back to cyan

        if self.stimulus.squarelock:
            self.stimulus.sltp.on = True
        else:
            self.stimulus.sltp.on = False
            
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
            
class ManGrating(ManStimulus):
    def __init__(self, disp_info, **kwargs):
        super(ManGrating, self).__init__(**kwargs)
        self.name = 'mangrating'
        self.COMMA, self.PERIOD = False,False
        self.LEFTBRACKET, self.RIGHTBRACKET = False,False

        self.make_stimuli(disp_info)
        self.register_controllers()
        self.register_event_handlers()
        # load preference from saved file
        self.load_preference(0)
    def make_stimuli(self, disp_info):
        
        nsinsamples = 2048 # number of samples of sine f'n, must be power of 2, quality/performance tradeoff
        self.grating = SinGrating2D(anchor='center',
                                    pedestal=self.ml,
                                    ignore_time=True,
                                    num_samples=nsinsamples,
                                    max_alpha=1.0) # opaque
        self.gp = self.grating.parameters
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
        
        # last entry will be topmost layer in viewport
        self.basic_stimuli = (self.background, self.grating)
        self.all_stimuli = (self.background, self.grating,
                            self.fixationspot, self.centerspot,
                            self.upperbar, self.squarelocktext, self.screentext,
                            self.lowerbar, self.stimulusparamtext)
        
        if disp_info:
            self.stimuli = self.all_stimuli
        else:
            self.stimuli = self.basic_stimuli
    
    def register_controllers(self):
        self.controllers.append(SizeController(self))
        self.controllers.append(SpatialFrequencyController(self))
        self.controllers.append(TemporalFrequencyController(self))
        self.controllers.append(OrientationController(self))
        self.controllers.append(ContrastController(self))
        self.controllers.append(ManGratingController(self))
        
    def register_event_handlers(self):
        super(ManGrating,self).register_event_handlers()
        
    def keydown_callback(self,event):
        super(ManGrating,self).keydown_callback(event)
        key = event.key
        if key == K_COMMA:
            self.COMMA = True
        elif key == K_PERIOD:
            self.PERIOD = True
        elif key == K_LEFTBRACKET:
            self.LEFTBRACKET = True
        elif key == K_RIGHTBRACKET:
            self.RIGHTBRACKET = True
            
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
        info = self.name + str(index) + ' in ' + name + '.'
        logger = logging.getLogger('VisionEgg')
        logger.info('Load preference for ' + info)
        self.defalut_preference = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':15.0,
                                   'heightDeg':15.0,
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
        if 'sfreqCycDeg' in self.preference:
            self.sfreqCycDeg = self.preference['sfreqCycDeg']
        if 'tfreqCycSec' in self.preference:
            self.tfreqCycSec = self.preference['tfreqCycSec']
        self.ori = self.preference['ori']
        # changes only after load/save a new preference
        self.x  = int(round(self.viewport.deg2pix(self.xorigDeg) + self.viewport.width_pix/2))
        self.y  = int(round(self.viewport.deg2pix(self.yorigDeg) + self.viewport.height_pix/2))
        self.fp.position = self.x, self.y
        if self.viewport.name == 'Viewport_control':
            pygame.mouse.set_pos([self.x, self.viewport.height_pix - self.y])
            
    def save_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + '.'
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
                self.preference['xorigDeg'] = self.viewport.pix2deg(self.x - self.viewport.width_pix / 2)
                self.preference['yorigDeg'] = self.viewport.pix2deg(self.y - self.viewport.height_pix / 2)
                self.preference['widthDeg'] = self.widthDeg
                #self.preference['heightDeg'] = self.heightDeg
                self.preference['sfreqCycDeg'] = self.sfreqCycDeg
                self.preference['tfreqCycSec'] = self.tfreqCycSec
                self.preference['ori'] = self.ori
                preferences_dict[name][index] = self.preference
                pickle.dump(preferences_dict, pkl_output)
        except:
            logger.warning('Cannot save preference ' + info)
        self.fp.position = self.x, self.y
        self.brightenText = "Manbar" + str(index)  # brighten the text for feedback
        