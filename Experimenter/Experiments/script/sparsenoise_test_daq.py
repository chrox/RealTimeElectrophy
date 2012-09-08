# Demo program using WhiteNoise.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division

from StimControl.LightStim.SweepSeque import SparseNoiseSeque
from StimControl.LightStim.SweepStamp import SoftStampTrigger
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.WhiteNoise import WhiteNoise,WhiteNoiseSweepStampController
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Core import DefaultScreen
        
eye = 'left'

DefaultScreen(['left','right'])

p = dictattr()

"""Grid settings"""
# grid dimension (x, y)
p.griddim = (32, 32)
# noise magnification fator relative to grid cell size
p.widthmag = 4
p.heightmag = 1
"""Background settings"""
# background brightness (0-1)
p.bgbrightness = 0.5
# screen gamma: None, or single value, or 3-tuple
p.gamma = None
"""CheckBoard settings"""
p.checkbdon = False
p.cbcolormap = 'ggr'

"""Noise settings"""
# sweep duration (sec)
p.sweepSec = 0.04
# post-sweep duration to display blank screen (sec)
p.postsweepSec = 0.0
# noise position index in stimulus grid
x_index = range(p.griddim[0])
y_index = range(p.griddim[1])
contrast = [0,1]

trigger_receiver_host = "127.0.0.1"
trigger_receiver_port = 8118

class WhiteNoiseSoftStampController(WhiteNoiseSweepStampController):
    def __init__(self,host,port,*args,**kwargs):
        super(WhiteNoiseSoftStampController, self).__init__(*args,**kwargs)
        self.soft_trigger = SoftStampTrigger(host,port)
    def post_stamp(self, postval):
        self.soft_trigger.post_stamp(postval)

class Test_WhiteNoise(WhiteNoise):
    def register_controllers(self):
        super(Test_WhiteNoise, self).register_controllers()
        self.controllers.append(WhiteNoiseSoftStampController(trigger_receiver_host,trigger_receiver_port,self))

noise_sequence = SparseNoiseSeque(repeat=8, x_index=x_index, y_index=y_index, contrast=contrast, frame_duration=p.sweepSec, blank_duration=p.postsweepSec)

stimulus_left = Test_WhiteNoise(viewport=eye, params=p, sweepseq=noise_sequence)

sweep = FrameSweep()
sweep.add_stimulus(stimulus_left)
sweep.go(prestim=5.0,poststim=5.0,RSTART=True)
