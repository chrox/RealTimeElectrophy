# Manual SED position.
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from __future__ import division
import math
import pygame
from pygame.locals import KMOD_CTRL

from SweepController import StimulusController
from ManGrating import ManGrating, ManGratingController 

class PositionController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(PositionController, self).__init__(*args,**kwargs)
        self.cp = self.stimulus.cp
        self.fp = self.stimulus.fp
        self.gp = self.stimulus.gp
    def during_go_eval(self):
        self.p.posDeg += self.stimulus.SCROLL_UP * self.p.snapDeg
        self.p.posDeg -= self.stimulus.SCROLL_DOWN * self.p.snapDeg
        self.p.posDeg = self.p.posDeg % 360
        self.stimulus.SCROLL_UP = False
        self.stimulus.SCROLL_DOWN = False
        
        self.fp.position = self.viewport.deg2pix(self.p.xorigDeg) + self.viewport.xorig ,\
                           self.viewport.deg2pix(self.p.yorigDeg) + self.viewport.yorig
        
        posRad = (self.p.posDeg % 360)/180 * math.pi
        radius = self.p.radius
        self.cp.position = self.fp.position[0] + math.cos(posRad) * self.viewport.deg2pix(radius) ,\
                           self.fp.position[1] + math.sin(posRad) * self.viewport.deg2pix(radius)
        self.gp.position = self.cp.position

class ManSED(ManGrating):
    def __init__(self, params, subject, **kwargs):
        super(ManSED, self).__init__(params=params, subject=subject, **kwargs)
        self.name = 'mansed'
        self.param_names += ['posDeg','radius']
        self.defalut_parameters.update({'posDeg':0.0,
                                        'radius':2.0,})
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        
    def register_stimulus_controller(self):
        self.controllers.append(ManGratingController(self))
        self.controllers.append(PositionController(self))
            
    def mousemotion_callback(self,event):
        mods = pygame.key.get_mods()
        # discard mousemotion when ctrl is not pressed
        if not mods & KMOD_CTRL:
            x = self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig
            y = self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig
            y = self.viewport.height_pix - y
            pygame.mouse.set_pos((x, y))
        else:
            super(ManSED, self).mousemotion_callback(event)
        