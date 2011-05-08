#!/usr/bin/env python
"""  """
# Copyright (c) 2010-2011 HuangXin.  Distributed under the terms
# of the GNU Lesser General Public License (LGPL).
import os

import OpenGL.GL as gl
import pygame.display
import platform

import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
import VisionEgg.Core
import VisionEgg.MoreStimuli

import SweepTable
from LightStim import SCREENWIDTH,SCREENHEIGHT,deg2pix
from SweepController import SweepTableController


class FrameSweep(VisionEgg.FlowControl.Presentation):
    """ Per frame visual stimulus generator"""
    def __init__(self, static, dynamic, variables, runs=None, blanksweeps=None):
        self.sweeptable = SweepTable.SweepTable(static, dynamic, variables, runs, blanksweeps)

        self.xorig = deg2pix(self.sweeptable.static.origDeg[0]) + SCREENWIDTH / 2  # do this once, since it's static, save time in main loop
        self.yorig = deg2pix(self.sweeptable.static.origDeg[1]) + SCREENHEIGHT / 2
        
        self.createscreen()
        self.createstimuli()
        self.createviewport()
                
        self.quit = False
        self.pause = False # init pause signal
        self.paused = False # remembers whether this experiment has been paused
        
        # key state global variables
        self.up = 0
        self.down = 0
        self.left = 0
        self.right = 0
        
        super(FrameSweep, self).__init__(viewports=[self.viewport])
        self.parameters.handle_event_callbacks = [(pygame.locals.QUIT, self.quit_callback),
                                                  (pygame.locals.KEYDOWN, self.keydown_callback),
                                                  (pygame.locals.KEYUP, self.keyup_callback)]
        
    def createscreen(self):
        # Init OpenGL graphics screen
        pygame.display.init()
        dispinfo = pygame.display.Info()
        pygame.display.quit()
        # Make sure that SDL_VIDEO_WINDOW_POS takes effect.
        VisionEgg.config.VISIONEGG_FRAMELESS_WINDOW = 0
        system = platform.system()
        if system == 'Linux':
            #os.environ['SDL_VIDEO_WINDOW_POS']="%u,0" %(dispinfo.current_w - 800)
            os.environ['SDL_VIDEO_WINDOW_POS']="%u,0" %(0)
        else:
            os.environ['SDL_VIDEO_WINDOW_POS']="%u,0" %(dispinfo.current_w)
        self.screen = VisionEgg.Core.Screen(size=(800,600), frameless=True, hide_mouse=True, alpha_bits=8)
        
    def createstimuli(self):
        """Creates the VisionEgg stimuli objects common to all Experiment subclasses"""
        self.background = VisionEgg.MoreStimuli.Target2D(position=(SCREENWIDTH/2, SCREENHEIGHT/2),
                                   anchor='center',
                                   size=(SCREENWIDTH, SCREENHEIGHT),
                                   on=True)

        self.bgp = self.background.parameters # synonym
        #set background color before real sweep
        bgb = self.sweeptable.static.bgbrightness # get it for sweep table index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        
    def createviewport(self):
        self.viewport = VisionEgg.Core.Viewport(screen=self.screen, stimuli=self.stimuli)
    
#    def saveparams(self):
#        """Called by FrameSweep. Save stimulus parameters when exits FrameSweep go loop.
#
#        Override this method in subclasses."""
#        raise RuntimeError("%s: Definition of saveparams() in abstract base class FrameSweep must be overriden."%(str(self),))
    
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
        """TODO: add pause_sweep_controllers"""
        quit_sweep_controller = QuitSweepController(sweeptable=self.sweeptable,framesweep=self)
        self.add_controller(None,None,quit_sweep_controller)
        self.add_stimulus_controllers()
        super(FrameSweep, self).go()
        self.remove_controller(None,None,None)
        """ Post-stimulus go"""    
        self.parameters.go_duration = (self.sweeptable.static.postframesweepSec, 'seconds')
        super(FrameSweep, self).go()
        
        self.screen.close()

class QuitSweepController(SweepTableController):
    def __init__(self,sweeptable=None,framesweep=None):
        super(QuitSweepController, self).__init__(sweeptable=sweeptable)
        self.framesweep = framesweep
    def during_go_eval(self):
        index = self.next_index()
        """If vsynctable runs to an end, quit the sweep right away."""
        if index == None:
            self.framesweep.parameters.go_duration = (0,'frames')
