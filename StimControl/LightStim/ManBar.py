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

from LightData import dictattr
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
        self.stimulus.tp.on = self.p.on
        width = self.viewport.deg2pix(self.p.widthDeg) # convenience
        height = self.viewport.deg2pix(self.p.bheightDeg)
        self.cp.position = self.viewport.deg2pix(self.p.xorigDeg) + self.viewport.xorig ,\
                           self.viewport.deg2pix(self.p.yorigDeg) + self.viewport.yorig
        self.cp.on = self.p.on
        self.fp.on = True
        self.tp.position = self.cp.position
        self.tp.size = width, height # convert to pix
        self.tp.orientation = self.p.ori
        self.tp.color = (self.p.brightness, self.p.brightness, self.p.brightness, 1.0)
        self.bgp.color = (self.p.bgbrightness, self.p.bgbrightness, self.p.bgbrightness, 1.0)
        self.tipp.position = ( self.cp.position[0] + width / 2 * math.cos(math.pi / 180 * self.p.ori),
                               self.cp.position[1] + width / 2 * math.sin(math.pi / 180 * self.p.ori) )
        self.tipp.on = self.p.on
        self.tipp.orientation = self.p.ori

class BarInfoController(StimulusController):
    """ update stimulus info """
    def __init__(self,*args,**kwargs):
        super(BarInfoController, self).__init__(*args,**kwargs)
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):                     
        self.sptp.text = u'pos : (%5.1f, %5.1f) º  |  size : (%5.1f, %4.1f) º  |  ori : %5.1f º | brightness : %.2f' \
                         % ( self.p.xorigDeg, self.p.yorigDeg,
                             self.p.widthDeg, self.p.bheightDeg, self.p.ori, self.p.brightness)

class SizeController(StimulusController):
    # Set bar size 
    def __init__(self,*args,**kwargs):
        super(SizeController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        multiplier = self.p.sizemultiplier
        if self.stimulus.UP:
            self.p.bheightDeg = self.p.bheightDeg * multiplier
            if self.stimulus.squarelock: self.p.widthDeg = self.p.bheightDeg
        elif self.stimulus.DOWN:
            self.p.bheightDeg = max(self.p.bheightDeg / multiplier, 0.1)
            if self.stimulus.squarelock: self.p.widthDeg = self.p.bheightDeg
        if self.stimulus.RIGHT:
            self.p.widthDeg = self.p.widthDeg * multiplier
            if self.stimulus.squarelock: self.p.bheightDeg = self.p.widthDeg
        elif self.stimulus.LEFT:
            self.p.widthDeg = max(self.p.widthDeg / multiplier, 0.1)
            if self.stimulus.squarelock: self.p.bheightDeg = self.p.widthDeg

class BrightnessController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(BrightnessController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.PLUS:
            self.p.brightness += self.p.brightnessstep
        elif self.stimulus.MINUS:
            self.p.brightness -= self.p.brightnessstep
        self.p.brightness = max(self.p.brightness, 0) # keep it >= 0
        self.p.brightness = min(self.p.brightness, 1) # keep it <= 1

class OrientationController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(OrientationController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        mod = self.p.ori % self.p.snapDeg
        self.p.ori += self.stimulus.SCROLL_UP * (self.p.snapDeg - mod)
        if mod == 0:
            mod = self.p.snapDeg
        self.p.ori -= self.stimulus.SCROLL_DOWN * mod  
        self.p.ori += self.stimulus.orthogonalize_ori * 90.0
        self.stimulus.orthogonalize_ori = False
        self.stimulus.SCROLL_UP = False
        self.stimulus.SCROLL_DOWN = False
        self.p.ori = self.p.ori % 360 # keep it in [0, 360)

class PerpendicOrientation(OrientationController):
    def __init__(self,*args,**kwargs):
        super(PerpendicOrientation, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        if self.stimulus.perpend_to_dir:
            if not hasattr(self,'last_pos'):
                self.last_pos = (0,0)
            self.current_pos = (self.stimulus.x, self.stimulus.y)
            if self.last_pos != self.current_pos:
                self.p.ori = 90.0 + math.atan2(self.current_pos[1]-self.last_pos[1], \
                                                      self.current_pos[0]-self.last_pos[0])*180.0/math.pi
            self.last_pos = self.current_pos
        super(PerpendicOrientation, self).during_go_eval()
        
class FlashController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(FlashController, self).__init__(*args,**kwargs)
        self.flash_duration_nvsync = self.viewport.sec2intvsync(self.p.flashduration)
        self.flash_interval_nvsync = self.viewport.sec2intvsync(self.p.flashinterval)
        self.flash_cycle_nvsync = self.flash_duration_nvsync + self.flash_interval_nvsync
        self.vsync_count = 1
        
    def during_go_eval(self):
        if self.p.flash:
            self.p.on = True if self.vsync_count <= self.flash_duration_nvsync else False
            self.vsync_count = (self.vsync_count + 1) % self.flash_cycle_nvsync if self.flash_cycle_nvsync != 0 else 1

class ManBar(ManStimulus):
    def __init__(self, params, disp_info=False, **kwargs):
        super(ManBar, self).__init__(params=params, disp_info=disp_info, **kwargs)
        """ Class specific data """
        self.name = 'manbar'
        self.logger = logging.getLogger('LightStim.ManBar')
        self.param_names = ['xorigDeg','yorigDeg','widthDeg','bheightDeg','ori']
        self.defalut_parameters = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':5.0,
                                   'bheightDeg':2.0,
                                   'ori': 0.0}
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        
        """ set special parameters """
        self.perpend_to_dir = False
        self.restored_on = self.parameters.on
        
        self.make_stimuli()
        self.stimuli = self.complete_stimuli if disp_info else self.essential_stimuli
        """ register controllers """
        self.register_controllers()
        
        self.restore_pos()
    
    def get_all_parameters(self):
        return self.get_parameters(self.parameters, self.param_names)
    
    def set_all_parameters(self, params):
        self.set_parameters(self.parameters, params)
    
    def make_stimuli(self):
        super(ManBar, self).make_stimuli()
        color = (self.parameters.brightness, self.parameters.brightness, self.parameters.brightness, 1.0)
        self.target = Target2D(anchor='center',
                               anti_aliasing=self.parameters.antialiase,
                               color=color,
                               on=False)
        self.tp = self.target.parameters # synonym
        self.tp.color = color
        self.tip = Target2D(size=(5, 1),
                            anchor='center',
                            anti_aliasing=self.parameters.antialiase,
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
    
    def register_stimulus_controller(self):
        self.controllers.append(SizeController(self))
        self.controllers.append(PerpendicOrientation(self))
        self.controllers.append(BrightnessController(self))
        self.controllers.append(FlashController(self))
        self.controllers.append(ManBarController(self))

    def register_info_controller(self):
        super(ManBar,self).register_info_controller()
        self.controllers.append(BarInfoController(self))
    
    def restore_pos(self):
        # changes only after load/save a new preference
        self.x  = int(round(self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig))
        self.y  = int(round(self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig))
        self.fp.position = self.x, self.y
        self.viewport.save_mouse_pos((self.x, self.viewport.height_pix - self.y))
    
    def load_params(self, index=0):
        super(ManBar,self).load_params(index)
        
    def save_params(self, index):
        super(ManBar,self).save_params(index)
        self.fp.position = self.x, self.y
        self.brightenText = "Index" + str(index)  # brighten the text for feedback
        
    def keydown_callback(self,event):
        super(ManBar,self).keydown_callback(event)
        key = event.key
        if key == K_f:
            if not self.parameters.flash:
                self.restored_on = self.parameters.on
            elif self.parameters.flash:
                self.parameters.on = self.restored_on
            self.parameters.flash = not self.parameters.flash
        if key == K_i: # invert background and bar brightness
            self.parameters.brightness, self.parameters.bgbrightness = self.parameters.bgbrightness, \
                self.parameters.brightness
        if key == K_o: # orientation is perpendicular to bar moving direction
            self.perpend_to_dir = not self.perpend_to_dir
        