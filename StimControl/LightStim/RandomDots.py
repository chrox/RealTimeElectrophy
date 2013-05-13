# Random Dot Sterogram.
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from __future__ import division
import math
from VisionEgg.Core import FixationSpot
from VisionEgg.MoreStimuli import Target2D

from Core import Stimulus
from Dots import TextureDots
from SweepController import StimulusController

class RandomDotsController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(RandomDotsController, self).__init__(*args,**kwargs)
        self.rp = self.stimulus.rp
        self.fp = self.stimulus.fp

    def during_go_eval(self):
        self.fp.position = self.viewport.deg2pix(self.p.xorigDeg) + self.viewport.xorig, \
                           self.viewport.deg2pix(self.p.yorigDeg) + self.viewport.yorig
        self.rp.position = self.fp.position

class RandomDots(Stimulus):
    def __init__(self, params, disp_info=False, **kwargs):
        super(RandomDots, self).__init__(params=params, **kwargs)
        self.name = 'randomdots'
        self.param_names += ['xorigDeg','yorigDeg',
                             'dotSquareWidth','randomSeed','dotsNumber',]
        self.defalut_parameters.update({'xorigDeg':0.0,
                                        'yorigDeg':0.0,})
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        """ make stimuli """
        self.make_stimuli()
        """ register controllers """
        self.register_controllers()

    def make_stimuli(self):
        size = self.viewport.get_size()
        #set background color before real sweep
        bgb = self.parameters.bgbrightness
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   color=(bgb, bgb, bgb, 1.0),
                                   on=True)
        width = self.viewport.deg2pix(self.parameters.dotSquareWidth)
        self.randomdots = TextureDots(on=True,
                                     size=(int(width), int(width)),
                                     bgcolor=(0.5,0.5,0.5),
                                     num_dots=self.parameters.dotsNumber,
                                     seed=self.parameters.randomSeed,
                                     dot_size=3,
                                     mask_on=False)
        self.rp = self.randomdots.parameters
        self.fixationspot = FixationSpot(anchor='center',
                                         color=(1.0, 0.0, 0.0, 0.0),
                                         size=(10, 10),
                                         on=False)
        self.fp = self.fixationspot.parameters
        self.stimuli = (self.background, self.randomdots, self.fixationspot)
        
    def register_controllers(self):
        self.controllers.append(RandomDotsController(self))

class DiscPositionController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(DiscPositionController, self).__init__(*args,**kwargs)
        self.dp = self.stimulus.dp

    def during_go_eval(self):
        posRad = (self.p.discPosDeg % 360)/180 * math.pi
        radius = self.p.discDistDeg / 2
        
        self.dp.mask_position = math.cos(posRad) * self.viewport.deg2pix(radius), \
                                math.sin(posRad) * self.viewport.deg2pix(radius)

class DiscDisparityController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(DiscDisparityController, self).__init__(*args,**kwargs)
        self.dp = self.stimulus.dp
        self.fp = self.stimulus.fp
        
    def during_go_eval(self):
        disparity = self.p.disparity
        self.dp.position = self.fp.position[0] + self.viewport.deg2pix(disparity), \
                           self.fp.position[1]

class StereoDisc(Stimulus):
    def __init__(self, params, disp_info=False, **kwargs):
        super(StereoDisc, self).__init__(params=params, **kwargs)
        self.name = 'stereodisc'
        self.param_names += ['xorigDeg','yorigDeg',
                             'dotSquareWidth','randomSeed','dotsNumber',
                             'discDistDeg', 'discPosDeg','discDiameter','disparity']
        self.defalut_parameters.update({'xorigDeg':0.0,
                                        'yorigDeg':0.0,
                                        'discPosDeg':0.0,})
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        """ make stimuli """
        self.make_stimuli()
        """ register controllers """
        self.register_controllers()

    def make_stimuli(self):
        size = self.viewport.get_size()
        #set background color before real sweep
        bgb = self.parameters.bgbrightness
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   color=(bgb, bgb, bgb, 1.0),
                                   on=True)
        
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
        self.stimuli = (self.background, self.randomdots, self.disc, self.fixationspot)
        
    def register_controllers(self):
        self.controllers.append(RandomDotsController(self))
        self.controllers.append(DiscPositionController(self))
        self.controllers.append(DiscDisparityController(self))
        