# This module contains the main class of LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import pygame
import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()

from SweepController import QuitSweepController,CheckViewportController

class FrameSweep(VisionEgg.FlowControl.Presentation):
    """ FrameSweep is a subclass of VisionEgg Presentation.The FrameSweep maintains the relationships among stimulus, viewport
        and screen. And it takes the responsibility for keeping proper order of these objects for VisionEgg presentation go method.
    """
    def __init__(self):
        # buffer is used to add delayed controllers so that presweep go don't call the controllers.
        self.stimuli_buffer = []
        
        # presentation state variables
        self.quit = False
        self.paused = False
        
        super(FrameSweep, self).__init__(go_duration=('forever',''))
        self.parameters.handle_event_callbacks = [(pygame.locals.QUIT, self.quit_callback),
                                                  (pygame.locals.KEYDOWN, self.keydown_callback),
                                                  (pygame.locals.KEYUP, self.keyup_callback)]
        self.add_controller(None, None, CheckViewportController(self))
        self.add_controller(None, None, QuitSweepController(self))

    def add_stimulus(self, stimulus):
        """ Update the stimulus in viewport and viewport in framesweep.
        """
        self.stimuli_buffer.append(stimulus)
        p = self.parameters
        # add new viewports in sweep screen
        if stimulus.viewport not in p.viewports:
            p.viewports.append(stimulus.viewport)
    def add_controllers(self):
        """ Update the controllers in framesweep.
        """
        for stimulus in self.stimuli_buffer:
            for controller in stimulus.controllers:
                self.controllers.append((None,None,controller))
                
    def attach_event_handlers(self):
        """ Update the event handlers in framesweep.
        """
        for stimulus in self.stimuli_buffer:
            self.parameters.handle_event_callbacks += stimulus.event_handlers
        
    def keydown_callback(self,event):
        if event.key == pygame.locals.K_ESCAPE:
            self.quit_callback(event)
            
    def keyup_callback(self,event):
        pass
            
    def quit_callback(self,event):
        self.parameters.go_duration = (0,'frames')

    def go(self,prestim=None,poststim=0):
        # pre stimulation go
        if prestim is not None:
            self.parameters.go_duration = (prestim, 'seconds')
            super(FrameSweep, self).go()
        # stimulation go
        self.parameters.go_duration=('forever','')
        self.add_controllers()
        super(FrameSweep, self).go()
        # post stimulation go
        if poststim is not None:
            self.remove_controller(None,None,None)
            self.parameters.go_duration = (poststim, 'seconds')
            super(FrameSweep, self).go()

        
