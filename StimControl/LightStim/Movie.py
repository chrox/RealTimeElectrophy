# -*- coding: utf-8 -*-
# Base class for grating stimulus.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise')
import logging

import VisionEgg.GL as gl
from VisionEgg.Textures import Texture, TextureStimulus
from VisionEgg.MoreStimuli import Target2D

import Image
import ImageEnhance

from Core import Stimulus
from SweepController import StimulusController,SweepSequeStimulusController

class MovieController(StimulusController):
    """ update movie from pygame surface """
    def __init__(self,*args,**kwargs):
        super(MovieController, self).__init__(*args,**kwargs)
        
        self.surface = self.stimulus.surface
        self.texture = self.stimulus.texture
        self.texture_obj = self.texture.get_texture_object()
        
        width, height = self.surface.get_size()
        viewport = self.viewport.get_name()
        if self.p.layout == "2D":
            self.crop_box = (0, 0, width, height)
            self.offset = (0, 0)
        elif self.p.layout == "LR":
            if viewport == "left":
                self.crop_box = (0, 0, width//2, height)
            elif viewport == "right":
                self.crop_box = (width//2, 0, width, height)
            self.offset = (width//4, 0)
        elif self.p.layout == "TB":
            if viewport == "left":
                self.crop_box = (0, 0, width, height//2)
            elif viewport == "right":
                self.crop_box = (0, height//2, width, height)
            self.offset = (0, height//4)
        else:
            self.logger.error("Cannot support layout: %s" %self.p.layout)
        print self.crop_box, self.offset
    def during_go_eval(self):
        image = self.texture.get_texels_as_image()
        image = ImageEnhance.Contrast(image).enhance(self.p.contrast)
        self.texture_obj.put_sub_image(image.crop(self.crop_box).transpose(Image.FLIP_TOP_BOTTOM), \
                                       offset_tuple=self.offset)

class Movie(Stimulus):
    def __init__(self, params, surface, subject=None, sweepseq=None, trigger=True, **kwargs):
        super(Movie, self).__init__(subject=subject, params=params, **kwargs)
        self.name = 'timingmovie'
        self.logger = logging.getLogger('LightStim.Movie')
        self.param_names = ['on','xorigDeg','yorigDeg','widthDeg','heightDeg']
        self.defalut_parameters = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'bgbrightness':0.0,}
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        self.parameters.on = False
    
        self.sweepseq = sweepseq
        self.trigger = trigger
        
        self.surface = surface
        
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
        
        self.texture = Texture(self.surface)
        self.texture_stim = TextureStimulus(texture=self.texture,
                                       position=(size[0]/2, size[1]/2),
                                       anchor='center',
                                       mipmaps_enabled=0,
                                       texture_min_filter=gl.GL_LINEAR)
        self.tp = self.texture_stim.parameters
        
        self.stimuli = (self.background, self.texture_stim)
    
    def register_controllers(self):
        self.logger = logging.getLogger('LightStim.Movie')
        self.controllers.append(MovieController(self))
        
class TimingController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(TimingController, self).__init__(*args,**kwargs)
        self.tp = self.stimulus.tp
    def during_go_eval(self):
        stimulus_on = self.next_param()
        if stimulus_on:
            self.tp.on = True
        else:
            self.tp.on = False
            
class TimingSetMovie(Movie):
    def register_controllers(self):
        super(TimingSetMovie, self).register_controllers()
        self.logger.info('Register TimingController.')
        self.controllers.append(TimingController(self))
        