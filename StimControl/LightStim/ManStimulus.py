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
import copy
import itertools

import pygame
from pygame.locals import K_UP,K_DOWN,K_RIGHT,K_LEFT,K_EQUALS,K_MINUS,K_RSHIFT,K_LSHIFT,K_SPACE,K_RETURN,K_KP_ENTER,KMOD_CTRL
from pygame.locals import K_h,K_e,K_0,K_KP0,K_1,K_KP1,K_2,K_KP2
import VisionEgg.GL as gl
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Text import Text
from SweepController import StimulusController

import LightStim.Core
from LightStim.Core import Viewport

STATUSBARHEIGHT = 15 # height of upper and lower status bars (pix)

class ViewportInfoController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(ViewportInfoController, self).__init__(*args,**kwargs)
        self.vips = self.stimulus.viewport_indicators
        self.sltp = self.stimulus.sltp
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):
        # display active viewports list and indicate the current viewport
        active_viewports_names = [viewport.name for viewport in Viewport.registered_viewports if viewport.is_active()]
        current_viewport_name = [viewport.name for viewport in Viewport.registered_viewports if viewport.is_current()]
        for indicator in self.vips:
            if indicator.text in active_viewports_names:
                indicator.on = True # display active viewport indicator
                if indicator.text in current_viewport_name:
                    indicator.color = (0.0, 1.0, 0.0, 1.0) # set current viewport indicator color to green
                else:
                    indicator.color = (0.0, 1.0, 1.0, 1.0) # set other indicator color to cyan
            else:
                indicator.on = False

        if self.stimulus.brightenText == 'Manbar0':
            self.sptp.color = (1.0, 1.0, 0.0, 1.0) # set to yellow
        elif self.stimulus.brightenText == 'Manbar1':
            self.sptp.color = (1.0, 0.0, 0.0, 1.0) # set to red
        else:
            self.stimulus.sptp.color = (0.0, 1.0, 0.0, 1.0) # set it back to green

        if self.stimulus.squarelock:
            self.stimulus.sltp.on = True
        else:
            self.stimulus.sltp.on = False

class ManViewport(LightStim.Core.Viewport):
    # add event control callback
    def __init__(self,**kwargs):
        super(ManViewport, self).__init__(**kwargs)
        self.active = True
        if self.name == 'control':
            self.visible = True
            self.current = True
        else:
            self.visible = False
            self.current = False
        self.event_handlers = [(pygame.locals.KEYDOWN, self.keydown_callback)]
    def draw(self):
        if not self.is_active() or not self.is_visible():
            return
        self.make_current()
        self._is_drawing = True
        for stimulus in self.parameters.stimuli:
            stimulus.draw()
        self._is_drawing = False
    def is_active(self):
        return self.active
    def set_activity(self,activity):
        self.active = activity
    def is_visible(self):
        return self.visible
    def set_visibility(self,visibility):
        self.visible = visibility
    def is_current(self):
        return self.current
    def set_current(self,current):
        self.current = current
    def keydown_callback(self,event):
        mods = pygame.key.get_mods()
        key = event.key
        # set viewport activity and currenty this should have no business with control viewport 
        def set_viewport(name):
#            if self.is_current(): #  must clear other activity state.
#                return
            if mods & pygame.locals.KMOD_CTRL:
                if self.name == name:
                    self.set_activity(True)
                    self.set_current(True)
                elif self.name == 'control':
                    colone_stimuli('control', name)
                else:
                    self.set_activity(False)
                    self.set_current(False)
            else:
                if self.name == name:
                    self.set_activity(not self.is_active())
       
        def colone_stimuli(dest_viewport_name, src_viewport_name):
            dest_viewports = [viewport for viewport in Viewport.registered_viewports if viewport.name == dest_viewport_name]
            src_viewports = [viewport for viewport in Viewport.registered_viewports if viewport.name == src_viewport_name]
            if dest_viewports == []:
                raise RuntimeError("Cannot find destined viewport " + dest_viewport_name + ' in registered viewports.')
            if src_viewports == []:
                raise RuntimeError("Cannot find source viewport " + dest_viewport_name + ' in registered viewports.')
            dest_viewport = dest_viewports[0]
            src_viewport = src_viewports[0]
            dest_viewport.parameters.stimuli = []
            # clone the complete stimulus to control viewport
            for stimulus in src_viewport.parameters.stimuli:
                cloned_stimulus = copy.copy(stimulus)
                cloned_stimulus.stimuli = stimulus.complete_stimuli
                cloned_viewport = copy.copy(stimulus.viewport)
                cloned_viewport.name = 'control'
                cloned_stimulus.viewport = cloned_viewport # set to control viewport in case the event callbacks are picked off
                cloned_stimulus.on = True # in control viewport it's not necessary to hide a stimulus
                dest_viewport.parameters.stimuli.append(cloned_stimulus)
                
        if key == K_h:
            if not self.name == 'control':
                self.set_visibility(not self.is_visible())
        elif key == pygame.locals.K_F1:
            pass  # control viewport should never be deactivated
        elif key == pygame.locals.K_F2:
            set_viewport('primary')
        elif key == pygame.locals.K_F3:
            set_viewport('left')
        elif key == pygame.locals.K_F4:
            set_viewport('right')
        elif key == pygame.locals.K_TAB:
            if self.name == 'control':
                active_viewports = [viewport for viewport in Viewport.registered_viewports if viewport.is_active()]
                # assert there is at least one current viewport
                assert len(active_viewports) > 0
                viewport_it = itertools.cycle(active_viewports)
                for viewport in viewport_it:
                    if viewport.is_current():
                        viewport.set_current(False)
                        next_viewport = viewport_it.next()
                        if next_viewport.name == 'control':
                            next_viewport = viewport_it.next()
                        next_viewport.set_current(True)
                        colone_stimuli('control',next_viewport.name)
                        break

class ManStimulus(LightStim.Core.Stimulus):
    def __init__(self, disp_info, params, viewport, **kwargs):
        super(ManStimulus, self).__init__(**kwargs)
        self.viewport = ManViewport(name=viewport) # use viewport 
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
        self.info = (self.upperbar, self.squarelocktext, self.viewportinfotext, self.screentext,
                     self.pvpindicatortext, self.lvpindicatortext, self.rvpindicatortext,
                     self.lowerbar, self.stimulusparamtext)
        self.make_stimuli()
        if disp_info:
            self.stimuli = self.complete_stimuli
        else:
            self.stimuli = self.essential_stimuli
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
        self.screentext.parameters.text = self.screenstring
        self.squarelocktext = Text(position=(1, self.viewport.height_pix - STATUSBARHEIGHT + 1),
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
        self.stimulusparamtext = Text(position=(1, 1),
                                    anchor='lowerleft',
                                    color=(0.0, 1.0, 0.0, 1.0),
                                    texture_mag_filter=gl.GL_NEAREST,
                                    font_name=fontname,
                                    font_size=10)
        self.sptp = self.stimulusparamtext.parameters
        self.viewportinfotext = Text(position=(1, self.viewport.height_pix - 1),
                                     anchor='upperleft',
                                     text='Viewports in control: ',
                                     color=(0.0, 1.0, 1.0, 1.0),
                                     texture_mag_filter=gl.GL_NEAREST,
                                     font_name=fontname,
                                     font_size=10)
        self.vitp = self.viewportinfotext.parameters
        self.pvpindicatortext = Text(position=(150, self.viewport.height_pix - 1),
                                     anchor='upperleft',
                                     text='primary',
                                     color=(0.0, 1.0, 1.0, 1.0),
                                     texture_mag_filter=gl.GL_NEAREST,
                                     font_name=fontname,
                                     font_size=10)
        self.lvpindicatortext = Text(position=(200, self.viewport.height_pix - 1),
                                     anchor='upperleft',
                                     text='left',
                                     color=(0.0, 1.0, 1.0, 1.0),
                                     texture_mag_filter=gl.GL_NEAREST,
                                     font_name=fontname,
                                     font_size=10)
        self.rvpindicatortext = Text(position=(230, self.viewport.height_pix - 1),
                                     anchor='upperleft',
                                     text='right',
                                     color=(0.0, 1.0, 1.0, 1.0),
                                     texture_mag_filter=gl.GL_NEAREST,
                                     font_name=fontname,
                                     font_size=10)
        self.viewport_indicators = (self.pvpindicatortext.parameters,self.lvpindicatortext.parameters,self.rvpindicatortext.parameters)

    def make_stimuli(self):
        raise RuntimeError("%s: Definition of make_stimuli() in abstract base class ManStimulus must be overriden."%(str(self),))
        
    def register_controllers(self):
        self.register_stimulus_controller()
        self.register_info_controller()
        
    def register_info_controller(self):
        self.controllers.append(ViewportInfoController(self))
            
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
        # x = min(x, self.viewport.width_pix)
        if x > self.viewport.width_pix:
            x = self.viewport.width_pix
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
