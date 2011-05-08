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
from VisionEgg.MoreStimuli import Target2D

from LightStim import SCREENWIDTH,SCREENHEIGHT,sec2vsync,sec2intvsync,deg2pix
from SweepController import SweepStampController,SweepTableController
from SweepStamp import DT,DTBOARDINSTALLED,MAXPOSTABLEINT,SWEEP
from SweepTable import SweepTable

class FrameSweep(VisionEgg.FlowControl.Presentation):
    """ Per frame visual stimulus generator"""
    def __init__(self, static, dynamic, variables, runs=None, blanksweeps=None):
        self.sweeptable = SweepTable(static, dynamic, variables, runs, blanksweeps)

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
        
        super(FrameSweep, self).__init__(go_duration=('forever',''),viewports=[self.viewport])
        self.parameters.handle_event_callbacks = [(pygame.locals.QUIT, self.quit_presentation),
                                       (pygame.locals.KEYDOWN, self.keydown),
                                       (pygame.locals.KEYUP, self.keyup)]
        self.add_all_controllers()
        
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
        self.background = Target2D(position=(SCREENWIDTH/2, SCREENHEIGHT/2),
                                   anchor='center',
                                   size=(SCREENWIDTH, SCREENHEIGHT),
                                   on=True)

        self.bgp = self.background.parameters # synonym  
        
    def createviewport(self):
        self.viewport = VisionEgg.Core.Viewport(screen=self.screen, stimuli=self.stimuli)
    
    def staticscreen(self, nvsyncs, postval=MAXPOSTABLEINT):
        """Display whatever's defined in the viewport on-screen for nvsyncs,
        and posts postval to the port. Adds ticks to self.vsynctimer"""
        #assert nvsyncs >= 1 # nah, let it take nvsyncs=0 and do nothing and return right away
        vsynci = 0
        if self.pause and nvsyncs == 0:
            nvsyncs = 1 # need at least one vsync to get into the while loop and pause the stimulus indefinitely
        while vsynci < nvsyncs: # need a while loop for pause to work
#            for event in pygame.event.get(): # for all events in the event queue
#                if event.type == pygame.locals.KEYDOWN:
#                    if event.key == pygame.locals.K_ESCAPE:
#                        self.quit = True
#                    if event.key == pygame.locals.K_PAUSE:
#                        self.pause = not self.pause # toggle pause
#                        self.paused = True
            if self.quit:
                break # out of vsync loop
            if self.pause: # indicate pause to Surf
                if DTBOARDINSTALLED: DT.clearBitsNoDelay(SWEEP) # clear sweep bit low, no delay
            else: # post value to port
                if DTBOARDINSTALLED:
                    DT.setBitsNoDelay(SWEEP) # make sure it's high
                    DT.postInt16NoDelay(postval) # post value to port, no delay
                    self.nvsyncsdisplayed += 1 # increment. Count this as a vsync that Surf has seen
            self.screen.clear()
            self.viewport.draw()
            VisionEgg.Core.swap_buffers() # returns immediately
            gl.glFlush() # waits for next vsync pulse from video card
            #self.vsynctimer.tick()
            vsynci += int(not self.pause) # don't increment if in pause mode
        if DTBOARDINSTALLED: DT.clearBits(SWEEP) # be tidy, clear sweep bit low, delay to make sure Surf sees the end of this sweep

    
    def saveparams(self):
        """Called by FrameSweep. Save stimulus parameters when exits FrameSweep go loop.

        Override this method in subclasses."""
        raise RuntimeError("%s: Definition of saveparams() in abstract base class FrameSweep must be overriden."%(str(self),))
    
    def keydown(self,event):
        if event.key == pygame.locals.K_ESCAPE:
            self.quit_presentation(event)
        elif event.key == pygame.locals.K_UP:
            self.up = 1
        elif event.key == pygame.locals.K_DOWN:
            self.down = 1
        elif event.key == pygame.locals.K_RIGHT:
            self.right = 1
        elif event.key == pygame.locals.K_LEFT:
            self.left = 1
            
    def keyup(self,event):
        if event.key == pygame.locals.K_UP:
            self.up = 0
        elif event.key == pygame.locals.K_DOWN:
            self.down = 0
        elif event.key == pygame.locals.K_RIGHT:
            self.right = 0
        elif event.key == pygame.locals.K_LEFT:
            self.left = 0
            
    def quit_presentation(self,event):
        self.parameters.go_duration = (0,'frames')

    def go(self):
        
        #set background color before real sweep
        bgb = self.sweeptable.static.bgbrightness # get it for sweep table index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        """Does 2 buffer swaps, each followed by a glFlush call
        This ensures that all following swap_buffers+glFlush call pairs
        return on the vsync pulse from the video card. This is a workaround
        for strange OpenGL behaviour. See Sol Simpson's 2007-01-29 post on
        the visionegg mailing list"""
        for dummy in range(2):
            VisionEgg.Core.swap_buffers() # returns immediately
            gl.glFlush() # if this is the first buffer swap, returns immediately, otherwise waits for next vsync pulse from video card
        
        # Do pre-experiment delay
        self.staticscreen(sec2vsync(self.sweeptable.static.presweepSec))
        
        super(FrameSweep, self).go()
        
        # Do post-experiment delay
        self.staticscreen(sec2vsync(self.sweeptable.static.postsweepSec))
        
        self.saveparams()
        self.screen.close()
