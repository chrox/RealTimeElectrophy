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

from SweepController import SweepController
from Core import Viewport

class QuitSweepController(SweepController):
    """ Quit the frame sweep loop if there is no viewports in the screen.
    """
    def during_go_eval(self):
        if self.framesweep.parameters.viewports == []:
            self.framesweep.parameters.go_duration = (0, 'frames')

class RemoveViewportController(SweepController):
    """ 
        Check each viewport. If all stimuli complete sweep, delete the viewport.
    """
    def during_go_eval(self):
        p = self.framesweep.parameters
        # assign to the real screen if the screen param is a dummy screen
        # remove the viewport if all the stimuli in the viewport has completed its sweep
        for viewport in p.viewports:
            viewport_cleaned = True
            for stimulus in viewport.parameters.stimuli:
                viewport_cleaned &= stimulus.sweep_completed
            if viewport_cleaned:
                Viewport.registered_viewports.remove(viewport)
                self.framesweep.parameters.viewports.remove(viewport)
                
class EventHandlerController(SweepController):
    """ Per viewport control of the stimulus event handler.
        If the stimulus is active then attach its event handlers to framesweep.
    """
    def during_go_eval(self):
        p = self.framesweep.parameters
        for viewport in p.viewports:
            for stimulus in viewport.parameters.stimuli:
                if hasattr(stimulus,'event_handlers'):
                    for event_handler in stimulus.event_handlers:
                        if event_handler not in p.handle_event_callbacks and viewport.active:
                            p.handle_event_callbacks.append(event_handler)
                        elif event_handler in p.handle_event_callbacks and not viewport.active:
                            p.handle_event_callbacks.remove(event_handler)

class FrameSweep(VisionEgg.FlowControl.Presentation):
    """ FrameSweep is a subclass of VisionEgg Presentation.The FrameSweep maintains the relationships among stimulus, viewport
        and screen. And it takes the responsibility for keeping proper order of these objects for VisionEgg presentation go method.
    """
    def __init__(self):
        # buffer is used to add delayed controllers so that presweep go don't call the controllers.
        self.stimulus_pool = []
        
        # presentation state variables
        self.quit = False
        self.paused = False
        
        super(FrameSweep, self).__init__(go_duration=('forever',''))
        self.parameters.handle_event_callbacks = [(pygame.locals.QUIT, self.quit_callback),
                                                  (pygame.locals.KEYDOWN, self.keydown_callback),
                                                  (pygame.locals.KEYUP, self.keyup_callback)]
        self.add_controller(None, None, EventHandlerController(self))
        self.add_controller(None, None, RemoveViewportController(self))
        self.add_controller(None, None, QuitSweepController(self))

    def add_stimulus(self, stimulus):
        """ The main maniputate interface of framesweep.
            Update the stimulus in viewport and viewport in framesweep.
        """
        self.stimulus_pool.append(stimulus)
        p = self.parameters
        # add new viewports in sweep screen
        if not hasattr(stimulus,'viewport'):
            stimulus.viewport = Viewport(name='control')
        if not hasattr(stimulus,'sweep_completed'):
            stimulus.sweep_completed = False
        stimulus.viewport.parameters.stimuli.append(stimulus)
        # for a new viewport not registered in the screen
        if stimulus.viewport.name not in [viewport.name for viewport in p.viewports]:
            Viewport.registered_viewports.append(stimulus.viewport)
            p.viewports.append(stimulus.viewport)
            p.handle_event_callbacks += stimulus.viewport.event_handlers 
        # there is already one viewport with the same viewport name
        else:
            for viewport in p.viewports:
                if stimulus.viewport.name == viewport.name:
                    viewport.parameters.stimuli.append(stimulus)
            
    def add_controllers(self):
        """ Update the controllers in framesweep. The controller of each stimulus should be delayed to add into the sweep.
            In case we have pre stimulus delay.
        """ 
        for stimulus in self.stimulus_pool:
            if hasattr(stimulus,'controllers'):
                for controller in stimulus.controllers:
                    if controller not in self.controllers:
                        self.controllers.append((None,None,controller))
        
    def keydown_callback(self,event):
        if event.key == pygame.locals.K_ESCAPE:
            self.quit_callback(event)
            
    def keyup_callback(self,event):
        pass
            
    def quit_callback(self,event):
        self.parameters.go_duration = (0,'frames')

    def go(self,prestim=None,poststim=None):
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

        
