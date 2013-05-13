# Sensory Eye Dominance(SED) experiment
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.Target import Fixation
from StimControl.LightStim.SEDGrating import SEDGrating
from StimControl.LightStim.Plaid import Plaid
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

class SED(object):
    def __init__(self, subject, eye):
        """ Fixation """
        fp = dictattr()
        fp.bgbrightness = 0.5
        fp.color = (1.0, 0.0, 0.0, 1.0)
        fp.width = 0.25
        
        self.fixation_left = Fixation(viewport='left', subject=subject, params=fp)
        self.fixation_right = Fixation(viewport='right', subject=subject, params=fp)
        
        """ SED Grating """
        gp = dictattr()
        gp.bgbrightness = 0.5
        gp.on = True
        gp.mask = "circle"
        gp.ml = 0.5
        gp.sfreqCycDeg = 3.0
        gp.tfreqCycSec = 0.0
        gp.phase0 = 0
        gp.contrast = 0.5
        gp.ori = 0.0
        gp.maskDiameterDeg = 1.25
        gp.radius = 2.0
        
        self.grating_left = SEDGrating(viewport='left', subject=subject, params=gp)
        gp.ori = 90.0
        self.grating_right = SEDGrating(viewport='right', subject=subject, params=gp)
        
        """ Mask """
        mp = dictattr()
        mp.bgbrightness = 0.5
        mp.ml = (0.5, 0.5)
        mp.ori = (0.0, 90.0)
        mp.sfreqCycDeg = (3.0, 3.0)
        mp.tfreqCycSec = (0.0, 0.0)
        
        self.plaid_left = Plaid(viewport="left", params=mp)
        self.plaid_right = Plaid(viewport="right", params=mp)
        
        """ Hint """
        hp = dictattr()
        hp.bgbrightness = 0.5
        hp.text = "Press left(right) or up(down) for grating orientation."
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
        
        self.test_eye = eye
        
    def update_orientation(self):
        self.test_eye_ori = random.choice([0, 90])
        if self.test_eye == "left":
            self.grating_left.parameters.ori = self.test_eye_ori
            self.grating_right.parameters.ori = abs(self.test_eye_ori - 90)
        else:
            self.grating_left.parameters.ori = abs(self.test_eye_ori - 90)
            self.grating_right.parameters.ori = self.test_eye_ori
        # if self.test_eye == "left":
            # self.grating_left.parameters.ori = self.orientation["test"][0]
            # self.grating_right.parameters.ori = self.orientation["control"][0]
        # else:
            # self.grating_left.parameters.ori = self.orientation["control"][0]
            # self.grating_right.parameters.ori = self.orientation["test"][0]

    def update_test_contrast(self, contrast):
        if self.test_eye == "left":
            self.grating_left.parameters.contrast = contrast
        elif self.test_eye == "right":
            self.grating_right.parameters.contrast = contrast
            
    def update_control_contrast(self, contrast):
        if self.test_eye == "left":
            self.grating_right.parameters.contrast = contrast
        elif self.test_eye == "right":
            self.grating_left.parameters.contrast = contrast
            
    def get_test_eye(self):
        return self.test_eye
    
    def get_test_eye_orientation(self):
        if self.test_eye_ori == 0:
            return "horizontal"
        else:
            return "vertical"
        #return self.orientation["test"][1]
    
    def run(self):
        #self.sweep = FrameSweep()
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(2.0,'seconds'))
        self.sweep.add_stimulus(self.grating_left)
        self.sweep.add_stimulus(self.grating_right)
        self.sweep.add_stimulus(self.fixation_left)
        self.sweep.add_stimulus(self.fixation_right)
        self.sweep.go(duration=(0.5,'seconds'))
        self.sweep.add_stimulus(self.plaid_left)
        self.sweep.add_stimulus(self.plaid_right)
        self.sweep.go(duration=(0.2,'seconds'))
        self.sweep.add_controller(None, None, self.key_response)
        self.sweep.add_controller(None, None, self.mouse_response)
        #self.sweep.add_stimulus(self.hint_left)
        #self.sweep.add_stimulus(self.hint_right)
        self.sweep.go(duration=('forever',''))
        key_response = self.key_response.get_last_response_since_go()
        mouse_response = self.mouse_response.get_last_response_since_go()
        if key_response in ("left", "right") or mouse_response == "left_button":
            return "horizontal"
        elif key_response in ("up", "down") or mouse_response == "right_button":
            return "vertical"            
        else:
            raise RuntimeError("Key or button press is not direction.")
