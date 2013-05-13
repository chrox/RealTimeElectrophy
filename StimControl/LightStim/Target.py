# Taget stimuli
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot
from Core import Stimulus

class Fixation(Stimulus):
    def __init__(self, params, subject, **kwargs):
        super(Fixation, self).__init__(subject=subject, **kwargs)
        self.name = 'fixation'
        self.param_names += ['xorigDeg','yorigDeg']
        self.defalut_parameters.update({'xorigDeg':0.0,
                                        'yorigDeg':0.0,})
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        
        self.make_stimuli()
        
    def make_stimuli(self):
        position = self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig ,\
                   self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig
        width = self.viewport.deg2pix(self.parameters.width)
        self.fixation = FixationSpot(position=position,
                                     color=self.parameters.color,
                                     size=(width, width),
                                     anchor='center',
                                     on=True)
        self.stimuli = [self.fixation]

class Nonius(Stimulus):
    def __init__(self, params, **kwargs):
        super(Nonius, self).__init__(**kwargs)
        self.name = 'nonius'
        self.set_parameters(self.parameters, params)
        
        self.make_stimuli()
        
    def make_stimuli(self):
        width = self.viewport.deg2pix(self.parameters.width)
        thickness = self.viewport.deg2pix(self.parameters.thickness)
        nonius_h_position = self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig ,\
                            self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig
        if self.parameters.direction == "up":
            v_position = -width/2
        elif self.parameters.direction == "down":
            v_position = width/2
        nonius_v_position = self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig ,\
                            self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig + v_position
        
            
        self.nonius_h = Target2D(position=nonius_h_position,
                                    anchor='center',
                                    size=(width, thickness),
                                    on=True)
        self.nonius_h.parameters.bgbrightness = (1.0,1.0,1.0,1.0)
        self.nonius_v = Target2D(position=nonius_v_position,
                                    anchor='center',
                                    size=(thickness, width),
                                    on=True)
        self.nonius_v.parameters.bgbrightness = (1.0,1.0,1.0,1.0)
        self.stimuli = [self.nonius_h, self.nonius_v]
        