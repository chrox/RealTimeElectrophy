# This module contains the main class of LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import OpenGL.GL as gl
import pygame

import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
import VisionEgg.Core

import LightStim.Core
from SweepController import SweepTableController


class FrameSweep(VisionEgg.FlowControl.Presentation):
    """ FrameSweep is a subclass of VisionEgg Presentation.The FrameSweep is initiated with stimulus parameter and get the sweeptable
    as the attribute.
    """
    def __init__(self):
        self.screen = LightStim.Core.Screen(num_displays=4, frameless=True, hide_mouse=True, alpha_bits=8)
        
        
        #################################
        """ Create screen and viewported stimuli """
        self.create_screen_viewport_stimuli()
        #################################
        # presentation state variables
        self.quit = False
        self.pause = False # init pause signal
        self.paused = False # remembers whether this experiment has been paused
        
        # key state variables
        self.up = 0
        self.down = 0
        self.left = 0
        self.right = 0
        
        super(FrameSweep, self).__init__(viewports=[self.viewport])
        self.parameters.handle_event_callbacks = [(pygame.locals.QUIT, self.quit_callback),
                                                  (pygame.locals.KEYDOWN, self.keydown_callback),
                                                  (pygame.locals.KEYUP, self.keyup_callback)]

    def create_viewport(self):
        """ Called by FrameSweep initiate method. Create viewports for different stimuli on specific display.
            Override this method in subclasses.
        """
        raise RuntimeError("%s: Definition of create_viewport() in abstract base class FrameSweep must be overriden."%(str(self),))
    
    def create_stimuli(self):
        """ Called by FrameSweep initiate method. Create stimuli on specific viewport.
            Override this method in subclasses.
        """
        raise RuntimeError("%s: Definition of create_stimuli() in abstract base class FrameSweep must be overriden."%(str(self),))

    
    def keydown_callback(self,event):
        if event.key == pygame.locals.K_ESCAPE:
            self.quit_callback(event)
        elif event.key == pygame.locals.K_UP:
            self.up = 1
        elif event.key == pygame.locals.K_DOWN:
            self.down = 1
        elif event.key == pygame.locals.K_RIGHT:
            self.right = 1
        elif event.key == pygame.locals.K_LEFT:
            self.left = 1
            
    def keyup_callback(self,event):
        if event.key == pygame.locals.K_UP:
            self.up = 0
        elif event.key == pygame.locals.K_DOWN:
            self.down = 0
        elif event.key == pygame.locals.K_RIGHT:
            self.right = 0
        elif event.key == pygame.locals.K_LEFT:
            self.left = 0
            
    def quit_callback(self,event):
        self.parameters.go_duration = (0,'frames')

    def go(self):
#        """Does 2 buffer swaps, each followed by a glFlush call
#        This ensures that all following swap_buffers+glFlush call pairs
#        return on the vsync pulse from the video card. This is a workaround
#        for strange OpenGL behaviour. See Sol Simpson's 2007-01-29 post on
#        the visionegg mailing list"""
        for dummy in range(2):
            VisionEgg.Core.swap_buffers() # returns immediately
            gl.glFlush() # if this is the first buffer swap, returns immediately, otherwise waits for next vsync pulse from video card
        
        """ Pre-stimulus go"""    
        self.parameters.go_duration = (self.sweeptable.static.preframesweepSec, 'seconds')
        super(FrameSweep, self).go()
        """ Stimulus go"""
        self.parameters.go_duration=('forever','')
        # add fundamental sweep controllers such as pause and quit
        #TODO: add pause_sweep_controllers
        quit_sweep_controller = QuitSweepController(sweeptable=self.sweeptable,framesweep=self)
        self.add_controller(None,None,quit_sweep_controller)
        self.add_stimulus_controllers()
        super(FrameSweep, self).go()
        self.remove_controller(None,None,None)
        """ Post-stimulus go"""    
        self.parameters.go_duration = (self.sweeptable.static.postframesweepSec, 'seconds')
        super(FrameSweep, self).go()
        
        self.screen.close()
