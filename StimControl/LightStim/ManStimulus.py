# Base class for manually controlled stimulus
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise')
import logging
import VisionEgg
import pygame
from pygame.locals import K_UP,K_DOWN,K_RIGHT,K_LEFT,K_EQUALS,K_MINUS,K_RSHIFT,K_LSHIFT,K_SPACE,K_RETURN,K_KP_ENTER,KMOD_CTRL
from pygame.locals import K_e,K_0,K_KP0,K_1,K_KP1,K_2,K_KP2, K_t, K_u
from VisionEgg.MoreStimuli import Target2D
from InfoText import BitmapText
from SweepController import StimulusController
from SweepController import ViewportController

from Core import Viewport, Stimulus
from ManViewport import ManViewport,ControlViewport

STATUSBARHEIGHT = 15 # height of upper and lower status bars (pix)

class InfoController(ViewportController):
    def __init__(self,*args,**kwargs):
        super(InfoController, self).__init__(eval_frequency=VisionEgg.FlowControl.Controller.ONCE,
                                             *args,**kwargs)
        self.upbp = self.stimulus.upbp # upperbar
        self.lwbp = self.stimulus.lwbp # lowerbar
        self.vitp = self.stimulus.vitp # viewportinfotext
        self.vips = self.stimulus.viewport_indicators
        self.stp = self.stimulus.stp   # screentext
        self.sltp = self.stimulus.sltp # squarelocktext
        self.sptp = self.stimulus.sptp # stimulusparamtext
    def during_go_eval(self):
        _width_pix, height_pix = self.viewport.parameters.size
        self.upbp.on = True
        self.upbp.position = (0, height_pix)
        self.upbp.size = (self.viewport.width_pix, STATUSBARHEIGHT)
        self.lwbp.on = True
        self.lwbp.position = (0, 0)
        self.lwbp.size = (self.viewport.width_pix, STATUSBARHEIGHT)
        self.vitp.on = True
        self.vitp.lowerleft = (1, height_pix - 12)
        self.vips[0].lowerleft = (200, height_pix - 12)
        self.vips[1].lowerleft = (245, height_pix - 12)
        #self.stp.on = True
        self.stp.lowerleft = (self.viewport.width_pix-325, height_pix-12)
        self.sltp.lowerleft = (1, height_pix - STATUSBARHEIGHT -12)
        self.sptp.on = True
        self.sptp.lowerleft = (2, 2)

class ViewportIndicatorsController(StimulusController):
    def __init__(self,*args,**kwargs):
        super(ViewportIndicatorsController, self).__init__(*args,**kwargs)
        self.vips = self.stimulus.viewport_indicators
        self.sltp = self.stimulus.sltp
        self.sptp = self.stimulus.sptp
    def during_go_eval(self):
        # display active viewports list and indicate the current viewport
        active_viewports_names = [viewport.get_name() for viewport in Viewport.registered_viewports if viewport.is_active()]
        current_viewport_name = [viewport.get_name() for viewport in Viewport.registered_viewports if viewport.is_current()]
        visible_viewport_name = [viewport.get_name() for viewport in Viewport.registered_viewports if viewport.is_visible()]
        for indicator in self.vips:
            if indicator.text in active_viewports_names:
                indicator.on = True # display active viewport indicator
                if indicator.text in current_viewport_name:
                    indicator.color = (0.0, 1.0, 0.0, 0.0) # set current viewport indicator color to green
                    if indicator.text in visible_viewport_name:
                        indicator.color = (1.0, 1.0, 0.0, 0.0)
                else:
                    indicator.color = (0.0, 1.0, 1.0, 0.0) # set other indicator color to cyan
                    if indicator.text in visible_viewport_name:
                        indicator.color = (1.0, 1.0, 1.0, 0.0)
            else:
                indicator.on = False

        if self.stimulus.brightenText == 'Index0':
            self.sptp.color = (1.0, 1.0, 0.0, 1.0) # set to yellow
        elif self.stimulus.brightenText == 'Index1':
            self.sptp.color = (1.0, 0.0, 0.0, 1.0) # set to red
        else:
            self.stimulus.sptp.color = (0.0, 1.0, 0.0, 1.0) # set it back to green

        if self.stimulus.squarelock:
            self.stimulus.sltp.on = True
        else:
            self.stimulus.sltp.on = False

class ViewportEventHandlerController(StimulusController):
    """ Event handlers should all registered in viewports which means that user interacts with the viewport not the actural stimulus.
        And it's the viewport 's duty to depute some interaction to the stimuli in it. In reality this is implemented by registering 
        the event handlers in stimulus.
        If the viewport is current viewport then add the event handlers of this stimulus to that viewport, otherwise delete the handlers.
    """
    def __init__(self,*args,**kwargs):
        super(ViewportEventHandlerController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        stimulus = self.stimulus
        viewport = self.viewport
        if hasattr(stimulus,'event_handlers'): # update the viewport event handler only when the viewport is the current viewport.
            for event_handler in stimulus.event_handlers:
                if event_handler not in viewport.event_handlers and viewport.is_current():
                    viewport.event_handlers.append(event_handler) 
                elif event_handler in viewport.event_handlers and not viewport.is_current():
                    viewport.event_handlers.remove(event_handler) 

class ManStimulus(Stimulus):
    __slots__ = ('complete_stimuli','essential_stimuli')
    def __init__(self, viewport, subject=None, disp_info=False, **kwargs):
        super(ManStimulus, self).__init__(viewport=viewport, subject=subject, **kwargs)
        logger = logging.getLogger('LightStim.ManStimulus')
        if disp_info and viewport is not 'control':
            logger.warning('Viewport ' + viewport +' may display incomplete stimulus information.')
        
        """ override viewport defined in base stimulus """
        if viewport == 'control':
            self.viewport = ControlViewport(name=viewport, bgcolor=self.bgcolor) # use viewport
        else:
            self.viewport = ManViewport(name=viewport, bgcolor=self.bgcolor) # use viewport

        self.parameters.on = True
        
        self.squarelock, self.brightenText = False, False
        self.UP, self.DOWN, self.LEFT, self.RIGHT = False, False, False, False
        self.PLUS, self.MINUS = False, False
        self.LEFTBUTTON, self.RIGHTBUTTON, self.SCROLL_UP, self.SCROLL_DOWN = False, False, False, False
        self.orthogonalize_ori = False
        self.reverse_direction = False

        self.register_event_handlers()
        
    def make_stimuli(self):
        self.p = self.parameters
        size = self.viewport.get_size()
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   on=True)

        self.bgp = self.background.parameters # synonym
        #set background color before real sweep
        bgb = self.p.bgbrightness # get it for sweep table index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        
        self.screenstring = 'screen (w, h, d) = (%.1f, %.1f, %.1f) cm' % \
                            (self.viewport.width_cm, self.viewport.height_cm, self.viewport.distance_cm)
        self.screentext = BitmapText(text=self.screenstring, color=(0.0, 1.0, 1.0, 1.0), on=False)
        self.stp = self.screentext.parameters

        self.squarelocktext = BitmapText(text='SQUARELOCK', color=(0.0, 1.0, 1.0, 1.0), on=False) # leave it off for now
        self.sltp = self.squarelocktext.parameters
        self.upperbar = Target2D(anchor='upperleft', anti_aliasing=self.p.antialiase, \
                                 color=(self.p.bgbrightness, self.p.bgbrightness, self.p.bgbrightness, 1.0), \
                                 on=False)
        self.upbp = self.upperbar.parameters
        self.lowerbar = Target2D(anchor='lowerleft', anti_aliasing=self.p.antialiase, \
                                 color=(self.p.bgbrightness, self.p.bgbrightness, self.p.bgbrightness, 1.0), \
                                 on=False)
        self.lwbp = self.lowerbar.parameters
        
        self.stimulusparamtext = BitmapText(color=(0.0, 1.0, 0.0, 1.0), on=False)
        self.sptp = self.stimulusparamtext.parameters

        self.viewportinfotext = BitmapText(text='Viewports in control: ', color=(0.0, 1.0, 1.0, 1.0), on=False)
        self.vitp = self.viewportinfotext.parameters

        self.lvpindicatortext = BitmapText(text='left', on=False)

        self.rvpindicatortext = BitmapText(text='right', on=False)
        
        self.viewport_indicators = (self.lvpindicatortext.parameters,self.rvpindicatortext.parameters)

        self.info = (self.upperbar, self.squarelocktext, self.viewportinfotext, self.screentext,
                     self.lvpindicatortext, self.rvpindicatortext,
                     self.lowerbar, self.stimulusparamtext)
        
    def register_controllers(self):
        self.controllers = []
        self.register_stimulus_controller()
        self.register_viewport_controller()
        self.register_info_controller()
        
    def register_info_controller(self):
        self.controllers.append(InfoController(self))
        self.controllers.append(ViewportIndicatorsController(self))
    
    def register_viewport_controller(self):
        #self.controllers.append(ViewportEventHandlerController(self))
        pass
    
    def update_viewportcontroller(self, viewport):
        assert hasattr(self, 'controllers')
        for controller in self.controllers:
            if isinstance(controller,ViewportController):
                controller.set_viewport(viewport)
        
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
            self.x = self.viewport.xorig
            self.y = self.viewport.yorig
            self.parameters.ori = 0
        elif key in [K_SPACE, K_RETURN, K_KP_ENTER] or mods & KMOD_CTRL and key in [K_1, K_KP1]:
            self.save_params(0)  # save  Manbar state 0
        elif mods & KMOD_CTRL and key in [K_2, K_KP2]:
            self.save_params(1)  # save  Manbar state 1
        elif not mods & KMOD_CTRL and key in [K_1, K_KP1]:
            self.load_params(0) # load Manbar state 0
        elif not mods & KMOD_CTRL and key in [K_2, K_KP2]:
            self.load_params(1) # load Manbar state 1
        elif key == K_t: # add 90 degrees to orientation
            self.orthogonalize_ori = True
        elif key == K_u: # add 180 degrees to orientation
            self.reverse_direction = True
            
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
        # print "pos in callback: %d,%d" % (x, y)
        # keep the cursor in the control viewport
        # x = min(x, self.viewport.width_pix)
        if x > self.viewport.width_pix:
            x = self.viewport.width_pix
            pygame.mouse.set_pos([x,y])
        y = self.viewport.height_pix - y
        self.parameters.xorigDeg = self.viewport.pix2deg(x - self.viewport.xorig)
        self.parameters.yorigDeg = self.viewport.pix2deg(y - self.viewport.yorig)
        self.x = x
        self.y = y
        self.viewport.save_mouse_pos((self.x, self.viewport.height_pix - y))
    
    def mousebuttondown_callback(self,event):
        button = event.button
        if button == 4:
            self.SCROLL_UP = True
        elif button == 5:
            self.SCROLL_DOWN = True
            
    def mousebuttonup_callback(self,event):
        button = event.button
        if button == 1:
            self.LEFTBUTTON = False
        elif button == 3:
            self.RIGHTBUTTON = False
