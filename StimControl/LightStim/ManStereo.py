# Manual Stereo Disc disparity.
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from __future__ import division
import math
import pygame
from pygame.locals import KMOD_CTRL

from VisionEgg.Core import FixationSpot
from ManStimulus import ManStimulus
from SweepController import StimulusController

from Dots import TextureDots

class PositionController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(PositionController, self).__init__(*args,**kwargs)
        self.rp = self.stimulus.rp
        self.dp = self.stimulus.dp
        self.fp = self.stimulus.fp

    def during_go_eval(self):
        self.p.discPosDeg += self.stimulus.SCROLL_UP * self.p.snapDeg
        self.p.discPosDeg -= self.stimulus.SCROLL_DOWN * self.p.snapDeg
        self.p.discPosDeg = self.p.discPosDeg % 360
        self.stimulus.SCROLL_UP = False
        self.stimulus.SCROLL_DOWN = False
        
        self.fp.position = self.viewport.deg2pix(self.p.xorigDeg) + self.viewport.xorig, \
                           self.viewport.deg2pix(self.p.yorigDeg) + self.viewport.yorig
        self.rp.position = self.fp.position
        
        posRad = (self.p.discPosDeg % 360)/180 * math.pi
        radius = self.p.discDistDeg / 2
        
        self.dp.mask_position = math.cos(posRad) * self.viewport.deg2pix(radius), \
                                math.sin(posRad) * self.viewport.deg2pix(radius)

class DisparityController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(DisparityController, self).__init__(*args,**kwargs)
        self.dp = self.stimulus.dp
        self.fp = self.stimulus.fp
        
    def during_go_eval(self):
        if self.stimulus.RIGHT:
            self.p.disparity += self.p.disparityStep
        if self.stimulus.LEFT:
            self.p.disparity -= self.p.disparityStep
        disparity = self.p.disparity
        self.dp.position = self.fp.position[0] + self.viewport.deg2pix(disparity), \
                           self.fp.position[1]

class ManStereo(ManStimulus):
    def __init__(self, params, disp_info=False, **kwargs):
        super(ManStereo, self).__init__(params=params, disp_info=disp_info, **kwargs)
        self.name = 'manstereo'
        self.param_names += ['xorigDeg','yorigDeg',
                             'dotSquareWidth','randomSeed','dotsNumber','discDistDeg',
                             'discPosDeg','discDiameter','disparity']
        self.defalut_parameters.update({'xorigDeg':0.0,
                                        'yorigDeg':0.0,
                                        'discPosDeg':0.0,})
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        """ make stimuli """
        self.make_stimuli()
        self.stimuli = self.complete_stimuli if disp_info else self.essential_stimuli
        """ register controllers """
        self.register_controllers()

    def make_stimuli(self):
        super(ManStereo, self).make_stimuli()
        width = self.viewport.deg2pix(self.parameters.dotSquareWidth)
        self.randomdots = TextureDots(on=True,
                                     size=(int(width), int(width)),
                                     bgcolor=(0.5,0.5,0.5),
                                     num_dots=self.parameters.dotsNumber,
                                     seed=self.parameters.randomSeed,
                                     dot_size=3,
                                     mask_on=False)
        self.rp = self.randomdots.parameters
        self.disc = TextureDots(on=True,
                               size=(int(width), int(width)),
                               bgcolor=(0.5,0.5,0.5),
                               num_dots=self.parameters.dotsNumber,
                               seed=self.parameters.randomSeed,
                               dot_size=3,
                               mask_on=True)
        self.dp = self.disc.parameters
        self.fixationspot = FixationSpot(anchor='center',
                                         color=(1.0, 0.0, 0.0, 0.0),
                                         size=(10, 10),
                                         on=False)
        self.fp = self.fixationspot.parameters
        self.complete_stimuli = (self.background, self.randomdots, self.disc, self.fixationspot)
        self.essential_stimuli = (self.background, self.randomdots, self.disc, self.fixationspot)
        
    def register_stimulus_controller(self):
        self.controllers.append(PositionController(self))
        self.controllers.append(DisparityController(self))
    
    def mousemotion_callback(self,event):
        mods = pygame.key.get_mods()
        # discard mousemotion when ctrl is not pressed
        if not mods & KMOD_CTRL:
            x = self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig
            y = self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig
            y = self.viewport.height_pix - y
            pygame.mouse.set_pos((x, y))
        else:
            super(ManStereo, self).mousemotion_callback(event)
        