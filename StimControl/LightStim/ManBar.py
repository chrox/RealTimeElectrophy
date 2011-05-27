# MarBar stimulus
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division
import math
import numpy as np
np.seterr(all='raise')
import pickle
import logging

import pygame
from pygame.locals import K_i
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot

from SweepController import StimulusController
from ManStimulus import ManStimulus

class ManBarController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(ManBarController, self).__init__(*args,**kwargs)
        self.tp = self.stimulus.tp
        self.bgp = self.stimulus.bgp
        self.tipp = self.stimulus.tipp
        self.cp = self.stimulus.cp

    def during_go_eval(self):
        self.stimulus.tp.on = self.stimulus.on
        width = self.viewport.deg2pix(self.stimulus.widthDeg) # convenience
        height = self.viewport.deg2pix(self.stimulus.heightDeg)
        self.tp.position = self.stimulus.x, self.stimulus.y
        self.tp.size = width, height # convert to pix
        self.tp.orientation = self.stimulus.ori
        self.tp.color = (self.stimulus.brightness, self.stimulus.brightness, self.stimulus.brightness, 1.0)
        self.bgp.color = (self.stimulus.bgbrightness, self.stimulus.bgbrightness, self.stimulus.bgbrightness, 1.0)
        self.tipp.position = ( self.stimulus.x + width / 2 * math.cos(math.pi / 180 * self.stimulus.ori),
                               self.stimulus.y + width / 2 * math.sin(math.pi / 180 * self.stimulus.ori) )
        self.tipp.orientation = self.stimulus.ori
        self.cp.position = self.stimulus.x, self.stimulus.y

class BarInfoController(StimulusController):
    """ update stimulus info """
    def __init__(self,*args,**kwargs):
        super(BarInfoController, self).__init__(*args,**kwargs)
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):                     
        self.sptp.text = 'pos : (%5.1f, %5.1f) deg  |  size : (%.1f, %.1f) deg  |  ori : %5.1f deg' \
                         % ( self.viewport.pix2deg(self.stimulus.x - self.viewport.width_pix / 2), \
                             self.viewport.pix2deg(self.stimulus.y - self.viewport.height_pix / 2),
                             self.stimulus.widthDeg, self.stimulus.heightDeg, self.stimulus.ori)

class SizeController(StimulusController):
    # Set bar size 
    def __init__(self,*args,**kwargs):
        super(SizeController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.UP:
            self.stimulus.heightDeg += self.stimulus.sizerateDegSec / self.viewport.refresh_rate
            if self.stimulus.squarelock: self.stimulus.widthDeg = self.stimulus.heightDeg
        elif self.stimulus.DOWN:
            self.stimulus.heightDeg = max(self.stimulus.heightDeg - self.stimulus.sizerateDegSec / self.viewport.refresh_rate, 0.1)
            if self.stimulus.squarelock: self.stimulus.widthDeg = self.stimulus.heightDeg
        if self.stimulus.RIGHT:
            self.stimulus.widthDeg += self.stimulus.sizerateDegSec / self.viewport.refresh_rate
            if self.stimulus.squarelock: self.stimulus.heightDeg = self.stimulus.widthDeg
        elif self.stimulus.LEFT:
            self.stimulus.widthDeg = max(self.stimulus.widthDeg - self.stimulus.sizerateDegSec / self.viewport.refresh_rate, 0.1)
            if self.stimulus.squarelock: self.stimulus.heightDeg = self.stimulus.widthDeg

class BrightnessController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(BrightnessController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.PLUS:
            self.stimulus.brightness += self.stimulus.brightnessstep
        elif self.stimulus.MINUS:
            self.stimulus.brightness -= self.stimulus.brightnessstep
        self.stimulus.brightness = max(self.stimulus.brightness, 0) # keep it >= 0
        self.stimulus.brightness = min(self.stimulus.brightness, 1) # keep it <= 1

class OrientationController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(OrientationController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        mod = self.stimulus.ori % self.stimulus.snapDeg
        self.stimulus.ori += self.stimulus.SCROLL_UP * (self.stimulus.snapDeg - mod)
        if mod == 0:
            mod = self.stimulus.snapDeg
        self.stimulus.ori -= self.stimulus.SCROLL_DOWN * mod
        if self.stimulus.LEFTBUTTON:
            self.stimulus.ori += self.stimulus.orirateDegSec / self.viewport.refresh_rate
        elif self.stimulus.RIGHTBUTTON:
            self.stimulus.ori -= self.stimulus.orirateDegSec / self.viewport.refresh_rate
        
        self.stimulus.SCROLL_UP = False
        self.stimulus.SCROLL_DOWN = False
        self.stimulus.ori = self.stimulus.ori % 360 # keep it in [0, 360)

class ManBar(ManStimulus):
    def __init__(self, **kwargs):
        super(ManBar, self).__init__(**kwargs)
        
        self.name = 'manbar'
        self.register_controllers()
        self.load_preference(0)
        
    def make_stimuli(self):
        self.target = Target2D(anchor='center',
                               anti_aliasing=self.antialiase,
                               color=(self.brightness, self.brightness, self.brightness, 1.0))
        self.tp = self.target.parameters # synonym
        self.tip = Target2D(size=(5, 1),
                            anchor='center',
                            anti_aliasing=self.antialiase,
                            color=(1.0, 0.0, 0.0, 1.0))
        self.tipp = self.tip.parameters
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
        self.complete_stimuli = (self.background, self.target, self.tip, self.fixationspot, self.centerspot) + self.info
        self.essential_stimuli = (self.background, self.target)
    
    def register_stimulus_controller(self):
        self.controllers.append(SizeController(self))
        self.controllers.append(OrientationController(self))
        self.controllers.append(BrightnessController(self))
        self.controllers.append(ManBarController(self))

    def register_info_controller(self):
        super(ManBar,self).register_info_controller()
        self.controllers.append(BarInfoController(self))

    def register_event_handlers(self):
        super(ManBar,self).register_event_handlers()

    def keydown_callback(self,event):
        super(ManBar,self).keydown_callback(event)
        key = event.key
        if key == K_i:
            self.brightness, self.bgbrightness = self.bgbrightness, self.brightness
    
    def load_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('VisionEgg')
        logger.info('Load preference for ' + info)
        self.defalut_preference = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':15.0,
                                   'heightDeg':3.0,
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
        self.heightDeg = self.preference['heightDeg']
        self.ori = self.preference['ori']
        # changes only after load/save a new preference
        self.x  = int(round(self.viewport.deg2pix(self.xorigDeg) + self.viewport.width_pix/2))
        self.y  = int(round(self.viewport.deg2pix(self.yorigDeg) + self.viewport.height_pix/2))
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
                self.preference['xorigDeg'] = self.viewport.pix2deg(self.x - self.viewport.width_pix / 2)
                self.preference['yorigDeg'] = self.viewport.pix2deg(self.y - self.viewport.height_pix / 2)
                self.preference['widthDeg'] = self.widthDeg
                self.preference['heightDeg'] = self.heightDeg
                self.preference['ori'] = self.ori
                preferences_dict[name][index] = self.preference
                pickle.dump(preferences_dict, pkl_output)
        except:
            logger.warning('Cannot save preference ' + info)
        self.fp.position = self.x, self.y
        self.brightenText = "Manbar" + str(index)  # brighten the text for feedback
        