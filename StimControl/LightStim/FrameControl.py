# This module contains the main class of LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.
import logging
import pygame
import VisionEgg
from Core import Viewport
from LightUtil import TimeFormat
from ManViewport import ManViewport
from SweepController import SweepController,RemoteStartController,RemoteStopController

class QuitSweepController(SweepController):
    """ Quit the frame sweep loop if there is no viewports in the screen.
    """
    def during_go_eval(self):
        if self.framesweep.parameters.viewports == []:
            self.framesweep.parameters.go_duration = (0, 'frames')

class RemoveViewportController(SweepController):
    """ 
        Check each viewport. If all stimuli complete sweep, delete the viewport.
        When all viewports are removed QuitSweepController will quit the main loop.
    """
    def during_go_eval(self):
        p = self.framesweep.parameters
        # assign to the real screen if the screen param is a dummy screen
        # remove the viewport if all the stimuli in the viewport has completed its sweep
        for viewport in p.viewports:
            viewport_cleaned = True
            for stimulus in viewport.parameters.stimuli:
                if hasattr(stimulus, 'sweep_completed'):
                    viewport_cleaned &= stimulus.sweep_completed
                else:
                    pass
            if viewport_cleaned:
                for registered_viewport in Viewport.registered_viewports:
                    if registered_viewport.name == viewport.name:
                        Viewport.registered_viewports.remove(registered_viewport)
                self.framesweep.parameters.viewports.remove(viewport)
                
class EventHandlerController(SweepController):
    """ Per viewport control of the stimulus event handlers.
        Attach viewport event handlers to framesweep.
    """
    def during_go_eval(self):
        p = self.framesweep.parameters
        p.handle_event_callbacks = list(self.framesweep.event_handlers)
        for viewport in p.viewports:
            if hasattr(viewport,'event_handlers'):
                p.handle_event_callbacks += viewport.event_handlers
            if isinstance(viewport,ManViewport) and viewport.is_current():
                for stimulus in viewport.parameters.stimuli:
                    if hasattr(stimulus,'event_handlers'): # update the viewport event handler only when the viewport is the current viewport.
                        p.handle_event_callbacks += stimulus.event_handlers
        
class FrameSweep(VisionEgg.FlowControl.Presentation):
    """ FrameSweep is a subclass of VisionEgg Presentation.The FrameSweep maintains the relationships among stimulus, viewport
        and screen. And it takes the responsibility for keeping proper order of these objects for VisionEgg presentation go method.
    """
    def __init__(self):
        self.logger = logging.getLogger('LightStim.FrameControl')
        # buffer is used to add delayed controllers so that presweep go don't call the controllers.
        self.stimulus_pool = []
        
        # presentation state variables
        self.quit = False
        self.paused = False
        self.interrupted = False
        
        # quit callback list
        self.quit_callbacks = []
        
        super(FrameSweep, self).__init__(go_duration=('forever',''))
        self.event_handlers = [(pygame.locals.QUIT, self.quit_callback),
                               (pygame.locals.KEYDOWN, self.keydown_callback),
                               (pygame.locals.KEYUP, self.keyup_callback)]
        
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
            stimulus.viewport.update_viewport()
            Viewport.registered_viewports.append(stimulus.viewport)
            p.viewports.append(stimulus.viewport)
            #p.handle_event_callbacks += stimulus.viewport.event_handlers 
        # there is already one viewport with the same viewport name
        else:
            for viewport in p.viewports:
                if stimulus.viewport.name == viewport.name:
                    viewport.parameters.stimuli.append(stimulus)
    
    def remove_stimuli(self):
        self.stimulus_pool = []
        p = self.parameters
        for viewport in p.viewports:
            viewport.parameters.stimuli = []
        
    def add_controllers(self):
        """ Update the controllers in framesweep. The controller of each stimulus should be delayed to add into the sweep.
            In case we have pre stimulus delay.
        """
        self.add_controller(None, None, EventHandlerController(self))
        self.add_controller(None, None, RemoveViewportController(self))
        self.add_controller(None, None, QuitSweepController(self))
        for stimulus in self.stimulus_pool:
            if hasattr(stimulus,'controllers'):
                for controller in stimulus.controllers:
                    if controller not in self.controllers:
                        self.controllers.append((None,None,controller))
                        
    def add_quit_callback(self, callback):
        self.quit_callbacks.append(callback)
        
    def keydown_callback(self,event):
        if event.key == pygame.locals.K_ESCAPE:
            self.interrupted = True
            self.quit_callback(event)
            
    def keyup_callback(self,event):
        pass
    
    def quit_callback(self,event):
        for callback in self.quit_callbacks:
            try:
                callback()
            except TypeError:
                self.logger.error('Cannot callback: %s' %str(callback))
        Viewport.registered_viewports = []
        self.parameters.go_duration = (0,'frames')

    def go(self,duration=None,prestim=None,poststim=None,RSTART=False):
        # pre stimulation go
        if prestim is not None:
            if RSTART:
                remote_start_controller = RemoteStartController()
                self.add_controller(None,None,remote_start_controller)
            self.parameters.go_duration = (prestim, 'seconds')
            super(FrameSweep, self).go()
            if RSTART:
                self.remove_controller(None,None,remote_start_controller)
        
        # stimulation go
        if duration is not None:
            self.parameters.go_duration = duration
        else:
            self.parameters.go_duration = ('forever','')
        self.add_controllers()
        # use VisionEgg timing function which handles platform specific problems
        sweep_begin = VisionEgg.true_time_func()
        super(FrameSweep, self).go()
        sweep_end = VisionEgg.true_time_func()
        sweep_duration = sweep_end - sweep_begin
        # remove all stimuli so that post presentation will show nothing.
        self.remove_stimuli()
        # the RemoveViewportController should be moved, otherwise post go will quit directly.
        self.remove_controller(None,None,None)
        
        # post stimulation go
        if poststim is not None:
            if RSTART:
                self.add_controller(None,None,RemoteStopController())
            self.parameters.go_duration = (poststim, 'seconds')
            super(FrameSweep, self).go()
        
        if self.interrupted:
            self.logger.warning('Stimulation was interrupted before completion.')
        else:
            self.logger.info('Stimulation completes successfully.')
        self.logger.info('Actual stimulus duration: %s' %str(TimeFormat(sweep_duration)))
