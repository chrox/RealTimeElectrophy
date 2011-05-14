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

import pygame
from pygame.locals import *
import VisionEgg.GL as gl
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot
from VisionEgg.Text import Text

import LightStim.Core
from SweepController import StimulusController

STATUSBARHEIGHT = 12 # height of upper and lower status bars (pix)

class ManBarController(StimulusController):
    """ update bar parameters """
    def __init__(self,*args,**kwargs):
        super(ManBarController, self).__init__(*args,**kwargs)
        self.tp = self.stimulus.tp
        self.bgp = self.stimulus.bgp
        self.tipp = self.stimulus.tipp
        self.cp = self.stimulus.cp
        self.mbtp = self.stimulus.mbtp
        self.stp = self.stimulus.stp
        self.sltp = self.stimulus.sltp 
    def during_go_eval(self):
        width = self.viewport.deg2pix(self.stimulus.widthDeg) # convenience
        height = self.viewport.deg2pix(self.stimulus.heightDeg)
        self.stimulus.tp.position = self.stimulus.x, self.stimulus.y
        self.stimulus.tp.size = width, height # convert to pix
        self.stimulus.tp.orientation = self.stimulus.ori
        self.stimulus.tp.color = (self.stimulus.brightness, self.stimulus.brightness, self.stimulus.brightness, 1.0)
        self.stimulus.bgp.color = (self.stimulus.bgbrightness, self.stimulus.bgbrightness, self.stimulus.bgbrightness, 1.0)
        self.stimulus.tipp.position = ( self.stimulus.x + width / 2 * math.cos(math.pi / 180 * self.stimulus.ori),
                               self.stimulus.y + width / 2 * math.sin(math.pi / 180 * self.stimulus.ori) )
        self.stimulus.tipp.orientation = self.stimulus.ori
        self.stimulus.cp.position = self.stimulus.x, self.stimulus.y # update center spot position
        # Update text params
        self.stimulus.mbtp.text = 'x, y = (%5.1f, %5.1f) deg  |  size = (%.1f, %.1f) deg  |  ori = %5.1f deg' \
                         % ( self.viewport.pix2deg(self.stimulus.x - self.viewport.width_pix / 2), \
                             self.viewport.pix2deg(self.stimulus.y - self.viewport.height_pix / 2),
                             self.stimulus.widthDeg, self.stimulus.heightDeg, self.stimulus.ori)

        self.stimulus.stp.text = self.stimulus.screenstring

        if self.stimulus.brightenText == 'Manbar0':
            self.mbtp.color = (1.0, 1.0, 0.0, 1.0) # set to yellow
        elif self.stimulus.brightenText == 'Manbar1':
            self.mbtp.color = (1.0, 0.0, 0.0, 1.0) # set to red
        elif self.stimulus.brightenText == 'Eye':
            self.stimulus.stp.color = (1.0, 0.0, 0.0, 1.0) # set to red
        else:
            self.stimulus.mbtp.color = (0.0, 1.0, 0.0, 1.0) # set it back to green
            self.stimulus.stp.color = (0.0, 1.0, 1.0, 1.0) # set it back to cyan

        if self.stimulus.squarelock:
            self.stimulus.sltp.on = True
        else:
            self.stimulus.sltp.on = False
            
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
            
class OrientationController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(OrientationController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        pass

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
        
class ManBar(LightStim.Core.Stimulus):
    """ Control Bar stimulus manually.  
    """
    def __init__(self, params, disp_info=True, **kwargs):
        super(ManBar, self).__init__(**kwargs)
        for paramname, paramval in params.items():
            setattr(self, paramname, paramval) # bind all parameter names to self
        self.savedpost = []
        
        self.x = self.xorigDeg
        self.y = self.yorigDeg
        
        self.squarelock, self.brightenText = False, False
        self.UP, self.DOWN, self.LEFT, self.RIGHT = False, False, False, False
        self.PLUS, self.MINUS = False, False
        self.LEFTBUTTON, self.RIGHTBUTTON, self.SCROLL = False, False, False

        self.make_stimuli(disp_info)
        self.register_controllers()
        self.register_event_handlers()
        
    def make_stimuli(self, disp_info):
        size = self.viewport.get_size()
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   on=True)

        self.bgp = self.background.parameters # synonym
        #set background color before real sweep
        bgb = self.bgbrightness # get it for sweep table index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        
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
        ##TODO: switch to pyglet.font
        fontname = pygame.font.match_font('lucidaconsole', bold=False, italic=False)
        self.screenstring = 'screen (w, h, d) = (%.1f, %.1f, %.1f) cm' % \
                            (self.viewport.width_cm, self.viewport.height_cm, self.viewport.distance_cm)
        self.screentext = Text(position=(self.viewport.width_pix-1, self.viewport.height_pix-1),
                               anchor='upperright',
                               text=self.screenstring,
                               color=(0.0, 1.0, 1.0, 1.0),
                               texture_mag_filter=gl.GL_NEAREST,
                               font_name=fontname,
                               font_size=10)
        self.stp = self.screentext.parameters
        self.manbartext = Text(position=(0, 0),
                               anchor='lowerleft',
                               color=(0.0, 1.0, 0.0, 1.0),
                               texture_mag_filter=gl.GL_NEAREST,
                               font_name=fontname,
                               font_size=10)
        self.mbtp = self.manbartext.parameters
        self.squarelocktext = Text(position=(0, self.viewport.height_pix),
                                   anchor='upperleft',
                                   text='SQUARELOCK',
                                   color=(0.0, 1.0, 1.0, 1.0),
                                   texture_mag_filter=gl.GL_NEAREST,
                                   font_name=fontname,
                                   font_size=10,
                                   on=False) # leave it off for now
        self.sltp = self.squarelocktext.parameters
        self.upperbar = Target2D(position=(0, self.viewport.height_pix),
                                 anchor='upperleft',
                                 size=(self.viewport.width_pix, STATUSBARHEIGHT),
                                 anti_aliasing=self.antialiase,
                                 color=(0.0, 0.0, 0.0, 1.0))
        self.lowerbar = Target2D(position=(0, 0),
                                 anchor='lowerleft',
                                 size=(self.viewport.width_pix, STATUSBARHEIGHT),
                                 anti_aliasing=self.antialiase,
                                 color=(0.0, 0.0, 0.0, 1.0))
        # last entry will be topmost layer in viewport
        self.basic_stimuli = (self.background, self.target)
        self.all_stimuli = (self.background, self.target, self.tip,
                            self.fixationspot, self.centerspot,
                            self.upperbar, self.squarelocktext, self.screentext,
                            self.lowerbar, self.manbartext)
        
        if disp_info:
            self.stimuli = self.all_stimuli
        else:
            self.stimuli = self.basic_stimuli
            
    def register_controllers(self):
        self.controllers.append(SizeController(self))
        self.controllers.append(OrientationController(self))
        self.controllers.append(BrightnessController(self))
        self.controllers.append(ManBarController(self))
        
    def register_event_handlers(self):
        self.event_handlers = [(pygame.locals.KEYDOWN, self.keydown_callback),
                               (pygame.locals.KEYUP, self.keyup_callback)]
        
    def keydown_callback(self,event):
        mods = pygame.key.get_mods()
        key = event.key
        if key == K_UP:
            self.UP = True
        elif key == K_DOWN:
            self.DOWN = True
        elif key == K_RIGHT:
            self.RIGHT = True
        elif key == K_LEFT:
            self.LEFT = True
        elif key == K_EQUALS:
            self.PLUS = True
        elif key == K_MINUS:
            self.MINUS = True
        elif key in [K_RSHIFT,K_LSHIFT]:
            self.squarelock = True
        elif key == K_i:
            self.brightness, self.bgbrightness = self.bgbrightness, self.brightness
        elif key in [K_0, K_KP0]: # set pos and ori to 0
            self.x = self.viewport.width_pix / 2
            self.y = self.viewport.height_pix / 2
            self.ori = 0
        elif key in [K_SPACE, K_RETURN, K_KP_ENTER] or mods & KMOD_CTRL and key in [K_1, K_KP1]:
            self.saveManbar(0) # save Manbar state 0
        elif mods & KMOD_CTRL and key in [K_2, K_KP2]:
            self.saveManbar(1) # save Manbar state 1
        elif not mods & KMOD_CTRL and key in [K_1, K_KP1]:
            self.loadManbar(0) # load Manbar state 0
        elif not mods & KMOD_CTRL and key in [K_2, K_KP2]:
            self.loadManbar(1) # load Manbar state 1
            
    def keyup_callback(self,event):
        mods = pygame.key.get_mods()
        key = event.key
        if key == K_UP:
            self.UP = False
        elif key == K_DOWN:
            self.DOWN = False
        elif key == K_RIGHT:
            self.RIGHT = False
        elif key == K_LEFT:
            self.LEFT = False
        elif key == K_EQUALS:
            self.PLUS = False
        elif key == K_MINUS:
            self.MINUS = False
        elif key in [K_RSHIFT,K_LSHIFT]:
            self.squarelock = False
        elif key in [K_SPACE, K_RETURN, K_KP_ENTER, K_e] or \
            mods & KMOD_CTRL and key in [K_1, K_KP1, K_2, K_KP2]:
            self.brightenText = False