# Plaid stimulus
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

# Taget stimuli
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from VisionEgg.Gratings import SinGrating2D
from LightData import dictattr
from Core import Stimulus

class Plaid(Stimulus):
    def __init__(self, params, **kwargs):
        super(Plaid, self).__init__(**kwargs)
        self.name = 'plaid'
        self.parameters = dictattr()
        self.set_parameters(self.parameters, params)
        
        self.make_stimuli()
    def make_stimuli(self):
        size = self.viewport.get_size()
        width = max(size)
        self.grating1 = SinGrating2D(anchor='center',
                                    position=(size[0]/2, size[1]/2),
                                    size=(width, width),
                                    pedestal=self.parameters.ml[0],
                                    orientation = self.parameters.ori[0],
                                    spatial_freq = self.viewport.cycDeg2cycPix(self.parameters.sfreqCycDeg[0]),
                                    temporal_freq_hz = self.parameters.tfreqCycSec[0],
                                    max_alpha=0.5,
                                    ignore_time=True,
                                    on=True)
        self.grating2 = SinGrating2D(anchor='center',
                                    position=(size[0]/2, size[1]/2),
                                    size=(width, width),
                                    pedestal=self.parameters.ml[1],
                                    orientation = self.parameters.ori[1],
                                    spatial_freq = self.viewport.cycDeg2cycPix(self.parameters.sfreqCycDeg[1]),
                                    temporal_freq_hz = self.parameters.tfreqCycSec[1],
                                    max_alpha=0.5,
                                    ignore_time=True,
                                    on=True)
        self.stimuli = (self.grating1, self.grating2)
        