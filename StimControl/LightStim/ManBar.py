# -*- coding: utf-8 -*-
# MarBar stimulus
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import math
import numpy as np
np.seterr(all='raise')
import pickle
import logging

from pygame.locals import K_f, K_i, K_o
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
        self.fp = self.stimulus.fp

    def during_go_eval(self):
        self.stimulus.tp.on = self.stimulus.on
        width = self.viewport.deg2pix(self.stimulus.widthDeg) # convenience
        height = self.viewport.deg2pix(self.stimulus.bheightDeg)
        self.cp.position = self.viewport.deg2pix(self.stimulus.xorigDeg) + self.viewport.xorig ,\
                           self.viewport.deg2pix(self.stimulus.yorigDeg) + self.viewport.yorig
        self.cp.on = self.stimulus.on
        self.fp.on = True
        self.tp.position = self.cp.position
        self.tp.size = width, height # convert to pix
        self.tp.orientation = self.stimulus.ori
        self.tp.color = (self.stimulus.brightness, self.stimulus.brightness, self.stimulus.brightness, 1.0)
        self.bgp.color = (self.stimulus.bgbrightness, self.stimulus.bgbrightness, self.stimulus.bgbrightness, 1.0)
        self.tipp.position = ( self.cp.position[0] + width / 2 * math.cos(math.pi / 180 * self.stimulus.ori),
                               self.cp.position[1] + width / 2 * math.sin(math.pi / 180 * self.stimulus.ori) )
        self.tipp.on = self.stimulus.on
        self.tipp.orientation = self.stimulus.ori

class BarInfoController(StimulusController):
    """ update stimulus info """
    def __init__(self,*args,**kwargs):
        super(BarInfoController, self).__init__(*args,**kwargs)
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):                     
        self.sptp.text = u'pos : (%5.1f, %5.1f) º  |  size : (%5.1f, %4.1f) º  |  ori : %5.1f º | brightness : %.2f' \
                         % ( self.stimulus.xorigDeg, self.stimulus.yorigDeg,
                             self.stimulus.widthDeg, self.stimulus.bheightDeg, self.stimulus.ori, self.stimulus.brightness)

class SizeController(StimulusController):
    # Set bar size 
    def __init__(self,*args,**kwargs):
        super(SizeController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        multiplier = self.stimulus.sizemultiplier
        if self.stimulus.UP:
            self.stimulus.bheightDeg = self.stimulus.bheightDeg * multiplier
            if self.stimulus.squarelock: self.stimulus.widthDeg = self.stimulus.bheightDeg
        elif self.stimulus.DOWN:
            self.stimulus.bheightDeg = max(self.stimulus.bheightDeg / multiplier, 0.1)
            if self.stimulus.squarelock: self.stimulus.widthDeg = self.stimulus.bheightDeg
        if self.stimulus.RIGHT:
            self.stimulus.widthDeg = self.stimulus.widthDeg * multiplier
            if self.stimulus.squarelock: self.stimulus.bheightDeg = self.stimulus.widthDeg
        elif self.stimulus.LEFT:
            self.stimulus.widthDeg = max(self.stimulus.widthDeg / multiplier, 0.1)
            if self.stimulus.squarelock: self.stimulus.bheightDeg = self.stimulus.widthDeg

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
        self.stimulus.ori += self.stimulus.orthogonalize_ori * 90.0
        self.stimulus.orthogonalize_ori = False
        self.stimulus.SCROLL_UP = False
        self.stimulus.SCROLL_DOWN = False
        self.stimulus.ori = self.stimulus.ori % 360 # keep it in [0, 360)

class PerpendicOrientation(OrientationController):
    def __init__(self,*args,**kwargs):
        super(PerpendicOrientation, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.perpend_to_dir:
            if not hasattr(self,'last_pos'):
                self.last_pos = (0,0)
            self.current_pos = (self.stimulus.x, self.stimulus.y)
            if self.last_pos != self.current_pos:
                self.stimulus.ori = 90.0 + math.atan2(self.current_pos[1]-self.last_pos[1], \
                                                      self.current_pos[0]-self.last_pos[0])*180.0/math.pi
            self.last_pos = self.current_pos
        super(PerpendicOrientation, self).during_go_eval()
        
class FlashController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(FlashController, self).__init__(*args,**kwargs)
        self.flash_duration_nvsync = self.viewport.sec2intvsync(self.stimulus.flashduration)
        self.flash_interval_nvsync = self.viewport.sec2intvsync(self.stimulus.flashinterval)
        self.flash_cycle_nvsync = self.flash_duration_nvsync + self.flash_interval_nvsync
        self.vsync_count = 1
        
    def during_go_eval(self):
        if self.stimulus.flash:
            self.stimulus.on = True if self.vsync_count <= self.flash_duration_nvsync else False
            self.vsync_count = (self.vsync_count + 1) % self.flash_cycle_nvsync if self.flash_cycle_nvsync != 0 else 1

class ManBar(ManStimulus):
    def __init__(self, params, **kwargs):
        super(ManBar, self).__init__(params=params, **kwargs)
        
        self.name = 'manbar'
        self.perpend_to_dir = False
        self.restored_on = self.on
        self.defalut_preference = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':5.0,
                                   'bheightDeg':2.0,
                                   'ori': 0.0}
        self.register_controllers()
        self.load_preference(0)
        self.set_parameters(params)
        
    def make_stimuli(self):
        self.target = Target2D(anchor='center',
                               anti_aliasing=self.antialiase,
                               color=(self.brightness, self.brightness, self.brightness, 1.0),
                               on=False)
        self.tp = self.target.parameters # synonym
        self.tip = Target2D(size=(5, 1),
                            anchor='center',
                            anti_aliasing=self.antialiase,
                            color=(1.0, 0.0, 0.0, 1.0),
                            on=False)
        self.tipp = self.tip.parameters
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
        self.complete_stimuli = (self.background, self.target, self.tip, self.fixationspot, self.centerspot) + self.info
        self.essential_stimuli = (self.background, self.target)
    
    def get_parameters(self):
        param_names = ['xorigDeg','yorigDeg','widthDeg','bheightDeg','ori']
        return dict((paramname,getattr(self,paramname)) for paramname in param_names)

    def set_parameters(self,parameters):
        for paramname, paramval in parameters.items():
            setattr(self, paramname, paramval)
    
    def register_stimulus_controller(self):
        self.controllers.append(SizeController(self))
        self.controllers.append(PerpendicOrientation(self))
        self.controllers.append(BrightnessController(self))
        self.controllers.append(FlashController(self))
        self.controllers.append(ManBarController(self))

    def register_info_controller(self):
        super(ManBar,self).register_info_controller()
        self.controllers.append(BarInfoController(self))

    def register_event_handlers(self):
        super(ManBar,self).register_event_handlers()

    def keydown_callback(self,event):
        super(ManBar,self).keydown_callback(event)
        key = event.key
        if key == K_f:
            if not self.flash:
                self.restored_on = self.on
            elif self.flash:
                self.on = self.restored_on
            self.flash = not self.flash
        if key == K_i: # invert background and bar brightness
            self.brightness, self.bgbrightness = self.bgbrightness, self.brightness
        if key == K_o: # orientation is perpendicular to bar moving direction
            self.perpend_to_dir = not self.perpend_to_dir
    
    def load_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('LightStim.ManBar')
        if self.viewport.get_name() != 'control':   # make control viewport like a passive viewport
            logger.info('Load preference for ' + info)
        try:
            with open('stimulus_params.pkl','rb') as pkl_input:
                preferences_dict = pickle.load(pkl_input)[name][index]
                for key in preferences_dict:
                    if key in self.defalut_preference and \
                              type(preferences_dict[key]) != type(self.defalut_preference[key]):
                        preferences_dict[key] = self.defalut_preference[key]
                        logger.warning("Found corrupted parameter '%s' for " %key + info + 
                                       ' Use the default value %s.'%str(self.defalut_preference[key]))
                self.defalut_preference.update(preferences_dict)
                self.preference = self.defalut_preference
        except:
            if self.viewport.get_name() != 'control':
                logger.warning('Cannot load preference for ' + info + ' Use the default preference.')
            self.preference = self.defalut_preference
        self.set_parameters(self.preference)
        # changes only after load/save a new preference
        self.x  = int(round(self.viewport.deg2pix(self.xorigDeg) + self.viewport.xorig))
        self.y  = int(round(self.viewport.deg2pix(self.yorigDeg) + self.viewport.yorig))
        self.fp.position = self.x, self.y
        self.viewport.save_mouse_pos((self.x, self.viewport.height_pix - self.y))
    def save_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('LightStim.ManBar')
        logger.info('Save preference for ' + info)
        preferences_dict = {}
        try:
            try:
                with open('stimulus_params.pkl','rb') as pkl_input:
                    preferences_dict = pickle.load(pkl_input)
            except:
                logger.warning('Cannot load previous preferences.'+ ' Use the default preference.')
            if name not in preferences_dict:
                preferences_dict[name] = [self.defalut_preference] * 2
            with open('stimulus_params.pkl','wb') as pkl_output:
                preferences_dict[name][index].update(self.get_parameters())
                pickle.dump(preferences_dict, pkl_output)
            logger.info('Saved parameters:\n' + str(self.get_parameters()))
        except:
            logger.warning('Cannot save preference ' + info)
        self.fp.position = self.x, self.y
        self.brightenText = "Index" + str(index)  # brighten the text for feedback
        