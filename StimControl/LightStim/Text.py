# Text stimulus
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

# Taget stimuli
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from VisionEgg.Text import Text
from LightData import dictattr
from Core import Stimulus

class Hint(Stimulus):
    def __init__(self, params, **kwargs):
        super(Hint, self).__init__(params=params, **kwargs)
        self.name = 'hint'
        self.parameters = dictattr()
        self.set_parameters(self.parameters, params)
        
        self.make_stimuli()
    def make_stimuli(self):
        position = self.viewport.deg2pix(self.parameters.xorigDeg) + self.viewport.xorig ,\
                   self.viewport.deg2pix(self.parameters.yorigDeg) + self.viewport.yorig
        self.text = Text(text=self.parameters.text,
                    position=position,
                    color=self.parameters.color,
                    font_size=self.parameters.fontsize,
                    anchor='center')
        self.stimuli = [self.text]