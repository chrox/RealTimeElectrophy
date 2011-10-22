# Generate random orientation and spatial frequency gratings.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
from LightStim.SweepSeque import dictattr,ParamSeque
from LightStim.FrameControl import FrameSweep
from LightStim.Grating import Grating

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 0.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

orientation = np.linspace(0.0, 180.0, 16)
spatial_freq = np.linspace(0.05, 1.0, 16)
phase = np.linspace(0.0, 360.0, 8)
param_sequence = ParamSeque(repeat=1, orientation=orientation, spatial_freq=spatial_freq, phase=phase, frame_duration=0.1)

random_grating = Grating(viewport='left', params=p, sweepseq=param_sequence)
sweep = FrameSweep()
sweep.add_stimulus(random_grating)
sweep.go()