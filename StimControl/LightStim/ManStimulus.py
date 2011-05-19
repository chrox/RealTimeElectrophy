# Base class for manually controlled stimulus
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise')

import pygame
from pygame.locals import *
import VisionEgg.GL as gl
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Text import Text

import LightStim.Core

STATUSBARHEIGHT = 15 # height of upper and lower status bars (pix)

class ManStimulus(LightStim.Core.Stimulus):
    def __init__(self, params, **kwargs):
        super(ManStimulus, self).__init__(**kwargs)
        for paramname, paramval in params.items():
            setattr(self, paramname, paramval) # bind all parameter names to self
        
        self.x = self.xorigDeg
        self.y = self.yorigDeg
        self.on = True
        
        self.squarelock, self.brightenText = False, False
        self.UP, self.DOWN, self.LEFT, self.RIGHT = False, False, False, False
        self.PLUS, self.MINUS = False, False
        self.LEFTBUTTON, self.RIGHTBUTTON, self.SCROLL_UP, self.SCROLL_DOWN = False, False, False, False

        self.make_screen_info()
        self.register_event_handlers()
        
    def make_screen_info(self):
        size = self.viewport.get_size()
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   on=True)

        self.bgp = self.background.parameters # synonym
        #set background color before real sweep
        bgb = self.bgbrightness # get it for sweep table index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        
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
        self.stimulusparamtext = Text(position=(0, 0),
                               anchor='lowerleft',
                               color=(0.0, 1.0, 0.0, 1.0),
                               texture_mag_filter=gl.GL_NEAREST,
                               font_name=fontname,
                               font_size=10)
        self.sptp = self.stimulusparamtext.parameters

    def make_stimuli(self):
        raise RuntimeError("%s: Definition of make_stimuli() in abstract base class ManStimulus must be overriden."%(str(self),))
        
    def register_controllers(self):
        raise RuntimeError("%s: Definition of register_controllers() in abstract base class ManStimulus must be overriden."%(str(self),))
        
    def register_event_handlers(self):
        self.event_handlers = [(pygame.locals.KEYDOWN, self.keydown_callback),
                               (pygame.locals.KEYUP, self.keyup_callback),
                               (pygame.locals.MOUSEMOTION, self.mousemotion_callback),
                               (pygame.locals.MOUSEBUTTONDOWN, self.mousebuttondown_callback),
                               (pygame.locals.MOUSEBUTTONUP, self.mousebuttonup_callback)]
        
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
        elif key == K_h:
            self.on = not self.on
        elif key in [K_0, K_KP0]: # set pos and ori to 0
            self.x = self.viewport.width_pix / 2
            self.y = self.viewport.height_pix / 2
            self.ori = 0
        elif key in [K_SPACE, K_RETURN, K_KP_ENTER] or mods & KMOD_CTRL and key in [K_1, K_KP1]:
            self.save_preference(0)  # save  Manbar state 0
        elif mods & KMOD_CTRL and key in [K_2, K_KP2]:
            self.save_preference(1)  # save  Manbar state 1
        elif not mods & KMOD_CTRL and key in [K_1, K_KP1]:
            self.load_preference(0) # load Manbar state 0
        elif not mods & KMOD_CTRL and key in [K_2, K_KP2]:
            self.load_preference(1) # load Manbar state 1
            
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
            
    def mousemotion_callback(self,event):
        (x,y) = pygame.mouse.get_pos()
        #print "pos in callback: %d,%d" % (self.x, self.viewport.height_pix - self.y)
        # keep the cursor in the control viewport
        x = min(x, self.viewport.width_pix)
        pygame.mouse.set_pos([x,y])
        y = self.viewport.height_pix - y
        self.x = x
        self.y = y
    
    def mousebuttondown_callback(self,event):
        button = event.button
        if button == 1:
            self.LEFTBUTTON = True
        elif button == 2:  # scroll wheel button
            self.save_preference(0) # save Manbar state 0
        elif button == 3:
            self.RIGHTBUTTON = True
        elif button == 4:
            self.SCROLL_UP = True
        elif button == 5:
            self.SCROLL_DOWN = True
            
    def mousebuttonup_callback(self,event):
        button = event.button
        if button == 1:
            self.LEFTBUTTON = False
        elif button == 3:
            self.RIGHTBUTTON = False
