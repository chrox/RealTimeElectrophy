# Demo program using WhiteNoise.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division

from StimControl.LightStim.SweepSeque import dictattr, SparseNoiseSeque
from StimControl.LightStim.WhiteNoise import WhiteNoise
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Core import DefaultScreen

DefaultScreen(['left','right'])

p = dictattr()

# pre-experiment duration to display blank screen (sec)
preframesweepSec = 1.0
# post-experiment duration to display blank screen (sec)
postframesweepSec = 1.0

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

noise_sequence = SparseNoiseSeque(repeat=8, x_index=x_index, y_index=y_index, contrast=contrast, frame_duration=p.sweepSec, blank_duration=p.postsweepSec)

stimulus_left = WhiteNoise(viewport='left', params=p, sweepseq=noise_sequence)

sweep = FrameSweep()
sweep.add_stimulus(stimulus_left)
sweep.go(preframesweepSec, postframesweepSec)
