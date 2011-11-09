# 
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import copy
import itertools
import logging
import pygame
from pygame.locals import K_h
import LightStim.Core
from LightStim.Core import Viewport

class ManViewport(LightStim.Core.Viewport):
    # add event control callback
    def __init__(self,**kwargs):
        super(ManViewport, self).__init__(**kwargs)
        self.active = True
        if self.get_name() == 'control':
            self.visible = True
            self.current = True
        else:
            self.visible = False
            self.current = False
        
        self.viewport_alted_once = False
        self.copied_stimuli = None
        self.copied_parameters = {}
        self.event_handlers = [(pygame.locals.KEYDOWN, self.keydown_callback),
                               (pygame.locals.MOUSEBUTTONDOWN, self.mousebuttondown_callback)]
        #self.viewport_event_handlers = [(pygame.locals.KEYDOWN, self.keydown_callback)]

    def draw(self):
        if not self.is_active() or not self.is_visible():
            return
        if not self.viewport_alted_once and self.get_name() == 'control':
            self.viewport_alted_once = True
            self.__alt_viewport()
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
        
    def __copy_stimuli(self, src_viewport_name):
        # copy stimuli from source viewport and register the stimuli in this viewport.
        src_viewports = [viewport for viewport in Viewport.registered_viewports if viewport.get_name() == src_viewport_name]
        if src_viewports == []:
            raise RuntimeError("Cannot find source viewport " + src_viewports + ' in registered viewports.')
        src_viewport = src_viewports[0]
        self.copied_stimuli = []
        for stimulus in src_viewport.parameters.stimuli:
            cloned_stimulus = copy.copy(stimulus)  # Explicit is better than implicit.
            #cloned_stimulus = stimulus
            self.copied_stimuli.append(cloned_stimulus)
        
    def __paste_stimuli(self, dest_viewport_name):
        # if this viewport has rigistered stimuli then use those stimuli to substitude stimuli in destined viewport.
        dest_viewports = [viewport for viewport in Viewport.registered_viewports if viewport.get_name() == dest_viewport_name]
        if dest_viewports == []:
            raise RuntimeError("Cannot find destined viewport " + dest_viewport_name + ' in registered viewports.')
        dest_viewport = dest_viewports[0]
        dest_viewport.parameters.stimuli = []
        for stimulus in self.copied_stimuli:
            stimulus.update_viewportcontroller(dest_viewport)
            if dest_viewport.get_name() == 'control':
                assert hasattr(stimulus,'complete_stimuli')
                stimulus.stimuli = stimulus.complete_stimuli
                stimulus.on = True # in control viewport it's not necessary to hide a stimulus
            dest_viewport.parameters.stimuli.append(stimulus)
        
    def __clone_viewport(self, dest_viewport_name, src_viewport_name):
        orignal_copied_stimuli = copy.copy(self.copied_stimuli)
        self.__copy_stimuli(src_viewport_name)
        self.__paste_stimuli(dest_viewport_name)
        self.copied_stimuli = orignal_copied_stimuli

    def __alt_viewport(self):
        # alternate control viewport stimuli from a cycle of available(active) viewports.
        active_viewports = [viewport for viewport in Viewport.registered_viewports if viewport.is_active()]
        current_active_viewports = [viewport for viewport in active_viewports if viewport.is_current()]
        if len(active_viewports) > 1: # there is only control viewport that is active. no need to change viewport.
            if len(current_active_viewports) == 0: # if current viewport is not active make the control the current viewport.
                for viewport in Viewport.registered_viewports:
                    if viewport.get_name() == 'control':
                        viewport.set_current(True)
                    else:
                        viewport.set_current(False)
            viewport_it = itertools.cycle(active_viewports)
            for viewport in viewport_it: 
                if viewport.is_current(): # find next active viewport and make it current viewport.
                    viewport.set_current(False)
                    next_viewport = viewport_it.next()
                    if next_viewport.get_name() == 'control':
                        next_viewport = viewport_it.next()
                    next_viewport.set_current(True)
                    self.__clone_viewport('control',next_viewport.get_name())
                    break
    
    def __copy_stimparams(self):
        current_viewport = [viewport for viewport in Viewport.registered_viewports if viewport.is_current()][0]
        for stimulus in current_viewport.parameters.stimuli:  # save stimuli parameters in control viewport
            if hasattr(stimulus,'get_parameters'):
                self.copied_parameters[type(stimulus).__name__] = stimulus.get_parameters()
                
    def __paste_stimparams(self):
        current_viewport = [viewport for viewport in Viewport.registered_viewports if viewport.is_current()][0]
        for stimulus in current_viewport.parameters.stimuli:
            if hasattr(stimulus,'set_parameters') and type(stimulus).__name__ in self.copied_parameters:
                stimulus.set_parameters(self.copied_parameters[type(stimulus).__name__])

    def __activate_viewport(self, mods, name):
        # set viewport activity and currenty this should have no business with control viewport 
        # if self.is_current(): #  must clear other activity state.
        #     return
        if mods & pygame.locals.KMOD_CTRL:
            if self.get_name() == name:
                self.set_activity(True)
                self.set_current(True)
            elif self.get_name() == 'control':
                self.__clone_viewport('control', name)
            else:
                self.set_activity(False)
                self.set_current(False)
        else:
            if self.is_current():
                pass
            if self.get_name() == name:
                self.set_activity(not self.is_active())
                
    def keydown_callback(self,event):
        mods = pygame.key.get_mods()
        key = event.key

        if key == K_h:
            if not self.get_name() == 'control':
                self.set_visibility(not self.is_visible())
        elif key == pygame.locals.K_F1:
            pass  # control viewport should never be deactivated
        elif key == pygame.locals.K_F2:
            self.__activate_viewport(mods, 'primary')
        elif key == pygame.locals.K_F3:
            self.__activate_viewport(mods, 'left')
        elif key == pygame.locals.K_F4:
            self.__activate_viewport(mods, 'right')
        elif mods & pygame.locals.KMOD_CTRL and key == pygame.locals.K_g: # group active viewports 
            for viewport in Viewport.registered_viewports:
                if viewport.is_active():
                    viewport.set_current(True)
        if self.get_name() == 'control':
            if key == pygame.locals.K_TAB:
                self.__alt_viewport()
            elif mods & pygame.locals.KMOD_CTRL and key == pygame.locals.K_c:
                self.__copy_stimparams()
            elif mods & pygame.locals.KMOD_CTRL and key == pygame.locals.K_v:
                self.__paste_stimparams()
    
    def mousebuttondown_callback(self,event):
        button = event.button
        if button == 1:  # left button
            if self.get_name() == 'left':
                self.set_visibility(not self.is_visible())
        elif button == 2:  # scroll wheel button
            if not self.get_name() == 'control':
                self.set_visibility(not self.is_visible())
        if button == 3:  # right button
            if self.get_name() == 'right':
                self.set_visibility(not self.is_visible())