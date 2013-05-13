# Grating used by SED experiment
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import math
from Grating import Grating
from SweepController import StimulusController

class PositionController(StimulusController):
    # Set bar orientation
    def __init__(self,*args,**kwargs):
        super(PositionController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
    def during_go_eval(self):
        fix_position = self.viewport.deg2pix(self.p.xorigDeg) + self.viewport.xorig ,\
                       self.viewport.deg2pix(self.p.yorigDeg) + self.viewport.yorig
        
        posRad = (self.p.posDeg % 360)/180 * math.pi
        radius = self.p.radius
        self.gp.position = fix_position[0] + math.cos(posRad) * self.viewport.deg2pix(radius) ,\
                           fix_position[1] + math.sin(posRad) * self.viewport.deg2pix(radius)

class SEDGrating(Grating):
    def __init__(self, params, subject, **kwargs):
        super(SEDGrating, self).__init__(params=params, subject=subject, **kwargs)
        self.name = 'sedgrating'
        self.param_names += ['posDeg','radius']
        self.defalut_parameters.update({'posDeg':0.0,
                                        'radius':2.0,})
        
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        
    def register_controllers(self):
        super(SEDGrating, self).register_controllers()
        self.controllers.append(PositionController(self))
        