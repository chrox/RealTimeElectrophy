# Disparity threshold experiment
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.Target import Fixation
from StimControl.LightStim.RandomDots import RandomDots, StereoDisc
from StimControl.LightStim.Text import Hint

import random
import pygame
import VisionEgg
import VisionEgg.ParameterTypes as ve_types
from VisionEgg.DaqKeyboard import KeyboardInput
from VisionEgg.ResponseControl import KeyboardResponseController

DefaultScreen(['left','right'],bgcolor=(0.5,0.5,0.5))

class KeyDirectionInput(KeyboardInput):
    def get_string_data(self):
        """Get keyboard input (return values are converted to keyboard symbols (strings))."""
        pressed = self.get_pygame_data()
        keys_pressed = []
        for k in pressed: # Convert integers to keyboard symbols (strings)
            name = pygame.key.name(k)
            if name in ("left","right","up","down"):
                keys_pressed.append(name)
        return keys_pressed
        
class MouseDirectionInput():
    def get_string_data(self):
        buttons = pygame.mouse.get_pressed()
        pressed = [k for k, v in enumerate(buttons) if v]
        buttons_pressed = []
        buttons_map = ("left_button","middle_button","right_button")
        for button in pressed: # Convert integers to keyboard symbols (strings)
            buttons_pressed.append(buttons_map[button])
        return buttons_pressed
    
class LeftRightKeyResponse(KeyboardResponseController):
    """Use the keyboard to collect responses during a presentation is running."""

    def __init__(self, sweep):
        VisionEgg.FlowControl.Controller.__init__(self,
            return_type=ve_types.get_type(None),
            eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME,
            temporal_variables=VisionEgg.FlowControl.Controller.TIME_SEC_SINCE_GO
        )
        self.input = KeyDirectionInput()
        self.sweep = sweep
        
    def during_go_eval(self):
        super(LeftRightKeyResponse, self).during_go_eval()
        if len(self.responses) > 0:
            self.sweep.parameters.go_duration = (0,'frames')
            
class LeftRightMouseResponse(LeftRightKeyResponse):
    def __init__(self, sweep):
        VisionEgg.FlowControl.Controller.__init__(self,
            return_type=ve_types.get_type(None),
            eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME,
            temporal_variables=VisionEgg.FlowControl.Controller.TIME_SEC_SINCE_GO
        )
        self.input = MouseDirectionInput()
        self.sweep = sweep
    
    def during_go_eval(self):
        super(LeftRightMouseResponse, self).during_go_eval()
        pygame.mouse.set_pos([400, 300])

class Disparity(object):
    def __init__(self, subject):
        """ Fixation """
        fp = dictattr()
        fp.bgbrightness = 0.5
        fp.color = (1.0, 0.0, 0.0, 1.0)
        fp.width = 0.25
        
        self.fixation_left = Fixation(viewport='left', subject=subject, params=fp)
        self.fixation_right = Fixation(viewport='right', subject=subject, params=fp)        
        
        """ Random Dots with disc"""
        dp = dictattr()
        dp.bgbrightness = 0.5
        dp.antialiase = True
        
        dp.dotsNumber = 2000
        dp.dotSquareWidth = 7.5
        dp.randomSeed = 0
        dp.discDistDeg = 2.5
        dp.discDiameter = 1.25
        dp.disparity = 0
        dp.discsize = 1.5
        
        self.disc_left = StereoDisc(viewport='left', subject=subject, params=dp)
        self.disc_right = StereoDisc(viewport='right', subject=subject, params=dp)
        
        """ Mask: Random Dots """
        mp = dictattr()
        mp.bgbrightness = 0.5
        mp.antialiase = True
        
        mp.dotsNumber = 3000
        mp.dotSquareWidth = 7.5
        mp.randomSeed = 1
        
        self.mask_left = RandomDots(viewport='left', subject=subject, params=mp)
        self.mask_right = RandomDots(viewport='right', subject=subject, params=mp)
        
        """ Hint """
        hp = dictattr()
        hp.bgbrightness = 0.5
        hp.text = "Press left or right for disc interval."
        hp.xorigDeg = 5.0
        hp.yorigDeg = 0.0
        hp.color = (1.0, 0.0, 0.0, 1.0)
        hp.fontsize = 25
        self.hint_left = Hint(viewport="left", params=hp)
        hp.xorigDeg = -5.0
        self.hint_right = Hint(viewport="right", params=hp)
        
        self.sweep = FrameSweep()
        self.key_response = LeftRightKeyResponse(self.sweep)
        self.mouse_response = LeftRightMouseResponse(self.sweep)        
    
    def set_disparity(self, disp):
        self.disparity = disp
    
    def update_disparity(self, cross):
        if random.choice([True, False]):
            self.disc_left.parameters.disparity = self.disparity if cross else 0
            self.disc_right.parameters.disparity = 0
        else:
            self.disc_left.parameters.disparity = 0
            self.disc_right.parameters.disparity = self.disparity if cross else 0
    
    def get_cross_interval(self):
        return self.cross_interval
    
    def run(self):
        random.seed()
        self.cross_interval = random.choice([1,2])
        """ Fixation """
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(2.0,'seconds'))
        """ Interval-1 """
        self.update_disparity(self.cross_interval == 1)
        self.sweep.add_stimulus(self.disc_left)
        self.sweep.add_stimulus(self.disc_right)
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(0.2,'seconds'))
        """ Blank """
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(0.4,'seconds'))
        """ Interval-2 """
        self.update_disparity(self.cross_interval == 2)
        self.sweep.add_stimulus(self.disc_left)
        self.sweep.add_stimulus(self.disc_right)
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(0.2,'seconds'))
        """ Blank """
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(0.4,'seconds'))
        """ Mask """
        self.sweep.add_stimulus(self.mask_left)
        self.sweep.add_stimulus(self.mask_right)
        self.sweep.go(duration=(0.5,'seconds'))
        
        self.sweep.add_controller(None, None, self.key_response)
        self.sweep.add_controller(None, None, self.mouse_response)
        #self.sweep.add_stimulus(self.hint_left)
        #self.sweep.add_stimulus(self.hint_right)
        self.sweep.go(duration=('forever',''))
        key_response = self.key_response.get_last_response_since_go()
        mouse_response = self.mouse_response.get_last_response_since_go()
        if key_response == "left" or mouse_response == "left_button":
            return self.cross_interval == 1
        elif key_response == "right" or mouse_response == "right_button":
            return self.cross_interval == 2
        else:
            raise RuntimeError("Key or button press is not direction.")
